"""Собирает цвет, сахар, крепость и объём вин из карточек сетей.

Запуск:
  python scripts/enrich_wine.py путь/ru_import/cache/amwine_pages.jsonl [ещё_файлы.jsonl ...]

Пишет data/wine_attrs.json: нормализованное название -> признаки из карточки сети.
В файл попадают только названия, которые есть в справочнике, и только сами признаки:
без ссылок, цен и остатков.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

COLOR = {"Красное": "Красное", "Белое": "Белое", "Розовое": "Розовое", "Оранжевое": "Оранжевое"}
SUGAR = {"Сухое": "Сухое", "Полусухое": "Полусухое", "Полусладкое": "Полусладкое", "Сладкое": "Сладкое",
         "Брют": "Брют", "Экстра брют": "Брют", "Брют натюр": "Брют"}


def norm(s):
    return re.sub(r"[^a-zа-я0-9]+", " ", (s or "").lower().replace("ё", "е")).strip()


def wanted_raw():
    names = []
    snap = json.loads((ROOT / "data" / "snapshot.json").read_text(encoding="utf-8"))
    names += [r["name"] for r in snap["verified"]]
    for f in ("catalog_extra.json", "manual_additions.json"):
        p = ROOT / "data" / f
        if p.exists():
            names += [i["name"] for i in json.loads(p.read_text(encoding="utf-8"))["items"]]
    return names


def wanted_names():
    names = {norm(n) for n in wanted_raw()}
    snap = json.loads((ROOT / "data" / "snapshot.json").read_text(encoding="utf-8"))
    names |= {norm(r["name"]) for r in snap["verified"]}
    extra = ROOT / "data" / "catalog_extra.json"
    if extra.exists():
        names |= {norm(i["name"]) for i in json.loads(extra.read_text(encoding="utf-8"))["items"]}
    return names


def from_amwine(path, want, out):
    with open(path, encoding="utf-8", newline="\n") as fh:
        for line in fh:
            if not line.strip():
                continue
            for p in json.loads(line).get("products", []):
                key = norm(p.get("name"))
                if key not in want:
                    continue
                props = {pp["code"]: str(pp.get("value") or "") for pp in p.get("preview_props", [])}
                raw = p.get("props") or {}
                rec = {}
                if props.get("COLOR") in COLOR:
                    rec["color"] = COLOR[props["COLOR"]]
                if props.get("SUGAR") in SUGAR:
                    rec["sugar"] = SUGAR[props["SUGAR"]]
                try:
                    abv = float(str(raw.get("alco") or "").replace(",", "."))
                    if 0 <= abv <= 23:
                        rec["abv"] = abv
                except ValueError:
                    pass
                try:
                    vol = float(str(raw.get("value") or "").replace(",", ".")) * 1000
                    if 50 <= vol <= 6000:
                        rec["volume_ml"] = vol
                except ValueError:
                    pass
                if rec:
                    out.setdefault(key, {}).update(rec)


# Слова, которые сети пишут по-разному или не пишут вовсе: тип, цвет, сахар, объём, урожай, страна.
NOISE = re.compile(r"\b(вино|винo|игристое|шампанское|тихое|столовое|сортовое|ординарное|выдержанное|красное|белое|розовое|оранжевое|"
                   r"сухое|полусухое|полусладкое|сладкое|брют|экстра|натюр|кр|бел|роз|сух|п|сл|л|мл|защищенным|географическим|указанием|"
                   r"наименованием|места|происхождения|категории|doc|docg|igt|aoc|aop|do|doca|igp|dop|vdt|франция|италия|испания|чили|"
                   r"аргентина|португалия|германия|австрия|юар|россия|грузия|новая|зеландия|австралия|сша|в|п|у|с|и|подарочной|упаковке|"
                   r"коробке|тубе|\d+[.,]?\d*)\b")


def core(name):
    t = NOISE.sub(" ", re.sub(r"\d+[.,]?\d*\s*(мл|л)", " ", norm(name)))
    return " ".join(sorted(set(t.split())))


def vintage(name):
    m = re.search(r"\b(19[5-9]\d|20[0-4]\d)\b", name or "")
    return m.group(1) if m else None


def from_amwine_fuzzy(path, want_raw, out):
    """Если вина нет в Ароматном Мире под тем же названием, ищется то же вино с другой записью названия.
    Берётся только однозначное совпадение; крепость — только при том же урожае."""
    idx = {}
    with open(path, encoding="utf-8", newline="\n") as fh:
        for line in fh:
            if not line.strip():
                continue
            for p in json.loads(line).get("products", []):
                k = core(p.get("name"))
                if len(k.split()) < 2:
                    continue
                props = {pp["code"]: str(pp.get("value") or "") for pp in p.get("preview_props", [])}
                raw = p.get("props") or {}
                rec = {}
                if props.get("COLOR") in COLOR:
                    rec["color"] = COLOR[props["COLOR"]]
                if props.get("SUGAR") in SUGAR:
                    rec["sugar"] = SUGAR[props["SUGAR"]]
                try:
                    abv = float(str(raw.get("alco") or "").replace(",", "."))
                    if 0 < abv <= 23:
                        rec["abv"] = abv
                except ValueError:
                    pass
                if rec:
                    idx.setdefault(k, []).append((vintage(p.get("name")), rec))
    n = 0
    for name in want_raw:
        key = norm(name)
        if key in out:
            continue
        hits = idx.get(core(name))
        if not hits:
            continue
        rec = {}
        for f in ("color", "sugar"):
            vals = {h[1][f] for h in hits if f in h[1]}
            if len(vals) == 1:
                rec[f] = vals.pop()
        v = vintage(name)
        abvs = {h[1]["abv"] for h in hits if "abv" in h[1] and h[0] == v}
        if len(abvs) == 1:
            rec["abv"] = abvs.pop()
        if rec:
            out[key] = rec
            n += 1
    print(f"Ароматный Мир, похожие названия: {n}")


def from_simple(path, want, out):
    """Строки {"key": нормализованное название, "color", "sugar", "abv"} — признаки со страниц товаров сети."""
    with open(path, encoding="utf-8", newline="\n") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("key") not in want:
                continue
            rec = {k: r[k] for k in ("color", "sugar", "abv", "volume_ml") if r.get(k) is not None}
            if rec:
                cur = out.setdefault(r["key"], {})
                for k, v in rec.items():
                    cur.setdefault(k, v)


def main():
    want = wanted_names()
    out = {}
    for path in sys.argv[1:]:
        if "amwine" in Path(path).name:
            from_amwine(path, want, out)
            amwine = path
        else:
            from_simple(path, want, out)
    if "amwine" in locals():
        from_amwine_fuzzy(amwine, wanted_raw(), out)
    dest = ROOT / "data" / "wine_attrs.json"
    dest.write_text(json.dumps(dict(sorted(out.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Признаки из карточек сетей: {len(out)} названий -> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
