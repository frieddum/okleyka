"""Reviewed Viu Manent prices, retailer withdrawals and product identity."""
import json
from pathlib import Path
from price_levels import ordinary_volume

root = Path(__file__).resolve().parent.parent
read = lambda path: json.loads((root / path).read_text(encoding='utf-8'))
data = read('_site/data/verified.json')
meta = read('_site/data/meta.json')['dicts']
records = {r[0]: r for r in data['records']}
viu = [r for r in records.values() if meta['producers'][r[5]] == 'Viu Manent Winery']
assert len(viu) == 53
assert sum(bool(r[2]) for r in viu) == 33
for r in viu:
    assert r[1] == 'v'
    if r[2]: assert r[0] in data['price_levels'], r[0]
    else: assert r[13] is None and r[0] not in data['price_levels']
for decision in read('data/retailer_withdrawals.json'):
    r = records[decision['id']]
    assert decision['network'] not in [meta['networks'][i] for i in r[2]]
    if meta['producers'][r[5]] == 'Viu Manent Winery':
        assert r[1] == 'v'  # Losing a shop observation does not remove the wine.
assert {meta['networks'][i] for i in records['mt-6d91a2dcdd'][2]} == {'METRO', 'Ароматный Мир'}
assert data['price_levels']['rfa-59325d9504aa']['volume_ml'] == 375
assert data['price_levels']['rfa-0949550b81e8']['volume_ml'] == 500
assert data['price_levels']['rfa-120e76878009']['volume_ml'] == 500
assert ordinary_volume(375, 'wine', records['rfa-59325d9504aa'][3])
assert ordinary_volume(500, 'wine', records['rfa-0949550b81e8'][3])
assert not ordinary_volume(375, 'wine', 'Unreviewed wine')
assert not ordinary_volume(200, 'wine', records['rfa-59325d9504aa'][3])
# No-year and dated releases with different strengths are not duplicates.
assert records['rfa-5e9fb4fe5a88'][11:13] == [12.0, None]
assert records['rfa-ab88f5f1847a'][11:13] == [13.0, 2023]
print('Viu Manent: 53 products preserved; all 33 retailer-linked cards have price bands')
