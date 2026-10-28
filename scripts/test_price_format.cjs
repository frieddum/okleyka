const assert = require('node:assert/strict');
const format = require('../site/price-format.js');
assert.equal(format(null, 'ru'), null);
assert.equal(format({level: 0}, 'en'), null);
for (let level = 1; level <= 5; level++) {
  assert.equal(format({level}, 'en').symbols, '$'.repeat(level));
  assert.equal(format({level}, 'en').label, `Price level ${level} of 5`);
  assert.equal(format({level}, 'ru').label, `Ценовой уровень ${level} из 5`);
  assert.equal(format({level}, 'ru').note, undefined);
}
const fs = require('node:fs');
assert.equal(format({level: 3, scale: 'wine', volume_ml: 375}, 'ru').symbols, '$$$ · 375 мл');
assert.equal(format({level: 3, scale: 'wine', volume_ml: 375}, 'en').label, 'Price level 3 of 5 · 375 ml');
assert.equal(format({level: 3, scale: 'wine', volume_ml: 750}, 'ru').symbols, '$$$');
const app = fs.readFileSync(require('node:path').join(__dirname, '../site/app.js'), 'utf8');
assert.ok(!app.includes('r.price.note'));
assert.ok(!app.includes('price-details'));
assert.ok(!app.includes('title="${esc(r.price.label)}"'));
console.log('Price symbols, accessible labels and no scale explanations in cards: passed');
