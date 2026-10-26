"""Regression checks for reviewed price gap fills (no network or catalogue writes)."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from complete_price_levels import fill_missing, reviewed_observations, select_observations

row = ["test", "v", [0], "Test wine", -1, -1, -1, None, 0, 750, None, 12, None, None, None, -1, "Белое", "Сухое", False]
rows = {"test": row, "existing": ["existing", *row[1:]]}
calibration = {"wine": {"boundaries": [700, 1100, 1750, 4150]}}
baseline = {"existing": {"level": 5, "scale": "wine", "volume_ml": 750, "observed_at": None}}
base = dict(name="Test wine 750ml", ids=["test"], expected_card_name="Test wine",
            price=1200, ml=750, network="A", checked="2026-10-26",
            reviewed=True, match_reason="Reviewed exact expression", url="https://example.test/item",
            source_kind="live_product")
obs = [base, dict(base, price=9999, ml=1500), dict(base, price=99, ml=187),
       dict(base, price=1800, network="B")]
tiers, audit = fill_missing(rows, ["Вино"], baseline, obs, calibration)
assert tiers["existing"] == baseline["existing"]
assert tiers["test"] == dict(level=3, scale="wine", volume_ml=750, observed_at="2026-10-26")
assert audit["test"]["selected_price"] == 1500
assert set(tiers["test"]) == {"level", "scale", "volume_ml", "observed_at"}
assert fill_missing(rows, ["Вино"], baseline, obs, calibration, {"test"})[0] == baseline
assert fill_missing(rows, ["Вино"], tiers, obs, calibration)[0] == tiers

# A newer SEO reference must not replace a real offer (in either input order).
reference = dict(base, price=9999, checked="2026-10-27", source_kind="product_page_reference")
assert select_observations([base, reference], "wine")[1] == 1200
assert select_observations([reference, base], "wine")[1] == 1200
assert select_observations([dict(base, checked=""), base], "wine")[2] == "2026-10-26"
assert select_observations([dict(base, ml=187)], "wine") is None
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "observations.json"
    def load(o):
        path.write_text(json.dumps([o]), encoding="utf8")
        return reviewed_observations(path, rows)
    assert load(base)[0]["ids"] == ["test"]
    for bad in (dict(base, reviewed=False), dict(base, expected_card_name="Other wine"),
                dict(base, price=float("nan")), dict(base, price=-1),
                dict(base, checked="yesterday"), dict(base, name="Test wine gift set"),
                dict(base, url=None)):
        try:
            load(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Accepted invalid evidence: {bad}")
print("Reviewed mappings, ordinary volumes, source precedence, holds, unchanged levels and public schema: passed")

