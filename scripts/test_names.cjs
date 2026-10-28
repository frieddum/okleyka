const assert = require('node:assert/strict');
const split = require('../site/name-format.js');
assert.equal(split.withoutVolume('Grey Goose 40%, 700мл'), 'Grey Goose 40%');
assert.equal(split.withoutVolume('Вино 19 Crimes 0,75 л'), 'Вино 19 Crimes');
assert.equal(split.withoutVolume('Коньяк 15 лет 0.7L'), 'Коньяк 15 лет');
assert.equal(split.withoutVolume('Виски 12-летний 40%'), 'Виски 12-летний 40%');
assert.equal(split('Tequila silver Sauza Hacienda Silver').title, 'Sauza Hacienda Silver');
assert.equal(split('серебряная Sauza Асьенда Сильвер 40% 750мл').title, 'Sauza Асьенда Сильвер 40% 750мл');
assert.equal(split('Светлое пиво фильтрованное безалкогольное Clausthaler 500мл').title, 'Clausthaler 500мл');
assert.equal(split('светлое BERLINER Geschichte Wheat Beer Blond').title, 'BERLINER Geschichte Wheat Beer Blond');
assert.equal(split('Настойка Сладкая Зеленая Марка Лимонная 29%').title, 'Зеленая Марка Лимонная 29%');
assert.equal(split('Золотая Балка').title, 'Золотая Балка');
assert.equal(split('Вино Wine People Sauvignon Blanc').title, 'Wine People Sauvignon Blanc');
assert.equal(split('Whisky White Horse').title, 'White Horse');
assert.equal(split('Whisky Port Charlotte').title, 'Port Charlotte');
assert.equal(split('Шампанское Taittinger Brut').title, 'Taittinger Brut');
assert.equal(split('Пиво Пиво Trappistes Rochefort 8').title, 'Trappistes Rochefort 8');
assert.equal(split('Light filtered non-alcoholic beer Clausthaler').title, 'Clausthaler');
assert.deepEqual(split.beerTags('светлое BERLINER Geschichte Wheat Beer Blond', 'Пиво'), ['Светлое', 'Пшеничное']);
assert.deepEqual(split.beerTags('Dark Rum', 'Ром'), []);
assert.deepEqual(split.beerTags('Пиво безалкогольное светлое Clausthaler', 'Пиво'), ['Светлое', 'Безалкогольное']);
assert.deepEqual(split('0,7Л ЛИКЕР ДЕСЕРТНЫЙ JAGERMEISTER WINTER EDITION'), {
  title: 'JAGERMEISTER WINTER EDITION', details: '0,7Л · ЛИКЕР ДЕСЕРТНЫЙ'
});
assert.equal(split('Белое вино игристое Tosti Asti').title, 'Tosti Asti');
assert.equal(split('White sparkling wine Tosti Asti').title, 'Tosti Asti');
for (const name of ['19 Crimes', 'Wine People Sauvignon Blanc', 'White Horse', 'Port Charlotte', 'Red Bull', 'Вино']) {
  assert.equal(split(name).title, name);
}
assert.equal(split('Вино 19 Crimes').title, '19 Crimes');
const fs = require('node:fs'), path = require('node:path');
const rows = JSON.parse(fs.readFileSync(path.join(__dirname, '../_site/data/verified.json'))).records;
for (const r of rows) {
  const display = split(r[3]);
  assert.ok(display.title.trim(), r[3]);
  assert.equal((display.details.replaceAll(' · ', ' ') + ' ' + display.title).trim(), split.withoutQuotes(r[3]).trim(), r[3]);
}
assert.equal(split('Водка "Балчуг" XVI век, 40%, 0,5 л').title, 'Балчуг XVI век, 40%, 0,5 л');
assert.equal(split('«Зелёная марка» Лимон').title, 'Зелёная марка Лимон');
assert.equal(split('“Лыхны”, красное полусладкое').title, 'Лыхны, красное полусладкое');
assert.equal(split("Wine ‘Example’ Merlot").title, 'Example Merlot');
assert.equal(split("Виски Jack Daniel’s Old No.7").title, 'Jack Daniel’s Old No.7');
assert.equal(split("Вино Montepulciano d'Abruzzo").title, "Montepulciano d'Abruzzo");
assert.equal(split('"Wine People" Sauvignon Blanc').title, 'Wine People Sauvignon Blanc');
for (const locale of ['ru', 'en']) {
  const collator = new Intl.Collator(locale, {sensitivity:'base', numeric:true, ignorePunctuation:true});
  const sorted = ['"Зелёная марка"', 'Балчуг', 'Аберфелди'].map(n => split(n).title).sort(collator.compare);
  assert.deepEqual(sorted, ['Аберфелди', 'Балчуг', 'Зелёная марка']);
}
console.log('Name prefixes, quotation marks, preserved apostrophes and alphabetical ordering: passed');

assert.deepEqual(split.beerTags('Светлое пиво пшеничное Hofbrau Original', 'Пиво'), ['Светлое']);
assert.equal(split('5.2% Palm 750мл').title, 'Palm 750мл');
assert.equal(split('Пиво светлое 5.2% Palm 750мл').title, 'Palm 750мл');
assert.equal(split('Глинтвейн Schmitt Sohne').title, 'Schmitt Sohne');
assert.equal(split('крепкий Перечная мята Minttu 40% 500мл').title, 'Minttu 40% 500мл');
assert.equal(split('п/сл столовое лыхны Вина и воды Абхазии').title, 'лыхны Вина и воды Абхазии');
assert.equal(split('шотландский купаж Ballantines Файнест 40% 750мл').title, 'Ballantines Файнест 40% 750мл');
assert.deepEqual(split.attributes('5.2% Palm 750мл'), {abv:5.2, volumeMl:750});
assert.deepEqual(split.attributes('Хеннесси ХО 40% 0,7л'), {abv:40, volumeMl:700});
assert.equal(split.attributes('Вино 10-12%').abv, null);
