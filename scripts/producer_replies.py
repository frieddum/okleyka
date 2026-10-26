"""Public, scoped decisions from direct producer replies. Raw mail stays private."""
import json
import re
from datetime import date


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
