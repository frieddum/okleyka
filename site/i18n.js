/* Presentation-only translations. Filter values and source decisions stay unchanged. */
(() => {
  'use strict';
  const requested = new URLSearchParams(location.search).get('lang');
  let saved; try { saved = localStorage.getItem('okleyka-language'); } catch (_) {}
  const lang = ['ru', 'en'].includes(requested) ? requested : saved === 'en' ? 'en' : 'ru';
  try { localStorage.setItem('okleyka-language', lang); } catch (_) {}
  document.documentElement.lang = lang;
  const words = {
    'Ценовой уровень':'Price level',
    'Описание':'Description',
    'Неясно':'Unclear', 'Противоречие':'Conflicting evidence',
    'Доминиканская Республика':'Dominican Republic','Доминикана':'Dominican Republic','Люксембург':'Luxembourg','Черногория':'Montenegro','Исландия':'Iceland','Сингапур':'Singapore','Словакия':'Slovakia','Вьетнам':'Vietnam','Таиланд':'Thailand','Литва':'Lithuania','Тринидад и Тобаго':'Trinidad and Tobago','Никарагуа':'Nicaragua','Гватемала':'Guatemala','Латвия':'Latvia','Абхазия':'Abkhazia','Турция':'Turkey','Ливан':'Lebanon','Словения':'Slovenia','Бразилия':'Brazil','Сент-Люсия':'Saint Lucia','Филиппины':'Philippines','Игристое вино':'Sparkling wine','Аперитив':'Aperitif','Писко':'Pisco','Портвейн':'Port','Херес':'Sherry','Соджу':'Soju',
    'Оклейка':'Okleika', 'Справочник':'Directory', 'Методика':'Methodology',
    'Российское пиво и сидр':'Russian beer and cider', '«Российское пиво и сидр»':'Russian beer and cider',
    'Независимый справочник веганского статуса алкоголя в российских сетях':'Independent guide to the vegan status of drinks in Russian retail chains',
    'К результатам':'Skip to results', 'К тексту':'Skip to content', 'Разделы':'Navigation',
    'Поиск по названию, бренду или производителю':'Search by name, brand or producer',
    'Название, бренд или производитель':'Name, brand or producer', 'Очистить поиск':'Clear search',
    'Фильтры':'Filters', 'Закрыть фильтры':'Close filters', 'Сбросить':'Reset', 'Показать':'Show',
    'Порядок':'Sort', 'Сначала точные совпадения':'Best matches first', 'По названию':'By name',
    'Выбранные фильтры':'Selected filters', 'Страницы выдачи':'Result pages',
    'Веганское':'Vegan', 'Невеганское':'Not vegan', 'Статус':'Status', 'Сеть':'Retail chain',
    'Вид напитка':'Drink category', 'Вид не указан':'Category not specified', 'Тип':'Type',
    'Страна':'Country', 'Не указана':'Not specified', 'Цвет':'Colour', 'Сахар':'Sweetness', 'Урожай':'Vintage',
    'Вино':'Wine', 'Виски':'Whisky', 'Коньяк':'Cognac', 'Бренди':'Brandy', 'Ром':'Rum', 'Водка':'Vodka',
    'Текила':'Tequila', 'Джин':'Gin', 'Ликёр':'Liqueur', 'Ликер':'Liqueur', 'Ликёры':'Liqueurs',
    'Настойка':'Infused spirit', 'Пиво':'Beer', 'Сидр':'Cider', 'Вермут':'Vermouth', 'Сакэ':'Sake',
    'Абсент':'Absinthe', 'Граппа':'Grappa', 'Кальвадос':'Calvados', 'Арманьяк':'Armagnac', 'Прочее':'Other',
    'Односолодовый':'Single malt', 'Солодовый':'Malt', 'Бурбон':'Bourbon', 'Купажированный':'Blended', 'Зерновой':'Grain',
    'Марочный':'Vintage', 'Выдержанный':'Aged', '3 звезды':'3 stars', '4 звезды':'4 stars', '5 звёзд':'5 stars',
    'Тёмный':'Dark', 'Золотой':'Gold', 'Светлый':'Light', 'Перцовая':'Pepper', 'Кедровая':'Pine nut',
    'Хлебная':'Grain', 'Ягодная':'Berry', 'Фруктовая':'Fruit', 'Белое':'White', 'Красное':'Red', 'Розовое':'Rosé', 'Оранжевое':'Orange',
    'Брют':'Brut', 'Экстра брют':'Extra brut', 'Сухое':'Dry', 'Полусухое':'Semi-dry', 'Полусладкое':'Semi-sweet', 'Сладкое':'Sweet',
    'Тихое':'Still', 'Игристое':'Sparkling', 'Найти страну':'Find a country', 'Свернуть':'Show less',
    'Сбросить фильтры':'Reset filters', 'Все фильтры':'All filters', 'Все сети':'All chains', 'Сбросить всё':'Reset all',
    'Показать все статусы':'Show all statuses', 'Ничего не нашлось':'No results',
    'По этому запросу и фильтрам записей нет. В справочнике только позиции с проверенным решением, поэтому отсутствие напитка ничего не говорит о его статусе.':'No entries match this search and these filters. Only reviewed decisions are included; a missing drink tells you nothing about its vegan status.',
    'Предыдущая страница':'Previous page', 'Следующая страница':'Next page', '← К списку':'← Back to results',
    'Запись не найдена':'Entry not found', 'Запись не найдена — Оклейка':'Entry not found — Okleika',
    'Возможно, данные обновились и этой записи больше нет. Позиции каталогов без проверенного решения в справочнике не публикуются. Попробуйте найти напиток через поиск.':'The data may have changed and this entry may no longer exist. Only entries with reviewed decisions are published. Try searching for the drink.',
    'Бренд':'Brand', 'Производитель':'Producer', 'Вид':'Category', 'Объём':'Volume', 'Крепость':'ABV',
    'Почему':'Reason', 'Область действия':'Scope', 'Упаковка':'Packaging', 'Источник:':'Source:', 'Дата копирования':'Date copied',
    'То же название в этой сети':'Same name in this chain', 'Статус между этими записями не переносится.':'The status of one entry does not apply to the others.',
    'Не удалось загрузить данные':'Could not load the data', 'Не удалось загрузить данные.':'Could not load the data.',
    'Файлы справочника не загрузились. Проверьте соединение и обновите страницу.':'The directory could not be loaded. Check your connection and refresh the page.',
    'Вам уже есть 18 лет?':'Are you 18 or older?', 'Сайт содержит сведения об алкогольной продукции и предназначен только для совершеннолетних.':'This site contains information about alcoholic drinks and is for adults only.',
    'Да, мне есть 18':'Yes, I am 18 or older', 'Нет':'No', 'Сайт доступен только с 18 лет.':'You must be 18 or older to access this site.',
    'Наверх страницы':'Back to top', 'Загружаю…':'Loading…', 'Ответ пивоварни':'Producer’s response', 'Не удалось загрузить список.':'Could not load the list.',
    'Проверьте состав на этикетке.':'Check the ingredients on the label.',
    'Даже у веганских пивоварен бывают сорта с лактозой (молочные стауты, «милкшейк»-IPA), мёдом, а у крафтовых — даже с мясом, рыбой, устрицами или беконом. Ответ пивоварни касается осветления и фильтрации, а не каждого рецепта.':'Even breweries using vegan production methods may make recipes with lactose (milk stouts or milkshake IPAs), honey, meat, fish, oysters or bacon. A brewery’s response about fining and filtration does not cover every recipe.',
    'Пивоварни и сидродельни, которые ответили, что не используют животные вещества при производстве и фильтрации. Ассортимент у них меняется часто, поэтому здесь ответы целиком, а не отдельные бутылки. Исключения из ответа указаны у каждой.':'Breweries and cider makers that report using no animal-derived substances in production and filtration. Their ranges change often, so this page lists producer responses rather than individual bottles. Each entry includes the exceptions stated in the response.',
    'Здесь только позиции с сохранённым решением. Позиции каталогов без проверки не публикуются.':'Only entries with a saved, reviewed decision are published.',
    'По названию в карточке сети. Позиции без такого указания здесь не учитываются.':'Based on the retailer’s product name. Entries without this detail are not included in this filter.',
    'Цвет и сахар — по карточке сети, названию или сорту винограда. Вина без этих сведений в фильтрах не участвуют.':'Colour and sweetness come from the retail listing, name or grape variety. Wines without these details are not included in these filters.',
    'Россия':'Russia','Франция':'France','Италия':'Italy','Испания':'Spain','Германия':'Germany','Португалия':'Portugal','Чили':'Chile','Аргентина':'Argentina','ЮАР':'South Africa','Австралия':'Australia','Новая Зеландия':'New Zealand','США':'USA','Австрия':'Austria','Грузия':'Georgia','Армения':'Armenia','Великобритания':'United Kingdom','Шотландия':'Scotland','Ирландия':'Ireland','Бельгия':'Belgium','Чехия':'Czechia','Польша':'Poland','Нидерланды':'Netherlands','Япония':'Japan','Мексика':'Mexico','Канада':'Canada','Швеция':'Sweden','Финляндия':'Finland','Дания':'Denmark','Норвегия':'Norway','Греция':'Greece','Венгрия':'Hungary','Румыния':'Romania','Болгария':'Bulgaria','Молдова':'Moldova','Сербия':'Serbia','Китай':'China','Индия':'India','Куба':'Cuba','Ямайка':'Jamaica','Барбадос':'Barbados','Израиль':'Israel','Уругвай':'Uruguay',
    'запись':'entry','записи':'entries','записей':'entries',
    'Как устроен справочник':'How the directory works', 'Статусы':'Statuses', 'Почему «оклейка»':'Why “Okleika”?', 'Источники':'Sources', 'Чего здесь нет':'What is not included', 'Покрытие по сетям':'Coverage by retail chain', 'С решением':'Reviewed', 'Из них веганских':'Of which vegan',
    'Здесь только напитки из российских сетей, по которым есть проверенное решение о веганском статусе:':'This directory includes drinks listed by Russian retail chains with a reviewed vegan-status decision:',
    'Если одна и та же бутылка есть в нескольких сетях, она показана одной записью со всеми сетями.':'If the same bottle appears in several chains, one entry lists all of those chains.',
    'Производитель сообщает, что животные продукты не используются.':'The producer reports that no animal-derived products are used.',
    'Используются продукты животного происхождения, например желатин или рыбий клей для осветления.':'Animal-derived products are used, such as gelatin or isinglass for fining.',
    'Вино, пиво и сидр часто осветляют, то есть оклеивают. Иногда для этого берут желатин, рыбий клей, казеин или яичный белок. На этикетке это не пишут, поэтому статус выясняют у производителя.':'Okleika is Russian for fining. Wine, beer and cider are often clarified using gelatin, isinglass, casein or egg white. These processing aids may not appear on the label, so we rely on the producer’s response.',
    'Решения опираются на ответы производителей, опубликованные на Barnivore и':'Decisions rely on producer responses published on Barnivore and',
    ', и на сайты производителей. Если ответ производителя расходится с плашкой Barnivore, верен ответ производителя. Ответ об одной линейке не переносится на весь бренд: в карточке указано, на что он распространяется. Если на Barnivore нет записи о самой бутылке, она публикуется, только когда производитель ответил про всю свою продукцию.':', as well as producers’ websites. If a producer’s response differs from the Barnivore badge, the response takes priority. A statement about one range is not applied to the whole brand: each entry states its scope. If Barnivore has no entry for the bottle itself, it is included only when the producer’s response covers its entire range.',
    'В поле «Производитель» указана компания, которая ответила на запрос, а не поставщик или импортёр из карточки сети.':'The Producer field identifies the company that answered the inquiry, rather than the supplier or importer listed by the retailer.',
    'Напитков без проверенного решения и напитков, по которым нет однозначного ответа производителя: если ответ касается другого продукта, источники противоречат друг другу, компания отказывается отвечать или найден только производитель с похожим названием. Если напитка нет в справочнике, это ничего не говорит о его статусе. Точных цен и наличия в отдельных магазинах здесь нет.':'We exclude drinks without a reviewed decision or a clear producer response: responses about another product, conflicting sources, refusals to answer, and matches to a different producer with a similar name. Absence from this directory says nothing about a drink’s vegan status. Exact prices and current availability in individual shops are not listed.',
    'Бутылок, произведённых в России по лицензии зарубежного бренда, если нет ответа самого российского завода. Ответ зарубежного производителя к ним не относится. Российские вина и крепкое с ответом производителя публикуются как обычные позиции, а пивоварни собраны на отдельной странице':'Bottles made in Russia under licence from a foreign brand are excluded unless the Russian factory itself has responded. The foreign producer’s response does not apply to them. Russian wines and spirits with a producer response appear as individual entries; breweries are listed on the separate page',
    'Нашли ошибку, знаете ответ производителя или хотите добавить позицию? Напишите на':'Found an error, have a producer response, or want to suggest a drink? Email'
  };
  const content = window.CONTENT_EN || {};
  const english = s => words[s] || content[s] || s;
  function translate(s) {
    if (lang !== 'en') return s;
    const key = s.trim();
    if (Object.hasOwn(words, key)) return s.replace(key, () => words[key]);
    if (Object.hasOwn(content, key)) return s.replace(key, () => content[key]);
    return s.replace(/Точного совпадения нет, показаны похожие написания:/g, 'No exact match; showing similar spellings:').replace(/Похожее написание не означает, что это тот же напиток./g, 'Similar spelling does not establish that this is the same drink.').replace(/Решение пересмотрено, раньше было «(.+)»./g, (_, v) => 'Decision revised; previously “' + english(v) + '”.').replace(/Ещё ([\d\s ]+) совпадени[еяй] с другими статусами/g, '$1 more matches with other statuses').replace(/невеганское:/g, 'not vegan:').replace(/веганское:/g, 'vegan:').replace(/(январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь) (\d{4})/g, (_, m, y) => ({январь:'January',февраль:'February',март:'March',апрель:'April',май:'May',июнь:'June',июль:'July',август:'August',сентябрь:'September',октябрь:'October',ноябрь:'November',декабрь:'December'}[m]) + ' ' + y).replace(/^(\s*)Показать все \((\d+)\)(\s*)$/, '$1Show all ($2)$3')
      .replace(/Показать ([\d\s ]+) (запись|записи|записей)/g, 'Show $1 entries')
      .replace(/([\d\s ]+) (запись|записи|записей)/g, '$1 entries')
      .replace(/^(\d[\d\s ]*–[\d\s ]+) из /, '$1 of ')
      .replace(/^Страница (\d+)$/, 'Page $1')
      .replace(/^урожай (\d+)$/, 'vintage $1')
      .replace(/^Тип: (.+)$/, (_, v) => 'Type: ' + (words[v[0].toUpperCase()+v.slice(1)] || v))
      .replace(/^Найти в списке «(.+)»$/, (_, v) => 'Search ' + english(v))
      .replace(/^Убрать фильтр «(.+)»$/, (_, v) => 'Remove “' + english(v) + '” filter')
      .replace(/^Убрать фильтр (.+): (.+)$/, (_, a, b) => 'Remove filter: ' + english(b))
      .replace(/^(\d[\d., ]*)\s*мл$/, '$1 ml').replace(/^(\d[\d., ]*)\s*л$/, '$1 L')
      .replace(/Оклейка — веганский статус алкоголя в российских сетях/g, 'Okleika — vegan status of drinks in Russian retail chains')
      .replace(/Методика — Оклейка/g, 'Methodology — Okleika').replace(/Российское пиво и сидр — Оклейка/g, 'Russian beer and cider — Okleika');
  }
  function apply(root = document.body) {
    if (lang !== 'en' || !root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      if (n.parentElement.closest('script,style,[data-original]')) continue;
      const value = translate(n.nodeValue); if (value !== n.nodeValue) n.nodeValue = value;
    }
    root.querySelectorAll('[aria-label],[placeholder],[title]').forEach(el => {
      for (const attr of ['aria-label','placeholder','title']) if (el.hasAttribute(attr)) el.setAttribute(attr, translate(el.getAttribute(attr)));
    });
    document.title = translate(document.title);
  }
  window.I18N = { lang, t: translate, en: english, apply, selector };
  function selector() {
    const group = document.createElement('div');
    group.className = 'language-picker';
    group.setAttribute('role', 'group');
    group.setAttribute('aria-label', 'Language / Язык');
    for (const [code, name] of [['ru', 'Русский'], ['en', 'English']]) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'language-flag';
      button.title = name; button.setAttribute('aria-label', name);
      button.setAttribute('aria-pressed', String(lang === code));
      button.textContent = code === 'ru' ? 'рус' : 'eng';
      button.addEventListener('click', () => {
        if (lang === code) return;
        const url = new URL(location.href); url.searchParams.set('lang', code); location.assign(url);
      });
      group.appendChild(button);
    }
    return group;
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('.nav')?.appendChild(selector());
    document.querySelectorAll('a[href="./"],a[href="beer.html"],a[href="method.html"]').forEach(a => {
      a.setAttribute('href', a.getAttribute('href') + '?lang=' + lang);
    });
    const gate = document.querySelector('.age-card'); if (gate) gate.prepend(selector());
    apply();
  });
})();
