// Progressive enhancement: the article and all figures work without JavaScript.
(() => {
  const images = Array.from(document.querySelectorAll('.par-article figure > img, .par-article .case-media img'));
  if (typeof HTMLDialogElement !== 'undefined' && images.length) {
    const dialog = document.createElement('dialog');
    dialog.className = 'par-lightbox';
    dialog.setAttribute('aria-label', 'Enlarged article figure');
    dialog.innerHTML = '<form method="dialog"><span>Figure detail</span><button type="submit" aria-label="Close enlarged figure">Close ×</button></form><div class="lightbox-scroll"><img alt=""></div>';
    document.body.appendChild(dialog);
    const large = dialog.querySelector('img');
    images.forEach(image => {
      image.tabIndex = 0;
      image.setAttribute('role', 'button');
      image.setAttribute('aria-label', `Enlarge figure: ${image.alt}`);
      image.classList.add('zoomable');
      const open = () => {
        large.src = image.currentSrc || image.src;
        large.alt = image.alt;
        dialog.showModal();
      };
      image.addEventListener('click', open);
      image.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          open();
        }
      });
    });
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
  }
  const links = Array.from(document.querySelectorAll('.par-toc nav a'));
  if (!links.length || !('IntersectionObserver' in window)) return;
  const byId = new Map(links.map(link => [link.hash.slice(1), link]));
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      links.forEach(link => {
        link.classList.remove('active');
        link.removeAttribute('aria-current');
      });
      const link = byId.get(entry.target.id);
      if (link) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'location');
      }
    }
  }, { rootMargin: `-${Math.round(innerHeight * 0.05)}px 0px -${Math.round(innerHeight * 0.75)}px 0px`, threshold: 0 });
  byId.forEach((_, id) => {
    const section = document.getElementById(id);
    if (section) observer.observe(section);
  });
})();
