"""New mail decisions preserve vintage limits, unresolved products and privacy."""
import json,re
from pathlib import Path
from producer_replies import load_replies
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'_site/data/verified.json').read_text(encoding='utf-8'))
rows={r[0]:r for r in d['records']}
loaded=load_replies(ROOT/'data/producer_replies.json',ROOT/'site')['items']
alpha=[i for i in loaded if i['reply_id']=='alpha-2026-11-16']
niva=[i for i in loaded if i['reply_id'].startswith('niva-')]
ragnaud=[i for i in loaded if i['reply_id']=='ragnaud-2026-11-16']
cert=[i for i in loaded if i['reply_id'].startswith('cert-')]
assert len(alpha)==17 and len(niva)==48 and len(ragnaud)==12 and len(cert)==24
assert sum(i['status']=='vegan' for i in niva)==32
assert all(i['status']=='nonvegan' for i in ragnaud)
assert len({i['name'].casefold() for i in alpha+niva+ragnaud+cert})==101
assert all(not rows[i['id']][2] for i in alpha+niva+ragnaud+cert)
assert all(i['id'] not in d['price_levels'] for i in alpha+niva+ragnaud+cert)
assert all(rows[k][1]=='n' for k in ('reply-niva-oasis-coffee','reply-niva-coffee-nd','reply-niva-bisquit-chocolate','reply-niva-bisquit-cream','reply-niva-oasis-maracuja'))
assert all(rows[i['id']][1]=='v' for i in loaded if i['reply_id']=='alliance-2026-11-16')
assert len([i for i in loaded if i['reply_id']=='alliance-2026-11-16'])==8
assert rows['reply-niva-oasis-coffee-cream'][1]=='n'
assert rows['reply-niva-niva-distillery-creme-de-cassis'][1]=='v'
old=rows['04ff672a92']
assert old[1]=='v' and old[2]==[]
assert old[0] not in d['price_levels']
assert not any(i['name']=='Errázuriz Reserva Estate Sauvignon Blanc' for i in cert)
a=d['assessments'][old[15]]
assert 'Подтверждённые урожаи: 2022, 2023, 2024, 2025, 2026.' in a['scope']
assert a['evidence_date']=='2026-11-16' and a['reviewed_at']=='2026-11-18'
for i in cert:
 scope=d['assessments'][rows[i['id']][15]]['scope']
 assert i['product_scope'][0] in scope
 assert '2019' not in ' '.join(scope)
 assert not rows[i['id']][12]  # Single product card; the exact eligible vintages are in its scope.
pages=[ROOT/'_site/alpha-estate.html',ROOT/'_site/chadwick-vlabel-2026.html',
       ROOT/'_site/niva.html',ROOT/'_site/ragnaud-sabourin.html']
for p in pages:
 text=p.read_text(encoding='utf-8')
 assert not re.search(r'Borisova|Манукян|Исаченков|Petridis|Lema|mailto:|mail\.google|@alpha|@nivaspb',text)
for p in pages[2:]:
 text=p.read_text(encoding='utf-8')
 assert '<blockquote' not in text and 'Оригинал ответа' not in text
 assert 'Краткое содержание ответа' in text
certificate=pages[1].read_text(encoding='utf-8')
assert len(re.findall(r'CL-0065-\d{4}',certificate))==25
assert len(set(re.findall(r'\?id=([^"]+)',certificate)))==25
assert '2026' in certificate and '31.12.2026' in certificate
print('November replies: Scoped November cards, exact certificate scope, exclusions and privacy passed')
