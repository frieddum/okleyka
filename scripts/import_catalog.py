"""Импорт сводного каталога сетей (catalog_public.json) по правилам справочника.

Запуск:
  python scripts/import_catalog.py путь/catalog_public.json путь/barnivore_export/companies.jsonl

Пишет:
  data/catalog_extra.json        — только публикуемые позиции, без цитат и служебных полей;
  data/barnivore_companies.json  — адрес страницы Barnivore -> название компании
                                   (только для страниц, на которые ссылаются записи справочника).

Правила отбора (те же, что для основного снимка):
  - только «веган» и «не веган»; «недостаточно данных» и противоречия не публикуются;
  - сопоставление только с компанией (конкретного продукта на Barnivore нет) не публикуется;
  - не публикуется, если статус зависит от вина, цвета, линии, бочки, версии или места производства,
    если перечень производителя не приведён или ответ касается только части ассортимента;
  - не публикуется российское производство: страна в сети «Россия» или российский производитель;
  - без ссылки на страницу Barnivore запись не публикуется.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, COMPANIES = Path(sys.argv[1]), Path(sys.argv[2])
SNAPSHOT = ROOT / "data" / "snapshot.json"

DEPENDS = re.compile(r"зависит от|может зависеть|отдельно не упоминается|таблица .* не приведена|"
                     r"только Barolo|нефильтрованный LBV|разные страны: .*Россия")
RU_PRODUCER = re.compile(r"\b(?:ООО|АО|ЗАО|ОАО|ПАО)\b|ЛВЗ|Балтика|ИНБЕВ ЭФЕС|Объединённые Пивоварни|"
                         r"Синергия|Башспирт|Русский Стандарт|Василеостровская|Мегапак|Глетчер|Игристые вина|Efes Rus",
                         re.I)
CAT_TO_SECTION = {"Вино": "wine", "Игристое и шампанское": "wine", "Вермут и креплёные вина": "wine",
                  "Пиво": "beer", "Сидр, перри, медовуха": "cider"}
DROP_LIMITS = re.compile(r"старый|^ответ \d{4} г\.|^ответы \d{4}|письма без дат|сети указывают разные страны")

# Сопоставление только с компанией (продукта на Barnivore нет) публикуется лишь для компаний,
# чьё письмо прочитано и относится ко всей продукции («all our wines», «none of our products»).
# Значение: (регэксп названий, которые всё равно не берём, минимальный урожай, примечание об упаковке).
WHOLE_RANGE = {
    c: (None, None, None) for c in """
