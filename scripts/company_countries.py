"""Страна компании по адресу из выгрузки Barnivore.

python scripts/company_countries.py <companies.jsonl>
Пишет data/company_countries.json: {адрес страницы компании на Barnivore: страна по-русски}.
Берутся только компании из data/barnivore_companies.json. В файл попадает только страна, адрес не сохраняется.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RU = {
    "USA": "США", "France": "Франция", "Italy": "Италия", "Spain": "Испания", "England": "Великобритания",
    "Wales": "Великобритания", "Scotland": "Шотландия", "Germany": "Германия", "South Africa": "ЮАР",
    "Australia": "Австралия", "Portugal": "Португалия", "Belgium": "Бельгия", "Chile": "Чили",
    "Argentina": "Аргентина", "Austria": "Австрия", "New Zealand": "Новая Зеландия",
    "The Netherlands": "Нидерланды", "Netherlands": "Нидерланды", "Ireland": "Ирландия", "Canada": "Канада",
    "Czech Republic": "Чехия", "Japan": "Япония", "Sweden": "Швеция", "China": "Китай", "Lithuania": "Литва",
    "Georgia": "Грузия", "Dominican Republic": "Доминиканская Республика", "Barbados": "Барбадос",
    "Finland": "Финляндия", "Estonia": "Эстония", "Poland": "Польша", "Malaysia": "Малайзия",
    "Philippines": "Филиппины", "Phillipines": "Филиппины", "Thailand": "Таиланд", "Luxembourg": "Люксембург",
    "Lebanon": "Ливан", "Slovenia": "Словения", "Montenegro": "Черногория", "Hungary": "Венгрия",
    "Brazil": "Бразилия", "Republic of Trinidad and Tobago": "Тринидад и Тобаго", "Russia": "Россия",
    "Mexico": "Мексика", "Nicaragua": "Никарагуа", "Cuba": "Куба", "India": "Индия", "Iceland": "Исландия",
    "Latvia": "Латвия", "Guatemala": "Гватемала", "Singapore": "Сингапур", "Slovak Republic": "Словакия",
    "Turkey": "Турция", "Jamaica": "Ямайка", "Greece": "Греция", "Switzerland": "Швейцария",
    "Denmark": "Дания", "Norway": "Норвегия", "Israel": "Израиль", "Uruguay": "Уругвай", "Peru": "Перу",
    "Moldova": "Молдова", "Armenia": "Армения", "Romania": "Румыния", "Bulgaria": "Болгария",
}


def main(src):
    used = set(json.loads((ROOT / "data" / "barnivore_companies.json").read_text(encoding="utf-8")))
    out = {}
    with open(src, encoding="utf-8", newline="\n") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            if d["company_url"] not in used:
                continue
            last = (d.get("address") or "").split(",")[-1].strip()
            if last in RU:
                out[d["company_url"]] = RU[last]
    path = ROOT / "data" / "company_countries.json"
    path.write_text(json.dumps(dict(sorted(out.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out)} компаний со страной -> {path.name}")


if __name__ == "__main__":
    main(sys.argv[1])
