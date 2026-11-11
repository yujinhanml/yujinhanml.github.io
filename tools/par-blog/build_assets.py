"""Build PAR figures using reported experimental values and original schematic artwork.
Case artwork contains no source presentation images or original video frames.
Usage: python tools/par-blog/build_assets.py --out assets/images/par
"""
import argparse
import csv
import html
import json
from pathlib import Path
import textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, TEAL, CORAL = "#193b45", "#147d73", "#c76243"
MUTED, LIGHT, SAND, LINE = "#60747a", "#eaf5f1", "#f8f5ee", "#dce5e4"


def esc(t):
    return html.escape(str(t))


class Diagram:
    def __init__(self, w, h, title, desc=""):
        self.w, self.h = w, h
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
                      f'<title id="title">{esc(title)}</title><desc id="desc">{esc(desc or title)}</desc>',
                      '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#7d969b"/></marker></defs>',
                      f'<rect width="{w}" height="{h}" rx="20" fill="white"/>']

    def text(self, x, y, text, size=18, color=INK, weight=400, anchor="start", wrap=None, line=1.45):
        lines = []
        for t in str(text).split("\n"):
            lines.extend(textwrap.wrap(t, wrap, break_long_words=False) if wrap else [t])
        self.parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">')
        for i, t in enumerate(lines):
            self.parts.append(f'<tspan x="{x}" dy="{0 if i == 0 else size * line}">{esc(t)}</tspan>')
        self.parts.append('</text>')

    def rect(self, x, y, w, h, fill=LIGHT, stroke=LINE, radius=12):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def box(self, x, y, w, h, title, body="", fill=LIGHT, size=19):
        self.rect(x, y, w, h, fill)
        self.text(x + w/2, y + 31, title, size, weight=600, anchor="middle")
        if body:
            self.text(x + w/2, y + 59, body, 16, MUTED, anchor="middle", wrap=max(16, int(w/8.7)))

    def arrow(self, x1, y1, x2, y2, dashed=False, points=None):
        pts = points or [(x1, y1), (x2, y2)]
        self.parts.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="#7d969b" stroke-width="2" {"stroke-dasharray=\"6 5\"" if dashed else ""} marker-end="url(#arrow)"/>')

    def label(self, text):
        self.text(30, 35, text, 14, TEAL, 600)

    def save(self, out, name):
        (out / (name + ".svg")).write_text("\n".join(self.parts + ['</svg>']) + '\n')


def rubric_pool_example(out):
    d = Diagram(1100, 1080, "A two-level rubric pool: selected English examples",
                "Five categories distilled from production evaluation experience, with selected subcategories and abbreviated criteria. Select relevant entries and ground them in the editing instruction.")
    d.label("RUBRIC POOL / SELECTED, ABBREVIATED ENTRIES")
    d.text(30, 76, "Select applicable categories and subcategories; ground each check in the task.", 22, weight=600)
    d.text(30, 108, "Use the existing top-level categories. Do not ask every question for every video.", 19, MUTED)
    groups = [
        ("Visual Editing", [
            ("Element Addition", "Required objects, counts, positions, and appearances"),
            ("Attribute Changes", "Color, shape, facial features, clothing, and props"),
            ("Actions and Timing", "Actions, event order, pacing, and duration")]),
        ("Audio Editing", [
            ("Dialogue Content", "Requested speech, narration, or lyrics"),
            ("Voice and Delivery", "Voice identity, tone, emotion, and speaking rate"),
            ("Music and Sound Effects", "Background music, ambient sound, and event sounds")]),
        ("Cross-Modal Editing", [
            ("Lip Synchronization", "Alignment of speech and visible mouth movements"),
            ("Audio–Visual Alignment", "Agreement between audible and visible events"),
            ("Cross-Modal Timing", "Timing of related edits across audio and video")]),
        ("Content Preservation", [
            ("Subject Identity", "Identity and appearance outside the requested changes"),
            ("Unedited Scene Content", "Background, props, and other unedited elements"),
            ("Camera and Timing", "Original camera motion, pacing, and duration")]),
        ("Editing Quality", [
            ("Overall Visual Quality", "Overall appearance and visual quality of the result"),
            ("Temporal Stability", "Flicker, transient deformation, and frame consistency"),
            ("Edit Integration", "Seams, residual content, and local blending")])]
    for i, (category, entries) in enumerate(groups):
        y = 143 + i * 178
        d.rect(30, y, 1040, 162, SAND if i % 2 else LIGHT)
        d.text(52, y + 35, f"0{i + 1} / CATEGORY", 13, TEAL, 600)
        d.text(52, y + 70, category, 22, weight=600)
        d.parts.append(f'<path d="M 310,{y+20} V {y+142}" stroke="{LINE}" stroke-width="2"/>')
        for j, (subcategory, criterion) in enumerate(entries):
            yy = y + 29 + j * 45
            d.text(335, yy, subcategory, 18, weight=600)
            d.text(335, yy + 20, criterion, 16, MUTED)
    d.text(550, 1061, "Category → Subcategory → Task-specific rubric", 18, TEAL, 600, anchor="middle")
    d.save(out, "rubric-pool-example")


