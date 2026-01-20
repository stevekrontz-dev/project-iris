#!/usr/bin/env python3
"""
CC4: KSU Full Directory Census
Captures EVERYONE - all employees, all departments, full hierarchy
"""

import json
import requests
import time
import string
from pathlib import Path

OUTPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_full_directory.json')
PROGRESS_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\directory_census_progress.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

DIRECTORY_API = "https://directory.kennesaw.edu/Search/People"

# Search strategy: Every letter + common name prefixes + departments
# This will find nearly everyone

# All 2-letter combinations to cast wide net
def generate_search_terms():
    terms = []
    
    # Single letters
    for c in string.ascii_lowercase:
        terms.append(c)
    
    # Common 2-letter starts
    for c1 in string.ascii_lowercase:
        for c2 in 'aeiou':  # vowels catch more names
            terms.append(c1 + c2)
    
    # Common name prefixes
    prefixes = [
        'mc', 'mac', 'de', 'van', 'von', 'la', 'le', 'st', 'san', 'del',
        'al', 'el', 'ben', 'abd', 'abu', 'ibn',
        'dr', 'mr', 'ms', 'mrs',
    ]
    terms.extend(prefixes)
    
    # Department/office searches
    depts = [
        'office', 'college', 'school', 'department', 'center', 'institute',
        'academic', 'administration', 'affairs', 'services', 'support',
        'technology', 'information', 'its', 'computing', 'software',
        'business', 'engineering', 'science', 'arts', 'health', 'education',
        'research', 'graduate', 'undergraduate', 'student', 'faculty',
        'human', 'resources', 'finance', 'budget', 'facilities', 'operations',
        'president', 'provost', 'dean', 'chair', 'director', 'coordinator',
        'manager', 'analyst', 'specialist', 'assistant', 'associate',
    ]
    terms.extend(depts)
    
    return list(set(terms))


def parse_level(title: str) -> int:
    """Extract hierarchy level from title"""
    if not title:
        return 99
    t = title.lower()
    
    if 'president' in t and 'vice' not in t and 'assistant' not in t:
        return 1
    if 'provost' in t and 'vice' not in t and 'associate' not in t and 'assistant' not in t:
        return 2
    if 'vice president' in t or 'vp ' in t:
        return 3
    if 'vice provost' in t:
        return 4
    if ('dean' in t and 'associate' not in t and 'assistant' not in t and 
        'sub' not in t and 'academic' not in t):
        return 5
    if 'associate dean' in t:
        return 6
    if 'assistant dean' in t:
        return 7
    if 'chair' in t and 'department' in t.lower():
        return 8
    if t.startswith('chair') or t.endswith('chair'):
        return 8
    if 'chief' in t and 'officer' in t:
        return 8
    if 'director' in t and 'associate' not in t and 'assistant' not in t:
        return 9
    if 'associate director' in t:
        return 10
    if 'assistant director' in t:
        return 10
    if 'manager' in t:
        return 11
    if 'coordinator' in t:
        return 12
    if 'supervisor' in t:
        return 12
    if 'professor' in t and 'assistant' not in t and 'associate' not in t:
        return 13  # Full professor
    if 'associate professor' in t:
        return 14
    if 'assistant professor' in t:
        return 15
    if 'lecturer' in t or 'instructor' in t:
        return 16
    if 'senior' in t:
        return 17
    if 'analyst' in t or 'specialist' in t:
        return 18
    if 'technician' in t or 'engineer' in t:
        return 18
    if 'administrator' in t:
        return 18
    if 'assistant' in t:
        return 19
    if 'student' in t:
        return 25  # Students at bottom
    return 20  # Default staff


def get_category(level: int, title: str) -> str:
    """Categorize by role type"""
    if level <= 4:
        return 'executive'
    if level <= 7:
        return 'dean'
    if level == 8:
        return 'chair'
    if level <= 12:
        return 'director'
    if level <= 16:
        return 'faculty'
    if level == 25:
        return 'student'
    return 'staff'


def search_directory(term: str) -> list:
    """Search KSU directory"""
    try:
        params = {'searchTerm': term, 'guidTerm': '-'}
        resp = requests.get(DIRECTORY_API, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            try:
                return resp.json()
            except:
                return []
        return []
    except Exception as e:
        return []


def main():
    print("=== CC4: KSU Full Directory Census ===\n")
    
    search_terms = generate_search_terms()
    print(f"Generated {len(search_terms)} search terms\n")
    
    # Load progress
    all_people = {}
    start_idx = 0
    
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            all_people = {p['name']: p for p in progress.get('people', [])}
            start_idx = progress.get('last_idx', 0)
            print(f"Resuming from index {start_idx}, {len(all_people)} people loaded\n")
    
    for i, term in enumerate(search_terms):
        if i < start_idx:
            continue
            
        print(f"[{i+1}/{len(search_terms)}] '{term}'...", end=' ', flush=True)
        
        results = search_directory(term)
        
        new_count = 0
        for r in results:
            name = r.get('name', '').strip()
            title = r.get('title', '').strip()
            dept = r.get('department', '').strip()
            
            if not name:
                continue
            
            # Skip if already have this person at same or higher rank
            level = parse_level(title)
            
            if name in all_people:
                if all_people[name]['level'] <= level:
                    continue
            
            # Parse college/unit
            college = ''
            unit = ''
            if dept:
                if ' - ' in dept:
                    parts = dept.split(' - ')
                    college = parts[0].strip()
                    unit = parts[-1].strip()
                else:
                    college = dept
            
            person = {
                'name': name,
                'title': title,
                'department': dept,
                'college': college,
                'unit': unit,
                'location': r.get('location', ''),
                'level': level,
                'category': get_category(level, title),
            }
            
            all_people[name] = person
            new_count += 1
        
        print(f"{len(results)} found, {new_count} new | Total: {len(all_people)}")
        
        # Checkpoint every 25
        if (i + 1) % 25 == 0:
            with open(PROGRESS_FILE, 'w') as f:
                json.dump({
                    'last_idx': i + 1,
                    'people': list(all_people.values())
                }, f)
            print(f"  [Checkpoint saved]")
        
        time.sleep(0.15)  # Rate limit
    
    # Sort by level then name
    people_list = sorted(all_people.values(), key=lambda x: (x['level'], x['name']))
    
    # Group by category
    by_category = {}
    for p in people_list:
        cat = p['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(p)
    
    # Group by college
    by_college = {}
    for p in people_list:
        col = p['college'] or 'Unknown'
        if col not in by_college:
            by_college[col] = []
        by_college[col].append(p)
    
    # Build output
    output = {
        'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_people': len(people_list),
        'by_category': {k: len(v) for k, v in by_category.items()},
        'by_college': {k: len(v) for k, v in by_college.items()},
        'categories': by_category,
        'colleges': by_college,
        'all_people': people_list,
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(people_list)} people captured")
    print(f"{'='*60}")
    print(f"\nBy category:")
    for cat, people in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {cat}: {len(people)}")
    
    print(f"\nTop colleges:")
    for col, people in sorted(by_college.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
        print(f"  {col[:50]}: {len(people)}")
    
    print(f"\nTop 15 leadership:")
    for p in people_list[:15]:
        print(f"  L{p['level']:2d} | {p['name'][:30]:30s} | {p['title'][:40]}")
    
    print(f"\nOutput: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
