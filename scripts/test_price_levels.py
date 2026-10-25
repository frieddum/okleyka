import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from price_levels import LIMITS, level, ordinary_volume
from import_price_levels import pasted_prices, name_key, volume

for scale, limits in LIMITS.items():
    assert level(1, scale) == 1
    for i, boundary in enumerate(limits, 1):
        assert level(boundary, scale) == i
        assert level(boundary + .01, scale) == i + 1
    assert not ordinary_volume(200, scale)
    assert not ordinary_volume(1500, scale)
assert ordinary_volume(750, 'bottle')
assert not ordinary_volume(500, 'bottle')
assert ordinary_volume(450, 'beer') and ordinary_volume(568, 'beer')
assert not ordinary_volume(750, 'beer')
assert volume('0,75 л') == 750
assert name_key('Вино «Тест» 2021, 750мл') == name_key('Вино Тест 2021, 1л')
assert name_key('Вино Тест 2021') != name_key('Вино Тест 2022')
assert list(pasted_prices('Вино Тест, 750мл\nЦена1 199 ₽\nСтарая цена1 499 ₽\n-20%\nЦена999 ₽')) == [('Вино Тест, 750мл', 1199, 750)]
print('Price boundaries, ordinary sizes, vintage identity and current-price extraction: passed')

from price_levels import category, category_limits, relative_level
assert category('Вино', True) == 'sparkling'
assert category('Вино', False) == 'wine'
assert category('Водка') == 'vodka'
assert ordinary_volume(500, 'vodka')
assert ordinary_volume(330, 'beer')
assert ordinary_volume(360, 'soju')
assert not ordinary_volume(200, 'soju')
assert relative_level(800, category_limits([800]*5, 'soju')) == 2
assert relative_level(2000, category_limits([], 'tequila')) == 1
for scale in ('wine','sparkling','vodka','tequila','beer'):
    bounds=category_limits(list(range(100,10100,100)),scale)
    assert all(a < b for a,b in zip(bounds,bounds[1:]))
    for i,bound in enumerate(bounds,1):
        assert relative_level(bound,bounds)==i
        assert relative_level(bound+.01,bounds)==i+1
print('Category-specific calibration, ordinary sizes and agreed reference cases: passed')

from collect_price_sources import key as source_key
from archive_availability import can_archive
assert source_key('Вино Лыхны 0,75 л') != source_key('Вино игристое Лыхны 0,75 л')
assert source_key('Игристое вино Test 750мл') == source_key('Вино игристое Test 0,75 л')
assert source_key('Виски Test в тубе 0,7 л') == source_key('Виски Test 700мл')
assert source_key('Виски Test Apple 700мл') != source_key('Виски Test 700мл')
negative={'availability':'unavailable','availability_scope':'catalog'}
regional={'availability':'unavailable','availability_scope':'regional'}
assert can_archive(['A'],{'A':[negative]})
assert not can_archive(['A','B'],{'A':[negative]})
assert not can_archive(['A'],{'A':[negative,{'availability':'available'}]})
assert not can_archive(['A'],{'A':[negative,{'error':'no_price'}]})
assert not can_archive(['A'],{'A':[regional]})
assert not can_archive([], {})
print('Sparkling identity and complete, nonregional archive evidence: passed')
