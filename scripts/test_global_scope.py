"""Regression checks for reviewed global additions, identity merges and public coverage."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent.parent
read = lambda p: json.loads((root / p).read_text(encoding="utf-8"))
data = read("_site/data/verified.json")
meta = read("_site/data/meta.json")
by_id = {r[0]: r for r in data["records"]}
assert len(by_id) == len(data["records"])
assert "Пятёрочка" not in meta["dicts"]["networks"]
assert len([r for r in data["records"] if r[2]]) == meta["rows"]["with_retail_observations"]
for old, keep in data["aliases"].items():
    assert old not in by_id and keep in by_id
    assert old not in data["price_levels"]
assert data["aliases"]["sp-87a7dd7147"] == "rfa-44091d2819c0"
assert data["price_levels"]["rfa-44091d2819c0"]["level"] == 5
hennessy = by_id["rfa-44091d2819c0"]
assert {"Ароматный Мир", "SPAR", "Joia"} <= {meta["dicts"]["networks"][i] for i in hennessy[2]}
withdrawn = {data['aliases'].get(d['id'], d['id']) for d in read('data/retailer_withdrawals.json')}
for r in data["records"]:
    if not r[2]:
        assert r[13] is None and r[0] not in data["price_levels"]
        assert r[1] == "v" or (r[1] == "n" and r[0] in withdrawn)
inputs = read("data/global_vegan.json")["items"]
for x in inputs:
    assert x["scope_reviewed"] and x["status"] == "vegan" and not x["chains"]
    name = x["name"].lower()
    if x["company"] == "Daou Vineyards": assert "2018 pessimist" not in name
    if x["company"] == "New England Brewing Co (US)": assert "coffee breath" not in name
    if x["company"] == "Fort Point HenHouse Inc.": assert "oyster stout" not in name and x["category"] == "Пиво"
    if x["company"] == "Upland Brewing Company": assert "modern tart" not in name
    if x["company"] == "Honeywood Winery": assert "mead" not in name and "honeysuckle" not in name
print("Global scope exceptions, duplicate redirects, prices and separated coverage: passed")
