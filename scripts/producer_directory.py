"""Alphabetical producer index and scoped detail pages."""
import json
import re
import hashlib
from html import escape
from producer_replies import load_replies, render_directory

KNOWN = {
    'АО «Татспиртпром»': ('Татспиртпром', 'tatspirtprom.html'),
    'АО «Башспирт»': ('Башспирт', 'bashspirt.html'),
    'Yerevan Brandy Company / ARARAT': ('ARARAT', 'ararat.html'),
    'АО «Кизлярский коньячный завод»': ('Кизлярский коньячный завод', 'kizlyar-brandy-factory.html'),
    'Weingut Peter Jakob Kühn': ('Peter Jakob Kühn', 'producer-peter-jakob-kuehn.html'),
}
VLABEL_PAGES = {
    'Gustave Lorentz': 'gustave-lorentz.html', 'Mahou': 'mahou.html',
    'Estates Costa Lazaridi': 'costa-lazaridi.html', 'Poças': 'pocas.html',
}

def company_name(company):
    return re.sub(r'^(?:(?:ПАО|ОАО|ЗАО|АО|ООО)\s+)+', '', company).strip(' «»"')

def entries(path, vlabel_path):
    data = json.loads(path.read_text(encoding='utf8'))
    result = {}
    for reply in data['replies'].values():
        if reply.get('publication_pending'):
            continue
        company = reply['company']
        name, page = KNOWN.get(company, (company_name(company), 'producer-' + hashlib.sha256(company.encode()).hexdigest()[:12] + '.html'))
        result[company] = dict(name=name, page=page, kind='reply', company=company)
    result['Viu Manent'] = dict(name='Viu Manent', page='viu-manent.html', kind='existing')
    for item in json.loads(vlabel_path.read_text(encoding='utf8'))['items']:
        company = item['company']
        result[company] = dict(name=company_name(company), page=VLABEL_PAGES[company], kind='vlabel', company=company)
    # Russian names first; browser re-sorts translated labels for the selected language.
    return sorted(result.values(), key=lambda x: (not bool(re.match('[А-Яа-яЁё]', x['name'])), x['name'].casefold().replace('ё', 'е')))

def render_index(rows):
    return '<ul class="producer-index" data-producer-index>\n' + '\n'.join(
        f'<li><a data-lang-link href="{escape(row["page"])}">{escape(row["name"])}</a></li>'
        for row in rows) + '\n</ul>'

def render_vlabel(items):
    groups = {}
    for item in items:
        groups.setdefault((item['rationale'], tuple(item['scope']), item['ref_url']), []).append(item)
    parts = []
    for (rationale, scope, url), products in groups.items():
        if not url.startswith('https://'):
            raise ValueError('Invalid manufacturer source')
        parts.append('<section class="producer-reply">')
        parts.append(f'<p>{escape(rationale)}</p>')
        for limit in scope:
            parts.append(f'<p class="reply-scope"><strong>Область действия:</strong> <span>{escape(limit)}</span></p>')
        parts.append(f'<p><a href="{escape(url)}" target="_blank" rel="noopener">Подтверждение на сайте производителя ↗</a></p>')
        parts.append('<h2>Напитки в справочнике</h2><ul>')
        for item in products:
            parts.append(f'<li><a data-lang-link href="./?id={escape(item["id"])}">{escape(item["name"])}</a></li>')
        parts.append('</ul></section>')
    return '\n'.join(parts)

def write_pages(path, vlabel_path, site, out, translations):
    load_replies(path, site)
    rows = entries(path, vlabel_path)
    template = (site / 'producers.html').read_text(encoding='utf8')
    (out / 'producers.html').write_text(template.replace('<!-- PRODUCER_REPLIES -->', render_index(rows)), encoding='utf8')
    vlabel = json.loads(vlabel_path.read_text(encoding='utf8'))['items']
    for row in rows:
        if row['kind'] == 'existing' or row['page'] in ('ararat.html', 'bashspirt.html'):
            continue
        content = (render_directory(path, site, translations, company_filter=row['company'])
                   if row['kind'] == 'reply' else render_vlabel([i for i in vlabel if i['company'] == row['company']]))
        content = content.replace(f'<h2>{escape(row.get("company", ""))}</h2>', '')
        content = '<p><a data-lang-link href="producers.html">Все производители</a></p>\n' + content
        page = template.replace('<h1>Производители</h1>', f'<h1>{escape(row["name"])}</h1>')
        page = page.replace('<title>Производители — Оклейка</title>', f'<title>{escape(row["name"])} — Оклейка</title>')
        page = page.replace('<!-- PRODUCER_REPLIES -->', content)
        (out / row['page']).write_text(page, encoding='utf8')

