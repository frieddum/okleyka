"""Search surfaces must preserve public evidence and expose every active record."""
import json
import re
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET
from search_pages import BASE, page_name, json_script

OUT = Path(__file__).resolve().parents[1] / "_site"
data = json.loads((OUT / "data/verified.json").read_text(encoding="utf-8"))
export = json.loads((OUT / "data/catalog.json").read_text(encoding="utf-8"))
records = {r[0]: r for r in data["records"]}
assert {r["id"] for r in export["records"]} == records.keys()
sitemap = ET.parse(OUT / "sitemap.xml")
urls = [el.text for el in sitemap.findall(".//{*}loc")]
assert len(urls) == len(set(urls))
assert BASE in urls and BASE + "index.html" not in urls
catalog_links = set()
for p in OUT.glob("catalog*.html"):
    catalog_links.update(re.findall(r'href="(drink-[^"?]+\.html)', p.read_text(encoding="utf-8")))
assert catalog_links == {page_name(rid) for rid in records}
for item in export["records"]:
    row = records[item["id"]]
    a = data["assessments"][row[15]]
    assert item["status"] == a["status"]
    if not a["refs"]:
        for ref in item["sources"]:
            assert ref["url"].startswith(BASE)
            evidence = (OUT / ref["url"].removeprefix(BASE)).read_text(encoding="utf-8")
            assert f'?id={item["id"]}"' in evidence
    assert item["assessment"] == {k: a[k] for k in ("rationale", "scope", "identity", "packaging", "caveats", "evidence_date", "evidence_date_precision", "reviewed_at") if k in a}
    html = (OUT / page_name(row[0])).read_text(encoding="utf-8")
    visible = unescape(re.sub(r"<script\b.*?</script>", "", html, flags=re.S))
    assert row[3] in visible
    if not item["sources"]:
        assert "Публичная ссылка на исходный ответ отсутствует." in visible
    for key in ("rationale", "scope", "identity", "packaging", "caveats", "evidence_date", "reviewed_at"):
        values = a.get(key) or []
        if isinstance(values, str):
            values = [values]
        assert all(v in visible for v in values), (row[0], key)
    assert item["url"] in urls
    assert all(ref["url"] in visible for ref in item["sources"])
    schemas = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert len(schemas) == 1
    graph = json.loads(schemas[0])["@graph"]
    assert graph[0]["citation"] == [ref["url"] for ref in item["sources"]]
    assert graph[0]["url"] == item["url"]
    assert "offers" not in schemas[0] and "aggregateRating" not in schemas[0]
for url in urls:
    path = OUT / (url.removeprefix(BASE) or "index.html")
    html = path.read_text(encoding="utf-8")
    assert html.count('rel="canonical"') == 1
    assert f'rel="canonical" href="{url}"' in html
    assert 'name="description"' in html
    assert 'noindex' not in html
assert "User-agent: *\nAllow: /" in (OUT / "robots.txt").read_text()
assert BASE + "sitemap.xml" in (OUT / "robots.txt").read_text()
beer = unescape((OUT / "beer.html").read_text(encoding="utf-8").split("<script>")[0])
for brewery in json.loads((OUT / "data/breweries.json").read_text(encoding="utf-8")):
    assert brewery["name"] in beer and brewery["url"] in beer
assert "</script>" not in json_script({"name": "</script><script>alert(1)</script>"})
try:
    page_name("../private")
    raise AssertionError("Unsafe ID accepted")
except ValueError:
    pass
print(f"Search: {len(records)} source-faithful cards; {len(urls)} sitemap URLs; all records linked; valid JSON-LD.")
