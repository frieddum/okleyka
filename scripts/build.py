"""Собирает статический сайт из публичного снимка каталога.

Запуск: python scripts/build.py [путь_к_json] [папка_вывода]
По умолчанию: data/snapshot.json -> _site/

Подготовка нового снимка: python scripts/build.py --trim путь_к_новому.json
записывает его в data/snapshot.json без раздела unmatched.

Скрипт переносит в публикуемые данные только записи с сохранённым решением
и только поля из белого списка, проверяет исходный файл на приватные данные
и останавливается при находке. Непроверенные позиции каталогов (unmatched)
не публикуются и не используются.
"""
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wine_attrs as wa  # noqa: E402
from producer_rules import RULES, color_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TRIM = len(sys.argv) > 1 and sys.argv[1] == "--trim"
ARGS = sys.argv[2:] if TRIM else sys.argv[1:]
SRC = Path(ARGS[0]) if ARGS else ROOT / "data" / "snapshot.json"
OUT = Path(ARGS[1]) if len(ARGS) > 1 else ROOT / "_site"
OVERRIDES = ROOT / "data" / "overrides.json"
EXTRA = ROOT / "data" / "catalog_extra.json"
COMPANIES = ROOT / "data" / "barnivore_companies.json"
# Производитель для ссылок на сайты самих производителей (не Barnivore).
MANUFACTURER_COUNTRY = {"williamgrant.com": "Шотландия", "hofbraeu-muenchen.de": "Германия"}
# Производители, у которых на Barnivore нет адреса со страной.
PRODUCER_COUNTRY = {
    "Bodega Catena Zapata": "Аргентина", "Ciroc": "Франция", "Cutty Sark": "Шотландия",
    "Feudi di San Gregorio": "Италия", "González Byass": "Испания", "ЗАО «Игристые вина»": "Россия",
    "Chairman's Reserve Rum": "Сент-Люсия", "Taittinger": "Франция", "Dooleys Toffee Cream Liqueur": "Германия",
    "Piccini 1882": "Италия", "La Marca": "Италия", "Sula Vineyards": "Индия",
    "The Old Bushmills Distillery": "Великобритания",
}
MANUFACTURER_SITES = {"williamgrant.com": "William Grant & Sons", "hofbraeu-muenchen.de": "Hofbräu München"}
EXTRA_CATEGORY = {"Вино": "Вино", "Игристое и шампанское": "Игристое вино", "Пиво": "Пиво",
                  "Ликёры, настойки, биттеры": "Ликёр", "Вермут и креплёные вина": "Вермут и креплёное вино",
                  "Крепкие напитки": "Крепкий алкоголь", "Сидр, перри, медовуха": "Сидр", "Прочее": "Алкогольный напиток"}

# Ссылки на доказательства публикуются только из assessment.references[].url
# и только с этих типов источников.
ALLOWED_REF_TYPES = {"Barnivore", "manufacturer", "VeganRussian"}

# Организации из карточек сетей, которые сами производят алкоголь в России (в том числе по лицензии).
# Ответ зарубежного производителя к такой бутылке не относится, поэтому эти записи не публикуются.
# Импортёры и поставщики (Симпл, Бакарди Рус, Перно Рикар Русь и т. п.) сюда не входят.
RU_PRODUCERS = {"АБ ИнБев Эфес", "ОПХ", "Калужский ЛВЗ Кристалл", "Татспиртпром"}

STATUS_CODE = {"vegan": "v", "nonvegan": "n", "unclear": "u", "conflict": "c"}

PRIVACY_PATTERNS = [
    ("адрес почты", re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)),
    ("путь Windows", re.compile(r"\b[A-Za-z]:\\\\")),
    ("путь Unix", re.compile(r"/(?:home|Users|tmp|mnt|var)/")),
    ("токен", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,}|xox[bp]-)")),
    ("mailto", re.compile(r"mailto:", re.I)),
    ("телефон", re.compile(r"\+7[\s(-]*\d{3}")),
]


def fail(msg):
    print("ОШИБКА:", msg, file=sys.stderr)
    sys.exit(1)


