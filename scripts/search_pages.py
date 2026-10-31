"""Search-readable pages generated exclusively from the public, filtered export."""
import json
import re
from html import escape, unescape
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, tostring

BASE = "https://okleika.win/"
SCHEMA = "https://schema.org"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
TITLE = "Оклейка — справочник веганского статуса алкоголя"
DESCRIPTION = "Веганский статус вина, пива и крепких напитков: основания решений, даты и источники. Ответы производителей и проверенные записи справочников."
STATUS = {"v": "Веганское", "n": "Невеганское"}
SOURCE_LABELS = {"producer_reply": "Ответ производителя", "manufacturer": "Сайт производителя"}


def json_script(value):
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def page_name(rid):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", rid):
        raise ValueError("Unsafe public card ID")
    return f"drink-{rid}.html"


def section(label, values):
    if not values:
        return ""
    if isinstance(values, str):
        values = [values]
    return f"<section><h2>{escape(label)}</h2>" + "".join(f"<p>{escape(str(v))}</p>" for v in values) + "</section>"


def write_search_pages(out):
    """Returns the exact extra URL allowlist required by generated artifacts."""
    data = json.loads((out / "data/verified.json").read_text(encoding="utf-8"))
    meta = json.loads((out / "data/meta.json").read_text(encoding="utf-8"))
    dicts = meta["dicts"]
    records = sorted(data["records"], key=lambda r: (r[3].casefold(), r[0]))
    template = (out / "method.html").read_text(encoding="utf-8")
    template = template.replace('href="method.html" aria-current="page"', 'href="method.html"')
    public = []
    # Some older direct replies have no refs in the compact export. Recover only
    # from the published producer pages that explicitly link this exact card ID.
    reply_pages = {}
    for path in out.glob("*.html"):
        source_html = path.read_text(encoding="utf-8")
        for rid in re.findall(r'href="\./\?id=([^"&]+)', source_html):
            reply_pages.setdefault(rid, []).append(BASE + path.name)

    def save(name, title, description, body):
        html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{escape(title)}</title>", template, count=1, flags=re.S)
        html = re.sub(r'<meta name="description" content="[^"]*">', lambda _: f'<meta name="description" content="{escape(description, quote=True)}">', html, count=1)
        html = re.sub(r'<main\b.*?</main>', lambda _: f'<main class="wrap" id="main"><article class="prose search-page">{body}</article></main>', html, count=1, flags=re.S)
        # method.html has page-specific scripts after main; keep only the shared assets.
        html = re.sub(r"<script\b(?![^>]*\bsrc=)[^>]*>.*?</script>", "", html, flags=re.S)
        (out / name).write_text(html, encoding="utf-8")

    def lookup(key, i):
        return dicts[key][i] if i >= 0 else None

    for r in records:
        a = data["assessments"][r[15]]
        name = page_name(r[0])
        url = BASE + name
        status = STATUS[r[1]]
        refs = [{"type": ref["type"], "url": urljoin(BASE, ref["url"])} for ref in a.get("refs", [])]
        if not refs:
            refs = [{"type": "producer_reply", "url": u} for u in reply_pages.get(r[0], [])]
        facts = {
            "Бренд": lookup("brands", r[4]), "Производитель": lookup("producers", r[5]),
            "Страна": lookup("countries", r[6]), "Вид": lookup("categories", r[8]),
            "Объём, мл": r[9], "Крепость, %": r[11], "Урожай": r[12],
            "Цвет": r[16], "Сахар": r[17],
        }
        if r[18]:
            facts["Вид"] = "Игристое вино"
        if r[0] in data.get("nonalcoholic", {}):
            facts["Безалкогольный аналог"] = "Да"
        desc = f'{r[3]} — {status.lower()}. {a.get("rationale") or "Основание и область действия решения — в карточке."}'
        body = f'<p><a data-lang-link href="catalog.html">Все напитки</a></p><h1>{escape(r[3])}</h1>'
        body += f'<p><span class="pill st st-{r[1]}">{status}</span></p>'
        body += section("Почему", a.get("rationale"))
        body += '<dl class="kv">' + "".join(f"<dt>{escape(k)}</dt><dd>{escape(str(v))}</dd>" for k, v in facts.items() if v is not None) + "</dl>"
        for label, key in [("Область действия", "scope"), ("Идентичность напитка", "identity"), ("Упаковка", "packaging"), ("Ограничения", "caveats")]:
            body += section(label, a.get(key))
        body += section("Дата подтверждения источника", a.get("evidence_date"))
        body += section("Дата проверки записи", a.get("reviewed_at"))
        body += "<h2>Источники</h2><ul>" + "".join(f'<li><a href="{escape(ref["url"], quote=True)}">{escape(SOURCE_LABELS.get(ref["type"], ref["type"]))} — {escape(ref["url"])}</a></li>' for ref in refs) + "</ul>"
        if not refs:
            body += '<p>Публичная ссылка на исходный ответ отсутствует.</p>'
        if r[2]:
            body += section("Замечен в продаже", [lookup("networks", n) for n in r[2]])
            body += section("Дата проверки каталога магазина", r[13])
        body += '<p><a data-lang-link href="method.html">Как устроен справочник</a></p>'
        body += f'<p><a data-lang-link href="./?id={escape(r[0])}">Открыть в справочнике с фильтрами</a></p>'
        save(name, f"{r[3]} — {status.lower()} | Оклейка", desc, body)
        public.append({
            "id": r[0], "url": url, "name": r[3], "status": a["status"],
            "brand": facts["Бренд"], "producer": facts["Производитель"],
            "country": facts["Страна"], "category": facts["Вид"],
            "volume_ml": r[9], "abv": r[11], "vintage": r[12],
            "nonalcoholic": r[0] in data.get("nonalcoholic", {}),
            "assessment": {k: a[k] for k in ("rationale", "scope", "identity", "packaging", "caveats", "evidence_date", "evidence_date_precision", "reviewed_at") if k in a},
            "sources": refs,
            "retail_observations": {"networks": [lookup("networks", n) for n in r[2]], "checked_at": r[13]},
        })

    # Crawlable pagination, bounded page size, all records reachable from ordinary links.
    size = 100
    count = max(1, (len(public) + size - 1) // size)
    def catalog_name(i):
        return "catalog.html" if i == 1 else f"catalog-{i}.html"
    for i in range(1, count + 1):
        items = public[(i - 1) * size:i * size]
        links = "".join(f'<li><a data-lang-link href="{escape(x["url"].removeprefix(BASE))}">{escape(x["name"])}</a> — {STATUS["v" if x["status"] == "vegan" else "n"]}</li>' for x in items)
        pager = '<nav aria-label="Страницы каталога">' + " · ".join(f'<a data-lang-link href="{catalog_name(j)}">{j}</a>' if j != i else f'<strong aria-current="page">{j}</strong>' for j in range(1, count + 1)) + "</nav>"
        save(catalog_name(i), f"Все напитки — страница {i} | Оклейка", f"Напитки с проверенным веганским статусом, страница {i}. Основания, ограничения и ссылки на источники.", f"<h1>Все напитки</h1><p>Страница {i} / {count}</p><ul>{links}</ul>{pager}")

    # Expose this path to people and crawlers, without changing existing filter behavior.
    for filename in ("index.html", "nonalcoholic.html"):
        path = out / filename
        html = path.read_text(encoding="utf-8")
        html = html.replace("</main>", '<p class="catalog-access"><a data-lang-link href="catalog.html">Все напитки с источниками</a></p>\n</main>', 1)
        if filename == "index.html":
            html = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", html, count=1)
            html = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{DESCRIPTION}">', html, count=1)
            html = html.replace('<section aria-labelledby="count" id="results-col">', '<section aria-labelledby="count" id="results-col"><h1 class="visually-hidden">Справочник веганского статуса алкоголя</h1>')
        path.write_text(html, encoding="utf-8")

    # Russian breweries also had no source text without JavaScript.
    breweries = json.loads((out / "data/breweries.json").read_text(encoding="utf-8"))
    brew_html = '<ul class="brew-list">' + "".join(
        f'<li><p class="brew-name"><b>{escape(b["name"])}</b> {escape(b.get("city") or "")}</p><p>{escape(b.get("note") or "")}</p><p><a href="{escape(b["url"], quote=True)}">Ответ пивоварни</a> {escape(b.get("date") or "")}</p></li>'
        for b in breweries) + "</ul>"
    path = out / "beer.html"
    html = path.read_text(encoding="utf-8").replace('<div id="breweries"><p>Загружаю…</p></div>', f'<div id="breweries">{brew_html}</div>')
    path.write_text(html, encoding="utf-8")

    (out / "data/catalog.json").write_text(json.dumps({
        "name": "Оклейка", "url": BASE, "methodology": BASE + "method.html",
        "description": DESCRIPTION, "records": public,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    public_by_url = {x["url"]: x for x in public}
    allowed = {SCHEMA, NS, BASE + "#website", BASE + "#organization"}
    pages = sorted(out.glob("*.html"))
    for path in pages:
        url = BASE + ("" if path.name == "index.html" else path.name)
        allowed.add(url)
        html = path.read_text(encoding="utf-8")
        title = unescape(re.search(r"<title>(.*?)</title>", html, re.S).group(1))
        match = re.search(r'<meta name="description" content="([^"]*)">', html)
        description = unescape(match.group(1)) if match else title
        page = {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": description,
                "inLanguage": "ru", "isPartOf": {"@id": BASE + "#website"}}
        if url in public_by_url:
            item = public_by_url[url]
            page["citation"] = [ref["url"] for ref in item["sources"]]
            page["about"] = {"@type": "Thing", "name": item["name"], "identifier": item["id"]}
        graph = [page, {"@type": "WebSite", "@id": BASE + "#website", "url": BASE,
                       "name": "Оклейка", "alternateName": "Okleika",
                       "publisher": {"@id": BASE + "#organization"}},
                 {"@type": "Organization", "@id": BASE + "#organization", "name": "Оклейка", "url": BASE}]
        tags = f'<link rel="canonical" href="{url}">\n<link rel="describedby" href="llms.txt">\n'
        tags += f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="Оклейка">\n<meta property="og:url" content="{url}">\n'
        tags += f'<meta property="og:title" content="{escape(title, quote=True)}">\n<meta property="og:description" content="{escape(description, quote=True)}">\n'
        tags += '<script type="application/ld+json">' + json_script({"@context": SCHEMA, "@graph": graph}) + "</script>\n"
        html = html.replace("</head>", tags + "</head>", 1)
        path.write_text(html, encoding="utf-8")

    root = Element("urlset", xmlns=NS)
    for path in pages:
        SubElement(SubElement(root, "url"), "loc").text = BASE + ("" if path.name == "index.html" else path.name)
    (out / "sitemap.xml").write_bytes(tostring(root, encoding="utf-8", xml_declaration=True))
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    (out / "llms.txt").write_text(
        "# Оклейка / Okleika\n\n"
        "> Independent reference for the vegan status of alcoholic drinks and alcohol-free alternatives. "
        "Records include evidence, source dates, scope and limitations. The site is not a shop.\n\n"
        "## Sources and scope\n\n"
        "Vegan status, retail availability and price are separate facts. A record is not confirmation of every vintage, batch, market or licensed producer. "
        "Evidence dates can be historical; a review date is not a new manufacturer confirmation. "
        "Absence from the catalogue does not establish a drink's status. "
        "For a specific drink, the permanent record URL and its linked evidence provide the citable source.\n\n"
        f"- [Methodology]({BASE}method.html): how decisions and sources are evaluated.\n"
        f"- [All drinks]({BASE}catalog.html): paginated HTML directory; every record is readable without JavaScript.\n"
        f"- [Producer responses]({BASE}producers.html): published manufacturer confirmations and their scope.\n"
        f"- [Russian beer and cider]({BASE}beer.html): brewery-level source records.\n"
        f"- [Structured catalogue]({BASE}data/catalog.json): public records with named fields, permanent URLs and sources.\n"
        f"- [Sitemap]({BASE}sitemap.xml): canonical HTML pages.\n",
        encoding="utf-8")
    allowed |= {BASE + "sitemap.xml", BASE + "data/catalog.json"}
    allowed |= {ref["url"] for item in public for ref in item["sources"]}
    return allowed
