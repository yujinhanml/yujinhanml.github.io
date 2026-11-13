#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local visual editor for PAR. Saves article HTML, never publishes to GitHub.

python3 tools/par-blog/editor.py --site /private/tmp/par-blog-build/site
"""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import tempfile
import subprocess
import threading
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

REPO = Path(__file__).resolve().parents[2]
SOURCES = {
    "zh": REPO / "_pages/blogs/prompt-aware-rubrics-zh.html",
    "en": REPO / "_pages/blogs/prompt-aware-rubrics.html",
}
ROUTES = {"/blogs/prompt-aware-rubrics/zh/": "zh", "/blogs/prompt-aware-rubrics/": "en"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
LOCK = threading.Lock()


def revision(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def article_body(source):
    match = re.match(r"\A---\r?\n.*?\r?\n---\r?\n", source, re.S)
    if not match:
        raise ValueError("文章 front matter 不完整")
    return source[:match.end()], source[match.end():]


class Blocks(HTMLParser):
    """Locate editable outer blocks without reserializing the source document."""
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0]
        self.lines.extend(m.end() for m in re.finditer("\n", source))
        self.stack, self.nodes, self.active = [], [], None
        self.feed(source)
        if self.active:
            raise ValueError("文章包含未闭合的可编辑段落")

    def pos(self):
        line, col = self.getpos()
        return self.lines[line-1] + col

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        selected = tag in {"p", "h2", "h3", "li", "td", "th", "figcaption", "blockquote"}
        selected = selected or bool(set(attrs.get("class", "").split()) & {"section-label", "case-kicker"})
        # Include the two metric cards' numbers and descriptions.
        metric = any("metric-strip" in classes for _, classes in self.stack)
        selected = selected or (metric and tag in {"strong", "span"})
        if selected and self.active is None:
            start = self.pos()
            self.active = {"id": str(len(self.nodes)), "start": start,
                           "inner": start+len(self.get_starttag_text()), "depth": len(self.stack)}
        if tag not in VOID:
            self.stack.append((tag, attrs.get("class", "").split()))

    def handle_startendtag(self, tag, attrs):
        if tag not in VOID:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        indexes = [i for i, (name, _) in enumerate(self.stack) if name == tag]
        if not indexes:
            return
        index = indexes[-1]
        if self.active and index == self.active["depth"]:
            self.active["end"] = self.pos()
            self.nodes.append(self.active)
            self.active = None
        self.stack = self.stack[:index]

    def annotated(self):
        result = self.source
        for node in reversed(self.nodes):
            at = node["inner"]-1
            result = result[:at] + ' data-par-edit="' + node["id"] + '" contenteditable="true" spellcheck="false"' + result[at:]
        return result


def source_at_revision(path, expected):
    """Find a known base for an already-open editor; never guess from block IDs."""
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        return None
    backup = Path(tempfile.gettempdir()) / "par-blog-editor-backups" / (path.stem+"-"+expected+".html")
    if backup.is_file():
        source = backup.read_text(encoding="utf-8")
        if revision(source) == expected:
            return source
    relative = str(path.relative_to(REPO))
    commits = subprocess.run(["git", "log", "-40", "--format=%H", "--", relative],
                             cwd=REPO, capture_output=True, text=True, timeout=10, check=True)
    for commit in commits.stdout.splitlines():
        result = subprocess.run(["git", "show", commit+":"+relative], cwd=REPO,
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and revision(result.stdout) == expected:
            return result.stdout
    return None


def merge_stale_changes(base_source, current_source, changes):
    """Rebase only uniquely identified, unchanged outer blocks onto the current file."""
    _, base_body = article_body(base_source)
    _, current_body = article_body(current_source)
    base_nodes = {node["id"]:node for node in Blocks(base_body).nodes}
    current_nodes = Blocks(current_body).nodes
    merged, conflicts = {}, []
    for key, value in changes.items():
        if key not in base_nodes or not isinstance(value, str):
            raise ValueError("段落标识或内容不正确")
        node = base_nodes[key]
        old_inner = base_body[node["inner"]:node["end"]]
        old_outer = base_body[node["start"]:node["end"]].rstrip()
        if value == old_inner:
            continue
        matches = [candidate for candidate in current_nodes
                   if current_body[candidate["start"]:candidate["end"]].rstrip() == old_outer]
        if len(matches) != 1:
            conflicts.append(key)
        else:
            merged[matches[0]["id"]] = value
    if conflicts:
        raise ValueError("同一段落存在版本冲突，未覆盖文件；你的修改已安全备份，请告诉 Codex 合并。")
    return merged


class Fragment(HTMLParser):
    """Accept ordinary rich text, excluding scripts, media and event handlers."""
    def handle_starttag(self, tag, attrs):
        if tag not in {"a", "strong", "b", "em", "i", "u", "s", "mark", "code", "sup", "sub", "span", "br", "p", "div", "ul", "ol", "li", "small"}:
            raise ValueError("这里只支持文字与基本格式，请通过对话修改图片或页面结构")
        for name, value in attrs:
            if name not in {"href", "class", "id", "title", "aria-label", "lang", "target", "rel"}:
                raise ValueError("不支持粘贴的格式，请使用纯文本")
            if name == "href" and urlsplit(value or "").scheme.lower() not in {"", "https", "http", "mailto"}:
                raise ValueError("链接格式不受支持")

    handle_startendtag = handle_starttag


CSS = """
body{padding-top:96px!important}.par-editor-bar{position:fixed;inset:0 0 auto;z-index:10000;background:#193b45;color:#fff;padding:12px 22px;font:14px/1.5 -apple-system,BlinkMacSystemFont,Arial,sans-serif;box-shadow:0 2px 12px #0002;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.par-toc{top:118px}.article-section,.par-article h3[id]{scroll-margin-top:120px}
.par-editor-bar a{color:#c5e9dd;text-decoration:none}.par-editor-bar a[aria-current]{color:#fff;font-weight:700;text-decoration:underline}.par-editor-bar button{background:#eaf5f1;color:#193b45;border:0;border-radius:5px;padding:9px 14px;font:inherit;cursor:pointer}.par-editor-bar button:disabled{opacity:.5;cursor:default}.par-editor-bar small{font-size:12px;color:#c8dbde}.par-editor-status{margin-left:auto}.par-editor-help{flex-basis:100%;font-size:12px;color:#c8dbde}
[data-par-edit]{outline:1px dashed transparent;outline-offset:5px;border-radius:2px;cursor:text;min-height:1em}[data-par-edit]:hover{outline-color:#a9c5bd}[data-par-edit]:focus{outline:2px solid #147d73;background:#f2faf6}[data-par-edit].par-editor-dirty{box-shadow:-4px 0 #c76243}.par-editor-bar [data-error]{color:#ffccbb}
@media(max-width:760px){body{padding-top:145px!important}.par-editor-bar{padding:10px 14px;gap:8px 14px;font-size:12px}.par-editor-status{margin-left:0}.par-editor-help{font-size:11px}}
"""

JS = r"""
(() => {
  const state = JSON.parse(document.getElementById('par-editor-state').textContent);
  const blocks = [...document.querySelectorAll('[data-par-edit]')];
  const original = new Map(blocks.map(e => [e.dataset.parEdit, e.innerHTML]));
  const key = 'par-local-editor-' + state.lang;
  const status = document.getElementById('par-editor-status');
  const save = document.getElementById('par-editor-save');
  let saving = false;
  const changes = () => Object.fromEntries(blocks.filter(e => e.innerHTML !== original.get(e.dataset.parEdit)).map(e => [e.dataset.parEdit, e.innerHTML]));
  function update() {
    const changed = changes(), count = Object.keys(changed).length;
    blocks.forEach(e => e.classList.toggle('par-editor-dirty', Object.hasOwn(changed, e.dataset.parEdit)));
    status.textContent = count ? `${count} 处修改尚未保存` : '本地草稿已保存';
    status.removeAttribute('data-error'); save.disabled = saving || !count;
    try { count ? localStorage.setItem(key, JSON.stringify({revision:state.revision,changes:changed})) : localStorage.removeItem(key); } catch (_) {}
  }
  let recovered = null;
  try { recovered = JSON.parse(localStorage.getItem(key)); } catch (_) {}
  if (recovered && recovered.revision === state.revision) {
    blocks.forEach(e => { if (Object.hasOwn(recovered.changes,e.dataset.parEdit)) e.innerHTML = recovered.changes[e.dataset.parEdit]; });
  }
  blocks.forEach(e => {
    e.addEventListener('input', update);
    e.addEventListener('paste', event => {
      event.preventDefault(); document.execCommand('insertText', false, event.clipboardData.getData('text/plain'));
    });
    e.addEventListener('click', event => { if (event.target.closest('a')) event.preventDefault(); });
  });
  async function persist() {
    const pending = changes(); if (!Object.keys(pending).length || saving) return;
    saving = true; save.disabled = true; status.textContent = '正在保存…';
    try {
      const response = await fetch('/__par_editor__/save', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lang:state.lang,revision:state.revision,changes:pending})});
      const result = await response.json(); if (!response.ok) throw new Error(result.error || '保存失败');
      state.revision = result.revision;
      for (const [id, value] of Object.entries(pending)) original.set(id,value);
      saving = false; update(); status.textContent = `已保存 ${new Date().toLocaleTimeString('zh-CN')} · 尚未上传`;
      // Reload after saving so structural edits receive fresh block identifiers.
      const scroll = scrollY; sessionStorage.setItem(key+'-scroll',String(scroll)); location.reload();
    } catch (error) {
      saving = false; save.disabled = false; status.textContent = error.message;status.setAttribute('data-error','');
    }
  }
  save.addEventListener('click',persist);
  document.addEventListener('keydown',event=>{if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='s'){event.preventDefault();persist();}});
  window.addEventListener('beforeunload',event=>{if(Object.keys(changes()).length){event.preventDefault();event.returnValue='';}});
  const savedScroll = sessionStorage.getItem(key+'-scroll');
  if(savedScroll !== null){sessionStorage.removeItem(key+'-scroll');requestAnimationFrame(()=>scrollTo(0,Number(savedScroll)));}
  update();
})();
"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server, directory=str(server.site))

    def log_message(self, fmt, *args):
        if not args or str(args[0]).startswith(('"GET /assets/', '"GET /images/')):
            return
        super().log_message(fmt, *args)

    def respond(self, content, kind="text/html; charset=utf-8", code=200):
        if isinstance(content, str):
            content = content.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/":
            self.send_response(302)
            self.send_header("Location", "/blogs/prompt-aware-rubrics/zh/")
            self.end_headers()
            return
        if request.path == "/__par_editor__/ui.js":
            return self.respond(JS, "text/javascript; charset=utf-8")
        if request.path == "/__par_editor__/ui.css":
            return self.respond(CSS, "text/css; charset=utf-8")
        lang = ROUTES.get(request.path)
        if not lang:
            return super().do_GET()
        source = SOURCES[lang].read_text(encoding="utf-8")
        _, body = article_body(source)
        page = (self.server.site / request.path.lstrip("/") / "index.html").read_text(encoding="utf-8")
        preview = parse_qs(request.query).get("preview") == ["1"]
        if not preview:
            body = Blocks(body).annotated()
        page, count = re.subn(r'(<article\b[^>]*id="article-body"[^>]*>).*?(</article>)',
                              lambda m: m[1]+body+m[2], page, count=1, flags=re.S)
        if count != 1:
            return self.respond("预览结构已改变，请重新构建网站。", code=500)
        page = re.sub(r"https?://127\.0\.0\.1:\d+", "", page)
        if not preview:
            # MathJax transforms source HTML; leave TeX editable as source instead.
            page = re.sub(r'<script\b[^>]*(?:mathjax|text/x-mathjax-config)[^>]*>.*?</script>', '', page, flags=re.I|re.S)
        links = ' · '.join('<a href="'+path+'"'+(' aria-current="page"' if value==lang else '')+'>'+('中文' if value=='zh' else 'English')+'</a>' for path,value in ROUTES.items())
        if preview:
            bar = '<div class="par-editor-bar"><strong>本地草稿预览</strong><a href="'+request.path+'">返回编辑</a><small>草稿尚未上传到主页</small></div>'
        else:
            bar = '<div class="par-editor-bar"><strong>PAR 可视化编辑</strong>'+links+'<button id="par-editor-save" disabled>保存草稿</button><a href="?preview=1" target="_blank">预览</a><span class="par-editor-status" id="par-editor-status" role="status"></span><div class="par-editor-help">点击正文即可修改 · ⌘/Ctrl+S 保存到本地 · 公式显示为可编辑的 TeX · 改完告诉 Codex「同步英文并上传」</div></div>'
        page = page.replace("</head>", '<link rel="stylesheet" href="/__par_editor__/ui.css"></head>')
        page = re.sub(r"<body([^>]*)>", lambda m: '<body'+m[1]+'>'+bar, page, count=1)
        if not preview:
            state = json.dumps({"lang":lang,"revision":revision(source)}, ensure_ascii=False).replace("<", "\\u003c")
            page = page.replace('</body>', '<script type="application/json" id="par-editor-state">'+state+'</script><script src="/__par_editor__/ui.js"></script></body>')
        self.respond(page)

    def do_POST(self):
        if self.path != "/__par_editor__/save":
            return self.respond("Not found", code=404)
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.headers.get("Host") not in allowed or self.headers.get("Origin") != "http://"+self.headers.get("Host", ""):
            return self.respond(json.dumps({"error":"请从本地编辑页面保存"}), "application/json", 403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                raise ValueError("保存内容过大")
            payload = json.loads(self.rfile.read(length))
            lang, changes = payload["lang"], payload["changes"]
            if lang not in SOURCES or not isinstance(changes, dict) or not changes:
                raise ValueError("没有可保存的修改")
            with LOCK:
                path = SOURCES[lang]
                source = path.read_text(encoding="utf-8")
                if payload.get("revision") != revision(source):
                    # Save the incoming draft before trying a merge, including on conflicts.
                    recovery = Path(tempfile.gettempdir()) / "par-blog-editor-recovery"
                    recovery.mkdir(exist_ok=True)
                    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=recovery,
                                                     prefix=lang+"-", suffix=".json", delete=False) as f:
                        json.dump(payload, f, ensure_ascii=False)
                    base = source_at_revision(path, payload.get("revision"))
                    if base is None:
                        return self.respond(json.dumps({"error":"旧版本暂时无法匹配；你的修改已安全备份，请告诉 Codex 合并。"}, ensure_ascii=False), "application/json; charset=utf-8", 409)
                    try:
                        changes = merge_stale_changes(base, source, changes)
                    except ValueError as error:
                        return self.respond(json.dumps({"error":str(error)}, ensure_ascii=False), "application/json; charset=utf-8", 409)
                prefix, body = article_body(source)
                nodes = {node["id"]:node for node in Blocks(body).nodes}
                replacements = []
                for key, value in changes.items():
                    if key not in nodes or not isinstance(value, str) or len(value) > 100_000:
                        raise ValueError("段落标识或内容不正确，请刷新页面")
                    if "{{" in value or "{%" in value:
                        raise ValueError("可视化编辑不支持 Liquid 模板语法")
                    Fragment().feed(value)
                    replacements.append((nodes[key], value))
                for node, value in sorted(replacements, key=lambda item:item[0]["inner"], reverse=True):
                    body = body[:node["inner"]]+value+body[node["end"]:]
                updated = prefix+body
                Blocks(body)  # Reject broken outer block structure before saving.
                backup = Path(tempfile.gettempdir()) / "par-blog-editor-backups"
                backup.mkdir(exist_ok=True)
                (backup / (path.stem+"-"+revision(source)+".html")).write_text(source, encoding="utf-8")
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as f:
                    f.write(updated)
                    tmp = Path(f.name)
                tmp.chmod(path.stat().st_mode & 0o777)
                os.replace(tmp, path)
            self.respond(json.dumps({"revision":revision(updated)}, ensure_ascii=False), "application/json; charset=utf-8")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self.respond(json.dumps({"error":str(error)}, ensure_ascii=False), "application/json; charset=utf-8", 400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True, help="Jekyll build destination")
    parser.add_argument("--port", type=int, default=4318)
    args = parser.parse_args()
    site = args.site.resolve()
    for route in ROUTES:
        if not (site / route.lstrip("/") / "index.html").is_file():
            parser.error("请先构建网站；--site 应指向生成的网站目录")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.site = site
    print(f"PAR editor: http://127.0.0.1:{args.port}/blogs/prompt-aware-rubrics/zh/", flush=True)
    print("Saves local article drafts only. Publishing remains a separate step.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
