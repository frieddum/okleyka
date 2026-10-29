"""A size estimate must not treat a miniature or a gift set as a regular bottle."""
from price_levels import reviewed_band

bounds = (1000, 2000, 4000, 10000)
half = reviewed_band(1500, 'wine', 375, bounds)
assert half['level'] == 3 and half['estimated_for_ml'] == 750
assert half['volume_ml'] == 375
large = reviewed_band(3000, 'wine', 1500, bounds)
assert large['level'] == 2 and large['estimated_for_ml'] == 750
regular = reviewed_band(1500, 'wine', 750, bounds)
assert regular['level'] == 2 and 'estimated_for_ml' not in regular
gift = reviewed_band(5000, 'wine', 375, bounds, gift_set=True)
assert gift['level'] == 4 and gift['gift_set'] is True
assert 'estimated_for_ml' not in gift
print('Regular-size estimates and full gift-set prices: passed')
