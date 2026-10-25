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
  assert.equal((display.details.replaceAll(' · ', ' ') + ' ' + display.title).trim(), r[3].trim(), r[3]);
}
console.log('Name prefixes: brand safeguards and lossless display of all records passed');
