"""
GENERATE INSTITUTION SUMMARIES
==============================
Create per-institution analytics from the mega scrape
"""
import json
from collections import defaultdict
from datetime import datetime

# Load mega data
with open('data/consortium/southeast_r1r2_20260114_040556.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

researchers = data['researchers']
print(f"Total researchers: {len(researchers):,}")

# Group by institution
by_inst = defaultdict(list)
for r in researchers:
    by_inst[r['institution']].append(r)

# Generate summaries
summaries = []
for inst, members in sorted(by_inst.items(), key=lambda x: -len(x[1])):
    if len(members) < 10:
        continue
    
    citations = sum(r['citations'] for r in members)
    avg_h = sum(r['h_index'] for r in members) / len(members)
    
    # Top 20 by h-index
    top20 = sorted(members, key=lambda x: -x['h_index'])[:20]
    
    # Top fields
    fields = defaultdict(int)
    for r in members:
        if r.get('field'):
            fields[r['field']] += 1
    top_fields = sorted(fields.items(), key=lambda x: -x[1])[:10]
    
    summary = {
        'institution': inst,
        'total_researchers': len(members),
        'total_citations': citations,
        'avg_hindex': round(avg_h, 2),
        'top_fields': [{'field': f, 'count': c} for f, c in top_fields],
        'top_researchers': [
            {'name': r['name'], 'h_index': r['h_index'], 'citations': r['citations'], 'field': r.get('field', '')}
            for r in top20
        ]
    }
    summaries.append(summary)
    
    print(f"{inst[:40]:<40} | {len(members):>6,} | {citations:>12,} | avg h={avg_h:.1f}")

# Save summaries
output = {
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'source': 'southeast_r1r2_20260114_040556.json',
    'total_institutions': len(summaries),
    'total_researchers': len(researchers),
    'summaries': summaries
}

with open('data/consortium/institution_summaries.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(summaries)} institution summaries")
