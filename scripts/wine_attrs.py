"""Цвет, сахар, крепость, урожай и объём вина.

Используется сборкой (scripts/build.py) и скриптом дополнения (scripts/enrich_wine.py).
Источники по убыванию надёжности: карточка сети (data/wine_attrs.json), явные слова в названии,
сорт винограда (только для цвета и только если сорт однозначно даёт цвет).
"""
import re

ROSE = r"розов\w*|розе|rosé|rose|rosato|rosado|pink|blush|ramato|white zinfandel|chiaretto|cerasuolo|clairet|ros[eé] de"
ORANGE = r"оранж\w*|orange wine|vin orange|ramato"
RED = r"красн\w*|кр\.|rosso|rouge|tinto|negre|\bred\b|rot\b|blauer|noir\b"
WHITE = r"бел(?:ое|ый|ая|ые)|бел\.|bianco|blanc\b|blanco|branco|\bwhite\b|weiss\w*|weiß\w*|blanc de blancs"
RED_GRAPES = (r"cabernet|каберне|merlot|мерло|pinot noir|пино нуар|pinot nero|shiraz|шираз|syrah|сира|malbec|мальбек|"
              r"tempranillo|темпранильо|sangiovese|санджовезе|nebbiolo|неббиоло|barbera|барбера|zinfandel|зинфандель|"
              r"pinotage|пинотаж|carmen[eè]re|карменер|primitivo|примитиво|montepulciano d|монтепульчано|corvina|корвина|"
              r"aglianico|альянико|chianti|кьянти|amarone|амароне|valpolicella|вальполичелла|barolo|бароло|barbaresco|"
              r"барбареско|bobal|бобаль|menc[ií]a|cannonau|nero d.avola|неро д.авола|negroamaro|негроамаро|gamay|"
              r"beaujolais|божоле|blaufr[aä]nkisch|zweigelt|petit verdot|bonarda|garnacha|гарнача|grenache|гренаш|"
              r"saperavi|саперави|kindzmarauli|киндзмараули|mukuzani|мукузани|kvareli|кварели|ahasheni|ахашени|"
              r"m[ée]doc|pauillac|margaux|saint-[ée]milion|pomerol|haut-m[ée]doc|ribera del duero|rioja tinto|"
              r"crozes|c[ôo]te[- ]r[ôo]tie|ch[âa]teauneuf|lagrein|dornfelder|tannat|touriga|nero di troia|teroldego")
WHITE_GRAPES = (r"chardonnay|шардоне|sauvignon blanc|совиньон блан|riesling|рислинг|pinot grigio|пино гриджио|"
                r"pinot gris|пино гри|gew[uü]rztraminer|гевюрцтраминер|chenin|шенен|viognier|вионье|verdejo|вердехо|"
                r"albari[nñ]o|альбариньо|vermentino|верментино|soave|соаве|gavi|гави|grillo|грилло|fiano|фиано|"
                r"greco|греко|torront[eé]s|торронтес|s[ée]millon|семильон|gr[uü]ner|грюнер|godello|годельо|viura|"
                r"виура|trebbiano|треббьяно|catarratto|катарратто|colombard|коломбар|aligot[eé]|алиготе|chablis|"
                r"шабли|sancerre|сансер|pouilly|vinho verde|винью верде|alvarinho|loureiro|muscadet|picpoul|"
                r"rkatsiteli|ркацители|tsinandali|цинандали|mtsvane|мцване|kisi|киси|furmint|silvaner|sylvaner|"
                r"weissburgunder|pinot blanc|пино блан|garganega|lugana|лугана|arneis|cortese|glera|глера|prosecco|"
                r"просекко|airen|macabeo|xarel|torbato|assyrtiko|ассиртико|marsanne|roussanne|sauternes|сотерн|"
                r"tokaji|токай|moscato|москато|muscat|мускат|blanc de blanc")
SUGAR = [
    ("Брют", r"экстра брют|extra brut|brut nature|брют натюр|pas dos[eé]|dosage z[ée]ro|zero dosage|брют|brut"),
    ("Полусухое", r"полусух\w*|п/сух\w*|semi[- ]?dry|demi[- ]?sec|halbtrocken|abboccato|semi[- ]?seco|off[- ]dry|feinherb"),
    ("Полусладкое", r"полуслад\w*|п/сл\w*|semi[- ]?sweet|semi[- ]?dolce|amabile|semidulce|semi[- ]?doux|moelleux"),
    ("Сладкое", r"слад(?:кое|кий|кая)|сл\.|\bsweet\b|dolce|\bdoux\b|dulce|s[uü][sß]|dessert|десертн\w*|"
                r"late harvest|auslese|beerenauslese|eiswein|ice ?wine|sauternes|сотерн|tokaji asz|moscato d.asti|"
                r"asti\b|асти\b|passito|vin santo|pedro xim[eé]nez|cream sherry|recioto"),
    ("Сухое", r"сух(?:ое|ой|ая|ие)|сух\.|\bdry\b|\bsec\b|\bsecco\b|\bseco\b|trocken|\bextra dry\b|экстра драй"),
]


def _has(pat, s):
    return re.search(rf"(?<![a-zа-яё]){pat}(?![a-zа-яё])", s) is not None


def color_from_name(name, sparkling=False):
    s = name.lower().replace("ё", "е")
    if _has(ORANGE, s):
        return "Оранжевое", "название"
    if _has(ROSE, s):
        return "Розовое", "название"
    if re.search(r"blanc de noirs", s):
        return "Белое", "название"
    red, white = _has(RED, s), _has(WHITE, s)
    if red and not white:
        return "Красное", "название"
    if white and not red:
        return "Белое", "название"
    rg, wg = _has(RED_GRAPES, s), _has(WHITE_GRAPES, s)
    if rg and not wg:
        return "Красное", "сорт"
    if wg and not rg:
        return "Белое", "сорт"
    if sparkling and not rg:
        return "Белое", "сорт"
    return None, None


def sugar_from_name(name):
    s = name.lower().replace("ё", "е")
    for label, pat in SUGAR:
        if _has(pat, s):
            return label
    return None


def abv_from_name(name):
    m = re.search(r"(?<![\d.,])(\d{1,2}(?:[.,]\d{1,2})?)\s*%", name)
    if m:
        v = float(m.group(1).replace(",", "."))
        if 0 <= v <= 23:
            return v
    return None


def vintage_from_name(name):
    years = [int(y) for y in re.findall(r"(?<!\d)(19[5-9]\d|20[0-2]\d)(?!\d)", name)]
    return years[0] if len(years) == 1 else None


def volume_from_name(name):
    s = name.lower().replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(мл|ml)\b", s)
    if m:
        return float(m.group(1))
    m = re.search(r"(?<![\d.])(\d(?:\.\d{1,3})?)\s*(л|l|литр\w*)(?![a-zа-я])", s)
    if m:
        v = float(m.group(1)) * 1000
        return v if 50 <= v <= 6000 else None
    return None
