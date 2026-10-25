const {readFileSync} = require('node:fs');
const {runInNewContext} = require('node:vm');
const assert = require('node:assert/strict');
const source = readFileSync(require('node:path').join(__dirname, '../site/i18n.js'), 'utf8');
function boot(search, saved, blocked = false) {
  const content = JSON.parse(readFileSync(require('node:path').join(__dirname, '../data/translations_en.json'), 'utf8'));
  const context = {URLSearchParams, window: {CONTENT_EN: content}, location: {search},
    document: {documentElement: {}, addEventListener() {}},
    localStorage: {getItem() {if (blocked) throw Error(); return saved;}, setItem() {if (blocked) throw Error();}}};
  runInNewContext(source, context);
  return context.window.I18N;
}
assert.equal(boot('?lang=ru', 'en').lang, 'ru');
assert.equal(boot('?lang=en', 'ru', true).lang, 'en');
assert.equal(boot('?lang=invalid', 'en').lang, 'en');
assert.equal(boot('', null, true).lang, 'ru');
assert.equal(boot('?lang=ru').t('Веганское'), 'Веганское');
const en = boot('?lang=en');
assert.equal(en.t('Невеганское'), 'Not vegan');
assert.equal(en.t('Показать 25 записей'), 'Show 25 entries');
assert.equal(en.t('1–25 из 100'), '1–25 of 100');
assert.equal(en.t('Вино Tosti 7% 750мл'), 'Вино Tosti 7% 750мл');
assert.equal(en.t('Невеганское'), 'Not vegan');
console.log('Language selection, unavailable storage, labels and original names: passed');
assert.equal(en.t('Магнит'), 'Magnit');
assert.equal(en.t('Производитель: красные веганские, белые нет.'), 'The producer confirms that red wines are vegan; white wines are not.');
assert.equal(boot('?lang=ru').t('Магнит'), 'Магнит');
assert.equal(boot('?lang=ru').en('Магнит'), 'Magnit');
const translations = JSON.parse(readFileSync(require('node:path').join(__dirname, '../data/translations_en.json'), 'utf8'));
for (const [original, translated] of Object.entries(translations)) {
  assert.ok(translated.trim(), original);
  assert.ok(!/[А-Яа-яЁё]/.test(translated), original);
  assert.equal(en.t(original), en.en(original), original);
}
console.log('All content translations, bilingual lookup and colour-dependent scope: passed');
