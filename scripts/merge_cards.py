"""Одна карточка на продукт: одинаковые позиции из разных сетей объединяются, сети перечисляются.

Названия в сетях пишут по-разному (латиница/кириллица, порядок слов, служебные слова),
поэтому сравнивается «скелет» названия. Объединяются только записи одного производителя,
вида, статуса, урожая, цвета и сахара; разные объёмы — одна карточка.
"""
import re
from collections import defaultdict
from difflib import SequenceMatcher

TR = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i',
      'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
      'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'iu', 'я': 'ia'}

NOISE = set("""
вино игристое шампанское красное белое розовое оранжевое сухое полусухое полусладкое сладкое брют натюр
столовое ординарное ординарный сортовое марочное выдержанное выдержанный защищенного географического указания
наименования места происхождения российское водка особая виски коньяк бренди ликер ликёр десертный джин ром
текила напиток спиртной ароматизированный виноградосодержащий газированный пиво светлое темное фильтрованное
нефильтрованное пастеризованное непастеризованное настойка горькая полусладкая сладкая купажированный шотландский
ирландский односолодовый солодовый зерновой лет года год летний летней выдержки трехлетний трёхлетний
years year old yo y.o the of de la le del di du et and в с со и на из по для
wine whisky whiskey vodka gin rum cognac liqueur tequila brandy dry brut sweet
""".split())


# Переводы и транскрипции одного слова: «Клюква» = «Кренберри» = Cranberry.
SYNONYMS = {}
for canon, variants in {
    "cranberry": "клюква клюквенная кренберри крэнберри", "ice": "айс", "cherry": "вишня вишневая черри",
    "raspberry": "малина малиновая распберри", "strawberry": "клубника клубничная строберри", "lemon": "лимон лимонная лемон",
    "orange": "апельсин апельсиновая оранж", "pear": "груша грушевая", "apple": "яблоко яблочная эппл", "peach": "персик персиковая пич",
    "honey": "мед медовая хани", "pepper": "перец перцовая пеппер", "black": "черный черная блэк блек", "white": "белый белая вайт",
    "gold": "золото золотая голд", "silver": "серебро серебряная сильвер", "platinum": "платинум платина",
    "original": "оригинальный оригинальная ориджинал", "classic": "классик классический классическая", "finest": "файнест",
    "spiced": "спайсд пряный", "currant": "смородина смородиновая", "mango": "манго", "coconut": "кокос кокосовая",
    "vanilla": "ваниль ванильная", "coffee": "кофе кофейная", "chocolate": "шоколад шоколадная", "mint": "мята мятная",
}.items():
    for w in [canon] + variants.split():
        SYNONYMS[w] = canon

LOG = []  # состав объединённых карточек, для проверки


def skeleton(name):
    s = name.lower().replace('ё', 'е')
    s = re.sub(r'\d+[.,]?\d*\s*(?:мл|л|ml|l|cl)(?![a-zа-я])', ' ', s)
    s = re.sub(r'\d+[.,]?\d*\s*[–-]?\s*\d*[.,]?\d*\s*%', ' ', s)
    toks = [t for t in re.findall(r'[a-zа-я0-9]+', s) if t not in NOISE]
    nums = frozenset(t for t in toks if t.isdigit())
    words = []
    for t in toks:
        if t.isdigit():
            continue
        t = SYNONYMS.get(t, t)
        t = ''.join(TR.get(ch, ch) for ch in t)
        for a, b in (('qu', 'k'), ('ph', 'f'), ('th', 't'), ('ck', 'k'), ('c', 'k'), ('w', 'v'), ('x', 'ks'), ('y', 'i'),
                     ('j', 'zh'), ('gh', 'g'), ('kh', 'h')):
            t = t.replace(a, b)
        t = re.sub(r'(.)\1+', r'\1', t)
        if t and t not in NOISE:
            words.append(t)
    return tuple(sorted(set(words))), nums


def same_words(a, b, threshold):
    # Каждое слово должно найти пару с похожим написанием (Джемесон/Jameson), лишних слов быть не должно:
    # иначе VS и VSOP, Anejo и Gran Anejo склеились бы.
    if len(a) != len(b):
        return False
    rest = list(b)
    for w in a:
        best = max(rest, key=lambda x: SequenceMatcher(None, w, x).ratio())
        if best != w and (abs(len(best) - len(w)) > 1 or SequenceMatcher(None, w, best).ratio() < threshold):
            return False
        rest.remove(best)
    return True


def company_key(rec, assessments):
    """Производитель по источнику: одна страница Barnivore/VR — одна компания, даже если название записано по-разному."""
    if rec[15] is not None and rec[15] >= 0:
        for ref in assessments[rec[15]]["refs"]:
            m = re.search(r"barnivore\.com/\w+/(\d+)", ref["url"])
            if m:
                return "b" + m.group(1)
            return ref["url"]
    return rec[5] if rec[5] is not None and rec[5] >= 0 else None


def merge(records, assessments, threshold=0.82):
    """records: список записей формата verified.json. Возвращает (новый список, сколько объединено)."""
    buckets = defaultdict(list)
    for i, r in enumerate(records):
        ck = company_key(r, assessments)
        if ck is None:
            continue
        buckets[(ck, r[8], r[1], r[12], r[16], r[17])].append(i)
    parent = list(range(len(records)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    sk = {}
    for idx in buckets.values():
        if len(idx) < 2:
            continue
        for i in idx:
            sk[i] = skeleton(records[i][3])
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = idx[a], idx[b]
                ri, rj = records[i], records[j]
                (wi, ni), (wj, nj) = sk[i], sk[j]
                if not wi or not wj or ni != nj:
                    continue
                if wi == wj or same_words(wi, wj, threshold):
                    parent[find(j)] = find(i)
    groups = defaultdict(list)
    for i in range(len(records)):
        groups[find(i)].append(i)
    out, merged = [], 0
    for members in groups.values():
        if len(members) == 1:
            out.append(records[members[0]])
            continue
        merged += len(members) - 1
        rs = [records[i] for i in members]
        LOG.append([r[3] for r in rs])
        # Основа — карточка с самым полным названием; пустые поля добираются из остальных.
        base = list(max(rs, key=lambda r: (len(r[2]), len(r[3]))))
        nets = []
        for r in rs:
            for n in r[2]:
                if n not in nets:
                    nets.append(n)
        base[2] = nets
        # Разные объёмы одного продукта — одна карточка, объём тогда не указывается.
        vols = {r[9] for r in rs if r[9] is not None}
        base[9] = next(iter(vols)) if len(vols) == 1 else None
        if len(vols) > 1:
            base[3] = re.sub(r",?\s*\d+[.,]?\d*\s*(?:мл|л|ml|l)(?![a-zа-я])\.?", "", base[3]).strip(" ,")
        for f in (6, 10, 11, 16, 17):
            if base[f] is None or base[f] == -1:
                base[f] = next((r[f] for r in rs if r[f] is not None and r[f] != -1), base[f])
        base[13] = max((r[13] for r in rs if r[13]), default=base[13])
        base[14] = sum(r[14] for r in rs)
        base[18] = max(r[18] for r in rs)
        out.append(base)
    return out, merged
