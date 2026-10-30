"""Retail-linked cards must retain complete, explicitly marked price coverage."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent.parent
d = json.loads((root / '_site/data/verified.json').read_text(encoding='utf8'))
assert all(r[0] in d['price_levels'] for r in d['records'] if r[2])
# Actual shop observations can replace estimates; retain the evidence flag,
# rather than freezing the number of estimates at one historical snapshot.
assert d['price_levels']['dx-66ca665389'].get('market_estimate') is True
for rid in ['0bfedfa5c6', 'av-1008759', 'eb88569786', 'edba5ca165']:
    assert not d['price_levels'][rid].get('market_estimate', False), rid
assert d['price_levels']['dx-66ca665389']['scale'] == 'vodka'
print('All retail cards priced;', sum(b.get('market_estimate', False) for b in d['price_levels'].values()), 'market estimates explicitly marked')
