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
assert(!main.some(r=>r.nonalcoholic));
assert.equal(main.length + na.length, data.records.length);
assert.equal(na.length, Object.keys(data.nonalcoholic).length);
const zhiguli=na.find(r=>r.id==='na-zhiguli-barnoe');
assert(zhiguli.nets.includes('ВкусВилл') && zhiguli.nets.includes('Яндекс Лавка'));
assert(na.find(r=>r.id==='0bfedfa5c6').nets.includes('ВкусВилл'));
const redirect = source.slice(source.indexOf('      const linkedId ='), source.indexOf('      ingest(verified.records);'));
function destination(id, nonalc=false) {
  let result=null;
  const context={verified:data, state:{id}, NONALCOHOLIC_PAGE:nonalc, NONALCOHOLIC:data.nonalcoholic, URL,
    location:{href:'https://okleika.win/?lang=en&id='+id, search:'?lang=en&id='+id, replace:url=>result=url}};
  vm.runInNewContext('(function(){'+redirect+'})()',context);
  return result;
}
assert.equal(destination('0bfedfa5c6'),'https://okleika.win/nonalcoholic.html?lang=en&id=0bfedfa5c6');
assert.equal(destination('2608d4481b'),'https://okleika.win/nonalcoholic.html?lang=en&id=0bfedfa5c6');
assert.equal(destination('0bfedfa5c6',true),null);
assert.equal(destination('499a3aaef3'),null);
console.log('Delivery-only retailers, hidden prices and Russian NA beer section boundaries: passed');
