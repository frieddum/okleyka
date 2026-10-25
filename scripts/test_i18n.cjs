const {readFileSync} = require('node:fs');
const {runInNewContext} = require('node:vm');
const assert = require('node:assert/strict');
const source = readFileSync(require('node:path').join(__dirname, '../site/i18n.js'), 'utf8');
function boot(search, saved, blocked = false) {
  const context = {URLSearchParams, window: {}, location: {search},
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
