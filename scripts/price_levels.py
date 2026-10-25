"""Approximate price bands per ordinary bottle/can, never per litre."""
from bisect import bisect_left
import math

LIMITS = {"bottle": (1000, 3000, 6000, 15000), "beer": (150, 300, 500, 1000)}

# Reference boundaries are used only when there are too few distinct products
# for a category distribution. Public UI shows relative levels, not these numbers.
REFERENCE = {
    'wine': (1000, 2000, 4000, 10000), 'sparkling': (700, 1500, 3000, 7000),
    'vodka': (500, 1000, 2000, 4000), 'whisky': (1500, 3000, 6000, 15000),
    'cognac': (1500, 3500, 7000, 15000), 'brandy': (1000, 2000, 4000, 8000),
    'rum': (1200, 2500, 5000, 10000), 'gin': (1000, 2000, 4000, 7000),
    'tequila': (2000, 3500, 6000, 12000), 'liqueur': (1000, 2000, 3500, 6000),
    'beer': (150, 300, 500, 1000), 'cider': (150, 300, 500, 1000),
    'soju': (500, 1000, 1500, 2500), 'sake': (1000, 2000, 4000, 7000),
    'vermouth': (700, 1500, 2500, 5000), 'aperitif': (1000, 2000, 3500, 6000),
    'fortified': (1000, 2500, 5000, 10000), 'other': (1000, 3000, 6000, 15000),
}


def category(kind, sparkling=False):
    if kind == 'Игристое вино' or (kind == 'Вино' and sparkling): return 'sparkling'
    return {'Вино':'wine','Водка':'vodka','Виски':'whisky','Коньяк':'cognac',
            'Бренди':'brandy','Ром':'rum','Джин':'gin','Текила':'tequila',
            'Ликёр':'liqueur','Пиво':'beer','Сидр':'cider','Соджу':'soju',
            'Сакэ':'sake','Вермут':'vermouth','Аперитив':'aperitif',
            'Портвейн':'fortified','Херес':'fortified'}.get(kind,'other')


def category_limits(prices, scale):
    """Robust category calibration, regularised for sparse/skewed retailer samples."""
    values=sorted(p for p in prices if math.isfinite(p) and p>0)
    reference=REFERENCE[scale]
    if len(values)<5: return reference
    bounds=[]
    for q, anchor in zip((.20,.50,.80,.95), reference):
        empirical=values[round((len(values)-1)*q)]
        # Sparse samples gradually yield to observations; established samples
        # use their actual distribution rather than hidden fixed ruble bands.
        weight=min(len(values)/20,1)
        value=anchor*(1-weight)+empirical*weight
        step=25 if scale in ('beer','cider') else 100
        rounded=max(step,round(value/step)*step)
        bounds.append(max(rounded,bounds[-1]+step) if bounds else rounded)
    return tuple(bounds)


def relative_level(price, boundaries):
    if not math.isfinite(price) or price<=0: raise ValueError('Price must be finite and positive')
    return bisect_left(boundaries,price)+1


def level(price, scale):
    if price <= 0:
        raise ValueError("Price must be positive")
    return bisect_left(LIMITS[scale], price) + 1


def ordinary_volume(ml, scale):
    if scale in ('beer','cider'): return 330 <= ml <= 568
    if scale == 'soju': return 350 <= ml <= 375
    if scale in ('wine','sparkling','bottle'): return 700 <= ml <= 1000
    return 500 <= ml <= 1000


def reference_volume(scale):
    return 360 if scale=='soju' else 500 if scale in ('beer','cider','vodka') else 750 if scale in ('wine','sparkling','fortified','vermouth') else 700