def specialist_operator_figures(out):
    d = Diagram(1100, 540, "Introduce operators to strengthen the answering model",
                "Business evaluation explanations and rubric-level errors locate weaknesses. Add specialist operators and adjust routing to extend the current verifier.")
    d.label("TARGET CAPABILITY GAPS / FROM ONE ANSWERING MODEL TO A TOOL POOL")
    d.box(30, 70, 310, 110, "Single answering model", "Existing PAR verifier", SAND, 22)
    d.arrow(345, 125, 425, 125)
    d.box(430, 70, 640, 110, "Answering model + specialist tool pool",
          "Audio consistency · lip synchronization · visual quality", LIGHT, 22)
    steps = [
        ("Step 1 / Run", "Current verifier inference"),
        ("Step 2 / Diagnose", "Business explanations + error cases + affected rubrics"),
        ("Step 3 / Extend", "Introduce operators + adjust routing"),
        ("Step 4 / Re-run", "Updated verifier inference")]
    for i, (title, body) in enumerate(steps):
        x = 30 + i * 270
        d.box(x, 265, 230, 145, title, body, LIGHT if i == 3 else SAND, 19)
        if i < 3:
            d.arrow(x + 234, 337, x + 264, 337)
    d.text(550, 470, "Human explanations identify the failure; rubrics locate the missing capability.", 20, anchor="middle")
    d.text(550, 506, "Discover and validate operators in a local sandbox before integration.", 18, MUTED, anchor="middle")
    d.save(out, "capability-extension")

    d = Diagram(1100, 760, "Step 3 expanded: operator discovery and validation",
                "Build a local validation set, execute candidate operators with a strong model, assess detection and false rejection, and select tools for fixed routing.")
    d.label("STEP 3 EXPANDED / LOCAL SANDBOX EXPERIMENTS")
    steps = [
        (70, "1. Build a focused validation set", "50 abnormal cases + 50 normal cases"),
        (220, "2. Execute candidate operators", "Strong model proposes and runs candidates in a local sandbox"),
        (370, "3. Validate on both sides", "High failure-detection rate + low false-rejection rate"),
        (520, "4. Select operators for deployment", "Bind validated specialists to applicable rubrics and fixed routes")]
    for y, title, body in steps:
        d.box(165, y, 770, 105, title, body, SAND if y == 370 else LIGHT, 23)
        if y < 520:
            d.arrow(550, y + 105, 550, y + 145)
    d.arrow(935, 422, 935, 272, True,
            points=[(935, 422), (1005, 422), (1005, 272), (941, 272)])
    d.text(1017, 342, "Retry", 16, CORAL)
    d.text(550, 690, "Example: Audio Consistency Checker for visual_only tasks", 21, TEAL, 600, anchor="middle")
    d.text(550, 728, "Apply preservation checks only where the instruction requires preservation.", 18, MUTED, anchor="middle")
    d.save(out, "sandbox")


def hybrid_figure(out):
    d = Diagram(1100, 710, "Proposed hybrid System 1 and System 2 verifier",
                "Checks within the base answering model's capabilities use expert-aligned fast verification. Difficult local and temporal inspection uses reasoning and tools.")
    d.label("PROPOSED ARCHITECTURE / CHOOSE THE ANSWERING PROCESS BY CAPABILITY")
    d.box(230, 65, 640, 90, "Task + video pair → prompt-aware rubrics", "Define what needs to be checked")
    d.arrow(550, 155, 550, 205)
    d.box(230, 210, 640, 75, "What capability does this rubric require?", fill=SAND)
    for x, title, body, fill in [
        (30, "System 1 / Direct judgment", "Within the base model's capabilities\nExpert-aligned answering-model training\nFast binary verification", LIGHT),
        (600, "System 2 / Deliberate inspection", "Difficult local or temporal evidence\nElaborate reasoning + inspection tools\nCrop · zoom · neighboring frames", SAND)]:
        d.box(x, 350, 470, 155, title, body, fill, 23)
        d.arrow(550, 285, x+235, 346, points=[(550, 285), (550, 315), (x+235, 315), (x+235, 346)])
        d.arrow(x+235, 505, 550, 570, points=[(x+235, 505), (x+235, 540), (550, 540), (550, 570)])
    d.box(160, 575, 780, 80, "Rubric-level evidence + verdicts → aggregate reward")
    d.text(550, 690, "One task-grounded interface; different processes for obtaining a reliable answer.", 18, MUTED, anchor="middle")
    d.save(out, "hybrid")


