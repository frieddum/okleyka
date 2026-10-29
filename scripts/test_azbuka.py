"""Run after build.py: reviewed AV identity, exclusions, sources and price formats."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from price_levels import ordinary_volume

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf8'))

data = read('_site/data/verified.json')
meta = read('_site/data/meta.json')['dicts']
rows = {r[0]: r for r in data['records']}
network = meta['networks'].index('Азбука вкуса')
av = {rid: r for rid, r in rows.items() if network in r[2]}
new = read('data/azbuka_additions.json')['items']
vlabel_av = {item['id'] for item in read('data/vlabel_additions.json')['items'] if any(chain['network'] == 'Азбука вкуса' for chain in item['chains'])}
assert len(set(av) - vlabel_av) == 324 and len(new) == 124
assert vlabel_av <= set(av)
# Every AV wine, including linked pre-existing cards, has complete attributes.
for row in av.values():
    if meta['categories'][row[8]] in ('Вино', 'Игристое вино', 'Портвейн', 'Херес', 'Вермут', 'Вермут и креплёное вино'):
        assert all(row[i] is not None for i in (11, 16, 17)), row[3]
assert rows['av-1017570'][17] == 'Экстра брют'  # Structured details resolve Brut/Extra Brut title.
assert rows['vr-0e93764df0'][11] == 13.9
assert rows['vr-0cc1eaed07'][11] == 14.0
assert all(rid in data['price_levels'] for rid in av)
assert data['price_levels']['av-370353']['estimated_for_ml'] == 750
assert data['price_levels']['av-370353']['market_estimate'] is True
for rid, row in av.items():
    assert row[1] in ('v', 'n')
    kind = meta['categories'][row[8]]
    country = meta['countries'][row[6]] if row[6] >= 0 else None
    assert not (kind == 'Пиво' and country == 'Россия'), row[3]
    assert len(row[2]) == len(set(row[2]))
    assessment = data['assessments'][row[15]]
    assert assessment['rationale']
    if not rid.startswith('reply-kkz-'):
        assert assessment['refs']
    if rid in data['price_levels']:
        band = data['price_levels'][rid]
        assert {'level', 'scale', 'volume_ml', 'observed_at'} <= set(band)
        assert set(band) <= {'level', 'scale', 'volume_ml', 'observed_at', 'estimated_for_ml', 'market_estimate'}
        assert 1 <= band['level'] <= 5
        assert ordinary_volume(band.get('estimated_for_ml', band['volume_ml']), band['scale'], row[3])

for item in new:
    row = av[item['id']]
    assert row[11] == item['abv'], item['id']
    for index, field in ((16, 'color'), (17, 'sugar')):
        if item.get(field):
            assert row[index] == item[field], item['id']
    assert not re.match(r'^(?:Вино|Пиво|Виски|немецкое|AOC|DOCG?|IGT|IGP|DO)\b', row[3])

assert rows['av-1014726'][17] == 'Экстра брют'
assert rows['av-1014725'][17] == 'Брют натюр'
assert rows['av-497055'][17] == 'Экстра драй'
assert rows['av-505005'][16] == 'Розовое'  # Touriga Nacional does not imply red.
assert rows['av-540078'][11] == rows['av-545880'][11] == 12.5
assert rows['av-1008759'][11] == 0.05
assert rows['av-377784'][1] == 'n'  # Opus One 2014: egg whites.
assert rows['av-1020884'][1] == 'n'  # Tignanello 2022.
assert 'av-1018166' not in rows  # ABF 1843: a different producer.
assert not any(re.search(r'7\s*Deadly', r[3], re.I) for r in av.values())

assert ordinary_volume(250, 'beer', 'Lindemans Kriek')
assert not ordinary_volume(250, 'beer', 'Other beer')
assert ordinary_volume(610, 'beer', 'Harbin Premium')
assert not ordinary_volume(610, 'beer', 'Other beer')
assert ordinary_volume(500, 'wine', 'Barberani Calcaia')
assert not ordinary_volume(500, 'wine', 'Other wine')
assert not ordinary_volume(50, 'fortified', 'ABF 1843')
public = json.dumps(new, ensure_ascii=False)
assert not re.search(r'av\.ru|₽|@|C:\\\\|price_rub', public, re.I)
print(f'Azbuka: {len(av)} cards; identity, scope, formats and privacy passed')
