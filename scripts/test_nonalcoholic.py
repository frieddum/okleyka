"""Reviewed NA identities, per-product retail evidence and dedicated-page metadata."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
read = lambda name: json.loads((root / name).read_text(encoding='utf-8'))
data = read('_site/data/verified.json')
meta = read('_site/data/meta.json')
rows = {r[0]: r for r in data['records']}
na = data['nonalcoholic']
nets = lambda rid: {meta['dicts']['networks'][i] for i in rows[rid][2]}
assert na and set(na) <= rows.keys()
assert {'7eacf7fe73', 'rfa-e3136e955b08', 'rfa-463c39c34182'} <= na.keys()
for rid, attrs in na.items():
    assert rows[rid][11] is None or rows[rid][11] <= 0.5, rid
    assert attrs.get('abv_max', 0) <= 0.5, rid

# Restore two priced Carl Jung products, retaining the unpriced Cabernet globally.
for rid in ['eb88569786', 'edba5ca165']:
    assert rid in na and 'Пятёрочка' in nets(rid)
    assert rid in data['price_levels']
cab = '0b9fc1eb17'
assert cab in na and rows[cab][1] == 'v'
assert not rows[cab][2] and cab not in data['price_levels']
for rid in ['eb88569786', 'edba5ca165', cab]:
    assert meta['dicts']['countries'][rows[rid][6]] == 'Германия'
    assert meta['dicts']['producers'][rows[rid][5]] == 'Carl Jung GmbH'

# Original/Classic is one product across volumes and stores; old links survive.
original = '0bfedfa5c6'
for alias in ['2608d4481b', 'rfa-69c5f44b5e98']:
    assert alias not in rows and data['aliases'][alias] == original
assert {'ВкусВилл', 'Пятёрочка', 'Магнит', 'Ароматный Мир'} <= nets(original)
assert na[original]['abv_max'] == 0.5
# 0.0 is a separate Paulaner expression, not a rename of its older NA beer.
assert {'na-paulaner-weissbier-00', 'rfa-dd6823095d52'} <= na.keys()
assert rows['na-paulaner-weissbier-00'][11] == 0

for rid in ['na-clausthaler-dry-hopped', 'na-clausthaler-lemon',
            'na-clausthaler-grapefruit', 'na-paulaner-weissbier-00',
            'na-budvar-nealko', 'av-1008759']:
    assert rid in na and 'ВкусВилл' in nets(rid)
    assert rid in data['price_levels']
for rid in ['na-zhiguli-barnoe', 'na-gorkovskaya-ipa']:
    assert rid in rows and rid in na and rid in data['price_levels']
# Russian beer cards are allowed in the alcohol-free section only.
for r in rows.values():
    if meta['dicts']['categories'][r[8]] == 'Пиво' and r[6] >= 0 and meta['dicts']['countries'][r[6]] == 'Россия':
        assert r[0] in na, r[0]
assert data['nonalcoholic_only_networks'] == ['Яндекс Лавка']
lavka = {rid for rid in rows if 'Яндекс Лавка' in nets(rid)}
assert len(lavka) == 8 and lavka <= na.keys()
assert lavka <= data['price_levels'].keys()
breweries = {b['name'] for b in read('_site/data/breweries.json')}
assert {'Московская пивоваренная компания', 'Горьковская пивоварня', 'Балтика'} <= breweries
assert 'ВкусВилл' not in nets('deda415bde'), '5% shelf Palm is not established as the 5.2% card'
assert not {'bembel-apfelwein-gold', 'bembel-apfelwein-pur'} & na.keys()
page = (root/'_site/nonalcoholic.html').read_text(encoding='utf8')
assert '<body data-section="nonalcoholic">' in page
assert '<title>Безалкогольное — Оклейка</title>' in page
assert 'href="nonalcoholic.html" aria-current="page"' in page
assert 'Безалкогольные аналоги' in page
content = (root/'_site/content-en.js').read_text(encoding='utf8')
assert json.loads(content.removeprefix('window.CONTENT_EN=').removesuffix(';'))['ВкусВилл'] == 'VkusVill'
print('NA subset, distinct expressions, merged aliases and priced retailer restoration: passed')
