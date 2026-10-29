"""Scope, privacy and publication checks for direct producer replies."""
import copy
import json
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from producer_replies import load_replies, render_directory

source = ROOT / "data/producer_replies.json"
original = json.loads(source.read_text(encoding="utf-8"))
loaded = load_replies(source, ROOT / "site")
data = json.loads((ROOT / "_site/data/verified.json").read_text(encoding="utf-8"))
rows = {r[0]: r for r in data["records"]}
assert len(loaded["items"]) == 89
ararat = [i for i in loaded["items"] if i["id"].startswith("reply-ararat-")]
assert len(ararat) == 25
assert sum(i["status"] == "vegan" for i in ararat) == 24
ararat_retail = [i for i in ararat if i["chains"]]
assert len(ararat_retail) == 15
assert all(i["id"] in data["price_levels"] for i in ararat_retail)
assert rows["reply-ararat-honey"][1] == "n"
assert rows["reply-ararat-3-stars"][3] != rows["reply-ararat-5-stars"][3]
ararat_page = (ROOT / "_site/ararat.html").read_text(encoding="utf-8")
assert "distillate derived from natural Armenian honey" in ararat_page
assert not re.search(r"Borisova|Gevorgyan|@|mail\.google|signitic", ararat_page)
for item in loaded["items"]:
    row = rows[item["id"]]
    assessment = data["assessments"][row[15]]
    assert row[1] == {"vegan": "v", "nonvegan": "n"}[item["status"]]
    assert assessment["evidence_date"] == item["evidence_date"]
    if item["reply_id"].startswith("pjk-"):
        assert row[3].startswith("Peter Jakob Kühn ")
        assert row[9] == 750 and row[11] and row[16:18] == ["Белое", "Сухое"]
        assert assessment["refs"] == [{"type": "producer_reply", "url": "peter-jakob-kuehn.html"}]
    elif item["reply_id"].startswith("ararat-"):
        assert assessment["refs"] == [{"type": "producer_reply", "url": "ararat.html"}]
    elif item["reply_id"].startswith("bash-"):
        assert assessment["refs"] == [{"type": "producer_reply", "url": "bashspirt.html"}]
    else:
        assert assessment["refs"] == []
assert rows["reply-pjk-quarzit-2016"][12] == 2016
assert rows["reply-kkz-lezginka-brandy"][8] != rows["reply-kkz-lezginka-kv"][8]
assert len(rows["reply-tat-bugulma"][2]) == 10
assert len([r for r in rows.values() if r[0].startswith("reply-tat-")]) == 20
assert len([i for i in loaded['items'] if i['reply_id']=='tat-other-2026-10-26']) == 14
for suffix in ('19a1fb1ae34a', '62b4d44330f7'):
    row = rows['reply-tat-' + suffix]
    assert row[1] == 'n'
    assert data['assessments'][row[15]]['refs'][0]['type'] == 'manufacturer'
    assert 'tatspirtprom.ru/catalog/' in data['assessments'][row[15]]['refs'][0]['url']
for row in rows.values():
    if row[0].startswith('reply-tat-'):
        assert row[0] in data['price_levels']
assert "reply-kkz-stars-kv" not in rows and "reply-kkz-stars-ks" not in rows
assert rows["reply-kkz-dagestan"][3] != rows["reply-kkz-dagestan-13"][3]

# Reject a missing page, external/private link, missing retail evidence and status override.
with TemporaryDirectory() as tmp:
    path = Path(tmp) / "replies.json"
    for change in (
        lambda d: d["replies"]["pjk-2026-10-26"].update(public_page="../private.html"),
        lambda d: d["replies"]["pjk-2026-10-26"].update(public_page="https://mail.google.com/"),
        lambda d: d["replies"]["pjk-2026-10-26"].update(public_page="missing.html"),
        lambda d: d["items"][0].update(chains=[]),
        lambda d: d["items"][0].update(status="vegan"),
        lambda d: d["replies"]["kkz-2026-10-26"].update(status="unclear"),
        lambda d: d["replies"]["massandra-gurzuf-2026-10-27"].update(public_page="peter-jakob-kuehn.html"),
    ):
        broken = copy.deepcopy(original)
        change(broken)
        path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        try:
            load_replies(path, ROOT / "site")
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid direct-reply record accepted")

