"""Combine private, attributable price observations into public relative levels."""
import argparse
import json
import re
import statistics
from collections import defaultdict, Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_price_sources import key, volume
from price_levels import category, ordinary_volume, category_limits, relative_level, reference_volume
from complete_price_levels import reviewed_observations


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--retail-root',type=Path,required=True)
    ap.add_argument('--site-dir',type=Path,help='Independent build to read; defaults to _site')
    args=ap.parse_args(); work=args.work
    root=Path(__file__).resolve().parent.parent
    site=args.site_dir or root/'_site'
    verified=json.loads((site/'data/verified.json').read_text(encoding='utf8'))
    meta=json.loads((site/'data/meta.json').read_text(encoding='utf8'))
    rows={r[0]:r for r in verified['records']}
    archive=site/'data/archive.json'
    if archive.exists():rows.update({r[0]:r for r in json.loads(archive.read_text(encoding='utf8'))['records']})
    aliases=json.loads((work/'price_card_aliases.json').read_text(encoding='utf8'))
    hold_path=work/'manual_price_holds.json'
    holds=json.loads(hold_path.read_text(encoding='utf8')) if hold_path.exists() else {}
    index=defaultdict(set)
    for rid,names in aliases.items():
        for name in names:index[key(name)].add(rid)
    offers=defaultdict(dict)
    populations=defaultdict(lambda:defaultdict(dict))
    def benchmark(o):
        if o.get('source_kind')=='product_page_reference' or o.get('availability')=='unavailable':return
        if o['network']=='Decanter' and o.get('source_kind')!='saved_catalog' and not o.get('independent_market'):return
        name=o.get('name','').casefold().replace('ё','е')
        if re.search(r'набор|бокал|gift\s*set',name):return
        kinds=sorted(meta['dicts']['categories'],key=len,reverse=True)
        kind=next((k for k in kinds if name.startswith(k.casefold().replace('ё','е')+' ')),None)
        if name.startswith(('игристое вино ','шампанское ')):kind='Вино'
        if not kind:return
        scale=category(kind,bool(re.search(r'игрист|шампан|prosecco|просекко|spumante',name)))
        if o.get('ml') and ordinary_volume(o['ml'],scale) and o.get('price',0)>0:
            samples=populations[scale][o['network']].setdefault(key(o['name']),[])
            samples.append(o)
    def accept(o, ids=None):
        if not o.get('price') or not o.get('ml') or o['price']<=0:return
        benchmark(o)
        if re.search(r'набор|бокал|gift\s*set',o['name'],re.I):return
        for rid in ids or index.get(key(o['name']),set()):
            if rid not in rows or rid in holds:continue
            row=rows[rid];scale=category(meta['dicts']['categories'][row[8]],bool(row[18]))
            if not ordinary_volume(o['ml'],scale):continue
            identity=(o['network'],o['ml'])
            prior=offers[rid].get(identity)
            if prior and o.get('source_kind')=='product_page_reference' and prior.get('source_kind')!='product_page_reference':continue
            if prior and prior['checked']>o['checked']:continue
            offers[rid][identity]=dict(o,scale=scale)
    # Re-read the actual saved prices, not old_price or undocumented middle_price.
    for line in (args.retail_root/'cache/amwine_pages.jsonl').open(encoding='utf-8-sig'):
        for p in json.loads(line).get('products',[]):
            amount=p.get('priceTag',{}).get('featuredPrice') or p.get('price')
            if not amount:continue
            try: price=float(amount); ml=round(float(p.get('props',{}).get('value',0))*1000)
            except (ValueError,TypeError):continue
            accept(dict(name=p['name'],price=price,ml=ml,network='Ароматный Мир',checked='2026-10-24',source_kind='saved_catalog'))
    old=json.loads((work/'price_levels_audit.json').read_text(encoding='utf8'))
    for rid,data in old.items():
        for o in data['observations']:accept(o,[rid])
    for live in [work/'live_price_sources.jsonl',work/'price_packaging_retry.jsonl',work/'availability_observations.jsonl']:
        if not live.exists():continue
        for line in live.open(encoding='utf8'):
            o=json.loads(line)
            if 'price' in o:accept(o)
    sample=work/'decanter_market_sample.jsonl'
    if sample.exists():
        for line in sample.open(encoding='utf8'):
            o=json.loads(line)
            if 'price' in o:benchmark(dict(o,independent_market=True))
    additional=work/'additional_saved_prices.json'
    source_records={}
    if additional.exists():
        extra=json.loads(additional.read_text(encoding='utf8'))
        for raw in extra if isinstance(extra,list) else extra.get('records',[]):
            if raw.get('price_kind') == 'from': continue
            o=dict(raw,ml=raw.get('volume_ml'),checked=raw.get('observed_at') or '',source_kind='saved_catalog')
            o['network']={'КуулКлевер':'КуулКлевер / ОТДОХНИ','JOIA':'Joia'}.get(o['network'],o['network'])
            source_records[raw['id']]=o
            accept(o)
    mappings=work/'manual_price_matches.json'
    if mappings.exists():
        for match in json.loads(mappings.read_text(encoding='utf8')):
            o=source_records[match['source_record_id']]
            if match['rid'] not in rows or o['name']!=match['source_name']:
                raise ValueError('Review stale manual price match')
            accept(dict(o,match_reason=match['reason']),[match['rid']])
    recovered=work/'recovered_user_prices.json'
    if recovered.exists():
        user_sources={}
        for raw in json.loads(recovered.read_text(encoding='utf8')):
            o=dict(raw,ml=raw['volume_ml'],checked=raw.get('date') or '',source_kind='user_catalog_paste')
            user_sources[raw['id']]=o
            accept(o)
        mappings=work/'manual_user_price_matches.json'
        if mappings.exists():
            for match in json.loads(mappings.read_text(encoding='utf8')):
                o=user_sources[match['source_record_id']]
                if match['rid'] not in rows or o['name']!=match['source_name']:
                    raise ValueError('Review stale user catalogue price match')
                accept(dict(o,match_reason=match['reason']),[match['rid']])
    # Retain reviewed gap fills when recalibrating the whole catalogue.
    for o in reviewed_observations(work/'reviewed_price_observations.json', rows, holds):
        accept(o, o['ids'])
    # Exact user-supplied amounts live outside the public repository.
    corrections=work/'user_price_corrections.json'
    if corrections.exists():
        for o in json.loads(corrections.read_text(encoding='utf8')):
            if o['id'] not in rows or rows[o['id']][3]!=o['name']:
                raise ValueError('Review stale user price correction')
            accept(o,[o['id']])
    selected={};markets=defaultdict(dict)
    for rid,group in offers.items():
        values=list(group.values());scale=values[0]['scale']
        target=reference_volume(scale)
        size=min({o['ml'] for o in values},key=lambda v:(abs(v-target),v))
        same=[o for o in values if o['ml']==size]
        # An explicit correction from the owner takes priority over retail offers.
        user=[o for o in same if o.get('source_kind')=='user_message']
        price=statistics.median(o['price'] for o in (user or same))
        selected[rid]=(scale,size,price,max(o['checked'] for o in same),same)
        # One product per category distribution, independent of duplicate cards.
        markets[scale][key(rows[rid][3])]=price
    # Benchmark one ordinary bottle size per product, chosen deterministically.
    for scale,networks in populations.items():
        for net,products in networks.items():
            for identity,samples in products.items():
                size=min({o['ml'] for o in samples},key=lambda ml:(abs(ml-reference_volume(scale)),ml))
                same=[o for o in samples if o['ml']==size]
                latest=max(o.get('checked','') for o in same)
                products[identity]=statistics.median({o['price'] for o in same if o.get('checked','')==latest})
    limits={}
    for scale,values in markets.items():
        # Give each sufficiently represented retailer one vote. Thousands of
        # premium wine listings must not drown out mainstream retail prices.
        groups=[list(p.values()) for net,p in populations[scale].items() if len(p)>=5 and net!='user']
        if groups:
            calibrated=[category_limits(group,scale) for group in groups]
            limits[scale]=tuple(statistics.median(b[i] for b in calibrated) for i in range(4))
        else: limits[scale]=category_limits(list(values.values()),scale)
        if scale=='tequila': limits[scale]=(max(2000,limits[scale][0]),*limits[scale][1:])
    tiers={};audit={}
    for rid,(scale,size,price,date,obs) in selected.items():
        tiers[rid]=dict(level=relative_level(price,limits[scale]),scale=scale,volume_ml=int(size),observed_at=date or None)
        audit[rid]=dict(selected_price=price,observations=obs)
    (root/'data/price_levels.json').write_text(json.dumps(tiers,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (work/'expanded_price_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    report={'coverage':len(tiers),'total':len(rows),'category_counts':dict(Counter(o['scale'] for o in tiers.values())),
            'calibration':{k:{'distinct_products':len(markets[k]),'boundaries':v,
                             'retailer_samples':{net:len(p) for net,p in populations[k].items()}} for k,v in limits.items()},
            'missing':[{'id':rid,'name':r[3],'category':meta['dicts']['categories'][r[8]],'networks':[meta['dicts']['networks'][i] for i in r[2]]} for rid,r in rows.items() if rid not in tiers]}
    (work/'price_coverage_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('Price coverage',len(tiers),'/',len(rows),report['category_counts'])


if __name__=='__main__':main()
