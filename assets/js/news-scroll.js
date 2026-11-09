// Keep the latest three complete entries visible as text wraps across screen sizes.
(() => {
  const region = document.querySelector('.news-scroll');
  const list = region && region.querySelector('ul');
  if (!list) return;

  const resize = () => {
    const items = list.children;
    if (!items.length) return;
    const lastVisible = items[Math.min(3, items.length) - 1];
    const height = lastVisible.getBoundingClientRect().bottom - list.getBoundingClientRect().top + 8;
    region.style.setProperty('--news-visible-height', `${Math.ceil(height)}px`);
  };

  resize();
  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(list);
  else window.addEventListener('resize', resize);
  if (document.fonts) document.fonts.ready.then(resize);
})();