public = source.read_text(encoding="utf-8") + (ROOT / "_site/peter-jakob-kuehn.html").read_text(encoding="utf-8")
assert not re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}|mailto:|[A-Za-z]:[\\/]|\+\d[\d ()-]{8,}|₽|mail\.google", public, re.I)
assert "Sophie" not in public and "Borisova" not in public
assert "Unsere Weine enthalten keine Zutaten tierischen Ursprungs" in public
print("Direct replies: scoped statuses, retail presence, local sources, wine attributes and privacy passed")

# The directory links every scoped product and does not expose extra private fields.
from html import unescape
from urllib.parse import urlsplit, parse_qs
page = (ROOT / "_site/producers.html").read_text(encoding="utf-8")
tat_page = (ROOT / "_site/tatspirtprom.html").read_text(encoding="utf-8")
assert 'target="_blank" rel="noopener">Подробнее об ответе' in page
assert "tatspirtprom.html" in page
assert "Tundra Authentic" not in page
assert '<h2>ARARAT</h2>' in page
assert 'href="ararat.html" target="_blank" rel="noopener">Подробнее об ответе' in page
assert "ARARAT CHARLES AZNAVOUR" not in page
bash_page = (ROOT / "_site/bashspirt.html").read_text(encoding="utf-8")
assert 'href="bashspirt.html" target="_blank" rel="noopener">Подробнее об ответе' in page
assert not re.search(r"Катаевская|222-45-57|293-74-10|mailto:|сертификата|\.pdf", bash_page)
bash_items = [i for i in loaded["items"] if i["reply_id"].startswith("bash-")]
assert len(bash_items) == 11
assert sum(i["status"] == "vegan" for i in bash_items) == 7
for item in bash_items:
    assert f'?id={item["id"]}' in bash_page
    assert not item.get("publication_pending")
assert original["replies"]["massandra-gurzuf-2026-10-27"]["publication_pending"]
page += tat_page + ararat_page + bash_page
ids = {parse_qs(urlsplit(unescape(url)).query)["id"][0]
       for url in re.findall(r'href="([^"]+)"', page) if "?id=" in url}
assert ids == {item["id"] for item in original["items"]
               if not original["replies"][item["reply_id"]].get("publication_pending")}
pending = [item for item in loaded["items"] if item.get("publication_pending")]
assert len(pending) == 1
assert sum(item["status"] == "vegan" for item in pending) == 1
for item in pending:
    assert item["id"] not in ids
    assert rows[item["id"]][9] and rows[item["id"]][11]
    if item.get("retail_optional"):
        assert rows[item["id"]][2] == [] and rows[item["id"]][13] is None
        assert item["id"] not in data["price_levels"]
    else:
        assert rows[item["id"]][2]
        assert data["price_levels"][item["id"]]["level"] in range(1, 6)
    assert data["assessments"][rows[item["id"]][15]]["refs"] == []
assert all(item_id in rows for item_id in ids)
assert "<!-- PRODUCER_REPLIES -->" not in page
assert not re.search(r"mail\.google|mailto:|(?<![A-Za-z])[A-Za-z]:[\\/]|Sophie|Borisova", page)
translations = json.loads((ROOT / "data/translations_en.json").read_text(encoding="utf-8"))
with TemporaryDirectory() as tmp:
    synthetic = copy.deepcopy(original)
    synthetic["replies"]["pjk-2026-10-26"]["company"] = '<script>alert(1)</script>'
    synthetic["replies"]["pjk-2026-10-26"]["private_note"] = 'DO_NOT_PUBLISH_THIS_FIELD'
    path = Path(tmp) / "replies.json"
    path.write_text(json.dumps(synthetic), encoding="utf-8")
    rendered = render_directory(path, ROOT / "site", translations)
    assert '<script>' not in rendered and '&lt;script&gt;' in rendered
    assert 'DO_NOT_PUBLISH_THIS_FIELD' not in rendered
print("Producer directory: all product links resolve; HTML escaped; extra private fields excluded")
