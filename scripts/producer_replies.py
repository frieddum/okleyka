"""Public, scoped decisions from direct producer replies. Raw mail stays private."""
import json
import re
from html import escape
from datetime import date
from urllib.parse import urlencode


def load_replies(path, site):
    data = json.loads(path.read_text(encoding="utf-8"))
    replies = data["replies"]
    items = []
    seen = set()
    for key, reply in replies.items():
        if reply["status"] not in ("vegan", "nonvegan"):
            raise ValueError(f"{key}: unconfirmed reply")
        date.fromisoformat(reply["evidence_date"])
        if not reply["company"] or not reply["rationale"] or not reply["scope"]:
            raise ValueError(f"{key}: missing producer or scope")
        page = reply.get("public_page")
        if reply.get("publication_pending") and page:
            raise ValueError(f"{key}: reply publication is still pending")
        if page is not None:
            if not re.fullmatch(r"[a-z0-9-]+\.html", page) or not (site / page).is_file():
                raise ValueError(f"{key}: invalid local reply page")
    for item in data["items"]:
        if item["id"] in seen:
            raise ValueError("Duplicate direct-reply record")
        seen.add(item["id"])
        reply = replies[item["reply_id"]]
        if set(item) & set(reply):
            raise ValueError("An item must not override the producer reply")
        if not item["chains"]:
            raise ValueError("Direct reply is not evidence of retail presence")
        for chain in item["chains"]:
            if not chain["network"]:
                raise ValueError("Missing retail chain")
            date.fromisoformat(chain["checked_at"])
        refs = ([{"type": "producer_reply", "url": reply["public_page"]}]
                if reply.get("public_page") else [])
        items.append({**item, **reply, "refs": refs})
    return {"items": items, "copied_at": max(r["evidence_date"] for r in replies.values())}


def render_directory(path, site, translations, company_filter=None):
    """Render only the already-public reply data, never raw correspondence."""
    load_replies(path, site)
    data = json.loads(path.read_text(encoding="utf-8"))
    companies = {}
    for key, reply in data["replies"].items():
        # Product verdicts may be public while publication of the letter is pending.
        # Do not generate an answer page or directory excerpt for those replies.
        if reply.get("publication_pending"):
            continue
        companies.setdefault(reply["company"], []).append((key, reply))
    parts = []
    for company, replies in companies.items():
        if company_filter and company != company_filter:
            continue
        if not company_filter and company == 'АО «Татспиртпром»':
            parts.append('<section class="producer-reply"><h2>Татспиртпром</h2>'
                         '<p>Ответ от 26.10.2026: подтверждённые позиции и исключения.</p>'
                         '<a data-lang-link href="tatspirtprom.html" target="_blank" rel="noopener">Подробнее об ответе ↗</a></section>')
            continue
        parts.append(f'<section class="producer-reply"><h2>{escape(company)}</h2>')
        for key, reply in replies:
            items = [item for item in data["items"] if item["reply_id"] == key]
            # Every product-specific reply identifies its products before the verdict.
            title = " · ".join(item["name"] for item in items) if len(replies) > 1 else ""
            visible = [company, reply["rationale"], *reply["scope"], *(i["name"] for i in items)]
            for value in visible:
                if re.search(r"[А-Яа-яЁё]", value) and value not in translations:
                    raise ValueError(f"Missing producer-directory translation: {value}")
            stamp = date.fromisoformat(reply["evidence_date"]).strftime("%d.%m.%Y")
            parts.append('<div class="reply-decision">')
            if title:
                # Separate spans let existing dictionary translations handle each name.
                parts.append('<h3>' + ' · '.join(f'<span>{escape(i["name"])}</span>' for i in items) + '</h3>')
            parts.append(f'<p class="producer-meta"><span>Ответ от</span> <time datetime="{escape(reply["evidence_date"])}">{stamp}</time></p>')
            css, label = ("st-v", "Веганское") if reply["status"] == "vegan" else ("st-n", "Невеганское")
            parts.append(f'<span class="pill st {css}">{label}</span>')
            parts.append(f'<p>{escape(reply["rationale"])}</p>')
            for scope in reply["scope"]:
                parts.append(f'<p class="reply-scope"><strong>Область действия:</strong> <span>{escape(scope)}</span></p>')
            if reply.get("public_page"):
                parts.append(f'<a class="reply-original" data-lang-link href="{escape(reply["public_page"])}">Оригинал ответа</a>')
            if items:
                parts.append(f'<details class="reply-products"><summary><span>Напитки в справочнике</span> ({len(items)})</summary><ul>')
                for item in items:
                    href = './?' + urlencode({"id": item["id"]})
                    parts.append(f'<li><a data-lang-link href="{escape(href)}">{escape(item["name"])}</a></li>')
                parts.append('</ul></details>')
            parts.append('</div>')
        parts.append('</section>')
    return '\n'.join(parts)