def diagrams(out):
    rubric_pool_example(out)
    specialist_operator_figures(out)
    hybrid_figure(out)
    d = Diagram(1100, 340, "Same model, different context", "A generic question leaves the model to choose its checks; targeted rubrics specify the object and edit to inspect.")
    d.label("CONTEXT IS PART OF THE VERIFIER")
    d.box(30, 65, 480, 150, "General question", "Does the edited video satisfy the instruction?", SAND, 23)
    d.box(590, 65, 480, 150, "Prompt-aware question", "Have all red delivery carts in the courtyard been changed to blue?", LIGHT, 23)
    d.text(55, 251, "Implicit task decomposition", 19, MUTED)
    d.text(615, 251, "Explicit object + attribute + target change", 19, TEAL)
    d.text(550, 305, "Same task. Same video. Same verifier. A more informative context.", 18, INK, anchor="middle")
    d.arrow(520, 140, 580, 140)
    d.save(out, "context")

    d = Diagram(1100, 430, "From human evaluation to PAR")
    d.label("THE DESIGN INSPIRATION")
    for x, human, machine, body in [(30, "Define the criteria", "Rubric Handbook", "Expert knowledge as a system prompt"), (405, "Create task-specific checks", "Rubric Generator", "Select and instantiate relevant criteria"), (780, "Train the evaluators", "Rubric Verifier", "Apply expert-aligned decision rules")]:
        d.box(x, 65, 290, 80, human, fill=SAND, size=18)
        d.arrow(x+145, 148, x+145, 199)
        d.box(x, 205, 290, 122, machine, body)
    for x in [325,700]:
        d.arrow(x, 267, x+70, 267)
    d.text(550, 383, "Task + video pair  →  task-specific checks  →  verdicts and reward", 20, anchor="middle")
    d.save(out, "human-to-par")

    d = Diagram(1100, 450, "Inside the rubric generator's system prompt")
    d.label("HANDBOOK = FIXED REQUIREMENTS + STRUCTURED RUBRIC POOL")
    d.box(30, 67, 495, 155, "Fixed generation requirements", "Atomicity · importance first\nConsistent polarity · no contradictions\nNo duplicates · verifiable wording", SAND)
    d.box(575, 67, 495, 155, "Two-level rubric pool", "Category → subcategory\nBroad categories and finer criteria\nOnly relevant criteria are selected")
    d.arrow(278, 224, 278, 265)
    d.arrow(823, 224, 823, 265)
    d.box(30, 270, 1040, 94, "Select → Ground in the task → Ask", "User prompt / editing instruction supplies the objects, attributes and constraints")
    d.text(550, 412, "The pool is a set of anchors, not a questionnaire to copy into every task.", 19, MUTED, anchor="middle")
    d.save(out, "handbook")

    d = Diagram(1100, 1240, "Black-box rubric pool optimization loop", "Initialize, evaluate, select an anchor, analyze errors, edit the rubric pool, validate the patch, regenerate rubrics, evaluate, retain the best and repeat.")
    d.label("TEXT SEARCH WITH EVALUATION AND BEST-CANDIDATE RETENTION")
    nodes=[(70,"Initialize","Handbook, train pairs, optional OOD data, verifier and metrics"),
           (185,"Measure the baseline","Freeze the initial prompt; collect wrong and tied cases"),
           (300,"Select anchor + edit budget","Prefer the current best; also consider historical candidates"),
           (415,"Analyze failure patterns","Instructions, generated rubrics, verdicts and human explanations"),
           (530,"Edit rubric pool entries","Add / Remove / Split / Merge; keep the protocol and output format"),
           (645,"Validate the patch","Check scope, format and edit count against budget L"),
           (760,"Regenerate rubrics","Track generation success and evaluate with the verifier")]
    for y,t,b in nodes:
        d.box(210,y,680,88,t,b, SAND if y==645 else LIGHT)
        if y>70:d.arrow(550,y-27,550,y-4)
    d.arrow(210,689,210,574,points=[(210,689),(118,689),(118,574),(205,574)])
    d.text(105,620,"Invalid",15,CORAL,anchor="middle")
    for x,t,b in [(30,"Train pairwise","Against human labels"),(405,"OOD pairwise","Optional"),(780,"OOD pointwise","Optional")]:
        d.box(x,885,290,85,t,b,SAND,17)
        d.arrow(550,848,x+145,881,points=[(550,848),(550,866),(x+145,866),(x+145,881)])
        d.arrow(x+145,970,550,1004,points=[(x+145,970),(x+145,990),(550,990),(550,1004)])
    d.box(210,1008,680,85,"Aggregate scores + generation success gate","Accept only a candidate that improves on the current best",SAND)
    d.box(30,1130,460,78,"No improvement: retain best", "Record the round", SAND,17)
    d.box(610,1130,460,78,"Improvement: save new best", "Return to anchor selection while budget remains", LIGHT,17)
    d.arrow(550,1093,260,1126,points=[(550,1093),(550,1110),(260,1110),(260,1126)])
    d.arrow(550,1093,840,1126,points=[(550,1093),(550,1110),(840,1110),(840,1126)])
    d.arrow(1070,1170,890,344,True,points=[(1070,1170),(1087,1170),(1087,344),(895,344)])
    d.arrow(30,1170,210,344,True,points=[(30,1170),(13,1170),(13,344),(205,344)])
    d.save(out, "pool-search")

    d = Diagram(1100, 440, "GRPO training for rubric verification")
    d.label("ONE BINARY VERDICT PER RUBRIC")
    d.box(30,70,290,110,"Video pair + N rubrics","Task-grounded evaluation inputs")
    d.box(405,70,290,110,"Verifier rollouts","N-bit output, e.g. 11001")
    d.box(780,70,290,110,"GRPO update","Improve the rubric-level judgments")
    d.arrow(325,125,400,125);d.arrow(700,125,775,125)
    for x,t,b in [(30,"Length check","Exactly N positions"),(405,"Format check","Every position is 0 or 1"),(780,"Accuracy reward","Correctness + token probability")]:
        d.box(x,240,290,104,t,b,SAND,18)
    d.text(550,398,"Direct GRPO: limited data, and the base model already knows the output format.",19,MUTED,anchor="middle")
    d.save(out,"verifier-training")

    d = Diagram(1100, 610, "Gold-Rescue training flow")
    d.label("RESCUE IS TRIGGERED PER RUBRIC")
    d.box(200,65,700,90,"Sample K rollouts","Score each rubric against its gold label")
    d.arrow(550,155,550,205)
    d.box(200,210,700,85,"Are all K answers wrong on rubric j?","Inspect correctness, not only the scalar reward",SAND)
    d.arrow(550,295,265,355,points=[(550,295),(550,325),(265,325),(265,355)])
    d.arrow(550,295,835,355,points=[(550,295),(550,325),(835,325),(835,355)])
    d.text(265,342,"No",16,TEAL,anchor="middle");d.text(835,342,"Yes",16,CORAL,anchor="middle")
    d.box(30,360,470,110,"Ordinary GRPO","Group-relative advantages\nPPO clipped loss")
    d.box(600,360,470,110,"Inject one gold answer","Recompute group advantages\nLUFFY-style shaped gold loss",SAND)
    d.text(550,540,"Gold supervision uses an off-policy token under a gold prefix.",19,anchor="middle")
    d.text(550,574,"The trigger is project-specific; policy shaping is adapted from LUFFY.",17,MUTED,anchor="middle")
    d.save(out,"gold-rescue")

    d = Diagram(1100, 650, "Agentic PAR V1 with fixed rubric routing")
    d.label("V1 · DEPLOYED · SPECIALISTS IN A FIXED WORKFLOW")
    d.box(30,65,310,100,"Task + video pair","Generate task-specific rubrics")
    d.box(410,65,660,100,"Applicable audio-preservation precheck","Run when the task requires the original audio to remain unchanged",SAND)
    d.arrow(345,115,405,115)
    d.box(240,225,620,85,"PAR verifier + rubric-based routing","Use the specialists relevant to the selected checks")
    d.arrow(740,165,550,221,points=[(740,165),(740,195),(550,195),(550,221)])
    tools=[(30,"PAR verifier","Default rubric judgments"),(405,"Lip-Sync Verifier","Cross-modal checks"),(780,"Quality Specialist","Visual artifact checks")]
    for x,t,b in tools:
        d.box(x,375,290,100,t,b,SAND,18)
        d.arrow(550,310,x+145,371,points=[(550,310),(550,342),(x+145,342),(x+145,371)])
        d.arrow(x+145,475,550,535,points=[(x+145,475),(x+145,505),(550,505),(550,535)])
    d.box(240,540,620,80,"Final filtering decision / rubric-level result")
    d.save(out,"agentic-v1")

    d = Diagram(1100, 655, "Agentic PAR V4 evidence-based harness")
    d.label("V4 · EXPLORATORY · EVIDENCE-BASED ORCHESTRATION")
    for y,t,b in [(65,"1. Rubric gap review","Review the task and add missing, task-relevant checks"),(230,"2. Tool orchestration","Bind tools to rubrics; collect an evidence bundle for each check"),(395,"3. Evidence-based judgment","Judge each rubric; send conflicting evidence to an independent adjudicator")]:
        d.box(190,y,720,110,t,b, LIGHT if y!=230 else SAND,23)
        if y<395:d.arrow(550,y+110,550,y+160)
    d.rect(30,552,1040,65,SAND)
    d.text(550,591,"Tool capability supplies evidence. The harness determines how to use it.",20,anchor="middle")
    d.save(out,"agentic-v4")



