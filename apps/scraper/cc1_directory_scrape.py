#!/usr/bin/env python3
"""
CC1: KSU Directory Scraper
Enriches faculty with official titles, departments, colleges from directory.kennesaw.edu
"""

import json
import requests
import time
import random
from pathlib import Path

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\faculty_with_embeddings.json')
OUTPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\faculty_directory_enriched.json')
PROGRESS_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\directory_progress.json')

DIRECTORY_API_URL = "https://directory.kennesaw.edu/Search/People"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

def search_directory(name: str, email: str = None) -> dict:
    """Search KSU directory for a person"""
    try:
        # Use last name for better matching
        search_term = name.split()[-1] if name else ""
        if not search_term:
            return {}
        
        params = {'searchTerm': search_term, 'guidTerm': '-'}
        resp = requests.get(DIRECTORY_API_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        results = resp.json()
        
        if not results:
            return {}
        
        # Find best match by name
        name_lower = name.lower()
        for r in results:
            result_name = r.get('name', '').lower()
            # Check if names match (allowing for Dr. prefix, etc.)
            if name_lower in result_name or result_name.replace('dr. ', '') in name_lower:
                return {
                    'directory_name': r.get('name'),
                    'directory_title': r.get('title'),
                    'directory_department': r.get('department'),
                    'directory_location': r.get('location'),
                    'directory_maildrop': r.get('maildrop'),
                }
        
        # If no exact match, return first result if only one
        if len(results) == 1:
            r = results[0]
            return {
                'directory_name': r.get('name'),
                'directory_title': r.get('title'),
                'directory_department': r.get('department'),
                'directory_location': r.get('location'),
                'directory_maildrop': r.get('maildrop'),
            }
        
        return {}
        
    except Exception as e:
        print(f"    Error: {e}")
        return {}


def extract_leadership_from_title(title: str) -> dict:
    """Extract leadership indicators from title"""
    if not title:
        return {}
    
    title_lower = title.lower()
    
    info = {
        'is_director': 'director' in title_lower,
        'is_chair': 'chair' in title_lower,
        'is_dean': 'dean' in title_lower,
        'is_coordinator': 'coordinator' in title_lower,
        'is_head': 'head' in title_lower,
        'is_lead': 'lead' in title_lower,
    }
    
    # Calculate leadership score
    score = 0
    if info['is_dean']: score += 5
    if info['is_director']: score += 4
    if info['is_chair']: score += 3
    if info['is_head']: score += 3
    if info['is_coordinator']: score += 2
    if info['is_lead']: score += 2
    
    info['leadership_score'] = score
    
    return info


def main():
    print("=== CC1: KSU Directory Enrichment ===\n")
    
    # Load faculty
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        faculty = json.load(f)
    
    print(f"Loaded {len(faculty)} faculty members")
    
    # Check progress
    start_idx = 0
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_idx = progress.get('last_index', 0)
            if start_idx > 0:
                print(f"Resuming from index {start_idx}")
    
    enriched = 0
    errors = 0
    
    for i in range(start_idx, len(faculty)):
        f = faculty[i]
        name = f.get('name', '')
        email = f.get('email', '')
        
        print(f"[{i+1}/{len(faculty)}] {name}...", end=' ')
        
        # Search directory
        dir_info = search_directory(name, email)
        
        if dir_info:
            # Merge directory info
            for key, value in dir_info.items():
                if value:
                    f[key] = value
            
            # Extract leadership info from title
            if dir_info.get('directory_title'):
                leadership = extract_leadership_from_title(dir_info['directory_title'])
                f.update(leadership)
            
            enriched += 1
            print(f"OK - {dir_info.get('directory_title', 'found')}")
        else:
            errors += 1
            print("X - not found")
        
        # Save progress every 50
        if (i + 1) % 50 == 0:
            with open(PROGRESS_FILE, 'w') as pf:
                json.dump({'last_index': i + 1, 'enriched': enriched, 'errors': errors}, pf)
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as of:
                json.dump(faculty, of, indent=2)
            print(f"  [Checkpoint saved: {enriched} enriched, {errors} not found]")
        
        # Rate limit
        time.sleep(random.uniform(0.5, 1.5))
    
    # Final save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(faculty, f, indent=2)
    
    print(f"\n=== Complete ===")
    print(f"Enriched: {enriched}")
    print(f"Not found: {errors}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
