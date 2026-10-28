"""Run after build.py: check reviewed retailer links and new wine variants."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from merge_cards import skeleton


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


data = read("_site/data/verified.json")
meta = read("_site/data/meta.json")
rows = {r[0]: r for r in data["records"]}
network = meta["dicts"]["networks"].index("КуулКлевер / ОТДОХНИ")
direct_ids = {item['id'] for item in read('data/producer_replies.json')['items']}

for match in read("data/retailer_matches.json"):
    rid = match["record_id"]
    row = rows[data.get('aliases', {}).get(rid, rid)]
    # The builder checks the exact original name before merging; exported titles
    # may omit bottle size, while explicit reviewed aliases may use another language.
    if rid not in data.get('aliases', {}):
        assert skeleton(row[3]) == skeleton(match["expected_name"])
    matched_network = meta["dicts"]["networks"].index(match["network"])
    assert matched_network in row[2] and len(row[2]) == len(set(row[2]))
    assert row[1] in ("v", "n")
    assert data["assessments"][row[15]]["refs"] or row[0] in direct_ids

new = read("data/coolclever_additions.json")["items"]
for item in new:
    row = rows[item["id"]]
    assert network in row[2]
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
