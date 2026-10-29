"""Approximate price bands per ordinary bottle/can, never per litre."""
from bisect import bisect_left
import math
import re

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


def ordinary_volume(ml, scale, name=''):
    # Standard lambic bottles are 250 ml; Harbin Premium is sold in 610 ml.
    # These are ordinary retail formats, not tasting miniatures or magnums.
    if scale == 'beer':
        if ml == 250 and re.search(r'Lindemans|Kriek Boon|Mort Subite', name, re.I): return True
        if ml == 610 and re.search(r'Harbin', name, re.I): return True
        return 330 <= ml <= 568
    if scale == 'cider': return 330 <= ml <= 568
    # These dessert wines have a standard half-litre bottling.
    if scale == 'wine' and ml == 500 and re.search(r'Barberani', name, re.I) and re.search(r'Calcaia|Moscato Passito', name, re.I): return True
    # Reviewed retail formats: dessert wine in 500 ml, and the available
    # Chardonnay half-bottle. Its price must retain the 375 ml size in the UI.
    if scale == 'wine' and re.search(r'Viu Manent', name, re.I):
        if ml == 500 and re.search(r'Noble Semillon Botrytis Selection', name, re.I): return True
        if ml == 375 and re.search(r'Estate Collection Reserva Chardonnay', name, re.I): return True
    if scale == 'soju': return 350 <= ml <= 375
    if scale in ('wine','sparkling','bottle'): return 700 <= ml <= 1000
    return 500 <= ml <= 1000


def reference_volume(scale):
    return 360 if scale=='soju' else 500 if scale in ('beer','cider','vodka') else 750 if scale in ('wine','sparkling','fortified','vermouth') else 700


def reviewed_band(price, scale, ml, boundaries, name='', gift_set=False, checked=None):
    """Use an observed bottle price; estimate a regular size only as a fallback."""
    if not math.isfinite(ml) or ml <= 0:
        raise ValueError('Invalid observed volume')
    band = dict(level=0, scale=scale, volume_ml=ml, observed_at=checked)
    if gift_set:
        band['gift_set'] = True
    elif not ordinary_volume(ml, scale, name):
        band['estimated_for_ml'] = reference_volume(scale)
        price *= band['estimated_for_ml'] / ml
    band['level'] = relative_level(price, boundaries)
    return band