def privacy_check(raw, data):
    for label, pat in PRIVACY_PATTERNS:
        m = pat.search(raw)
        if m:
            fail(f"в исходном JSON найдено похожее на «{label}»: {m.group(0)!r}")
    allowed_urls = set()
    for r in data.get("verified", []):
        for ref in (r.get("assessment") or {}).get("references") or []:
            allowed_urls.add(ref.get("url"))
    for url in re.findall(r"https?://[^\s\"]+", raw):
        if url not in allowed_urls:
            fail(f"ссылка вне поля источников: {url}")


def clean(s):
    if s is None:
        return None
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s or None


# Хвост с ценой и кнопкой из карточки магазина: «… Цена за 1 шт С Картой №1 799,99 ₽ … В корзину».
PRICE_TAIL = re.compile(r"\s*(?:Цена за |С Картой|\d[\d\s]*,\d{2}\s*(?:₽|руб)).*$", re.S)


def clean_name(s):
    s = clean(s)
    return clean(PRICE_TAIL.sub("", s)) if s else s


def norm_category(c):
    c = clean(c)
    if not c:
        return None
    c = c[0].upper() + c[1:]
    return c.replace("Ликер", "Ликёр")


# Вид берётся из названия, если в нём прямо назван напиток; иначе из категории каталога.
# Порядок важен: «вино игристое» раньше «вина», «пивной напиток» раньше общего «напитка».
KIND_WORDS = [
    ("Игристое вино", r"игрист\w*|шампанск\w*"),
    ("Игристое вино", r"просекко|prosecco|креман\w*|франчакорт\w*"),
    ("Вермут", r"вермут\w*"),
    ("Портвейн", r"портвейн\w*"),
    ("Сакэ", r"саке|сакэ"),
    ("Писко", r"писко"),
    ("Херес", r"херес\w*"),
    ("Вино", r"вин(?:о|а|ный|ное)"),
    ("Пиво", r"пив(?:о|а|ной|ное)"),
    ("Сидр", r"сидр\w*|пуаре"),
    ("Коньяк", r"коньяк\w*|арманьяк\w*"),
    ("Бренди", r"бренди|кальвадос\w*|граппа"),
    ("Виски", r"виски|бурбон\w*"),
    ("Водка", r"водк\w*"),
    ("Ром", r"ром"),
    ("Джин", r"джин"),
    ("Текила", r"текил\w*|мескал\w*"),
    ("Ликёр", r"лик[её]р\w*"),
    ("Аперитив", r"аперитив\w*|биттер\w*"),
    ("Настойка", r"настойк\w*|бальзам\w*"),
    ("Медовуха", r"медовух\w*"),
    ("Алкогольный напиток", r"напит\w*"),
]


GENERIC_CATS = {"Вермут и креплёное вино", "Крепкий алкоголь", "Напиток", "Спиртной", "Пиво / сидр", "Алкогольный напиток, категория не уточнена"}


def kind_from_name(name, category):
    low = name.lower().replace("ё", "е")
    cat = norm_category(category)
    for label, pat in KIND_WORDS:
        if re.search(rf"(?<![а-яa-z]){pat.replace('ё', 'е')}(?![а-яa-z])", low):
            # «Напиток» в названии слишком общий: конкретная категория каталога точнее.
            if label == "Алкогольный напиток" and cat and cat not in GENERIC_CATS:
                return cat
            return label
    return cat


def norm_country(c):
    c = clean(c)
    if not c:
        return None
    if c.isupper() and len(c) > 3:
        c = c.capitalize()
    return COUNTRY_ALIASES.get(c.lower(), c)


# Длинные и старые названия стран из каталогов сетей приводятся к привычным.
COUNTRY_ALIASES = {
    "соединённое корол-во великобритании и сев.ирландии": "Великобритания",
    "соединенное корол-во великобритании и сев.ирландии": "Великобритания",
    "соединённое королевство": "Великобритания", "англия": "Великобритания", "уэльс": "Великобритания",
    "тринидад и тобаго": "Тринидад и Тобаго", "южная африка": "ЮАР", "голландия": "Нидерланды",
}


def num(x):
    if x is None:
        return None
    x = float(x)
    return int(x) if x.is_integer() else round(x, 2)


def date_only(s):
    s = clean(s)
    if not s:
        return None
    m = re.match(r"\d{4}-\d{2}-\d{2}", s)
    return m.group(0) if m else s