def chart_style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':INK,
        'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':LINE,
        'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
        'axes.spines.bottom':False,'axes.titleweight':'bold','axes.titlepad':15,
        'figure.facecolor':'white','axes.facecolor':'white','svg.fonttype':'none'})


def save_chart(fig,out,name):
    fig.savefig(out/(name+'.svg'),bbox_inches='tight',pad_inches=.25,metadata={'Date':None})
    plt.close(fig)
    target = out / (name + '.svg')
    target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines()) + '\n')


def metric_bars(out,name,labels,values,title,reference,colors=None,horizontal=False,ylabel='Accuracy (%)',reference_line=None):
    fig,ax=plt.subplots(figsize=(9.3,max(4.5,len(labels)*.56+1.4)))
    colors=colors or [TEAL]*len(values)
    if horizontal:
        ax.barh(range(len(labels)),values,color=colors,height=.5)
        ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis()
        ax.set_xlim(0,100);ax.set_xlabel(ylabel)
        ax.xaxis.grid(True,color=LINE,alpha=.6)
        if reference_line is not None:
            ax.vlines(reference_line, 0, len(labels)-.5, color=CORAL,
                      linestyles=(0,(5,4)), linewidth=1.7, zorder=3)
        for i,v in enumerate(values):
            label_x=max(v,reference_line)+1.2 if reference_line is not None else v+1.2
            ax.text(label_x,i,f'{v:.2f}%',va='center',fontweight='bold')
    else:
        ax.bar(range(len(labels)),values,color=colors,width=.5)
        ax.set_xticks(range(len(labels)),labels);ax.set_ylim(0,100)
        ax.set_ylabel(ylabel);ax.yaxis.grid(True,color=LINE,alpha=.6)
        for i,v in enumerate(values):ax.text(i,v+1.7,f'{v:.2f}%',ha='center',fontweight='bold',fontsize=15)
    ax.set_axisbelow(True);ax.tick_params(axis='both',length=0,pad=10)
    ax.set_title(title,loc='left',fontsize=14,pad=44)
    ax.text(0,1.055,reference,transform=ax.transAxes,fontsize=10,color=MUTED)
    save_chart(fig,out,name)


