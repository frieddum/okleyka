"""Producer navigation: clean names, exact scope, and working detail pages."""
import json
import re
from pathlib import Path
from html import unescape
from producer_directory import company_name, entries, render_index
ROOT = Path(__file__).resolve().parent.parent
rows = entries(ROOT / 'data/producer_replies.json', ROOT / 'data/vlabel_additions.json')
assert len(rows) == 10 and len({r['page'] for r in rows}) == 10
assert company_name('ОАО «Компания»') == 'Компания'
assert company_name('АО «Завод»') == 'Завод'
assert company_name('ПАО ООО «Компания»') == 'Компания'
page = (ROOT / '_site/producers.html').read_text(encoding='utf8')
index = re.search(r'<ul class="producer-index".*?</ul>', page, re.S).group()
assert len(re.findall('<li>', index)) == 10
assert not any(value in index for value in ('Ответ от', 'Область действия', '<p>', '<h2>', 'АО «', 'ОАО'))
assert not any('Массандра' in r['name'] for r in rows)
assert '&lt;script&gt;' in render_index([{'name':'<script>', 'page':'safe.html'}])
for row in rows:
    detail = (ROOT / '_site' / row['page']).read_text(encoding='utf8')
    assert 'producers.html' in detail and '<!-- PRODUCER_REPLIES -->' not in detail
    if row['kind'] == 'vlabel':
        items = json.loads((ROOT / 'data/vlabel_additions.json').read_text(encoding='utf8'))['items']
        own = [i for i in items if i['company'] == row['company']]
        linked = set(re.findall(r'\?id=([^"]+)', detail))
        assert linked == {i['id'] for i in own}
        for item in own:
            assert item['ref_url'] in unescape(detail)
            assert all(scope in unescape(detail) for scope in item['scope'])
print('Producer index: clean names; 10 detail pages; all 37 V-Label links and scopes preserved')

