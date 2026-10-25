"""Collect prices only for exact catalogue-name matches, with a private resumable cache.

No shop URLs or exact amounts produced here belong in the public data directory.
"""
import argparse
import concurrent.futures
import html
import json
import re
import subprocess
import time
import unicodedata
from datetime import date
from collections import defaultdict
from pathlib import Path


def key(name):
    s = html.unescape(unicodedata.normalize('NFKC', name)).casefold().replace('ё', 'е')
    # A single bottle's standard carton/tube does not identify a different drink.
    # Multi-item gift sets are excluded separately, never stripped into a match.
    s = re.sub(r'\bв\s+(?:подарочной\s+упаковке|коробке|тубе|упаковке)\b|\bп/у\b', ' ', s)
    s = re.sub(r'\d+(?:[.,]\d+)?\s*(?:мл|ml|л|l)(?![a-zа-я])', ' ', s)
    s = re.sub(r'^(?:вино\s+игристое|игристое\s+вино)\s+', 'игристое ', s.strip())
    s = re.sub(r'^(?:вино|виски|водка|пиво|сидр|ром|лик[её]р|коньяк|бренди|джин|текила|соджу)\s+', '', s.strip())
    s = s.replace('’', "'").replace('`', "'")
    return re.sub(r'[^\w%]+', ' ', s).strip()


def volume(name):
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*(мл|ml|л|l)(?![a-zа-я])', str(name), re.I)
    return round(float(m[1].replace(',', '.')) * (1000 if m[2].lower() in ('л','l') else 1)) if m else None


def fetch(item):
    url, source_name, ml, network, ids = item
    try:
        result = subprocess.run(['curl.exe','-sS','-L','--max-time','20','--fail',url],capture_output=True,timeout=24)
        if result.returncode: return {'url':url,'error':'http_or_timeout'}
        s = result.stdout.decode('utf8')
        h = re.search(r'<h1[^>]*>(.*?)</h1>',s,re.S)
        title = html.unescape(re.sub('<[^>]+>',' ',h[1])).strip() if h else ''
        if key(title) != key(source_name): return {'url':url,'error':'title_changed','expected':source_name,'actual':title}
        actual_ml=volume(title) or ml
        source_kind='live_product'
        states=[]
        for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',s,re.S):
            try: obj=json.loads(raw)
            except ValueError:continue
            for product in obj if isinstance(obj,list) else [obj]:
                matches=isinstance(product,dict) and product.get('@type')=='Product' and key(product.get('name',''))==key(source_name)
                if isinstance(product,dict) and network=='Decanter' and product.get('@type')=='SaleEvent':
                    sale=product.get('offers',{})
                    matches=isinstance(sale,dict) and key(sale.get('name',''))==key(source_name) and sale.get('url')==url.split('decanter.ru',1)[-1]
                if matches:
                    offers=product.get('offers',{})
                    for offer in offers if isinstance(offers,list) else [offers]:
                        if isinstance(offer,dict): states.append(offer.get('availability','').rsplit('/',1)[-1])
        availability='available' if 'InStock' in states else 'unavailable' if states and all(x=='OutOfStock' for x in states) else 'unknown'
        evidence=dict(url=url,name=source_name,ml=actual_ml,network=network,checked=date.today().isoformat(),ids=ids,availability=availability,
                      availability_scope='regional',actual_title=title,availability_parser_version=2)
        if network == 'Decanter':
            # First price belongs to the main Offer; later ones are recommendations.
            offer = re.search(r'class="prod-card__price"[^>]*>(.*?itemprop="priceCurrency"[^>]*>)',s,re.S)
            stock=re.search(r'itemprop="availability"\s+href="https?://schema.org/(\w+)"',offer[1]) if offer else None
            if stock:
                evidence['availability']={'InStock':'available','OutOfStock':'unavailable'}.get(stock[1],'unknown')
            p = re.search(r'itemprop="price"\s+content="([\d.]+)"',offer[1]) if offer else None
            price=float(p[1]) if p else None
        else:
            price=None
            for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',s,re.S):
                try: obj=json.loads(raw)
                except ValueError:continue
                for product in obj if isinstance(obj,list) else [obj]:
                    if product.get('@type')=='Product' and key(product.get('name',''))==key(source_name):
                        offer=product.get('offers',{})
                        if isinstance(offer,dict) and offer.get('priceCurrency')=='RUB':price=float(offer.get('price',0))
            if not price:
                reference=re.findall(r'Цена на [^<>\r\n]{1,250}?\s[—–]\s*([\d\s]+(?:[.,]\d+)?)\s*руб\.',s)
                if len(reference)==1:
                    price=float(re.sub(r'\s','',reference[0]).replace(',','.'))
                    source_kind='product_page_reference'
        if not price or price<=0:return dict(evidence,error='no_price')
        return dict(evidence,price=price,source_kind=source_kind)
    except Exception as e:return {'url':url,'error':type(e).__name__}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--aliases',type=Path,required=True)
    ap.add_argument('--retail-root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--workers',type=int,default=6)
    ap.add_argument('--retry-file',type=Path)
    args=ap.parse_args()
    aliases=json.loads(args.aliases.read_text(encoding='utf8'))
    index=defaultdict(set)
    for rid,names in aliases.items():
        for name in names:index[key(name)].add(rid)
    items={}
    for line in (args.retail_root/'cache/decanter_tiles.jsonl').open(encoding='utf-8-sig'):
        for path,name in json.loads(line)['items'].items():
            if '/reviews' in path:continue
            if key(name) in index:
                url='https://decanter.ru'+path
                items[url]=(url,name,volume(name),'Decanter',sorted(index[key(name)]))
    for line in (args.retail_root/'out_amwine.jsonl').open(encoding='utf-8-sig'):
        c=json.loads(line); name=c['name']
        if key(name) in index:
            items[c['url']]=(c['url'],name,volume(c['volume']),'Ароматный Мир',sorted(index[key(name)]))
    done=set()
    if args.out.exists():
        for line in args.out.open(encoding='utf8'):done.add(json.loads(line)['url'])
    if args.retry_file:
        retry={o['url'] for line in args.retry_file.open(encoding='utf8') if (o:=json.loads(line)).get('error')=='no_price' or (o.get('error')=='title_changed' and key(o['expected'])==key(o['actual']))}
        items={url:item for url,item in items.items() if url in retry}
    todo=[item for url,item in items.items() if url not in done and item[2] and 330<=item[2]<=1000 and not re.search(r'бокал|набор|gift\s*set',item[1],re.I)]
    print('Matched URLs',len(items),'pending ordinary bottles',len(todo),flush=True)
    with args.out.open('a',encoding='utf8') as out, concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        good=0
        for n,result in enumerate(pool.map(fetch,todo),1):
            out.write(json.dumps(result,ensure_ascii=False)+'\n');out.flush();good+='price' in result
            if n%50==0 or n==len(todo):print('Fetched',n,'/',len(todo),'prices',good,flush=True)


if __name__=='__main__':main()