def extension_charts(out):
    chart_style()
    data = json.loads((Path(__file__).parent/'results.json').read_text())
    gains = data['version_gain_sources']
    fig, axes = plt.subplots(3, 1, figsize=(10.4, 10.2), gridspec_kw={'height_ratios': [1, 1.35, 1]})
    ax = axes[0]
    values = gains['single_to_v1']
    ax.barh([0, 1], values, color=[TEAL, '#69aa9e'], height=.48)
    ax.set_yticks([0, 1], ['Audio-consistency\noperators', 'Visual-quality\nspecialists'])
    ax.set_title('Single PAR → V1 · specialist discoveries', loc='left', fontsize=14)
    for i, value in enumerate(values):
        ax.text(value+.8, i, str(value), va='center', fontweight='bold')
    ax.set_xlabel('Newly detected failure cases')
    for ax, indices, labels, title in [
        (axes[1], [0, 1, 2], ['Per-rubric judgment\n(replaces averaging)', 'Rubric-gap review\n(synthetic checks)', 'Independent conflict\nadjudication'], 'V1 → V4 · harness design'),
        (axes[2], [3, 4], ['Local operators\n(10 lightweight tools)', 'External VLM expert'], 'V1 → V4 · expanded tool pool')]:
        y = np.arange(len(indices))
        corrected = [gains['v4_corrected'][i] for i in indices]
        errors = [gains['v4_new_errors'][i] for i in indices]
        ax.barh(y-.17, corrected, color=TEAL, height=.29, label='Decisions corrected')
        ax.barh(y+.17, errors, color=CORAL, height=.29, label='New errors introduced')
        ax.set_yticks(y, labels)
        ax.set_title(title, loc='left', fontsize=14)
        ax.set_xlabel('Decision count in component-level error review')
        for values, offset in [(corrected, -.17), (errors, .17)]:
            for i, value in enumerate(values):
                ax.text(value+.8, i+offset, str(value), va='center', fontsize=11, fontweight='bold')
    for ax in axes:
        ax.invert_yaxis(); ax.set_xlim(0, 48)
        ax.xaxis.grid(True, color=LINE, alpha=.6); ax.set_axisbelow(True)
        ax.tick_params(axis='both', length=0, pad=8)
    axes[1].legend(frameon=False, loc='lower right', fontsize=10)
    fig.tight_layout(h_pad=3)
    save_chart(fig, out, 'version-gain-sources')

    calibration = data['calibration']
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5))
    for ax, values, title, limit, labels in [
        (axes[0], calibration['mean_score'], 'Mean rubric probability', 1, ['0.803', '0.775']),
        (axes[1], calibration['high_confidence_share'], 'Scores in [0.95, 1.00]', 100, ['75%', '67%'])]:
        ax.bar([0, 1], values, color=['#bccbc7', TEAL], width=.5)
        ax.set_xticks([0, 1], ['Standard\nGRPO', 'GRPO-RLCD'])
        ax.set_ylim(0, limit); ax.set_title(title, loc='left', fontsize=13)
        ax.yaxis.grid(True, color=LINE, alpha=.6); ax.set_axisbelow(True)
        ax.tick_params(axis='both', length=0, pad=8)
        for i, (value, label) in enumerate(zip(values, labels)):
            ax.text(i, value+limit*.035, label, ha='center', fontweight='bold', fontsize=14)
    axes[0].set_ylabel('Mean probability'); axes[1].set_ylabel('Share of rubric scores (%)')
    fig.tight_layout(w_pad=3)
    save_chart(fig, out, 'calibration-confidence')


def charts(out):
    chart_style()
    extension_charts(out)
    data=json.loads((Path(__file__).parent/'results.json').read_text())
    labels=['Fixed\nrubrics','Expert-informed\nhandbook','Agent-refined\nhandbook']
    colors=['#bccbc7','#69aa9e',TEAL]
    for name in ['handbook-results','context-activation']:
        metric_bars(out,name,labels,data['handbook'],'Better context activates base-model capabilities',
                   'Bench1 · context optimization · +9.6 pp',colors)
    metric_bars(out,'training-results',['Baseline','Augmentation V1','Augmentation V2','V2 + Gold-Rescue'],
               data['training'],'Learning to apply expert judgments','Bench1 · verifier training variants',horizontal=True)
    metric_bars(out,'expert-alignment',['Before expert-aligned\ntraining','After expert-aligned\ntraining'],
               [data['training'][0],data['training'][2]],'Align the answering model with expert standards',
               'Bench1 · expert-aligned training · +4.3 pp',['#bccbc7',TEAL])
    metric_bars(out,'relevance',['Content preservation','Visual editing','Editing quality','Cross-modal editing','Audio editing'],
               data['relevance'],'Rubric relevance across categories','Human-reviewed questions',horizontal=True,ylabel='Fully relevant (%)')
    order=[3,0,1,2]
    metric_bars(out,'precision-overview',
               ['External SOTA ensemble\nGemini-3-Pro-Preview + GPT-5.6-Sol','Single PAR','Agentic PAR V1','Agentic PAR V4'],
               [data['precision'][i] for i in order], 'Bench2 · precision across PAR versions and external SOTA',
               'V4 exceeds the external ensemble by 5.24 pp',[CORAL,'#93b8ad','#4c9e8e',TEAL],True,ylabel='Precision (%)',reference_line=data['precision'][3])
    fig,axes=plt.subplots(1,2,figsize=(11.4,4.4))
    names=['Single PAR','Agentic V1','Agentic V4','External ensemble'];cs=['#93b8ad','#4c9e8e',TEAL,CORAL]
    for i,n in enumerate(names):
        axes[0].scatter(data['recall'][i],data['precision'][i],s=100,color=cs[i])
        axes[0].annotate(n,(data['recall'][i],data['precision'][i]),xytext=(7,-15 if i in [1,3] else 5),textcoords='offset points',fontsize=9)
    axes[0].set(xlim=(73,85),ylim=(64,76),xlabel='Recall (%)',ylabel='Precision (%)')
    axes[0].set_title('Bench2 · precision / recall',loc='left',fontsize=12);axes[0].grid(True,color=LINE,alpha=.6)
    axes[1].barh(range(3),data['accuracy'],color=cs[:3],height=.5)
    axes[1].set_yticks(range(3),names[:3]);axes[1].invert_yaxis();axes[1].set_xlim(0,90)
    axes[1].set_xlabel('Accuracy (%)')
    axes[1].set_title('Bench2 · PAR accuracy',loc='left',fontsize=12)
    for i,v in enumerate(data['accuracy']):axes[1].text(v+1,i,f'{v:.2f}%',va='center',fontweight='bold')
    fig.tight_layout(w_pad=3);save_chart(fig,out,'versions')
    base,strict,tolerable=data['production'];total=strict+tolerable
    fig,ax=plt.subplots(figsize=(9.3,4.8))
    ax.bar(0,base,color='#bccbc7',width=.5)
    ax.bar(1,strict,color=TEAL,width=.5,label='Strictly usable')
    ax.bar(1,tolerable,bottom=strict,color='#b5934b',width=.5,label='Tolerable')
    ax.set_xticks([0,1],['Baseline','Agentic PAR V1']);ax.set_xlim(-.7,1.9);ax.set_ylim(0,100)
    ax.set_ylabel('Usable + tolerable share (%)')
    ax.set_title('Real synthesis pipeline · 2.20× baseline usability',loc='left',pad=44)
    ax.text(0,1.055,'V1 · strictly usable and tolerable outcomes shown separately',transform=ax.transAxes,fontsize=10,color=MUTED)
    ax.yaxis.grid(True,color=LINE,alpha=.6);ax.set_axisbelow(True);ax.tick_params(axis='both',length=0,pad=10)
    ax.text(0,base+2,'31.0%',ha='center',fontweight='bold',fontsize=15)
    ax.text(1,total+2,f'{total:.2f}%',ha='center',fontweight='bold',fontsize=15)
    ax.text(1,strict/2,f'{strict:.2f}%',ha='center',va='center',color='white',fontweight='bold',fontsize=14)
    ax.annotate(f'{tolerable:.2f}%',xy=(1.26,strict+tolerable/2),xytext=(1.48,strict+tolerable/2),va='center',fontsize=11,arrowprops={'arrowstyle':'-','color':MUTED})
    ax.legend(frameon=False,loc='upper right',fontsize=10);save_chart(fig,out,'business')
    metric_bars(out,'failure-analysis',['Rubric missing','Tool / verifier judgment error','Evidence aggregation failure'],
               data['failures'],'Where the remaining failures occur','Analyzed failure subset',horizontal=True,ylabel='Share of analyzed failures (%)')
    metric_bars(out,'artifact-cot',['5 FPS\nwithout CoT','5 FPS\nwith CoT + crop'],data['artifact_cot'],
               'CoT + crop helps identify local quality artifacts','Bench5 · artifact-focused SP · +6.4 pp',['#9ac5bb',TEAL],ylabel='Artifact detection rate (%)')
    metric_bars(out,'artifact-frames',['Uniform 5 FPS\nwith CoT','Manually selected frames\nwith CoT'],data['artifact_frames'],
               'Selected frames provide no additional gain','Bench5 · artifact-focused SP · selected frames: −3.2 pp',[TEAL,'#b5934b'],ylabel='Artifact detection rate (%)')
    rows=list(csv.DictReader((out/'training-curves-digitized.csv').open()))
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.0))
    for ax,split in zip(axes,['Training','Validation']):
        for variant,color in [('Augmentation V2','#b5934b'),('Gold-Rescue',TEAL)]:
            pts=[r for r in rows if r['split']==split and r['variant']==variant]
            ax.plot([float(r['step']) for r in pts],[100*float(r['accuracy']) for r in pts],label=variant,color=color,linewidth=2)
        ax.set_title(split+' · overall accuracy',loc='left',fontsize=12)
        ax.set_xlabel('Training step');ax.set_ylabel('Accuracy (%)')
        ax.grid(True,color=LINE,alpha=.6);ax.set_xlim(0,94)
    axes[0].legend(frameon=False,fontsize=9,loc='lower right');fig.tight_layout(w_pad=3);save_chart(fig,out,'training-curves')


