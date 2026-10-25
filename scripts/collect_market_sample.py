"""Private deterministic retailer sample independent of reviewed vegan entries."""
import argparse
import concurrent.futures
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_price_sources import fetch, key, volume
from price_levels import category, ordinary_volume

ap=argparse.ArgumentParser()
ap.add_argument('--retail-root',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--category')
args=ap.parse_args()
groups=defaultdict(dict)
for line in (args.retail_root/'cache/decanter_tiles.jsonl').open(encoding='utf-8-sig'):
    for path,name in json.loads(line)['items'].items():
        m=re.match(r'^(Вино игристое|Игристое вино|Шампанское|Вино|Водка|Виски|Коньяк|Бренди|Ром|Джин|Текила|Ликёр|Ликер|Вермут|Аперитив|Портвейн|Херес)\s',name,re.I)
        if not m or '/reviews' in path or re.search(r'набор|бокал|gift\s*set',name,re.I):continue
        kind=m[1].capitalize().replace('Ликер','Ликёр').replace('Вино игристое','Игристое вино').replace('Шампанское','Игристое вино')
        scale=category(kind,bool(re.search(r'игрист|шампан|prosecco|просекко|spumante',name,re.I)))
        ml=volume(name)
        if ml and ordinary_volume(ml,scale):groups[scale][key(name)]=('https://decanter.ru'+path,name,ml,'Decanter',[])
done=set()
if args.out.exists():
    done={json.loads(line)['url'] for line in args.out.open(encoding='utf8')}
rng=random.Random(20261026);todo=[]
for scale,products in sorted(groups.items()):
    if args.category and scale!=args.category:continue
    sample=rng.sample(sorted(products.values()),min(120 if scale=='wine' else 40,len(products)))
    todo.extend(item for item in sample if item[0] not in done)
print('Independent market sample',len(todo),flush=True)
with args.out.open('a',encoding='utf8') as out,concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for n,o in enumerate(pool.map(fetch,todo),1):
        out.write(json.dumps(o,ensure_ascii=False)+'\n');out.flush()
        if n%100==0 or n==len(todo):print('Sample',n,'/',len(todo),flush=True)
