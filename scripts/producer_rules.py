"""Правила по письмам производителей, у которых ответ зависит от цвета, линейки или урожая.

Ключ — компания, ответившая на запрос (название страницы Barnivore).
  red / white / rose — статус для этого цвета: "vegan", "nonvegan" или None (не публиковать);
                       если указан хотя бы один цвет, вино без известного цвета не публикуется;
  only     — публиковать только позиции, чьё название подходит под регэксп (названные в письме линейки);
  drop     — не публиковать позиции компании (письмо о другом продукте или другой компании);
  status   — статус для всех позиций (более свежий ответ производителя);
  min_vintage — для вин с указанным урожаем раньше этого года статус не подтверждён;
  note     — пояснение в карточке.
Все правила взяты из переписки на страницах Barnivore, приведённых в карточках.
"""

V, N = "vegan", "nonvegan"

RULES = {
    # Ответ различает цвета
    "Maison Louis Jadot": dict(red=V, white=N, rose=None,
                               note="Производитель: веганские только красные вина; белые и шабли оклеены казеином."),
    "Bodegas Protos": dict(red=N, white=V, rose=V,
                           note="Производитель: белые и розовые осветляются бентонитом, красные — желатином."),
    "Cavit s.c.": dict(red=None, white=V, rose=None,
                       note="Производитель: веганские только белые вина и белые игристые."),
    "Bodegas Martín Códax": dict(red=None, white=V, rose=None,
                                 note="Производитель: ответ касается белых вин."),
    "Mollydooker Wines": dict(red=V, white=N, rose=None,
                              note="Производитель: красные веганские, белые оклеены обезжиренным молоком."),
    "Marqués De Murrieta": dict(red=N, white=V, rose=V,
                                note="Производитель: в красных яичный альбумин, в белых и розовых его нет."),
    "Ken Forrester Vineyards": dict(red=None, white=V, rose=None,
                                    note="Производитель: белые веганские, для красных зависит от урожая."),
    "CVNE (Compañia Vitivinícola del Norte de Españá)": dict(red=N, white=V, rose=V,
                                                            note="Производитель: красные осветляются яичным белком."),
    "Beringer Vineyards": dict(red=N, white=None, rose=V,
                               note="Производитель: красные могут быть оклеены животными веществами."),
    "Viña Errazuriz S.A": dict(red=V, white=N, rose=None,
                               note="Производитель: красные веганские, белые нет."),
    "MGM Mondo Del Vino": dict(red=N, white=V, rose=None,
                               note="Производитель: в красных (кроме BIO) желатин, белые веганские."),
    "Berton Vineyards": dict(red=V, white=N, rose=None,
                             note="Производитель: красные веганские, белые оклеены желатином и казеинатами."),
    "Belle Glos": dict(red=V, white=N, rose=N,
                       note="Производитель: красные веганские, белые и розовые оклеены животным веществом."),
    "Langmeil Winery": dict(red=V, white=N, rose=None,
                            note="Производитель: красные веганские, белые оклеены молочным белком."),
    "Baron Philippe de Rothschild S.A.": dict(red=N, white=V, rose=None,
                                              note="Производитель: для красного — свиной желатин, Sauvignon Blanc веганский."),
    "Trapiche Wines USA": dict(red=V, white=V, rose=None,
                               note="Производитель: ответ касается красных и белых вин."),
    "Wines & Winemakers by Saven": dict(red=N, white=None, rose=None,
                                        note="Производитель: во всех красных — желатин."),
    "Simonsig Wine Estate": dict(red=V, white=V, rose=V, min_vintage_red=2018,
                                 note="Производитель: белые и игристые веганские, красные — с урожая 2018."),
    # Ответ касается только названных линеек
    "Finca Las Moras": dict(only=r"Cabernet|Malbec|Syrah|Sauvignon",
                            note="Сертифицированы веганскими Cabernet, Malbec, Syrah и Sauvignon Blanc."),
    "Bodegas Ramón Bilbao": dict(only=r"Crianza|Reserva|Edici[oó]n Limitada|Vi[nñ]edos de Altura|Mirto",
                                 note="Производитель: веганские названные красные вина."),
    "Porto Dalva": dict(only=r"LBV|Vintage", status=V,
                        note="Производитель: веганские только LBV и Vintage, остальные порто осветляются желатином."),
    "Hardy's Wines": dict(only=r"Sauvignon", note="Веганский знак только на Banrock Station Sauvignon Blanc."),
    "Vicente Gandía": dict(only=r"Viura|Blanco", note="Веганский знак производителя — у El Pescaíto белого."),
    "Santa Julia Winery": dict(only=r"Reserva|Org[aá]nica", note="Производитель: веганские Santa Julia Reserva и Orgánica."),
    # Более свежий ответ производителя
    "Ruffino Wines": dict(status=V, note="Производитель (2023): животные вещества для оклейки не используются, все вина Ruffino веганские."),
    "Vilarnau": dict(status=V, min_vintage=2015,
                     note="Производитель: с урожая 2015 рыбий клей заменён гороховым и картофельным белком."),
    # Письмо о другом продукте, другой компании или без однозначного ответа
    "August Cellars": dict(drop=True),            # американская винодельня ≠ немецкий August Eser
    "Caroline Cellars Winery": dict(drop=True),   # ≠ Caroline Bay, Caroline Parent
    "Navarro Vineyards and Winery": dict(drop=True),  # ≠ Navarro Correas, Navarro López
    "El Grifo": dict(drop=True),                  # ≠ Grifo (Апулия)
    "Celler Credo": dict(drop=True),              # ответ только о Miranius
    "Marisco Vineyards Ltd": dict(drop=True),     # The Ned: веганского статуса нет
    "Sella & Mosca": dict(drop=True),             # веганские только перечисленные урожаи
    "Bread & Butter Wines": dict(drop=True),      # «без молочного», но не веганские
    "The Winery of Good Hope": dict(drop=True),   # красные иногда с желатином
    "Van Loveren Vineyards": dict(drop=True),
    "Rotkäppchen-Mumm Sektkellereien GmbH": dict(drop=True),
    "Carolina Wine Brands": dict(drop=True),
    "JUSTINO'S, MADEIRA WINES, S.A.": dict(drop=True),
    "Taylors Wines Pty Limited": dict(drop=True),
    "Vincente Gandia": dict(drop=True),
    "Henschke Cellars": dict(drop=True),
}


def color_key(color):
    return {"Красное": "red", "Белое": "white", "Розовое": "rose"}.get(color)