def circle(d,x,y,r,fill,stroke='none',width=1):
    d.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')


def cart(d,x,y,color):
    d.rect(x,y,88,49,color,color,5)
    d.parts.append(f'<path d="M {x-15},{y-12} L {x-5},{y-12} L {x+5},{y+48}" fill="none" stroke="{INK}" stroke-width="5"/>')
    for xx in [x+20,x+68]:circle(d,xx,y+58,10,INK)


def robot(d,x,y,scale=1,defect=False,variant=False):
    # Original geometric artwork, with no raster image or external reference.
    d.parts.append(f'<g transform="translate({x},{y}) scale({scale})">')
    d.rect(-55,-50,110,95,'#a8d6c9',TEAL,15)
    if variant:
        d.parts.append(f'<path d="M -30,-25 L -5,-10 L -30,5 Z" fill="{CORAL}"/>')
        circle(d,24,-10,9,CORAL)
    else:
        for xx in [-23,23]:circle(d,xx,-10,8,INK)
    d.parts.append(f'<path d="M -22,22 L 22,22" stroke="{INK}" stroke-width="5"/>')
    d.rect(-40,59,80,60,'#bfd9e4','#bfd9e4',8)
    path='M 0,-50 L 0,-75 L 16,-66 L 0,-91 L -18,-76 L 0,-75' if defect else 'M 0,-50 L 0,-82'
    d.parts.append(f'<path d="{path}" stroke="{CORAL if defect else TEAL}" stroke-width="5" fill="none"/>')
    d.parts.append('</g>')


