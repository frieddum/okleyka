"""End-to-end guards for known scope mistakes, identity merging and public links."""
import json,re,sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,parse_qs,unquote
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
import merge_cards
from wine_attrs import volume_from_name,abv_from_name
read=lambda p:json.loads((root/p).read_text(encoding='utf-8'))
data=read('_site/data/verified.json')
rows={r[0]:r for r in data['records']}
archive=read('_site/data/archive.json')
all_ids=set(rows)|{r[0] for r in archive['records']}
aliases=data['aliases']
direct_ids={i['id'] for i in read('data/producer_replies.json')['items']}
assert len(rows)==len(data['records'])
for old,new in aliases.items():
    assert old not in rows and new in all_ids and new not in aliases
for r in rows.values():
    a=data['assessments'][r[15]]
    assert a['refs'] or r[0] in direct_ids, ('Missing status source',r[0])
    assert a['status']=={'v':'vegan','n':'nonvegan'}[r[1]]
    v=volume_from_name(r[3])
    assert not(v and r[9] and v!=r[9]), (r[0],r[3],v,r[9])
    if re.search(r'\d+(?:[.,]\d+)?\s*[-–—]\s*\d+(?:[.,]\d+)?\s*%',r[3]):
        assert isinstance(r[11],str) and '–' in r[11], (r[0],r[3],r[11])
cream=rows['rfa-8fc330d93f19']
assert cream[1]=='n'
assert data['assessments'][cream[15]]['refs']==[{'type':'manufacturer','url':'https://www.limoncello.com/en/crema/'}]
assert 'dx-81e6e11a32' not in rows  # Sparkling Lykhny is not covered by the still-wine source.
assert aliases['rfa-76301e4a3e2b']=='rfa-84e907b350d2'
assert rows['rfa-84e907b350d2'][18]==1
assert rows['reply-ararat-honey'][1]=='n' and 'мёда' in rows['reply-ararat-honey'][3]
assert len([r for r in rows.values() if r[0].startswith('reply-ararat-')])==25

# The newer Viu Manent statement covers two ranges, not the entire winery.
viu = [r for r in rows.values() if 'Viu Manent' in r[3]]
updated = [r for r in viu if re.search(r'\b(?:Gran Reserva|Secreto)\b', r[3], re.I)]
assert len(updated) == 18
for r in viu:
    a = data['assessments'][r[15]]
    covered = r in updated
    assert any('tienda.viumanent.cl' in ref['url'] for ref in a['refs']) == covered
    assert a['evidence_date'] == ('2022-11-22' if covered else '2016-10')

# Matching names must not collapse different strengths, ages or star ratings.
def row(i,name,volume=None,abv=None):
    return [i,'v',[0],name,-1,0,0,'f',0,volume,None,abv,None,'2026-10-28',1,0,None,None,0]
assessment=[{'refs':[{'type':'manufacturer','url':'source.html'}]}]
assert merge_cards.skeleton('ARARAT ***')!=merge_cards.skeleton('ARARAT *****')
out,_=merge_cards.merge([row('a','Spirit 3 stars 500мл',None,40),row('b','Spirit 3 stars',700,40)],assessment)
assert len(out)==1 and out[0][9] is None and volume_from_name(out[0][3]) is None
assert len(merge_cards.ALIASES)==1
small,big=row('small','Bottle 500мл',500,40),row('big','Bottle 700мл',700,40)
small[10]='500 мл'
out,_=merge_cards.merge([small,big],assessment)
assert out[0][9] is None and out[0][10] is None
out,_=merge_cards.merge([row('a','Spirit',None,40),row('unknown','Spirit'),row('b','Spirit',None,43)],assessment)
assert len(out)==2  # An unknown ABV must not bridge two different known strengths.
out,_=merge_cards.merge([row('a','Fruitage 3.4%'),row('b','Fruitage',None,3.9)],assessment)
assert len(out)==2
out,_=merge_cards.merge([row('a','Spirit 40%'),row('b','Spirit 43%')],assessment)
assert len(out)==2
assert abv_from_name('Fruitage 3.4–3.9%') is None

class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key not in ('href','src') or not value:continue
            u=urlsplit(value)
            if u.scheme or u.netloc or value.startswith('#'):continue
            file=(root/'_site'/unquote(u.path or 'index.html')).resolve()
            assert file.exists(), (self.page,value)
            rid=parse_qs(u.query).get('id',[None])[0]
            if rid:assert rid in all_ids or rid in aliases,(self.page,rid)
for page in (root/'_site').glob('*.html'):
    parser=Links();parser.page=page.name;parser.feed(page.read_text(encoding='utf-8'))
print(f"Catalog integrity: {len(rows)} cards, {len(aliases)} redirects, local links, scope, bottle sizes and ABV ranges passed")

