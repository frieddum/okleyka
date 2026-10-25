"""Import bands from saved AM cards/pages and user-pasted retailer text.

All inputs and the optional audit stay outside the public repository. Only
reviewed-card IDs, bands, scale and observation date are exported. Exact-name
matches include aliases already merged by build.py; ambiguous matches are skipped.
"""
import argparse
import json
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from price_levels import level, ordinary_volume
import build

ROOT = Path(__file__).resolve().parent.parent
build.SRC = ROOT / "data/snapshot.json"
build.OUT = ROOT / "_site"


def name_key(name):
    name = unicodedata.normalize("NFKC", name).lower().replace("ё", "е")
    # Volume is handled separately; do not discard vintage, colour or strength.
    name = re.sub(r"\d+(?:[.,]\d+)?\s*(?:мл|ml|л|l)(?![a-zа-я])", " ", name)
    name = re.sub(r"[\"«»„“”]", "", name)
    return re.sub(r"[^\w%]+", " ", name).strip()


def volume(text):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(мл|ml|л|l)(?![a-zа-я])", str(text), re.I)
    return float(m[1].replace(",", ".")) * (1000 if m[2].lower() in ("л", "l") else 1) if m else None


def pasted_prices(text):
    # Use only the price directly following a product title, never 'old price'
    # or a discount percentage, and do not carry a price into the next product.
    previous = ""
    for line in text.splitlines():
        line = line.strip()
        m = re.fullmatch(r"Цена\s*([\d\s\u00a0]+(?:[,.]\d{1,2})?)\s*₽", line)
        if m and previous and re.match(r"(?:Вино|Игристое вино|Портвейн|Напиток|Винный|Плодовый|Виски|Бурбон|Коньяк|Бренди|Ром|Водка|Джин|Текила|Лик[её]р|Вермут|Аперитив|Настойка|Бальзам|Абсент|Соджу|Сакэ|Пиво|Сидр)\b", previous, re.I):
            price = float(re.sub(r"\s", "", m[1]).replace(",", "."))
            yield previous, price, volume(previous)
        if line:
            previous = line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amwine-cards", type=Path, required=True)
    ap.add_argument("--amwine-pages", type=Path, required=True)
    ap.add_argument("--pasted-lists", type=Path, required=True)
    ap.add_argument("--pasted-date", required=True)
    ap.add_argument("--audit", type=Path, required=True)
    args = ap.parse_args()
    # Capture only aliases in the already approved merge result.
    captured = {}
    merge = build.merge_cards.merge
    def capture(records, assessments):
        originals = {r[0]: list(r) for r in records}
        build.merge_cards.LOG.clear()
        result = merge(records, assessments)
        groups = build.merge_cards.LOG
        for row in result[0]:
            origin = originals[row[0]][3]
            captured[row[0]] = {origin, row[3]}
            for group in groups:
                if origin in group:
                    captured[row[0]].update(group)
        return result
    build.merge_cards.merge = capture
    build.main()
    data = json.loads((ROOT / "_site/data/verified.json").read_text(encoding="utf8"))
    meta = json.loads((ROOT / "_site/data/meta.json").read_text(encoding="utf8"))
    rows = {r[0]: r for r in data["records"]}
    keys = defaultdict(set)
    for rid, aliases in captured.items():
        for alias in aliases:
            keys[name_key(alias)].add(rid)
    found = defaultdict(dict)
    def accept(name, price, ml, network, checked):
        if not ml or not price or price <= 0 or re.search(r"набор|бокал|под/уп|подароч|п/у|gift|pack", name, re.I):
            return
        ids = keys.get(name_key(name), set())
        if len(ids) != 1:
            return
        rid = next(iter(ids)); row = rows[rid]
        nets = [meta["dicts"]["networks"][n] for n in row[2]]
        if network not in nets:
            return
        kind = meta["dicts"]["categories"][row[8]]
        scale = "beer" if kind in ("Пиво", "Сидр") else "bottle"
        if not ordinary_volume(ml, scale):
            return
        key = (network, name, ml)
        found[rid][key] = dict(name=name, price=price, ml=ml, network=network, checked=checked, scale=scale)
    cards = {}
    with args.amwine_cards.open(encoding="utf-8-sig") as f:
        for line in f:
            c = json.loads(line); cards[str(c["product_id"])] = c
    with args.amwine_pages.open(encoding="utf-8-sig") as f:
        for line in f:
            for p in json.loads(line).get("products", []):
                c = cards.get(str(p.get("id")))
                if c and p.get("price"):
                    try: price = float(str(p["price"]).replace(",", "."))
                    except ValueError: continue
                    accept(c["name"], price, volume(c.get("volume")), "Ароматный Мир", c["checked_at"][:10])
    for text in json.loads(args.pasted_lists.read_text(encoding="utf8")):
        for name, price, ml in pasted_prices(text):
            accept(name, price, ml, "Перекрёсток", args.pasted_date)
    tiers, audit = {}, {}
    for rid, values in found.items():
        offers = list(values.values())
        # Prefer 750 ml for wine, 700 ml for spirits, 500 ml for beer/cider;
        # use the closest observed ordinary size and never mix sizes in a median.
        scale = offers[0]["scale"]
        kind = meta["dicts"]["categories"][rows[rid][8]]
        target = 500 if scale == "beer" else 750 if kind in ("Вино", "Игристое вино", "Херес", "Портвейн", "Вермут") else 700
        size = min({o["ml"] for o in offers}, key=lambda ml: (abs(ml-target), ml))
        same_size = [o for o in offers if o["ml"] == size]
        price = statistics.median(o["price"] for o in same_size)
        tiers[rid] = dict(level=level(price, scale), scale=scale, volume_ml=int(size), observed_at=max(o["checked"] for o in same_size))
        audit[rid] = dict(selected_price=price, observations=offers)
    (ROOT / "data/price_levels.json").write_text(json.dumps(tiers, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(f"Price bands: {len(tiers)} cards; beer/cider: {sum(t['scale']=='beer' for t in tiers.values())}")


if __name__ == "__main__":
    raise SystemExit("Legacy fixed-band importer retired; use expand_price_levels.py with the private price evidence.")
