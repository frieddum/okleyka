// Кнопка «Вверх»: появляется, когда страница прокручена ниже первого экрана.
(function () {
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'to-top';
  btn.hidden = true;
  btn.setAttribute('aria-label', window.I18N.t('Наверх страницы'));
  btn.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  document.body.appendChild(btn);
  var ticking = false;
  function update() {
    btn.hidden = window.scrollY < window.innerHeight;
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }, { passive: true });
  btn.addEventListener('click', function () {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
    var main = document.getElementById('main');
    if (main) { main.setAttribute('tabindex', '-1'); main.focus({ preventScroll: true }); }
  });
  update();
})();
