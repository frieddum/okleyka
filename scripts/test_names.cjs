const assert = require('node:assert/strict');
const split = require('../site/name-format.js');
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