def illustrative_cases(out):
    d=Diagram(1100,480,'Fictional courtyard editing example')
    d.label('ORIGINAL SCHEMATIC ARTWORK · ILLUSTRATIVE, NOT A PROJECT SAMPLE')
    for x,title in [(30,'Original video'),(580,'Edited video')]:
        d.rect(x,65,490,325,SAND);d.text(x+24,100,title,21,weight=600)
        d.rect(x+165,130,150,70,'#d1ded9',LINE,2)
        d.text(x+240,175,'Gate',18,MUTED,anchor='middle')
        cart(d,x+65,260,CORAL if x==30 else TEAL);cart(d,x+300,260,CORAL)
        if x==580:
            for tx in [x+90,x+390]:
                d.rect(tx-5,181,10,46,'#a48b70','#a48b70',2);circle(d,tx,167,29,'#81b69d')
    d.text(275,430,'Two red carts',20,MUTED,anchor='middle')
    d.text(825,430,'One cart remains red: incomplete edit',19,CORAL,anchor='middle')
    d.save(out,'courtyard-example')
    d=Diagram(1100,580,'Fictional dialogue edit with a lip-sync failure')
    d.label('FICTIONAL DIALOGUE · WORDS CHANGE, LIP TIMING DOES NOT')
    for x,title,lines in [(30,'Original video',['Meet me at noon','I’ll bring lunch']),(580,'Edited video',['Meet me at dusk','I’ll bring a lantern'])]:
        d.rect(x,65,490,440,SAND if x==30 else LIGHT)
        d.text(x+25,102,title,22,weight=600)
        for j,txt in enumerate(lines):
            px=x+65+j*220
            circle(d,px+70,197,32,'#bed6dd' if j==0 else '#d9c6ad')
            d.rect(px+35,235,70,74,'#9dbbb3' if j==0 else '#b8a2aa',INK,10)
            d.rect(px-15,330,175,63,'white',LINE,10);d.text(px+72,354,txt,16,anchor='middle',wrap=19)
        for row,label in enumerate(['Speech timing','Lip timing']):
            yy=435+row*36;d.text(x+20,yy,label,13,MUTED)
            start=x+150+(50 if x==580 and row==0 else 0)
            d.rect(start,yy-13,185,15,TEAL if row==0 else '#b5934b',radius=3)
    d.text(550,548,'Content checks: pass  /  Lip-sync checks: fail',21,TEAL,anchor='middle')
    d.save(out,'dialogue-example')
    d=Diagram(1100,480,'Fictional visual edit with an audio-preservation failure')
    d.label('ILLUSTRATIVE AUDIO-PRESERVATION FAILURE · NO ORIGINAL MEDIA')
    for x,title,color in [(30,'Original video',CORAL),(580,'Edited video',TEAL)]:
        d.rect(x,65,490,310,SAND);d.text(x+25,103,title,22,weight=600)
        cart(d,x+200,170,color)
        pts=[]
        for i in range(65):
            yy=302+np.sin(i*(.65 if x==30 else 1.17))*(10+9*np.sin(i*.19)**2)
            pts.append((x+50+i*6,round(float(yy),2)))
        d.parts.append(f'<polyline points="{" ".join(f"{a},{b}" for a,b in pts)}" fill="none" stroke="{TEAL if x==30 else CORAL}" stroke-width="3"/>')
        d.text(x+245,348,'Original audio' if x==30 else 'Unexpectedly changed audio',17,MUTED,anchor='middle')
    d.text(550,435,'Requested visual replacement: pass  /  Audio preservation: fail',20,TEAL,anchor='middle')
    d.save(out,'audio-example')
    d=Diagram(1100,520,'Illustrative spatial defect and local inspection')
    d.label('ORIGINAL SCHEMATIC ARTWORK · INSPECT A SMALL LOCAL DEFECT')
    d.rect(30,65,490,350,SAND);d.text(55,103,'Global video view',22,weight=600)
    robot(d,275,245,.9,defect=True)
    d.rect(250,153,50,44,'none',CORAL,2)
    d.arrow(527,235,574,235)
    d.rect(580,65,490,350,LIGHT);d.text(605,103,'Crop / zoom inspection',22,weight=600)
    d.parts.append('<defs><clipPath id="detail-crop"><rect x="582" y="120" width="486" height="290"/></clipPath></defs><g clip-path="url(#detail-crop)">')
    robot(d,825,340,2.1,defect=True)
    d.parts.append('</g>')
    d.text(550,473,'A small malformed antenna becomes easier to judge after cropping.',19,MUTED,anchor='middle')
    d.save(out,'spatial-example')
    d=Diagram(1100,460,'Illustrative transient quality artifact')
    d.label('FICTIONAL TEMPORAL SEQUENCE · AN ARTIFACT APPEARS AND RECOVERS')
    for i,label in enumerate(['Frame t − 1','Frame t','Frame t + 1']):
        x=30+i*365;d.rect(x,65,310,300,SAND if i!=1 else '#fff0eb',CORAL if i==1 else LINE)
        d.text(x+155,108,label,21,anchor='middle',weight=600)
        robot(d,x+155,220,.9,variant=i==1)
    d.text(550,417,'A brief shape inconsistency calls for neighboring-frame inspection.',19,MUTED,anchor='middle')
    d.save(out,'temporal-example')


