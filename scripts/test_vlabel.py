"""Certification scope and retailer evidence invariants for the reviewed V-Label additions."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
read = lambda path: json.loads((ROOT / path).read_text(encoding='utf-8'))
items = read('data/vlabel_additions.json')['items']
data = read('_site/data/verified.json')
rows = {row[0]: row for row in data['records']}
assert len(items) == len({item['id'] for item in items}) == 37
assert Counter(item['company'] for item in items) == {'Gustave Lorentz': 5, 'Mahou': 7, 'Estates Costa Lazaridi': 23, 'Poças': 2}
for item in items:
    row = rows[item['id']]
    assert row[1] == 'v' and item['scope_reviewed'] and item['ref_url'].startswith('https://')
    assert bool(row[2]) == bool(item['chains'])
    assert (item['id'] in data['price_levels']) == bool(item['chains'])
    if item['company'] == 'Gustave Lorentz':
        assert 'Évidence' in row[3]
    if item['company'] == 'Poças' and 'Coroa' in item['name']:
        assert item['vintage'] == 2023 and not item['chains']
assert sum(bool(item['chains']) for item in items) == 3
assert sum(len(item['chains']) for item in items) == 4
assert all(not item['chains'] for item in items if item['name'] == 'Poças White Port белое сладкое')
print('V-Label: 37 scoped products; 3 priced cards, 4 verified retail links; no invented availability')
