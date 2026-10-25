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
