"""
STRICT NAME VALIDATOR + TOP RESEARCHERS EXTRACTION
===================================================
Extract ONLY valid researchers with h-index data
"""
import json
import re

# Load enriched data
with open('data/consortium/georgia_ENRICHED.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# STRICT name validation
def is_real_person_name(name):
    """Very strict check - must look like a real person's name"""
    if not name:
        return False
    
    # Must have at least 2 space-separated parts
    parts = name.split()
    if len(parts) < 2:
        return False
    
    # Each part must be mostly alphabetic
    for part in parts:
        clean = re.sub(r'[,.\-\']', '', part)
        if not clean.isalpha():
            return False
    
    # Must not start with common garbage words
    garbage_starts = [
        'professor', 'director', 'chair', 'dean', 'associate', 'assistant',
        'research', 'academic', 'faculty', 'staff', 'student', 'graduate',
        'undergraduate', 'phd', 'postdoc', 'ece', 'bme', 'me', 'cs', 'mse',
        'department', 'college', 'school', 'center', 'institute', 'program',
        'previous', 'next', 'page', 'home', 'about', 'contact', 'email',
        'office', 'building', 'room', 'floor', 'campus', 'north', 'south',
        'georgia', 'tech', 'emory', 'gsu', 'uga', 'university', 'state',
        'news', 'events', 'calendar', 'careers', 'giving', 'support',
        'emergency', 'safety', 'privacy', 'legal', 'human', 'title',
        'education', 'training', 'clinical', 'medical', 'health',
        'filter', 'current', 'last', 'menu', 'skip', 'search',
    ]
    
    first_word = parts[0].lower()
    if first_word in garbage_starts:
        return False
    
    # Must not contain certain words anywhere
    garbage_contains = [
        'page', 'menu', 'navigation', 'footer', 'header', 'sidebar',
        'directory', 'listing', 'employment', 'opportunity', 'resource',
        'curriculum', 'degree', 'program', 'course', 'class', 'seminar',
    ]
    name_lower = name.lower()
    for word in garbage_contains:
        if word in name_lower:
            return False
    
    # Name shouldn't be too short or too long
    if len(name) < 5 or len(name) > 50:
        return False
    
    return True


# Extract only valid researchers with h-index
valid_researchers = []
for f in data['faculty']:
    if f.get('h_index', 0) > 0:
        name = f.get('name', '')
        # Some names have credentials attached - clean them
        name = re.sub(r',?\s*(PhD|MD|DO|MS|MPH|MBA|DrPH|BSN|RN)\.?', '', name)
        name = name.strip()
        
        if is_real_person_name(name):
            f['name_clean'] = name
            valid_researchers.append(f)

# Sort by h-index
valid_researchers.sort(key=lambda x: -x.get('h_index', 0))

print('=' * 70)
print('VALID RESEARCHERS WITH h-INDEX')
print('=' * 70)
print(f'Total found: {len(valid_researchers)}')
print(f'Total citations: {sum(r.get("citations_count", 0) for r in valid_researchers):,}')

print('\nTOP 25 BY h-INDEX:')
print('-' * 70)
for i, r in enumerate(valid_researchers[:25], 1):
    name = r.get('name_clean', r.get('name', ''))[:35]
    inst = r.get('institution', '')[:20]
    h = r.get('h_index', 0)
    c = r.get('citations_count', 0)
    print(f'{i:2}. h={h:3} c={c:>7,} | {name:<35} | {inst}')

# Save clean version
output = {
    'timestamp': data['timestamp'],
    'consortium': 'Georgia Research Consortium - VALIDATED',
    'version': '6.0',
    'total_researchers': len(valid_researchers),
    'total_citations': sum(r.get('citations_count', 0) for r in valid_researchers),
    'researchers': valid_researchers
}

outfile = 'data/consortium/georgia_VALIDATED.json'
with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f'\nSaved to: {outfile}')
