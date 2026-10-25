"""Check known catalogue offers; archive only with complete negative evidence.

Private evidence contains URLs. The public decision contains IDs and dates only.
Unknown, renamed, inaccessible or unexamined offers always prevent archiving.
"""
import argparse
import concurrent.futures
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_price_sources import key, volume, fetch


def can_archive(networks, evidence):
    return bool(networks) and all(evidence.get(net) and
        all(o.get('availability')=='unavailable' and o.get('availability_scope') in ('catalog','network')
            for o in evidence[net]) for net in networks)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--retail-root',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--refresh',action='store_true')
    args=ap.parse_args(); work=args.work
    root=Path(__file__).resolve().parent.parent
    meta=json.loads((root/'_site/data/meta.json').read_text(encoding='utf8'))
    rows={}
    for filename in ('verified.json','archive.json'):
        path=root/'_site/data'/filename
        if path.exists(): rows.update({r[0]:r for r in json.loads(path.read_text(encoding='utf8'))['records']})
    aliases=json.loads((work/'price_card_aliases.json').read_text(encoding='utf8'))
    index=defaultdict(set)
    for rid,names in aliases.items():
        if rid not in rows:continue
        for name in names:index[key(name)].add(rid)
    items={}
    for line in (args.retail_root/'cache/decanter_tiles.jsonl').open(encoding='utf-8-sig'):
        for path,name in json.loads(line)['items'].items():
            if '/reviews' not in path and key(name) in index:
                url='https://decanter.ru'+path
                items[url]=(url,name,volume(name),'Decanter',sorted(index[key(name)]))
    for line in (args.retail_root/'out_amwine.jsonl').open(encoding='utf-8-sig'):
        c=json.loads(line);name=c['name']
        if key(name) in index:items[c['url']]=(c['url'],name,volume(c['volume']),'Ароматный Мир',sorted(index[key(name)]))
    path=work/'availability_observations.jsonl'
    existing={}
    if path.exists():
        for line in path.open(encoding='utf8'):
            o=json.loads(line);existing[o['url']]=o
    todo=[item for url,item in items.items() if args.refresh or url not in existing or
          (item[3]=='Decanter' and existing[url].get('availability')=='unknown' and existing[url].get('error') in (None,'no_price') and existing[url].get('availability_parser_version',0)<2)]
    print('Checking availability:',len(todo),'known offers',flush=True)
    def check(item):
        o=fetch(item)
        o.setdefault('network',item[3]);o.setdefault('ids',item[4])
        o.setdefault('availability','unknown');o.setdefault('checked',date.today().isoformat())
        o.setdefault('availability_scope','regional')
        if item[3]=='Decanter' and o['availability']=='unavailable':
            # The site's city menu lists precisely Moscow, SPB and Ivanovo.
            regional=[o]
            for city in ('spb','ivn'):
                regional.append(fetch((item[0].replace('https://decanter.ru/',f'https://{city}.decanter.ru/'),*item[1:])))
            states=[x.get('availability','unknown') for x in regional]
            o['regional_checks']=[{'url':x['url'],'availability':x.get('availability','unknown')} for x in regional]
            if 'available' in states:o['availability']='available'
            elif all(x=='unavailable' for x in states):o['availability_scope']='network'
            else:o['availability']='unknown'
        return o
    with path.open('a',encoding='utf8') as out, concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n,o in enumerate(pool.map(check,todo),1):
            out.write(json.dumps(o,ensure_ascii=False)+'\n');out.flush();existing[o['url']]=o
            if n%100==0 or n==len(todo):print('Availability',n,'/',len(todo),flush=True)
    evidence=defaultdict(lambda:defaultdict(list))
    for url,item in items.items():
        o=dict(existing.get(url,{'availability':'unknown'}))
        o.setdefault('availability_scope','regional')
        for rid in item[4]:evidence[rid][item[3]].append(o)
    decision_path=root/'data/archived.json'
    previous=json.loads(decision_path.read_text(encoding='utf-8-sig')) if decision_path.exists() else {}
    archived={rid:decision for rid,decision in previous.items() if rid in rows};review=[]
    for rid,row in rows.items():
        networks=[meta['dicts']['networks'][i] for i in row[2]]
        if any(o.get('availability')=='available' for net in networks for o in evidence[rid].get(net,[])):
            archived.pop(rid,None)
        elif can_archive(networks,evidence[rid]):
            archived[rid]={'checked_at':max(o['checked'] for net in networks for o in evidence[rid][net]),
                           'reason':'out_of_stock_all_checked_networks'}
        elif any(o.get('availability')=='unavailable' for observations in evidence[rid].values() for o in observations):
            review.append({'id':rid,'name':row[3],'networks':networks})
    (root/'data/archived.json').write_text(json.dumps(archived,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    report={'archived':len(archived),'total':len(rows),'offer_states':dict(Counter(o['availability'] for o in existing.values())),
            'incomplete_or_mixed':review}
    (work/'availability_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='incomplete_or_mixed'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
