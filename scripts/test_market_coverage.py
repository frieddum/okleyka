"""Retail-linked cards must retain complete, explicitly marked price coverage."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent.parent
d = json.loads((root / '_site/data/verified.json').read_text(encoding='utf8'))
assert all(r[0] in d['price_levels'] for r in d['records'] if r[2])
assert sum(b.get('market_estimate', False) for b in d['price_levels'].values()) == 193
assert d['price_levels']['dx-66ca665389']['scale'] == 'vodka'
print('All retail cards priced; 193 market estimates explicitly marked')