Botter S.p.a.|Macallan Distillery|Mezzacorona|Weingut Dr. Loosen|Casa Santos Lima|Glenfarclas Distillery|
Tarapaca Vineyards|Talisker Distillery|Antigal Winery & Estates|Louis Roederer Champagne|Nittnaus|Hardys|
Glengoyne Distillery|Château du Breuil|Paul Jaboulet Aîné|La Gioiosa S.p.A.|Glen Moray Distillery|Absolut Vodka|
Auchentoshan Distillery|Glen Scotia|De Wetshof Estate|Moët & Chandon|Neethlingshof Estate|Warwick Wine Estate|
Glen Grant Distillery|Lagavulin Distillery|Zacapa|Martini & Rossi|Casa Vinicola Botter Carlo & C. S.p.A|
Canard-Duchêne|Overhex Wine International|Highland Park Distillery|Tesseron Cognac|Brugal Rum|
Michael David Winery|William Grant & Sons Ltd|Paulaner Brewery|Angostura|Araldica Castelvero S.C.A.|
Johannes Zillinger GmbH|José Maria da Fonseca|Murphy-Goode Winery|Quinta das Arcas|Cardhu Distillery|Cutty Sark|
Ciroc|Bombay Sapphire Gin|Bodegas Williams & Humbert|Veuve Clicquot|Sandeman|Dopff Au Moulin|Nals Margreid|
Isle of Jura Distillery|Bouvet Ladubay|Appleton Estate|Legendario S.L.|Sauza|Félix Solís Avantis|Messias Port|
Bollinger Champagne|Tanglin Gin|M. Chapoutier S.A.|Watershed Distillery|Le Contesse srl|älska cider|
Celtic Marches Beverages Limited|Piper Heidsieck Champagne|Choya Umeshu Co., Ltd|Tinazzi srl|
Caves Bernard-Massard SA|Domaine Moncourt|Kaesler Vineyards|Marqués de Cáceres Winery|Monte Bernardi|
Paxton Vineyards Pty Ltd|Tenuta Il Poggione|The Critic|Viu Manent Winery|Akashi Sake Brewery Co. Ltd|
Early Times Distillery Co|Mackmyra Svensk Whisky AB|Spicebox|Masons Yorkshire Gin Ltd.|Albet i Noya|
Ca' del Bosco S.r.l.|Fresita|Kleine Zalze|Santa Margherita USA, Inc.|United Dutch Breweries B.V.|Royal Unibrew|
Brouwerij Van Honsebrouck|Barsol USA LLC|Villa Sandi S.P.A.|Aston Manor Brewery|Champagne Lanson|
Domaine Laurent-Perrier|Le Brun de Neuville|Champagne Lombard|Barefoot Wine|Famille Perrin|te Pa Family Vineyards|
Ecusson|Champagne Billecart-Salmon|Jägermeister|Southern Comfort|Casa Ermelinda Freitas|Alpha Box & Dice|
Cantina Terlano|E. Guigal S.A.S.|Domaine Bousquet|Domaine La Suffrène|Fat Bastard Wine|Georges Duboeuf|
Château Smith Haut Lafitte|Les Jamelles|Lungarotti|Marqués de Riscal|Pascal Jolivet|Weingut R&A Pfaffl|
Produttori di Manduria Wines|Springfield Estate|Urlar Estate|Ben Nevis Distillery|Glendalough Distillery|
Glenfiddich|Willett Distillery|Chase Distillery|Waldemar Behn GmbH|Grey Goose Vodka|Western Son Distillery|
Greenall's|Juvé y Camps|Vinicola Salton|Cantina Santa Maria la Palma|Braastad Cognac|Thomas Hine & Co.|
Domaines Francis Abecassis|AleSmith Brewing Co|Berliner-Kindl-Schultheiss-Brauerei|Budějovický Budvar|
Brouwerij Verhaeghe Vichte|Flensburger Brauerei|Jopen BV|Kulmbacher Brauerei|Brouwerij Haacht|San Miguel Beer|
Sapporo Breweries Ltd|Volfas Engelman|Zardetto Prosecco S.r.l.|Bumbu Rum Co.|Chairman's Reserve Rum|
Thatchers Cider|Don Julio Tequila|Champagne Fleury S.A.|Champagne Jacquart|Champagne Mailly Grand Cru|
Maison Burtin|Champagne Pol Roger|Champagne Thienot|Chateau Mukhrani|Dominus Estate|Don Simón|Obikwa|
Azienda Vinicola Rivera S.p.A.|The Hess Collection Winery|Jim Barry Wines|Stellenbosch Vineyards|Bartenura Winery|
Charles de Fère|Domaine Delmas|Louis Bouillot|Bodegas López Morenas|Bolla Wines|Champagne Diebolt-Vallois|
Gruet Winery""".replace("\n", "").split("|")
}
# Ошибки сопоставления, найденные при проверке: другая компания с похожим названием, слишком общее
# название позиции или российское производство. «*» — компания не публикуется целиком.
BLOCK = {
    "Christian Brothers Brandy": "*",            # американский бренди ≠ кальвадос Coeur de Lion
    "Ste. Chapelle Winery": "*",                 # ≠ Château Lafaurie-Peyraguey
    "Stella Bella Wines": "*",                   # австралийская ≠ итальянская «Стелла Белла»
    "Graziano Family of Wines": "*",             # ≠ Graziano Prà
    "Beluga": "*",                               # российское производство
    "The Sazerac Company": r"Сперон|Sperone",
    "Vivanco": r"Vivanza",
    "Heineken": r"Моретти|Moretti",              # возможен российский розлив
    "Finca Las Moras": r"Ros[eé]|Розе",
    "Mastroberardino Spa": r"Lacryma",
    "Casa Vinicola Natale Verga s.p.a.": r"Marazzine",
    "Fetzer Vineyards": r"Artius",
    "Hugel & Fils": r"Gentil, AOC|Riesling Alsace AOC",
    "Botter S.p.a.": r"Prima Alta",
    "Louis Roederer Champagne": r"^Шампанское (Brut Premier|Carte Blanche)$",
    "Barton & Guestier": r"^Вино Sauvignon Blanc Cotes de Gascogne$",
    "Brancott Estate": r"South Island",
    "Félix Solís Avantis": r"Verano",
    "Chiarli": r"Poderi Alti",
}
# У Tinazzi в карточках сетей много чужих и безымянных вин; берём только собственные линейки.
ONLY = {"Tinazzi srl": r"Tinazzi|Rocchi|Santa Croce|Feudo Croce|Valleselle|Campo delle Rose|Selezione di Famiglia|"
                       r"Prato del Faggio|Megale|Malnera|Byzantium|Monteiasi|Alea"}
GLUE = "Клей этикеток на бутылках содержит казеин (по словам производителя)."
WHOLE_RANGE.update({
    "Glaetzer Wines": (r"Dixon", None, None),             # Glaetzer-Dixon — другая винодельня
    "Ballantine's": (r"Brasil", None, None),              # ароматизированный напиток, не виски
    "Alken-Maes Brewery": (r"Стронгбоу|Strongbow", None, None),
    "Bodegas Altanza": (None, 2018, None),                # веганские с урожая 2018
    "Quintessa": (None, 2013, None),                      # веганские с урожая 2013
    "Bayreuther Bierbrauerei AG": (None, None, GLUE),
    "G. Schneider & Sohn": (None, None, GLUE),
    "Einbecker Brauhaus AG": (None, None, GLUE),
})


def norm(s):
    return re.sub(r"[^a-zа-я0-9]+", " ", (s or "").lower().replace("ё", "е")).strip()


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    by_company = {}
    # Читаем построчно по \n: внутри текстов писем встречаются U+2028, splitlines() их бы разрезал.
    with COMPANIES.open(encoding="utf-8", newline="\n") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    for c in rows:
        by_company.setdefault(c["company"], []).append((c["category"], c["company_url"]))

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    taken = {(norm(r["name"]), r["network"]) for r in snap["verified"]}

    out, skipped = [], {}

    def skip(reason):
        skipped[reason] = skipped.get(reason, 0) + 1

    for it in data["items"]:
        if it["status"] not in ("веган", "не веган"):
            skip("нет однозначного статуса"); continue
        block = BLOCK.get(it["barnivore_company"])
        if block == "*" or (block and re.search(block, it["name"], re.I)):
            skip("ошибка сопоставления или общее название"); continue
        only = ONLY.get(it["barnivore_company"])
        if only and not re.search(only, it["name"], re.I):
            skip("ошибка сопоставления или общее название"); continue
        company_level = "компанией" in it["match_state"]
        extra_scope = []
        if company_level:
            rule = WHOLE_RANGE.get(it["barnivore_company"])
            if not rule:
                skip("только компания, письмо не про весь ассортимент"); continue
            bad_name, min_year, note = rule
            years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", it["name"])]
            if bad_name and re.search(bad_name, it["name"], re.I):
                skip("только компания, позиция не покрыта письмом"); continue
            if min_year and years and min(years) < min_year:
                skip("только компания, урожай раньше подтверждения"); continue
            extra_scope = [note] if note else []
        if any(DEPENDS.search(l) for l in it["limitations"]):
            skip("статус зависит от вина/версии/места"); continue
        if it["country"] == "Россия" or RU_PRODUCER.search(it["producer"] or ""):
            skip("российское производство"); continue
        pages = by_company.get(it["barnivore_company"], [])
        section = CAT_TO_SECTION.get(it["category"], "liquor")
        url = next((u for cat, u in pages if cat == section), pages[0][1] if pages else None)
        if not url:
            skip("нет ссылки на Barnivore"); continue
        chains = [c for c in it["chains"] if (norm(it["name"]), c["chain"]) not in taken]
        if not chains:
            skip("уже есть в основном снимке"); continue
        out.append({
            "id": it["id"],
            "name": it["name"],
            "company": it["barnivore_company"],
            "category": it["category"],
            "country": it["country"] or None,
            "status": "vegan" if it["status"] == "веган" else "nonvegan",
            "rationale": (
                f"Производитель ответил про всю свою продукцию: "
                f"{'животные продукты не используются' if it['status'] == 'веган' else 'используются продукты животного происхождения'}. "
                f"Отдельной записи об этой позиции на Barnivore нет." if company_level else it["explanation"]),
            "scope": ([f"Вся продукция компании «{it['barnivore_company']}»."] if company_level else [])
                     + [l for l in it["limitations"] if not DROP_LIMITS.search(l) and "уровне компании" not in l]
                     + extra_scope,
            "evidence_date": it["confirmed_at"] or None,
            "barnivore_url": url,
            "chains": [{"network": c["chain"], "checked_at": c["checked_at"]} for c in chains],
        })

    used = {o["barnivore_url"] for o in out}
    used |= {ref["url"] for r in snap["verified"] for ref in r["assessment"]["references"] if ref["type"] == "Barnivore"}
    ov = ROOT / "data" / "overrides.json"
    if ov.exists():
        used |= {ref["url"] for o in json.loads(ov.read_text(encoding="utf-8"))["overrides"] for ref in o.get("refs") or []}
    url_to_company = {}
    for name, pages in by_company.items():
        for _, u in pages:
            if u in used:
                url_to_company[u] = name

    (ROOT / "data" / "catalog_extra.json").write_text(json.dumps(
        {"source": "сводный каталог сетей", "copied_at": data["meta"].get("generated_at"), "items": out},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / "data" / "barnivore_companies.json").write_text(json.dumps(
        dict(sorted(url_to_company.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Публикуется позиций: {len(out)}")
    for k, v in sorted(skipped.items(), key=lambda x: -x[1]):
        print(f"  не публикуется — {k}: {v}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
