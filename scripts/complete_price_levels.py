"""Fill missing public price levels from reviewed private observations.

Exact prices, source URLs and the audit stay outside the repository. Existing
levels and the current category calibration are preserved during a gap fill.
Use expand_price_levels.py for an intentional full market recalibration.
"""
import argparse
from collections import defaultdict
from datetime import date
import json
import math
from pathlib import Path
import re
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from price_levels import category, ordinary_volume, reference_volume, relative_level


def reviewed_observations(path, rows, holds=()):
    """Reject stale/manual mappings instead of silently pricing another drink."""
    if not path.exists():
        return []
    result = []
    for raw in json.loads(path.read_text(encoding="utf8")):
        if raw.get("reviewed") is not True or not raw.get("match_reason"):
            raise ValueError("Price observation needs an explicit reviewed match")
        price, ml = raw.get("price"), raw.get("ml")
        if (isinstance(price, bool) or not isinstance(price, (int, float))
                or not math.isfinite(price) or price <= 0
                or not isinstance(ml, (int, float)) or not math.isfinite(ml) or ml <= 0):
            raise ValueError("Invalid price or bottle volume")
        checked = raw.get("checked") or ""
        if checked:
            date.fromisoformat(checked)
        if not raw.get("network") or not raw.get("name"):
            raise ValueError("Missing retailer or product name")
        if not (raw.get("url") or raw.get("source_locator") or raw.get("source_locators")):
            raise ValueError("Price observation has no traceable source")
        if re.search(r"набор|бокал|стакан|gift\s*set", raw["name"], re.I):
            raise ValueError("Gift sets cannot price an ordinary bottle")
        for rid in raw.get("ids", []):
            if rid not in rows or raw.get("expected_card_name") != rows[rid][3]:
                raise ValueError(f"Review stale price mapping: {rid}")
            if rid not in holds:
                result.append(dict(raw, ids=[rid], checked=checked))
    return result


def select_observations(observations, scale):
    """One latest offer per retailer/volume, then median at the reference size."""
    offers = {}
    for o in observations:
        if not ordinary_volume(o["ml"], scale):
            continue
        identity = (o["network"], o["ml"])
        prior = offers.get(identity)
        reference = o.get("source_kind") == "product_page_reference"
        if prior:
            prior_reference = prior.get("source_kind") == "product_page_reference"
            if reference != prior_reference:
                if reference:
                    continue
            elif prior.get("checked", "") > o.get("checked", ""):
                continue
        offers[identity] = o
    if not offers:
        return None
    size = min({o["ml"] for o in offers.values()},
               key=lambda v: (abs(v - reference_volume(scale)), v))
    selected = [o for o in offers.values() if o["ml"] == size]
    owner = [o for o in selected if o.get("source_kind") == "user_message"]
    price = statistics.median(o["price"] for o in (owner or selected))
    return size, price, max(o.get("checked", "") for o in selected), selected


def fill_missing(rows, categories, baseline, observations, calibration, holds=()):
    groups = defaultdict(list)
    for o in observations:
        for rid in o["ids"]:
            if rid not in baseline and rid not in holds:
                groups[rid].append(o)
    tiers = dict(baseline)
    audit = {}
    for rid, group in groups.items():
        row = rows[rid]
        scale = category(categories[row[8]], bool(row[18]))
        selected = select_observations(group, scale)
        if selected is None:
            continue
        bounds = calibration[scale]["boundaries"]
        if len(bounds) != 4 or not all(math.isfinite(b) for b in bounds) or not all(a < b for a, b in zip(bounds, bounds[1:])):
            raise ValueError(f"Invalid category calibration: {scale}")
        size, price, checked, used = selected
        tiers[rid] = dict(level=relative_level(price, bounds), scale=scale,
                          volume_ml=int(size), observed_at=checked or None)
        audit[rid] = dict(selected_price=price, observations=used)
    return tiers, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    read = lambda p: json.loads(p.read_text(encoding="utf8"))
    data = read(args.site_dir / "data/verified.json")
    rows = {r[0]: r for r in data["records"]}
    archive = args.site_dir / "data/archive.json"
    if archive.exists():
        rows.update({r[0]: r for r in read(archive)["records"]})
    categories = read(args.site_dir / "data/meta.json")["dicts"]["categories"]
    holds = read(args.work / "manual_price_holds.json")
    observations = reviewed_observations(args.work / "reviewed_price_observations.json", rows, holds)
    baseline = read(root / "data/price_levels.json")
    calibration = read(args.work / "price_coverage_report.json")["calibration"]
    tiers, audit = fill_missing(rows, categories, baseline, observations, calibration, holds)
    args.out.write_text(json.dumps(tiers, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    report = dict(added=len(audit), priced_active=sum(r[0] in tiers for r in data["records"]),
                  total_active=len(data["records"]), added_ids=list(audit),
                  missing=[dict(id=r[0], name=r[3]) for r in data["records"] if r[0] not in tiers])
    (args.work / "completion_price_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf8")
    (args.work / "completion_price_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("added_ids", "missing")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

