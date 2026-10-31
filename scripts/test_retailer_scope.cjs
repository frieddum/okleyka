const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('site/app.js', 'utf8');
const data = JSON.parse(fs.readFileSync('_site/data/verified.json', 'utf8'));
const meta = JSON.parse(fs.readFileSync('_site/data/meta.json', 'utf8'));
const unpack = source.slice(source.indexOf('  function unpack(arr)'), source.indexOf('  function beerTags(r)'));
const ingest = source.slice(source.indexOf('    for (const arr of list) {', source.indexOf('  function ingest(list)')), source.indexOf('    RECS.forEach', source.indexOf('  function ingest(list)')));
function renderScope(nonalc) {
  const context = {META:meta, PRICE_LEVELS:data.price_levels, NONALCOHOLIC:data.nonalcoholic,
    NONALCOHOLIC_ONLY_NETWORKS:data.nonalcoholic_only_networks, NONALCOHOLIC_PAGE:nonalc,
    ASSESS:data.assessments, NONE:'none', subtype:()=>'', RECS:[], list:data.records,
    window:{I18N:{lang:'ru'}, formatPriceBand:b=>b ? 'price' : null, splitDrinkName:{attributes:()=>({})}}};
  vm.createContext(context); vm.runInContext(unpack+'\n'+ingest, context);
  return context.RECS;
}
const main=renderScope(false), na=renderScope(true);
assert(!main.some(r=>r.nets.includes('Яндекс Лавка')));
assert(!main.some(r=>r.cat==='Пиво' && r.country==='Россия'));
assert.equal(na.filter(r=>r.nets.includes('Яндекс Лавка')).length, 8);
assert(na.every(r=>r.nonalcoholic));
assert(na.filter(r=>r.nets.includes('Яндекс Лавка')).every(r=>r.price));
const wine=main.find(r=>r.id==='na-vina-albali-sauvignon-blanc');
assert.equal(wine.nets.length,0); assert.equal(wine.price,null); assert.equal(wine.priceLevel,'none');
const zhiguli=na.find(r=>r.id==='na-zhiguli-barnoe');
assert(zhiguli.nets.includes('ВкусВилл') && zhiguli.nets.includes('Яндекс Лавка'));
assert(main.find(r=>r.id==='0bfedfa5c6').nets.includes('ВкусВилл'));
console.log('Delivery-only retailers, hidden prices and Russian NA beer section boundaries: passed');
