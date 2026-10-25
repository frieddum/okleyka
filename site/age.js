// Подтверждение возраста. Ответ хранится только в браузере посетителя.
(function () {
  var KEY = 'okleyka-age-18';
  try { if (localStorage.getItem(KEY) === '1') return; } catch (e) {}
  var root = document.documentElement;
  root.classList.add('age-locked');

  function build() {
    var box = document.createElement('div');
    box.className = 'age-gate';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-labelledby', 'age-title');
    box.innerHTML =
      '<div class="age-card">' +
        '<p class="age-mark">18+</p>' +
        '<h2 id="age-title">Вам уже есть 18 лет?</h2>' +
        '<p>Сайт содержит сведения об алкогольной продукции и предназначен только для совершеннолетних.</p>' +
        '<div class="age-actions">' +
          '<button type="button" class="age-yes">Да, мне есть 18</button>' +
          '<button type="button" class="age-no">Нет</button>' +
        '</div>' +
        '<p class="age-refused" hidden>Сайт доступен только с 18 лет.</p>' +
      '</div>';
    box.querySelector(".age-card").prepend(window.I18N.selector());
    document.body.appendChild(box);
    window.I18N.apply(box);
    var yes = box.querySelector('.age-yes');
    yes.focus();
    yes.addEventListener('click', function () {
      try { localStorage.setItem(KEY, '1'); } catch (e) {}
      root.classList.remove('age-locked');
      box.remove();
    });
    box.querySelector('.age-no').addEventListener('click', function () {
      box.querySelector('.age-actions').hidden = true;
      box.querySelector('.age-refused').hidden = false;
    });
    box.addEventListener('keydown', function (e) {
      if (e.key === 'Tab') {
        var items = Array.from(box.querySelectorAll('select, button')).filter(el => !el.closest('[hidden]'));
        var i = items.indexOf(document.activeElement);
        e.preventDefault(); items[(i + (e.shiftKey ? -1 : 1) + items.length) % items.length].focus();
      }
    });
  }
  if (document.body) build(); else document.addEventListener('DOMContentLoaded', build);
})();
