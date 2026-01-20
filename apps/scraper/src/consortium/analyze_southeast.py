"""Analyze the Southeast R1/R2 dataset"""
import json

with open('data/consortium/southeast_r1r2_20260114_041911.json', encoding='utf-8') as f:
    d = json.load(f)

print("=" * 70)
print("SOUTHEAST R1/R2 RESEARCH CONSORTIUM - DATA ANALYSIS")
print("=" * 70)
print()
print(f"Total Researchers: {d['total_researchers']:,}")
print(f"Total Citations:   {d['total_citations']:,}")
print()

print("BY STATE:")
print("-" * 50)
for state, stats in sorted(d['by_state'].items(), key=lambda x: -x[1]['count']):
    schools = ', '.join(stats.get('schools', []))
    print(f"  {state}: {stats['count']:>6,} researchers | {stats['citations']:>12,} citations")
    print(f"      Schools: {schools}")

print()
print("TOP 25 RESEARCHERS BY h-INDEX:")
print("-" * 70)
for i, r in enumerate(d['researchers'][:25], 1):
    name = r.get('name', 'Unknown')[:32]
    inst = r.get('institution', '')[:18]
    h = r.get('h_index', 0)
    c = r.get('citations', 0)
    field = r.get('field', '')[:25]
    print(f"{i:2}. h={h:3} c={c:>9,} | {name:<32} | {inst:<18} | {field}")

print()
print("FIELDS PER RESEARCHER:")
print("-" * 50)
sample = d['researchers'][0]
for k, v in sample.items():
    print(f"  {k}: {type(v).__name__} (e.g. {str(v)[:50]})")

# Count by institution
print()
print("TOP 15 INSTITUTIONS BY RESEARCHER COUNT:")
print("-" * 50)
inst_counts = {}
for r in d['researchers']:
    inst = r.get('institution', 'Unknown')
    inst_counts[inst] = inst_counts.get(inst, 0) + 1

for inst, count in sorted(inst_counts.items(), key=lambda x: -x[1])[:15]:
    print(f"  {inst[:40]:<40} {count:>6,}")

# BCI/Neuro researchers
print()
print("BCI/NEUROSCIENCE RESEARCHERS (by field):")
print("-" * 50)
bci_keywords = ['neuro', 'brain', 'cognit', 'neural', 'bci', 'eeg', 'fmri', 'psychiatr', 'psycholog']
bci_researchers = []
for r in d['researchers']:
    field = (r.get('field', '') + ' ' + r.get('subfield', '')).lower()
    if any(kw in field for kw in bci_keywords):
        bci_researchers.append(r)

print(f"Found {len(bci_researchers)} researchers in neuro/BCI/psychology fields")
print()
print("TOP 20 NEURO/BCI RESEARCHERS:")
for i, r in enumerate(sorted(bci_researchers, key=lambda x: -x.get('h_index', 0))[:20], 1):
    name = r.get('name', 'Unknown')[:28]
    inst = r.get('institution', '')[:15]
    h = r.get('h_index', 0)
    c = r.get('citations', 0)
    field = r.get('field', '')[:25]
    print(f"{i:2}. h={h:3} c={c:>8,} | {name:<28} | {inst:<15} | {field}")
