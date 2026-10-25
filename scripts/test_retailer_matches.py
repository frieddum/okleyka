"""Run after build.py: check reviewed retailer links and new wine variants."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


data = read("_site/data/verified.json")
meta = read("_site/data/meta.json")
rows = {r[0]: r for r in data["records"]}
network = meta["dicts"]["networks"].index("КуулКлевер / ОТДОХНИ")

for match in read("data/retailer_matches.json"):
    row = rows[match["record_id"]]
    assert row[3] == match["expected_name"]
    assert network in row[2] and len(row[2]) == len(set(row[2]))
    assert row[1] in ("v", "n")
    assert data["assessments"][row[15]]["refs"]

new = read("data/coolclever_additions.json")["items"]
for item in new:
    row = rows[item["id"]]
    assert row[2] == [network]
    assert row[11] == item["abv"], (item["name"], row[11])
    assert row[16] and row[17], item["name"]
    assert data["assessments"][row[15]]["refs"][0]["url"] == item["barnivore_url"]

assert rows["rfa-f4e75d7b9598"][16] == "Белое"
assert rows["rfa-2458ab2a801c"][16] == "Красное"
assert rows["cc-63f2524bad"][18] == 1  # Cap Classique remains sparkling.
assert rows["cc-2fa5489c2d"][12] == 2021
assert rows["cc-62ca064653"][12] == 2022  # Pardus vintages stay separate.
assert rows["cc-14ad0dcdd7"][1] == rows["cc-9905a1f45f"][1] == "n"
assert rows["cc-10ef7f8dd2"][17] == "Сухое"  # Confidence is not the sweet château wine.
assert rows["cc-a71b0c1239"][17] == "Сладкое"
print("Reviewed retailer links, sources, wine variants and ABV ranges: passed")
