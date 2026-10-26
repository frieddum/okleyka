'use strict';
(() => {
  const tr = s => window.I18N.t(s);
  const PAGE = 25;
  const ST_ORDER = ['v', 'n'];
  const STATUS = {
    v: { label: 'Веганское', group: 'Веганское' },
    n: { label: 'Невеганское', group: 'Невеганское' },
  };
  const NONE = '__none';

  // Подтипы по явным словам в названии; фильтр появляется, когда выбран один вид напитка.
  const SUBTYPES = {
    'Виски': [['Односолодовый', /односолод|single malt|сингл молт/], ['Солодовый', /солодов|blended malt|pure malt|пьюа? молт|пьюр молт/],
      ['Бурбон', /бурбон|bourbon/], ['Купажированный', /купаж|blended|блендед/], ['Зерновой', /зернов|grain/]],
    'Коньяк': [['XO', /(^|[^a-zа-я])(xo|хо)([^a-zа-я]|$)/], ['VSOP', /vsop/], ['VS', /(^|[^a-zа-я])vs([^a-zа-я]|$)|very special/],
      ['Марочный', /марочн|(^|[^а-я])(кс|кввк)([^а-я]|$)/], ['Выдержанный', /выдержанн|(^|[^а-я])кв([^а-я]|$)/],
      ['3 звезды', /тр[её]хлет|3-летн|3 года|3 звезд|три зв[её]здочк/], ['4 звезды', /четыр[её]хлет|4-летн|4 года|4 звезд/],
      ['5 звёзд', /пятилет|5-летн|5 лет|5 звезд|пять зв[её]здоч/]],
    'Ром': [['Тёмный', /т[её]мн|dark|black|negro|блэк/], ['Золотой', /золот|gold|dorado|дорадо|oro/], ['Светлый', /светл|white|уайт|blanco|бланко|бел|silver|platino/]],
    'Текила': [['Silver', /silver|сильвер|plata/], ['Blanco', /blanco|бланко/], ['Gold', /gold|голд|oro/], ['Reposado', /reposado|репосадо/], ['Añejo', /a[nñ]ejo|аньехо/]],
    'Настойка': [['Перцовая', /перц|перец/], ['Кедровая', /кедр/], ['Хлебная', /хлеб|рожь|ржан|пшени/],
      ['Ягодная', /клюкв|брусн|смородин|малин|вишн|черник|облепих|рябин|землян|клубник|ежевик|ягод/],
      ['Фруктовая', /яблок|яблоч|груш|лимон|абрикос|слив|апельсин|айв|манго|персик|цитрус/]],
  };
  function subtype(kind, name) {
    const rules = SUBTYPES[kind];
    if (!rules) return null;
    const s = name.toLowerCase().replace(/ё/g, 'е');
    const hit = rules.find(([, re]) => re.test(s));
    return hit ? hit[0] : null;
  }
  const GROUPS = [
    { key: 'st', title: 'Статус', get: r => r.st,
      label: v => STATUS[v].group, order: 'fixed',
      hint: 'Здесь только позиции с сохранённым решением. Позиции каталогов без проверки не публикуются.' },
    { key: 'net', title: 'Сеть', get: r => r.nets, order: 'total' },
    { key: 'price', title: 'Ценовой уровень', get: r => r.priceLevel, order: 'fixed',
      list: ['1', '2', '3', '4', '5', NONE],
      label: v => v === NONE ? 'Без цены' : '$'.repeat(Number(v)),
      ariaLabel: v => v === NONE ? tr('Без цены') : window.formatPriceBand({ level: Number(v) }, window.I18N.lang).label },
    { key: 'kind', title: 'Вид напитка', get: r => r.cat || NONE, label: v => v === NONE ? 'Вид не указан' : v, order: 'total', limit: 8 },
    { key: 'sub', title: 'Тип', solo: true, get: r => r.sub, order: 'fixedList',
      list: Object.values(SUBTYPES).flatMap(t => t.map(x => x[0])),
      hint: 'По названию в карточке сети. Позиции без такого указания здесь не учитываются.' },
    { key: 'country', title: 'Страна', get: r => r.country || NONE,
      label: v => v === NONE ? 'Не указана' : v, order: 'total', limit: 8, search: true },
    { key: 'color', title: 'Цвет', wine: true, get: r => r.color, order: 'total' },
    { key: 'sugar', title: 'Сахар', wine: true, get: r => r.sugar, order: 'fixedList',
      list: ['Брют', 'Сухое', 'Полусухое', 'Полусладкое', 'Сладкое'] },
    { key: 'sp', title: 'Тип', wine: true, get: r => r.cat === 'Вино' ? (r.sp ? 'Игристое' : 'Тихое') : null,
      order: 'fixedList', list: ['Тихое', 'Игристое'] },
    { key: 'vin', title: 'Урожай', wine: true, get: r => r.vin == null ? null : String(r.vin), order: 'desc' },
  ];
  const GROUP = Object.fromEntries(GROUPS.map(g => [g.key, g]));

  const $ = s => document.querySelector(s);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmtInt = n => n.toLocaleString('ru-RU');
  const plural = (n, one, few, many) => {
    const a = Math.abs(n) % 100, b = a % 10;
    if (a > 10 && a < 20) return many;
    if (b > 1 && b < 5) return few;
    if (b === 1) return one;
    return many;
  };
  const records_word = n => plural(n, 'запись', 'записи', 'записей');
  const fmtShort = s => {
    const m = /^(\d{2})(\d{2})-(\d{2})-(\d{2})/.exec(s || '');
    return m ? `${m[4]}.${m[3]}.${m[2]}` : s;
  };
  const fmtVolume = r => {
    if (r.volMl != null) return r.volMl >= 1000 ? `${(r.volMl / 1000).toLocaleString('ru-RU', { maximumFractionDigits: 3 })}\u00a0л` : `${fmtInt(r.volMl)}\u00a0мл`;
    return null;
  };
  const fmtAbv = r => r.abv == null ? null : `${r.abv.toLocaleString('ru-RU')}\u202f%`;

  /* ---------- Нормализация и поиск ---------- */
  const HOMO = { 'а': 'a', 'в': 'b', 'е': 'e', 'к': 'k', 'м': 'm', 'н': 'h', 'о': 'o', 'р': 'p', 'с': 'c', 'т': 't', 'у': 'y', 'х': 'x' };
  const TR = { 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya' };
  const LAT = /[a-z]/, CYR = /[а-я]/;

  function tokenize(s) {
    if (!s) return [];
    const base = s.toLowerCase().replace(/ё/g, 'е').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/ß/g, 'ss').replace(/æ/g, 'ae').replace(/œ/g, 'oe').replace(/ø/g, 'o');
    const out = [];
    for (let t of base.split(/[^a-z0-9а-я]+/)) {
      if (!t) continue;
      if (LAT.test(t) && CYR.test(t)) {
        const fixed = t.replace(/[а-я]/g, c => HOMO[c] || c);
        if (!CYR.test(fixed)) t = fixed;
      }
      out.push(t);
    }
    return out;
  }
  function skeleton(t) {
    let s = '';
    for (const c of t) s += TR[c] !== undefined ? TR[c] : c;
    return s.replace(/dzh/g, 'j').replace(/zh/g, 'j').replace(/sch/g, 'sh').replace(/ph/g, 'f').replace(/w/g, 'v')
      .replace(/ck/g, 'k').replace(/q/g, 'k').replace(/x/g, 'ks').replace(/c(?=[eiy])/g, 's').replace(/c/g, 'k')
      .replace(/kh/g, 'h').replace(/y/g, 'i').replace(/(.)\1+/g, '$1');
  }
  function editDistance(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    let prev2 = null, prev = Array.from({ length: b.length + 1 }, (_, j) => j);
    for (let i = 1; i <= a.length; i++) {
      const cur = [i];
      let rowMin = i;
      for (let j = 1; j <= b.length; j++) {
        let v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (prev2 && i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, prev2[j - 2] + 1);
        cur[j] = v;
        if (v < rowMin) rowMin = v;
      }
      if (rowMin > max) return max + 1;
      prev2 = prev; prev = cur;
    }
    return prev[b.length];
  }
  const FIELD_W = [1, 0.9, 0.6, 0.35];

  function buildIndex(recs) {
    const vocab = new Map(), skel = new Map(), skelRep = new Map();
    const add = (map, key, val) => { let a = map.get(key); if (!a) map.set(key, a = []); a.push(val); };
    recs.forEach((r, i) => {
      const fields = [r.name, r.brand, r.producer, [r.country, r.cat].filter(Boolean).join(' ')].map(s => s ? s + ' ' + window.I18N.en(s) : s);
      fields.forEach((f, fi) => {
        const seen = new Set();
        for (const t of tokenize(f)) {
          if (seen.has(t)) continue;
          seen.add(t);
          add(vocab, t, i * 4 + fi);
          if (!/^\d+$/.test(t)) {
            const sk = skeleton(t);
            add(skel, sk, i * 4 + fi);
            if (!skelRep.has(sk) || (LAT.test(t) && !LAT.test(skelRep.get(sk)))) skelRep.set(sk, t);
          }
        }
      });
    });
    const vocabKeys = [...vocab.keys()].sort();
    const skelKeys = [...skel.keys()].sort();
    return { vocab, skel, skelRep, vocabKeys, skelKeys };
  }
  function prefixRange(keys, p) {
    let lo = 0, hi = keys.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (keys[m] < p) lo = m + 1; else hi = m; }
    const out = [];
    for (let i = lo; i < keys.length && keys[i].startsWith(p); i++) out.push(keys[i]);
    return out;
  }
  function search(qstr) {
    const qtokens = [...new Set(tokenize(qstr))];
    if (!qtokens.length || !INDEX) return null;
    const fuzzy = [];
    let acc = null;
    for (const qt of qtokens) {
      const hits = new Map();
      const put = (postings, score) => {
        for (const p of postings) {
          const ri = p >> 2, s = score * FIELD_W[p & 3];
          if ((hits.get(ri) || 0) < s) hits.set(ri, s);
        }
      };
      const isNum = /^\d+$/.test(qt);
      for (const k of prefixRange(INDEX.vocabKeys, qt)) put(INDEX.vocab.get(k), k === qt ? 10 : 7);
      if (!isNum && qt.length >= 4) {
        for (const k of INDEX.vocabKeys) if (k.length > qt.length && !k.startsWith(qt) && k.includes(qt)) put(INDEX.vocab.get(k), 4);
      }
      if (!isNum) {
        const qs = skeleton(qt);
        for (const k of prefixRange(INDEX.skelKeys, qs)) put(INDEX.skel.get(k), k === qs ? 6 : 5);
        if (!hits.size && qs.length >= 3) {
          const max = qs.length >= 7 ? 2 : 1;
          const found = [];
          for (const k of INDEX.skelKeys) {
            if (k.length < qs.length - max) continue;
            const d = editDistance(qs, k, max);
            const dp = k.length > qs.length ? editDistance(qs, k.slice(0, qs.length), max) : max + 1;
            if (d <= max || dp <= max) { put(INDEX.skel.get(k), 2); found.push(k); }
          }
          if (found.length) fuzzy.push({ q: qt, as: [...new Set(found.map(k => INDEX.skelRep.get(k)))].slice(0, 4) });
        }
      }
      if (!acc) acc = hits;
      else {
        const next = new Map();
        for (const [ri, s] of hits) if (acc.has(ri)) next.set(ri, acc.get(ri) + s);
        acc = next;
      }
      if (!acc.size) break;
    }
    return { hits: acc || new Map(), fuzzy, tokens: qtokens };
  }

  /* ---------- Данные ---------- */
  let META = null, RECS = [], BY_ID = new Map(), INDEX = null, ASSESS = [], PRICE_LEVELS = {};
  let groupTotals = {};
  const collator = new Intl.Collator(window.I18N.lang, { sensitivity: 'base', numeric: true, ignorePunctuation: true });

  function unpack(arr) {
    const d = META.dicts;
    const at = (list, i) => i < 0 ? null : list[i];
    const price = window.formatPriceBand(PRICE_LEVELS[arr[0]], window.I18N.lang);
    return {
      price,
      priceLevel: price ? String(PRICE_LEVELS[arr[0]].level) : NONE,
      id: arr[0], st: arr[1], nets: arr[2].map(i => d.networks[i]), name: arr[3], brand: at(d.brands, arr[4]),
      producer: at(d.producers, arr[5]), country: at(d.countries, arr[6]), origin: arr[7], cat: at(d.categories, arr[8]),
      volMl: arr[9], volRaw: arr[10], abv: arr[11], vin: arr[12], checked: arr[13], merged: arr[14],
      a: arr[15] >= 0 ? ASSESS[arr[15]] : null, color: arr[16], sugar: arr[17], sp: !!arr[18],
      sub: subtype(at(d.categories, arr[8]), arr[3]),
    };
  }
  function ingest(list) {
    for (const arr of list) RECS.push(unpack(arr));
    RECS.forEach(r => { const display = window.splitDrinkName(tr(r.name)); r.displayName = display.title; r.nameDetails = display.details; });
    RECS.sort((a, b) => collator.compare(a.displayName, b.displayName));
    RECS.forEach((r, i) => { r.rank = i; r.nameKey = tokenize(r.name).join(' '); r.brandKey = r.brand ? tokenize(r.brand).join(' ') : null; });
    BY_ID = new Map(RECS.map(r => [r.id, r]));
    INDEX = buildIndex(RECS);
    groupTotals = {};
    for (const g of GROUPS) {
      const m = new Map();
      for (const r of RECS) for (const v of values(g, r)) m.set(v, (m.get(v) || 0) + 1);
      groupTotals[g.key] = m;
    }
  }

  // Значения группы для записи: у сети их может быть несколько, у остальных групп одно или ни одного.
  function values(g, r) {
    const v = g.get(r);
    return Array.isArray(v) ? v : (v == null ? [] : [v]);
  }
  const passes = (g, r) => values(g, r).some(v => state.f[g.key].has(v));
  const bump = (m, g, r) => { for (const v of values(g, r)) m.set(v, (m.get(v) || 0) + 1); };

  /* ---------- Состояние и адрес ---------- */
  const state = { q: '', f: {}, sort: 'rel', p: 1, id: null, archive: false };
  GROUPS.forEach(g => state.f[g.key] = new Set());
  const DEFAULT_ST = ['v'];

  function readURL() {
    const sp = new URLSearchParams(location.search);
    state.archive = sp.get('archive') === '1';
    state.q = sp.get('q') || '';
    state.sort = ['rel', 'name'].includes(sp.get('sort')) ? sp.get('sort') : 'rel';
    state.p = Math.max(1, parseInt(sp.get('p'), 10) || 1);
    state.id = sp.get('id') || null;
    for (const g of GROUPS) {
      const raw = state.archive && g.key === 'price' ? null : sp.get(g.key);
      if (g.key === 'st') state.f.st = new Set(raw === null ? DEFAULT_ST : raw.split('').filter(c => STATUS[c]));
      else state.f[g.key] = new Set(raw ? raw.split('|').filter(v => v && (g.key !== 'price' || g.list.includes(v))) : []);
    }
    if (state.archive && sp.has('price')) writeURL(false);
  }
  function urlFor(over = {}) {
    const s = { ...state, ...over };
    const sp = new URLSearchParams();
    sp.set("lang", window.I18N.lang);
    if (s.archive) sp.set('archive', '1');
    if (s.q) sp.set('q', s.q);
    for (const g of GROUPS) {
      if (s.archive && g.key === 'price') continue;
      const set = (over.f && over.f[g.key]) || state.f[g.key];
      if (g.key === 'st') {
        const v = ST_ORDER.filter(c => set.has(c)).join('');
        if (v !== DEFAULT_ST.join('')) sp.set('st', v);
      } else if (set.size) sp.set(g.key, [...set].join('|'));
    }
    if (s.sort !== 'rel') sp.set('sort', s.sort);
    if (s.p > 1) sp.set('p', s.p);
    if (s.id) sp.set('id', s.id);
    const qs = sp.toString();
    return qs ? `?${qs}` : location.pathname;
  }
  function writeURL(push) {
    const url = urlFor();
    if (url === location.search || (url === location.pathname && !location.search)) return;
    history[push ? 'pushState' : 'replaceState'](null, '', url);
  }

  /* ---------- Выборка ---------- */
  let lastResult = null;
  function compute() {
    const sres = state.q.trim() ? search(state.q) : null;
    const base = sres ? [...sres.hits.keys()].map(i => RECS[i]) : RECS;
    const active = GROUPS.filter(g => state.f[g.key].size);
    const counts = {};
    GROUPS.forEach(g => counts[g.key] = new Map());
    const out = [];
    for (const r of base) {
      let failed = null, nfail = 0;
      for (const g of active) {
        if (!passes(g, r)) { nfail++; failed = g; if (nfail > 1) break; }
      }
      if (nfail > 1) continue;
      if (nfail === 0) {
        out.push(r);
        for (const g of GROUPS) bump(counts[g.key], g, r);
      } else {
        bump(counts[failed.key], failed, r);
      }
    }
    // Счётчики для групп без выбора тоже должны учитывать только прошедшие записи; для выбранных — без своей группы.
    // Для невыбранных групп записи, отсеянные другой группой, не учитываются (выше это уже так).
    const score = r => sres ? sres.hits.get(r.rank) : 0;
    const stIdx = r => ST_ORDER.indexOf(r.st);
    if (state.sort === 'name') out.sort((a, b) => a.rank - b.rank);
    else out.sort((a, b) => (score(b) - score(a)) || stIdx(a) - stIdx(b) || a.rank - b.rank);
    lastResult = { out, counts, sres };
    return lastResult;
  }

  /* ---------- Фильтры: построение и обновление ---------- */
  const groupEls = {};
  const expanded = new Set();
  function optionValues(g) {
    const totals = groupTotals[g.key] || new Map();
    let vals = [...totals.keys()];
    if (g.order === 'fixed') vals = (g.list || ST_ORDER).slice();
    else if (g.order === 'fixedList') vals = g.list.filter(v => totals.has(v));
    else if (g.order === 'desc') vals.sort((a, b) => b.localeCompare(a));
    else vals.sort((a, b) => (a === NONE) - (b === NONE) || totals.get(b) - totals.get(a) || collator.compare(a, b));
    return vals;
  }
  function buildFilters() {
    const body = $('#filters-body');
    body.innerHTML = '';
    let wineBox = null;
    for (const g of GROUPS) {
      if (state.archive && g.key === 'price') continue;
      const fs = document.createElement('fieldset');
      fs.className = 'fgroup';
      fs.dataset.group = g.key;
      if (g.wine) {
        if (!wineBox) {
          wineBox = document.createElement('fieldset');
          wineBox.className = 'fgroup';
          wineBox.id = 'wine-box';
          wineBox.innerHTML = '<legend>Вино</legend>';
          body.appendChild(wineBox);
        }
        fs.className = 'subgroup';
        fs.style.border = '0'; fs.style.padding = '0'; fs.style.margin = '';
        fs.innerHTML = `<legend class="sublegend">${esc(g.title)}</legend>`;
      } else {
        fs.innerHTML = `<legend>${esc(g.title)}</legend>`;
      }
      if (g.search) {
        fs.insertAdjacentHTML('beforeend', `<label class="visually-hidden" for="find-${g.key}">Найти в списке «${esc(g.title)}»</label><input class="inner-search" id="find-${g.key}" type="search" placeholder="Найти страну" autocomplete="off">`);
      }
      const list = document.createElement('div');
      list.className = 'opts';
      fs.appendChild(list);
      const items = new Map();
      for (const v of optionValues(g)) {
        const id = `f-${g.key}-${items.size}`;
        const lab = document.createElement('label');
        lab.className = 'opt';
        lab.htmlFor = id;
        const sw = g.key === 'st' ? `<span class="swatch st-${v}" aria-hidden="true"></span>` : '';
        lab.innerHTML = `<input type="checkbox" id="${id}" value="${esc(v)}"${g.ariaLabel ? ` aria-label="${esc(g.ariaLabel(v))}"` : ''}>${sw}<span class="lab">${esc(g.label ? g.label(v) : v)}</span><span class="n"></span>`;
        list.appendChild(lab);
        items.set(v, lab);
      }
      if (g.limit && items.size > g.limit) {
        fs.insertAdjacentHTML('beforeend', `<button type="button" class="more-btn" data-more="${g.key}"></button>`);
      }
      if (g.hint) fs.insertAdjacentHTML('beforeend', `<p class="hint">${esc(g.hint)}</p>`);
      (g.wine ? wineBox : body).appendChild(fs);
      groupEls[g.key] = { fs, items, more: fs.querySelector('.more-btn'), find: fs.querySelector('.inner-search') };
    }
    if (wineBox) wineBox.insertAdjacentHTML('beforeend', '<p class="hint">Цвет и сахар — по карточке сети, названию или сорту винограда. Вина без этих сведений в фильтрах не участвуют.</p>');
    body.insertAdjacentHTML('beforeend', '<div class="fgroup"><button type="button" class="reset-all" id="reset-all">Сбросить фильтры</button></div>');
  }

  function updateFilters(counts) {
    for (const g of GROUPS) {
      const el = groupEls[g.key];
      if (!el) continue;
      const sel = state.f[g.key];
      const c = counts[g.key];
      const findText = el.find ? tokenize(el.find.value).join(' ') : '';
      let shown = 0, hiddenByLimit = 0;
      const isOpen = expanded.has(g.key) || findText;
      for (const [v, lab] of el.items) {
        const n = c.get(v) || 0;
        const input = lab.firstElementChild;
        input.checked = sel.has(v);
        lab.classList.toggle('zero', n === 0);
        const nEl = lab.querySelector('.n');
        nEl.textContent = fmtInt(n);
        let visible = true;
        if (findText) visible = tokenize(window.I18N.t(g.label ? g.label(v) : v)).join(' ').includes(findText);
        else if (g.wine || g.solo || g.limit) visible = n > 0 || sel.has(v);
        if (visible && g.limit && !isOpen && !sel.has(v)) {
          if (shown >= g.limit) { visible = false; hiddenByLimit++; }
        }
        lab.hidden = !visible;
        if (visible) shown++;
      }
      if (el.more) {
        el.more.hidden = !!findText || (!expanded.has(g.key) && hiddenByLimit === 0);
        el.more.textContent = expanded.has(g.key) ? 'Свернуть' : `Показать все (${el.items.size})`;
      }
      if (g.wine) el.fs.hidden = shown === 0;
      if (g.solo) {
        const kinds = [...state.f.kind];
        el.fs.hidden = !(kinds.length === 1 && SUBTYPES[kinds[0]] && shown > 0) && !sel.size;
        el.fs.querySelector('legend').textContent = kinds.length === 1 ? `Тип: ${kinds[0].toLowerCase()}` : 'Тип';
      }
    }
    const wineBox = $('#wine-box');
    if (wineBox) wineBox.hidden = GROUPS.filter(g => g.wine).every(g => groupEls[g.key].fs.hidden);
  }

  /* ---------- Быстрые ряды (телефон) ---------- */
  function activeFilterCount() {
    let n = 0;
    for (const g of GROUPS) if (g.key !== 'st' && g.key !== 'net') n += state.f[g.key].size;
    return n;
  }
  function renderQuick(counts) {
    const st = state.f.st;
    $('#quick-status').innerHTML = ST_ORDER.map(c => {
      const n = fmtInt(counts.st.get(c) || 0);
      return `<button type="button" class="chip" data-quick="st" data-v="${c}" aria-pressed="${st.has(c)}"><span class="swatch st-${c}" style="width:9px;height:9px;border-radius:2px" aria-hidden="true"></span>${esc(STATUS[c].label)} <span class="n">${n}</span></button>`;
    }).join('');
    const nets = optionValues(GROUP.net);
    const extra = activeFilterCount();
    $('#quick-net').innerHTML =
      `<button type="button" class="chip filters-btn" id="open-filters" aria-haspopup="dialog">Все фильтры${extra ? ` <span class="badge">${extra}</span>` : ''}</button>` +
      `<button type="button" class="chip" data-quick="net" data-v="" aria-pressed="${state.f.net.size === 0}">Все сети</button>` +
      nets.map(v => `<button type="button" class="chip" data-quick="net" data-v="${esc(v)}" aria-pressed="${state.f.net.has(v)}">${esc(v)} <span class="n">${fmtInt(counts.net.get(v) || 0)}</span></button>`).join('');
  }

  /* ---------- Выдача ---------- */
  function highlight(text, tokens) {
    let html = esc(text);
    if (!tokens || !tokens.length) return html;
    const parts = tokens.filter(t => t.length > 1).map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/е/g, '[её]'));
    if (!parts.length) return html;
    const re = new RegExp(`(${parts.join('|')})`, 'giu');
    return esc(text).replace(re, '<mark>$1</mark>');
  }
  function pill(st) { return `<span class="pill st st-${st}">${esc(STATUS[st].label)}</span>`; }
  function factsHTML(r) {
    const f = [];
    if (r.nameDetails) f.push(r.nameDetails);
    if (r.brand && !r.nameKey.includes(r.brandKey)) f.push(r.brand);
    if (r.producer) f.push(r.producer);
    if (r.country) f.push(r.country);
    const vol = fmtVolume(r); if (vol) f.push(vol);
    const abv = fmtAbv(r); if (abv) f.push(abv);
    if (r.vin) f.push(`урожай ${r.vin}`);
    return f.map(x => `<span>${esc(x)}</span>`).join('');
  }
  function rowHTML(r, tokens) {
    const where = [`<span class="net">${esc(r.nets.map(tr).join(', '))}</span>`];
    const facts = factsHTML(r);
    return `<li class="row"><a href="${esc(urlFor({ id: r.id, p: state.p }))}" data-id="${esc(r.id)}">
      <div class="status-col">${pill(r.st)}</div>
      ${!state.archive && r.price ? `<span class="price-band" aria-label="${esc(r.price.label)}">${r.price.symbols}</span>` : ''}
      <div class="body">
        <div class="name">${highlight(r.displayName, tokens)}</div>
        ${facts ? `<div class="facts">${facts}</div>` : ''}
        <div class="where">${where.join('')}</div>
        ${r.a && r.a.rationale ? `<div class="why">${esc(r.a.rationale)}</div>` : ''}
      </div></a></li>`;
  }
  function tagFor(g, v) {
    const label = g.key === 'st' ? STATUS[v].label : (g.label ? g.label(v) : v);
    const accessibleLabel = g.ariaLabel ? g.ariaLabel(v) : label;
    const name = g.wine ? g.title.toLowerCase() : g.title.toLowerCase();
    return `<button type="button" class="tag" data-remove="${g.key}" data-v="${esc(v)}" aria-label="Убрать фильтр ${esc(name)}: ${esc(accessibleLabel)}">${esc(label)}<span class="x" aria-hidden="true">×</span></button>`;
  }
  function renderApplied() {
    const tags = [];
    if (state.q.trim()) tags.push(`<button type="button" class="tag" data-remove="q" aria-label="Очистить поиск">«${esc(state.q.trim())}»<span class="x" aria-hidden="true">×</span></button>`);
    for (const g of GROUPS) for (const v of state.f[g.key]) tags.push(tagFor(g, v));
    const nonDefault = state.q.trim() || GROUPS.some(g => g.key === 'st'
      ? ST_ORDER.filter(c => state.f.st.has(c)).join('') !== DEFAULT_ST.join('')
      : state.f[g.key].size);
    if (nonDefault) tags.push('<button type="button" class="tag clear" data-remove="all">Сбросить всё</button>');
    $('#applied').innerHTML = tags.join('');
  }
  function sumMap(m) { let s = 0; for (const v of m.values()) s += v; return s; }
  function renderNotices(res) {
    const notes = [];
    if (res.sres && res.sres.fuzzy.length) {
      const parts = res.sres.fuzzy.map(f => `«${esc(f.q)}» → ${f.as.map(a => `<b>${esc(a)}</b>`).join(', ')}`);
      notes.push(`<div class="notice">Точного совпадения нет, показаны похожие написания: ${parts.join('; ')}. Похожее написание не означает, что это тот же напиток.</div>`);
    }
    if (res.sres) {
      const hidden = ST_ORDER.filter(c => !state.f.st.has(c) && (res.counts.st.get(c) || 0) > 0);
      if (state.f.st.size && hidden.length) {
        const n = hidden.reduce((s, c) => s + res.counts.st.get(c), 0);
        const det = hidden.map(c => `${STATUS[c].label.toLowerCase()}: ${fmtInt(res.counts.st.get(c))}`).join(', ');
        notes.push(`<div class="notice">Ещё ${fmtInt(n)} ${plural(n, 'совпадение', 'совпадения', 'совпадений')} с другими статусами (${det}). <button type="button" data-action="all-statuses">Показать все статусы</button></div>`);
      }
    }
    $('#notices').innerHTML = notes.join('');
  }
  function renderEmpty(res) {
    const tips = [];
    if (state.q.trim()) tips.push(`<li><button type="button" data-remove="q">Очистить поиск</button></li>`);
    for (const g of GROUPS) {
      if (!state.f[g.key].size) continue;
      const n = sumMap(res.counts[g.key]);
      if (g.key === 'st') {
        if (n > 0) tips.push(`<li><button type="button" data-action="all-statuses">Показать все статусы</button>: ${fmtInt(n)} ${records_word(n)}</li>`);
      } else if (n > 0) {
        tips.push(`<li><button type="button" data-remove="${g.key}" data-v="*">Убрать фильтр «${esc(g.title)}»</button>: ${fmtInt(n)} ${records_word(n)}</li>`);
      }
    }
    return `<li class="empty"><h2>Ничего не нашлось</h2>
      <p>По этому запросу и фильтрам записей нет. В справочнике только позиции с проверенным решением, поэтому отсутствие напитка ничего не говорит о его статусе.</p>
      ${tips.length ? `<ul>${tips.join('')}</ul>` : ''}</li>`;
  }
  function pageLinks(total) {
    const pages = Math.max(1, Math.ceil(total / PAGE));
    if (state.p > pages) state.p = pages;
    const from = total ? (state.p - 1) * PAGE + 1 : 0, to = Math.min(total, state.p * PAGE);
    let html = `<span class="range">${fmtInt(from)}–${fmtInt(to)} из ${fmtInt(total)}</span>`;
    if (pages <= 1) return total ? html : '';
    const link = (p, text, label) => p === state.p
      ? `<span class="cur" aria-current="page">${text}</span>`
      : `<a href="${esc(urlFor({ p }))}" data-page="${p}"${label ? ` aria-label="${label}"` : ''}>${text}</a>`;
    if (state.p > 1) html += link(state.p - 1, '←', 'Предыдущая страница');
    const set = new Set([1, pages, state.p - 1, state.p, state.p + 1].filter(p => p >= 1 && p <= pages));
    let prev = 0;
    for (const p of [...set].sort((a, b) => a - b)) {
      if (p - prev > 1) html += '<span class="gap">…</span>';
      html += link(p, fmtInt(p), `Страница ${p}`);
      prev = p;
    }
    if (state.p < pages) html += link(state.p + 1, '→', 'Следующая страница');
    return html;
  }

  function renderList() {
    const res = compute();
    const total = res.out.length;
    $('#count').innerHTML = `${fmtInt(total)} <span class="word">${records_word(total)}</span>`;
    $('#sort').value = state.sort;
    $('#pager').innerHTML = pageLinks(total);
    const slice = res.out.slice((state.p - 1) * PAGE, state.p * PAGE);
    const tokens = res.sres ? res.sres.tokens : null;
    $('#results').innerHTML = slice.length ? slice.map(r => rowHTML(r, tokens)).join('') : renderEmpty(res);
    updateFilters(res.counts);
    renderQuick(res.counts);
    renderApplied();
    renderNotices(res);
    $('#show-results').textContent = `Показать ${fmtInt(total)} ${records_word(total)}`;
  }

  /* ---------- Карточка ---------- */
  function kv(label, value, note) {
    if (value == null || value === '') return '';
    return `<dt>${esc(label)}</dt><dd>${esc(value)}${note ? `<span class="note">${esc(note)}</span>` : ''}</dd>`;
  }
  function refHTML(ref) {
    const short = ref.url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '');
    const label = ref.type === 'Barnivore' ? 'Страница на Barnivore' : ref.type === 'VeganRussian' ? 'VeganRussian' : 'Сайт производителя';
    return `<li>${label}: <a href="${esc(ref.url)}" rel="noopener nofollow" target="_blank">${esc(short)}</a></li>`;
  }
  function renderCard() {
    const view = $('#card-view');
    const r = BY_ID.get(state.id);
    const backHref = urlFor({ id: null });
    const navigation = `<div class="card-nav"><a class="back" href="${esc(backHref)}" data-back>← К списку</a>${state.archive ? `<a class="archive-link" href="${esc(urlFor({ archive: false, id: null, p: 1 }))}">К справочнику</a>` : ''}</div>`;
    const archiveNotice = state.archive ? '<p class="notice archive-notice">Нет в наличии в проверенных сетях</p>' : '';
    if (!r) {
      document.title = 'Запись не найдена — Оклейка';
      view.innerHTML = `${navigation}${archiveNotice}
        <h1>Запись не найдена</h1><p class="sub">Возможно, данные обновились и этой записи больше нет. Позиции каталогов без проверенного решения в справочнике не публикуются. Попробуйте найти напиток через поиск.</p>`;
      return;
    }
    document.title = `${r.displayName} — ${tr('Оклейка')}`;
    const a = r.a;
    const vol = fmtVolume(r) || r.volRaw;
    let html = `${navigation}${archiveNotice}
      <div class="card-status">${pill(r.st)}${!state.archive && r.price ? ` <span class="price-band" aria-label="${esc(r.price.label)}">${r.price.symbols}</span>` : ''}</div>
      <h1>${esc(r.displayName)}</h1>
      <p class="sub">${esc(r.nets.map(tr).join(', '))}${r.checked ? ` ${fmtShort(r.checked)}` : ''}</p>
      <div class="label-box"><dl class="kv">
        ${kv('Описание', r.nameDetails)}
        ${kv('Бренд', r.brand)}
        ${kv('Производитель', r.producer)}
        ${kv('Страна', r.country)}
        ${kv('Вид', r.cat)}
        ${kv('Объём', vol)}
        ${kv('Крепость', fmtAbv(r))}
        ${kv('Урожай', r.vin)}
        ${kv('Цвет', r.color)}
        ${kv('Сахар', r.sugar)}
      </dl></div>`;
    if (a) {
      const was = { vegan: 'Веганское', nonvegan: 'Невеганское', unclear: 'Неясно', conflict: 'Противоречие' }[a.revised_from];
      const revised = was ? `<p class="note">Решение пересмотрено, раньше было «${was}».</p>` : '';
      if (a.rationale) html += `<section class="section"><h2>Почему</h2><p class="rationale">${esc(a.rationale)}</p>${revised}</section>`;
      if (a.scope.length) html += `<section class="section"><h2>Область действия</h2><ul>${a.scope.map(s => `<li>${esc(s)}</li>`).join('')}</ul></section>`;
      if (a.packaging && !/^Упаковка отдельно не проверена\.?$/.test(a.packaging)) html += `<section class="section"><h2>Упаковка</h2><p>${esc(a.packaging)}</p></section>`;
      const src = [];
      for (const ref of a.refs) {
        if (ref.type === 'producer_reply') {
          src.push(`<a href="${esc(ref.url)}?lang=${window.I18N.lang}">${esc('Ответ производителя')}</a>`);
          continue;
        }
        const short = ref.url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '');
        const date = ref.type === 'Barnivore' && a.reviewed_at ? ` <span class="src-date" title="Дата копирования">${fmtShort(a.reviewed_at)}</span>` : '';
        src.push(`<a href="${esc(ref.url)}" rel="noopener nofollow" target="_blank">${esc(short)}</a>${date}`);
      }
      if (src.length) html += `<p class="source">Источник: ${src.join(', ')}</p>`;
    }
    const same = RECS.filter(x => x !== r && x.nameKey === r.nameKey && x.nets.some(n => r.nets.includes(n)));
    if (same.length) {
      html += `<section class="section"><h2>То же название в этой сети</h2>
        <p class="note">Статус между этими записями не переносится.</p>
        <ul class="related">${same.slice(0, 12).map(x => `<li>${pill(x.st)} <a href="${esc(urlFor({ id: x.id }))}" data-id="${esc(x.id)}">${esc(x.displayName)}</a> <span class="note">${esc([fmtVolume(x), fmtAbv(x)].filter(Boolean).join(' · '))}</span></li>`).join('')}</ul></section>`;
    }
    view.innerHTML = html;
  }

  /* ---------- Переключение видов ---------- */
  let cameFromList = false;
  function renderArchiveNavigation() {
    const link = $('#archive-link');
    link.href = urlFor({ archive: !state.archive, id: null, p: 1 });
    link.textContent = state.archive ? 'К справочнику' : 'Архив';
    $('#archive-notice').hidden = !state.archive;
  }
  function render() {
    renderArchiveNavigation();
    const inCard = !!state.id;
    $('#list-view').hidden = inCard;
    $('#card-view').hidden = !inCard;
    if (inCard) renderCard();
    else {
      document.title = state.archive ? tr('Архив — Оклейка') : 'Оклейка — веганский статус алкоголя в российских сетях';
      renderList();
    }
    window.I18N.apply();
    if ($('#q').value !== state.q && document.activeElement !== $('#q')) $('#q').value = state.q;
    $('#clear-q').hidden = !state.q;
  }
  function update({ push = false, resetPage = true } = {}) {
    if (resetPage) state.p = 1;
    writeURL(push);
    render();
  }
  function openCard(id) {
    cameFromList = !state.id;
    state.id = id;
    writeURL(true);
    render();
    window.scrollTo(0, 0);
    const h = $('#card-view h1');
    if (h) { h.tabIndex = -1; h.focus({ preventScroll: true }); }
  }
  function closeCard() {
    if (cameFromList) { history.back(); return; }
    state.id = null;
    writeURL(true);
    render();
  }

  /* ---------- События ---------- */
  function toggle(key, v, on) {
    const set = state.f[key];
    if (on === undefined) on = !set.has(v);
    if (on) set.add(v); else set.delete(v);
  }
  let typingTimer = null;
  function bind() {
    const q = $('#q');
    q.addEventListener('input', () => {
      clearTimeout(typingTimer);
      $('#clear-q').hidden = !q.value;
      typingTimer = setTimeout(() => {
        state.q = q.value;
        if (state.id) state.id = null;
        update();
      }, 140);
    });
    $('#search-form').addEventListener('submit', e => {
      e.preventDefault();
      clearTimeout(typingTimer);
      state.q = q.value; state.id = null;
      update({ push: true });
      if (matchMedia('(max-width: 900px)').matches) q.blur();
    });
    $('#clear-q').addEventListener('click', () => { q.value = ''; state.q = ''; update(); q.focus(); });
    document.addEventListener('keydown', e => {
      if (e.key === '/' && !/^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement.tagName)) { e.preventDefault(); q.focus(); q.select(); }
      if (e.key === 'Escape') {
        if ($('#filters').classList.contains('open')) closeFilters();
        else if (document.activeElement === q && q.value) { q.value = ''; state.q = ''; update(); }
      }
    });
    $('#filters-body').addEventListener('change', e => {
      const t = e.target;
      if (t.type !== 'checkbox') return;
      const key = t.closest('[data-group]').dataset.group;
      toggle(key, t.value, t.checked);
      update();
    });
    $('#filters-body').addEventListener('input', e => {
      if (e.target.classList.contains('inner-search')) updateFilters(lastResult.counts);
    });
    $('#filters-body').addEventListener('click', e => {
      const more = e.target.closest('[data-more]');
      if (more) {
        const k = more.dataset.more;
        if (expanded.has(k)) expanded.delete(k); else expanded.add(k);
        updateFilters(lastResult.counts);
      }
      if (e.target.id === 'reset-all') resetAll();
    });
    $('#reset-mobile').addEventListener('click', resetAll);
    $('#sort').addEventListener('change', e => { state.sort = e.target.value; update(); });
    document.addEventListener('click', e => {
      const a = e.target.closest('a[data-id]');
      if (a && !e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) { e.preventDefault(); openCard(a.dataset.id); return; }
      const back = e.target.closest('a[data-back]');
      if (back && !e.ctrlKey && !e.metaKey && e.button === 0) { e.preventDefault(); closeCard(); return; }
      const pg = e.target.closest('a[data-page]');
      if (pg && !e.ctrlKey && !e.metaKey && e.button === 0) {
        e.preventDefault();
        state.p = +pg.dataset.page;
        update({ push: true, resetPage: false });
        window.scrollTo(0, Math.max(0, $('#results-col').getBoundingClientRect().top + window.scrollY - 90));
        $('#count').focus({ preventScroll: true });
        return;
      }
      const rm = e.target.closest('[data-remove]');
      if (rm) {
        const k = rm.dataset.remove;
        if (k === 'q') { state.q = ''; $('#q').value = ''; }
        else if (k === 'all') { resetAll(); return; }
        else if (rm.dataset.v === '*') state.f[k].clear();
        else toggle(k, rm.dataset.v, false);
        update();
        return;
      }
      const act = e.target.closest('[data-action="all-statuses"]');
      if (act) { state.f.st = new Set(ST_ORDER); update(); return; }
      const qk = e.target.closest('[data-quick]');
      if (qk) {
        const k = qk.dataset.quick, v = qk.dataset.v;
        if (k === 'net' && !v) state.f.net.clear();
        else toggle(k, v);
        update();
        const again = document.querySelector(`[data-quick="${k}"][data-v="${CSS.escape(v)}"]`);
        if (again) again.focus({ preventScroll: true });
        return;
      }
      if (e.target.closest('#open-filters')) { openFilters(); return; }
    });
    $('#close-filters').addEventListener('click', closeFilters);
    $('#show-results').addEventListener('click', () => { closeFilters(); window.scrollTo(0, 0); });
    window.addEventListener('popstate', () => {
      const wasCard = !!state.id;
      readURL();
      cameFromList = false;
      render();
      if (wasCard && !state.id && lastScroll != null) window.scrollTo(0, lastScroll);
    });
  }
  let lastScroll = null;
  window.addEventListener('scroll', () => { if (!state.id) lastScroll = window.scrollY; }, { passive: true });

  function resetAll() {
    state.q = ''; $('#q').value = '';
    for (const g of GROUPS) state.f[g.key] = new Set(g.key === 'st' ? DEFAULT_ST : []);
    expanded.clear();
    update();
  }
  let filtersOpener = null;
  function openFilters() {
    filtersOpener = document.activeElement;
    $('#filters').classList.add('open');
    $('#filters').setAttribute('role', 'dialog');
    $('#filters').setAttribute('aria-modal', 'true');
    document.body.style.overflow = 'hidden';
    $('#close-filters').focus();
  }
  function closeFilters() {
    $('#filters').classList.remove('open');
    $('#filters').removeAttribute('role');
    $('#filters').removeAttribute('aria-modal');
    document.body.style.overflow = '';
    const opener = document.getElementById('open-filters') || filtersOpener;
    if (opener) opener.focus({ preventScroll: true });
  }

  /* ---------- Запуск ---------- */
  async function getJSON(url) {
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${url}: ${res.status}`);
    return res.json();
  }
  async function start() {
    readURL();
    renderArchiveNavigation();
    $('#q').value = state.q;
    bind();
    try {
      META = await getJSON('data/meta.json');
      const ver = encodeURIComponent(META.snapshot_finished_utc || META.as_of);
      const verified = await getJSON(`data/${state.archive ? 'archive' : 'verified'}.json?v=${ver}`);
      ASSESS = verified.assessments;
      PRICE_LEVELS = verified.price_levels || {};
      ingest(verified.records);
      const missingId = state.id;
      if (!state.archive && missingId && !BY_ID.has(missingId)) {
        try {
          const archive = await getJSON(`data/archive.json?v=${ver}`);
          if (state.id === missingId && !state.archive && archive.records.some(r => r[0] === missingId)) {
            location.replace(urlFor({ archive: true }));
            return;
          }
        } catch (_) {
          // An unavailable archive must not prevent the normal missing-entry view.
        }
      }
      buildFilters();
      render();
    } catch (err) {
      $('#count').textContent = 'Не удалось загрузить данные';
      $('#results').innerHTML = '<li class="empty"><p>Файлы справочника не загрузились. Проверьте соединение и обновите страницу.</p></li>';
    }
    window.I18N.apply();
  }
  start();
})();
