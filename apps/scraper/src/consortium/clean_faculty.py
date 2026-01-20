"""
FACULTY DATA CLEANER & DEDUPLICATOR
===================================
Clean names, filter garbage, dedupe, prepare for enrichment
"""
import json
import re
from collections import defaultdict

# Load mega swarm data
with open('data/consortium/georgia_mega_20260114_033213.json', 'r', encoding='utf-8') as f:
    mega_data = json.load(f)

# Load validated consortium data (250 good records)
with open('data/consortium/georgia_consortium_FINAL.json', 'r', encoding='utf-8') as f:
    validated_data = json.load(f)

print("=" * 70)
print("FACULTY DATA CLEANER")
print("=" * 70)
print(f"Mega swarm records: {len(mega_data['faculty'])}")
print(f"Validated records: {len(validated_data['faculty'])}")

# ============================================================================
# STEP 1: Filter out obvious garbage names
# ============================================================================
GARBAGE_PATTERNS = [
    r'^(Professor|Director|Chair|Dean|Associate|Assistant|Adjunct|Senior|Junior)(\s|$)',
    r'^(College|School|Department|Office|Center|Institute|Program)',
    r'^(Research|Academic|Administrative|Faculty|Staff|Student)',
    r'^(Our|The|A|An|About|Contact|Home|Menu|Skip)',
    r'^[A-Z]{2,}$',  # All caps acronyms
    r'^\d',  # Starts with number
    r'^(Neuroscience|Psychology|Biology|Chemistry|Physics|Math|Computer)',
    r'^(Engineering|Business|Medicine|Health|Science)',
    r'(Foundation|Professorship|Fellowship|Scholarship|Award|Chair$)',
    r'^(Bernie|Marcus|McCamish|Rozelle|Vanda|Wesley)',  # Chair names
    r'^(Regents|Distinguished|Emeritus|Visiting|Affiliate)',
    r'@',  # Contains email
    r'\d{3}',  # Contains phone-like numbers
    r'^.{1,3}$',  # Too short
    r'^.{60,}$',  # Too long
]

def is_valid_name(name: str) -> bool:
    """Check if a string looks like a valid person name"""
    if not name or not name.strip():
        return False
    
    name = name.strip()
    
    # Check garbage patterns
    for pattern in GARBAGE_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return False
    
    # Must have at least 2 words or be "Last, First" format
    if ',' in name:
        parts = name.split(',')
        if len(parts) >= 2 and len(parts[0].strip()) > 1 and len(parts[1].strip()) > 1:
            return True
    
    words = name.split()
    if len(words) < 2:
        return False
    
    # At least first word should start with capital
    if not words[0][0].isupper():
        return False
    
    # Should have mostly letters
    letters = sum(c.isalpha() or c in " '-." for c in name)
    if letters / len(name) < 0.8:
        return False
    
    return True


def normalize_name(name: str) -> str:
    """Normalize name format"""
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)  # Multiple spaces
    name = re.sub(r'\n', ' ', name)   # Newlines
    
    # Convert "Last, First" to "First Last" for deduping
    if ',' in name and name.count(',') == 1:
        parts = name.split(',')
        if len(parts) == 2:
            last = parts[0].strip()
            first = parts[1].strip()
            return f"{first} {last}"
    
    return name


def get_name_key(name: str) -> str:
    """Get normalized key for deduplication"""
    normalized = normalize_name(name).lower()
    # Remove common suffixes
    normalized = re.sub(r',?\s*(jr\.?|sr\.?|ii|iii|iv|ph\.?d\.?|md|do|m\.?d\.?)$', '', normalized, flags=re.IGNORECASE)
    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    # Sort words for "John Smith" == "Smith John"
    words = sorted(normalized.split())
    return ' '.join(words)


# ============================================================================
# STEP 2: Clean mega swarm data
# ============================================================================
print("\n[STEP 1] Filtering garbage names...")

cleaned_faculty = []
garbage_count = 0

for f in mega_data['faculty']:
    name = f.get('name', '')
    if is_valid_name(name):
        f['name_normalized'] = normalize_name(name)
        f['name_key'] = get_name_key(name)
        cleaned_faculty.append(f)
    else:
        garbage_count += 1

print(f"  Valid names: {len(cleaned_faculty)}")
print(f"  Garbage filtered: {garbage_count}")


# ============================================================================
# STEP 3: Deduplicate
# ============================================================================
print("\n[STEP 2] Deduplicating...")

seen_keys = {}
deduped_faculty = []
dupe_count = 0

for f in cleaned_faculty:
    key = f['name_key']
    
    if key in seen_keys:
        # Keep the one with more data
        existing = seen_keys[key]
        existing_score = sum([
            bool(existing.get('email')),
            bool(existing.get('phone')),
            bool(existing.get('position')),
            bool(existing.get('research_interests')),
        ])
        new_score = sum([
            bool(f.get('email')),
            bool(f.get('phone')),
            bool(f.get('position')),
            bool(f.get('research_interests')),
        ])
        
        if new_score > existing_score:
            # Replace with better record
            deduped_faculty.remove(existing)
            deduped_faculty.append(f)
            seen_keys[key] = f
        
        dupe_count += 1
    else:
        seen_keys[key] = f
        deduped_faculty.append(f)

print(f"  After dedup: {len(deduped_faculty)}")
print(f"  Duplicates merged: {dupe_count}")


# ============================================================================
# STEP 4: Merge with validated data
# ============================================================================
print("\n[STEP 3] Merging with validated data...")

# Add validated records that aren't already present
validated_keys = set()
for f in validated_data['faculty']:
    f['name_normalized'] = normalize_name(f.get('name', ''))
    f['name_key'] = get_name_key(f.get('name', ''))
    validated_keys.add(f['name_key'])
    
    # Check if already in deduped
    if f['name_key'] not in seen_keys:
        deduped_faculty.append(f)
        seen_keys[f['name_key']] = f

print(f"  Added from validated: {len(validated_keys - set(f['name_key'] for f in cleaned_faculty))}")
print(f"  Final count: {len(deduped_faculty)}")


# ============================================================================
# STEP 5: Stats by institution
# ============================================================================
print("\n[STEP 4] Final statistics...")

by_institution = defaultdict(int)
with_email = 0
with_position = 0

for f in deduped_faculty:
    inst = f.get('institution', 'Unknown')
    by_institution[inst] += 1
    if f.get('email'):
        with_email += 1
    if f.get('position'):
        with_position += 1

print(f"\n  By Institution:")
for inst, count in sorted(by_institution.items(), key=lambda x: -x[1]):
    print(f"    {inst}: {count}")

print(f"\n  Data Quality:")
print(f"    With email: {with_email}")
print(f"    With position: {with_position}")


# ============================================================================
# STEP 6: Save cleaned data
# ============================================================================
output = {
    'timestamp': mega_data['timestamp'],
    'consortium': 'Georgia Research Consortium - CLEANED',
    'version': '4.1',
    'total_faculty': len(deduped_faculty),
    'by_institution': dict(by_institution),
    'data_quality': {
        'with_email': with_email,
        'with_position': with_position,
        'original_count': len(mega_data['faculty']),
        'garbage_filtered': garbage_count,
        'duplicates_merged': dupe_count,
    },
    'faculty': deduped_faculty
}

outfile = 'data/consortium/georgia_CLEANED.json'
with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"CLEANED DATA SAVED: {outfile}")
print(f"{'='*70}")