WINE_CATS = re.compile(r"вин|шампан|игрист", re.I)
COLOR_WORDS = [
    ("Красное", r"красн(?:ое|ый|ая|ые)"),
    ("Белое", r"бел(?:ое|ый|ая|ые)"),
    ("Розовое", r"розов(?:ое|ый|ая)"),
    ("Оранжевое", r"оранжев(?:ое|ый|ая)"),
]
SUGAR_WORDS = [
    ("Брют", r"(?:экстра\s+)?брют|brut"),
    ("Полусухое", r"полусух(?:ое|ой|ая)|п/сух\w*"),
    ("Полусладкое", r"полуслад(?:кое|кий|кая)|п/слад\w*"),
    ("Сухое", r"сух(?:ое|ой|ая)"),
    ("Сладкое", r"слад(?:кое|кий|кая)"),
]


def wine_attrs(name, category):
    """Цвет и сахар берутся только из явных слов в названии карточки."""
    low = name.lower().replace("ё", "е")
    if not (WINE_CATS.search(category or "") or re.search(r"\bвино\b|игрист|шампанск", low)):
        return None, None, False
    color = next((lab for lab, p in COLOR_WORDS if re.search(rf"(?<![а-яa-z]){p}(?![а-яa-z])", low)), None)
    sugar = None
    for lab, p in SUGAR_WORDS:
        if re.search(rf"(?<![а-яa-z/]){p}(?![а-яa-z])", low):
            sugar = lab
            break
    sparkling = bool(re.search(r"игрист|шампанск", low + " " + (category or "").lower()))
    return color, sugar, sparkling


class Dict:
    def __init__(self):
        self.items, self.index = [], {}

    def __call__(self, v):
        if v is None:
            return -1
        if v not in self.index:
            self.index[v] = len(self.items)
            self.items.append(v)
        return self.index[v]