def par_at_a_glance(out):
    """Original fictional case; every answer and probability is illustrative."""
    d = Diagram(1200, 1640, "PAR at a glance: from expert criteria to interpretable rewards",
                "A fictional dialogue edit demonstrates the handbook as a system prompt, "
                "task-specific atomic questions, ordered binary answers, normalized token "
                "probabilities, and agreement with an illustrative human diagnosis. "
                "All images, answers, and probabilities are illustrative, not experiment outputs.")
    d.label("PAR AT A GLANCE / ONE TASK, EXPLICIT CHECKS, EXPLAINABLE FEEDBACK")
    d.text(30, 79, "Define what matters. Ask precisely. Verify each requirement.", 30, weight=600)
    d.text(30, 111, "Fictional dialogue edit · newly drawn media · illustrative answers and probabilities", 19, MUTED)
    cards = [
        (30, "1  Rubric Handbook", "System prompt for the generator\nAtomic, task-grounded questions\nCategory / subcategory pool"),
        (425, "2  Rubric Generator", "Handbook + editing instruction\nSelect applicable criteria\nGenerate checks Q1–Q5"),
        (820, "3  Rubric Verifier", "Original + edited video + rubrics\nAnswer Q1–Q5 in order\nReturn bits and rubric scores")]
    for x, title, body in cards:
        d.rect(x, 139, 350, 165, LIGHT if x != 820 else '#eef2f6')
        d.text(x+20, 176, title, 24, weight=600)
        d.text(x+20, 212, body, 19, MUTED, line=1.6)
    d.arrow(384, 219, 418, 219)
    d.arrow(779, 219, 813, 219)
    d.rect(30, 326, 1140, 94, '#f1f4f7')
    d.text(50, 355, "EDITING INSTRUCTION", 15, TEAL, 600)
    d.text(50, 383, 'Change “Meet me at noon” to “Meet me at dusk,” and “I’ll bring lunch” to “I’ll bring a lantern.”', 20)
    d.text(50, 409, 'Keep both speakers’ lips synchronized and preserve dialogue outside this exchange.', 20)

    for x, title, lines, edited in [
            (30, "Original video", ['Meet me at noon', 'I’ll bring lunch'], False),
            (615, "Edited video", ['Meet me at dusk', 'I’ll bring a lantern'], True)]:
        d.rect(x, 442, 555, 300, SAND if not edited else LIGHT)
        d.text(x+20, 476, title, 23, weight=600)
        d.rect(x+20, 494, 515, 161, '#f4f6f3', radius=6)
        d.rect(x+220, 501, 92, 90, '#e1e9e4', '#d1ded9', 2)
        for j, words in enumerate(lines):
            cx = x+143+j*268
            circle(d, cx, 533, 25, '#bed6dd' if j==0 else '#d9c6ad')
            for ex in [-8,8]:circle(d, cx+ex, 529, 2, INK)
            d.parts.append(f'<path d="M {cx-6},544 L {cx+6},544" stroke="{INK}" stroke-width="3"/>')
            d.rect(cx-28, 563, 56, 49, '#9dbbb3' if j==0 else '#b8a2aa', radius=8)
            d.rect(cx-119, 617, 238, 30, 'white', LINE, 5)
            d.text(cx, 639, words, 18, anchor='middle')
        for j, label in enumerate(['Speech timing', 'Lip timing']):
            yy = 680+j*34
            d.text(x+20, yy, label, 17, MUTED)
            d.parts.append(f'<path d="M {x+165},{yy-6} H {x+524}" stroke="{LINE}" stroke-width="9"/>')
            start=x+180+(40 if edited and j==0 else 0)
            for offset in [0,150]:d.rect(start+offset, yy-14, 112, 16, TEAL if j==0 else '#b5934b', radius=3)
        if edited:
            d.parts.append(f'<path d="M {x+180},727 H {x+220}" stroke="{CORAL}" stroke-width="3"/>')

    d.text(30, 782, "Atomic questions, grounded in the instruction", 24, weight=600)
    d.text(30, 813, "s = p(1) / [p(1) + p(0)]  ·  p(1), p(0): next-token probabilities at each answer position", 19, MUTED)
    d.text(30, 841, "1 = requirement satisfied; 0 = not satisfied  ·  Human column: illustrative expert labels", 18, MUTED)
    # Fixed column positions keep the rubric text and numerical outputs separate.
    d.rect(30, 862, 1140, 52, '#edf2f0', radius=5)
    d.text(48, 895, "Generated rubric / category → subcategory", 18, weight=600)
    for xx, name in [(745,'Bit'),(837,'p(1)'),(930,'p(0)'),(1024,'s'),(1120,'Human')]:
        d.text(xx, 895, name, 18, weight=600, anchor='middle')
    rows = [
        ('Q1', 'Audio Editing → Dialogue Content', 'Does the first speaker now say “Meet me at dusk”?', '1', .81, .09, .90),
        ('Q2', 'Audio Editing → Dialogue Content', 'Does the reply now say “I’ll bring a lantern”?', '1', .72, .08, .90),
        ('Q3', 'Cross-Modal Editing → Lip Synchronization', 'Are the first speaker’s lips synchronized with the new speech?', '0', .09, .81, .10),
        ('Q4', 'Cross-Modal Editing → Lip Synchronization', 'Are the second speaker’s lips synchronized with the new reply?', '0', .18, .72, .20),
        ('Q5', 'Content Preservation → Audio Preservation', 'Is dialogue outside the edited exchange preserved?', '1', .81, .09, .90)]
    for i, (qid, path, question, bit, p1, p0, score) in enumerate(rows):
        y=914+i*96
        fill='#fff0eb' if bit=='0' else ('#fbfcfb' if i%2==0 else 'white')
        d.rect(30,y,1140,96,fill,LINE,0)
        d.text(48,y+28,qid+'  '+path,16,TEAL,600)
        d.text(48,y+58,question,20,wrap=60,line=1.25)
        circle(d,745,y+48,18, '#f9ded3' if bit=='0' else '#d9ece3')
        d.text(745,y+55,bit,21,CORAL if bit=='0' else TEAL,700,'middle')
        for xx,value in [(837,p1),(930,p0),(1024,score)]:
            d.text(xx,y+55,f'{value:.2f}',20,weight=600 if xx==1024 else 400,anchor='middle')
        d.text(1120,y+55,bit,21,CORAL if bit=='0' else TEAL,600,'middle')
    d.rect(30, 1416, 555, 83, '#eef2f6')
    d.text(50, 1446, "ORDERED BINARY OUTPUT", 15, MUTED, 600)
    d.text(50, 1479, "11001  ·  3 / 5 checks pass", 27, weight=600)
    d.rect(605, 1416, 565, 83, '#eef2f6')
    d.text(625, 1446, "ILLUSTRATIVE AGGREGATE REWARD", 15, MUTED, 600)
    d.text(625, 1479, "Mean(s) = 0.60  ·  equal weights", 27, weight=600)
    d.rect(30, 1520, 1140, 90, LIGHT)
    d.text(50, 1553, "MODEL + HUMAN DIAGNOSIS (ILLUSTRATIVE)", 15, TEAL, 600)
    d.text(50, 1586, "Dialogue: correct. Lip synchronization: wrong. The failing requirements are explicit.", 23, weight=600)
    d.save(out, 'par-at-a-glance')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='assets/images/par')
    args=parser.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    diagrams(out);charts(out);illustrative_cases(out);par_at_a_glance(out)
    print('Rebuilt experiment figures and original schematic cases')


if __name__=='__main__':main()