def main():
    raw = SRC.read_text(encoding="utf-8")
    data = json.loads(raw)
    for key in ("as_of", "counts", "verified"):
        if key not in data:
            fail(f"в JSON нет поля {key}")
    # Непроверенные позиции не используются: раздел отбрасывается до любых проверок и сборки.
    data.pop("unmatched", None)
    raw = json.dumps(data, ensure_ascii=False)
    privacy_check(raw, data)
    if TRIM:
        dest = ROOT / "data" / "snapshot.json"
        dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Записан {dest.relative_to(ROOT)}: {len(data['verified'])} записей с решением, раздел unmatched удалён.")
        return

    nets, prods, countries, cats, brands = Dict(), Dict(), Dict(), Dict(), Dict()
    assessments, assess_index = [], {}
    groups = {}

    # Пересмотренные решения: data/overrides.json, запись ищется по сети и точному названию из снимка.
    overrides = {}
    if OVERRIDES.exists():
        for o in json.loads(OVERRIDES.read_text(encoding="utf-8")).get("overrides", []):
            if o.get("status") not in STATUS_CODE:
                fail(f"overrides.json: неизвестный статус {o.get('status')!r}")
            for ref in o.get("refs") or []:
                if ref.get("type") not in ALLOWED_REF_TYPES or not str(ref.get("url", "")).startswith("https://"):
                    fail(f"overrides.json: недопустимый источник {ref!r}")
            overrides[(o["network"], o["name"])] = o
    used_overrides = set()
    skipped = {"unclear": 0}
    company_by_url = json.loads(COMPANIES.read_text(encoding="utf-8")) if COMPANIES.exists() else {}
    cc_path = ROOT / "data" / "company_countries.json"
    country_by_url = json.loads(cc_path.read_text(encoding="utf-8")) if cc_path.exists() else {}

    def producer_of(refs):
        """Производитель — компания, ответившая на запрос (Barnivore или сайт производителя), а не поставщик из карточки сети."""
        for ref in refs:
            if ref["url"] in company_by_url:
                return company_by_url[ref["url"]]
            host = re.sub(r"^https?://(www\.)?([^/]+).*", r"\2", ref["url"])
            if host in MANUFACTURER_SITES:
                return MANUFACTURER_SITES[host]
        return None

    def add(r, kind):
        a = r.get("assessment")
        if not a:
            fail(f"запись без решения в разделе verified: {r.get('name')!r}")
        o = overrides.get((r.get("network"), r.get("name")))
        if o:
            used_overrides.add((r.get("network"), r.get("name")))
            a = dict(a, status=o["status"], rationale=o.get("rationale") or a.get("rationale"),
                     scope_and_exceptions=o.get("scope") or a.get("scope_and_exceptions"),
                     references=o.get("refs") or a.get("references"), revised_from=a["status"])
        status = STATUS_CODE.get(a["status"])
        if not status:
            fail(f"неизвестный статус {a['status']!r}")
        # «Неясно» и «Противоречие» не публикуются: на сайте только позиции с однозначным ответом производителя.
        if status in ("u", "c"):
            skipped["unclear"] += 1
            return
        name = clean_name(r.get("name"))
        if not name:
            fail("запись без названия")
        cat = kind_from_name(name, r.get("category"))
        color, sugar, sparkling = wine_attrs(name, cat)
        ai = -1
        if a:
            refs = []
            for ref in a.get("references") or []:
                if ref.get("type") not in ALLOWED_REF_TYPES:
                    fail(f"неизвестный тип источника {ref.get('type')!r}")
                refs.append({"type": ref["type"], "url": ref["url"]})
            pub = {
                "status": a["status"],
                "reviewed_at": date_only(a.get("reviewed_at")),
                "evidence_date": clean(a.get("evidence_date")),
                "evidence_date_precision": clean(a.get("evidence_date_precision")),
                "rationale": clean(a.get("rationale")),
                "scope": [clean(x) for x in a.get("scope_and_exceptions") or [] if clean(x)],
                "identity": clean(a.get("identity_scope")),
                "packaging": clean(a.get("packaging")),
                "caveats": [clean(x) for x in a.get("caveats") or [] if clean(x)],
                "refs": refs,
            }
            if a.get("revised_from"):
                pub["revised_from"] = a["revised_from"]
            k = json.dumps(pub, ensure_ascii=False, sort_keys=True)
            if k not in assess_index:
                assess_index[k] = len(assessments)
                assessments.append(pub)
            ai = assess_index[k]
        vol_ml = num(r.get("volume_ml"))
        rec = [
            None,  # id
            status,
            [nets(clean(r.get("network")))],
            name,
            brands(clean(r.get("brand"))),
            prods(producer_of(refs)),
            countries(norm_country(r.get("country_as_reported"))),
            "f" if r.get("origin_classification") == "foreign" else "u",
            cats(cat),
            vol_ml,
            None if vol_ml is not None else clean(r.get("volume_as_reported")),
            num(r.get("abv_percent")),
            r.get("vintage_as_reported"),
            date_only(r.get("catalog_checked_at")),
            1,  # сколько одинаковых строк объединено
            ai,
            color,
            sugar,
            1 if sparkling else 0,
        ]
        # Объединяются только строки, совпадающие во всех полях.
        key = json.dumps([kind, r.get("network"), r.get("name"), r.get("brand"), r.get("producer_as_reported"),
                          r.get("country_as_reported"), r.get("origin_classification"), r.get("category"),
                          r.get("volume_ml"), r.get("volume_as_reported"), r.get("abv_percent"),
                          r.get("vintage_as_reported"), r.get("catalog_checked_at"), ai], ensure_ascii=False)
        if key in groups:
            groups[key][14] += 1
            return
        rec[0] = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
        groups[key] = rec

    skipped_ru = 0
    for r in data["verified"]:
        if clean(r.get("producer_as_reported")) in RU_PRODUCERS:
            skipped_ru += 1
            continue
        add(r, "v")

    # Сводный каталог сетей (уже отобранный scripts/import_catalog.py): одна запись может быть в нескольких сетях.
    extra_count = 0
    # data/manual_additions.json — позиции, проверенные вручную по письмам производителей (тот же формат).
    for extra_path in (EXTRA, ROOT / "data" / "manual_additions.json"):
      if not extra_path.exists():
        continue
      extra = json.loads(extra_path.read_text(encoding="utf-8"))
      if True:
        for it in extra["items"]:
            name = clean_name(it["name"])
            refs = [{"type": it.get("ref_type", "Barnivore"), "url": it.get("ref_url") or it["barnivore_url"]}]
            pub = {"status": it["status"], "reviewed_at": date_only(extra.get("copied_at")), "evidence_date": clean(it.get("evidence_date")),
                   "evidence_date_precision": None, "rationale": clean(it["rationale"]),
                   "scope": [clean(x)[0].upper() + clean(x)[1:] for x in it.get("scope") or [] if clean(x)], "identity": None,
                   "packaging": None, "caveats": [], "refs": refs}
            k = json.dumps(pub, ensure_ascii=False, sort_keys=True)
            if k not in assess_index:
                assess_index[k] = len(assessments)
                assessments.append(pub)
            cat = kind_from_name(name, EXTRA_CATEGORY.get(it["category"], it["category"]))
            color, sugar, sparkling = wine_attrs(name, cat)
            chains = it["chains"]
            groups["x:" + it["id"]] = [
                it["id"], STATUS_CODE[it["status"]], [nets(c["network"]) for c in chains], name, -1,
                prods(it.get("company")), countries(norm_country(it.get("country"))), "f" if it.get("country") else "u",
                cats(cat), None, None, None, None, date_only(chains[0]["checked_at"]), 1, assess_index[k],
                color, sugar, 1 if sparkling else 0]
            extra_count += 1

    # Признаки вина и правила производителей, у которых ответ зависит от цвета, линейки или урожая.
    attrs_path = ROOT / "data" / "wine_attrs.json"
    card_attrs = json.loads(attrs_path.read_text(encoding="utf-8")) if attrs_path.exists() else {}
    WINE_KINDS = {"Вино", "Игристое вино", "Портвейн", "Херес", "Вермут", "Вермут и креплёное вино"}
    dropped_by_rule = 0
    filled_country = 0
    for key, rec in list(groups.items()):
        name, kind = rec[3], cats.items[rec[8]] if rec[8] >= 0 else None
        # Страны нет в карточке сети: берётся страна ответившего производителя.
        if rec[6] < 0 and rec[15] >= 0:
            for ref in assessments[rec[15]]["refs"]:
                host = re.sub(r"^https?://(www\.)?([^/]+).*", r"\2", ref["url"])
                c = country_by_url.get(ref["url"]) or MANUFACTURER_COUNTRY.get(host)
                if c:
                    rec[6] = countries(c)
                    filled_country += 1
                    break
        if rec[6] < 0 and rec[5] >= 0 and prods.items[rec[5]] in PRODUCER_COUNTRY:
            rec[6] = countries(PRODUCER_COUNTRY[prods.items[rec[5]]])
            filled_country += 1
        is_wine = kind in WINE_KINDS
        if is_wine:
            card = card_attrs.get(re.sub(r"[^a-zа-я0-9]+", " ", name.lower().replace("ё", "е")).strip(), {})
            rec[16] = card.get("color") or wa.color_from_name(name, kind == "Игристое вино")[0]
            rec[17] = card.get("sugar") or wa.sugar_from_name(name)
            if rec[11] is None:
                rec[11] = card.get("abv") or wa.abv_from_name(name)
            if rec[9] is None:
                rec[9] = card.get("volume_ml") or wa.volume_from_name(name)
            if rec[12] is None:
                rec[12] = wa.vintage_from_name(name)
        rule = RULES.get(prods.items[rec[5]] if rec[5] >= 0 else None)
        if not rule:
            continue
        status = {"v": "vegan", "n": "nonvegan"}[rec[1]]
        new = status
        ok = not rule.get("drop")
        if ok and rule.get("only"):
            ok = re.search(rule["only"], name, re.I) is not None
        if ok and any(k in rule for k in ("red", "white", "rose")):
            ck = color_key(rec[16])
            new = rule.get(ck) if ck else None
            ok = new is not None
            if ok and ck == "red" and rule.get("min_vintage_red") and rec[12] and rec[12] < rule["min_vintage_red"]:
                ok = False
        if ok and "status" in rule:
            new = rule["status"]
        if ok and rule.get("min_vintage") and rec[12] and rec[12] < rule["min_vintage"]:
            ok = False
        if not ok:
            del groups[key]
            dropped_by_rule += 1
            continue
        pub = dict(assessments[rec[15]])
        if rule.get("note"):
            pub["rationale"] = rule["note"]
        if new != status:
            pub["status"], pub["revised_from"] = new, status
        k = json.dumps(pub, ensure_ascii=False, sort_keys=True)
        if k not in assess_index:
            assess_index[k] = len(assessments)
            assessments.append(pub)
        rec[15] = assess_index[k]
        rec[1] = STATUS_CODE[new]
    unknown_rules = set(RULES) - set(prods.items)
    if unknown_rules:
        print("Внимание: правила для компаний, которых нет в данных:", ", ".join(sorted(unknown_rules)))

    records = list(groups.values())
    ids = [r[0] for r in records]
    if len(ids) != len(set(ids)):
        fail("совпадение идентификаторов записей")
    verified = records
    for key in set(overrides) - used_overrides:
        print(f"Внимание: пересмотр не применён, записи нет в снимке: {key[0]} / {key[1]}")

    c = data["counts"]
    if len(data["verified"]) != c.get("verified_assessments"):
        fail("число записей с решением не совпадает с counts.verified_assessments")

    meta = {
        "title": clean(data.get("title")),
        "as_of": data["as_of"],
        "partial": bool(data.get("partial")),
        "snapshot_started_utc": data.get("snapshot_started_utc"),
        "snapshot_finished_utc": data.get("snapshot_finished_utc"),
        "notes": {k: clean(data.get(k)) for k in (
            "collection_note", "inclusion_note", "review_note", "identity_note", "producer_note",
            "detail_note", "country_note", "date_note", "coverage_note") if data.get(k)},
        "counts": c,
        "networks_declared": data.get("networks_with_accepted_observations") or [],
        "rows": {"verified": len(data["verified"]), "verified_after_merge": len(verified)},
        "dicts": {"networks": nets.items, "producers": prods.items, "countries": countries.items,
                  "categories": cats.items, "brands": brands.items},
        "fields": ["id", "status", "network", "name", "brand", "producer", "country", "origin", "category",
                   "volume_ml", "volume_raw", "abv", "vintage", "catalog_checked_at", "merged_rows",
                   "assessment", "wine_color", "wine_sugar", "sparkling"],
    }

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "site", OUT)
    (OUT / "data").mkdir(exist_ok=True)

    def dump(name, obj):
        (OUT / "data" / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    dump("meta.json", meta)
    dump("verified.json", {"records": verified, "assessments": assessments})
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    brew = ROOT / "data" / "ru_breweries.json"
    dump("breweries.json", json.loads(brew.read_text(encoding="utf-8"))["breweries"] if brew.exists() else [])

    for rec in verified:
        if re.search(r"₽|руб\.?(?:\s|$)|В корзину|Цена за ", rec[3]):
            fail(f"в названии осталась цена: {rec[3]!r}")

    # Финальная проверка: в публикуемых файлах нет ссылок, кроме разрешённых источников.
    allowed = {ref["url"] for a in assessments for ref in a["refs"]}
    # Пивоварни: допускаются только ссылки на записи VeganRussian.
    for b in (json.loads(brew.read_text(encoding="utf-8"))["breweries"] if brew.exists() else []):
        if not b["url"].startswith("https://veganrussian.ru/"):
            fail(f"ru_breweries.json: ссылка не на VeganRussian: {b['url']}")
        allowed.add(b["url"])
    allowed |= {"https://veganrussian.ru/", "https://www.barnivore.com/", "https://www.barnivore.com/terms", "http://www.w3.org/2000/svg"}
    allowed_files = {".html", ".js", ".css", ".json", ".woff2", ".svg", ".txt", ""}
    for f in OUT.rglob("*"):
        if f.is_dir():
            continue
        if f.suffix not in allowed_files:
            fail(f"неожиданный файл в публикации: {f.relative_to(OUT)}")
        if f.suffix in {".json", ".html", ".js", ".css", ".svg", ".txt"}:
            text = f.read_text(encoding="utf-8")
            for url in re.findall(r"https?://[^\s\"'<>)`]+", text):
                if url not in allowed and not url.startswith("https://github.com/"):
                    fail(f"{f.name}: неожиданная ссылка {url}")

    print(f"Снимок {meta['as_of']}: решений {len(data['verified'])} -> {len(verified)} записей; "
          f"сетей с решениями {len(nets.items)}; российское производство исключено: {skipped_ru}; "
          f"без однозначного ответа исключено: {skipped['unclear']}; "
          f"пересмотрено решений: {len(used_overrides)}; из сводного каталога сетей: {extra_count}; снято по правилам производителей: {dropped_by_rule}; страна по производителю: {filled_country}.")


if __name__ == "__main__":
    main()
