#!/usr/bin/env python3
"""
CC2: Faculty Web Page Deep Parser
Extracts lab affiliations, center leadership, detailed bios from faculty web pages
"""

import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from pathlib import Path

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\faculty_with_embeddings.json')
OUTPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\faculty_labs_enriched.json')
PROGRESS_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\labs_progress.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# Patterns to find leadership roles
LEADERSHIP_PATTERNS = [
    r'director\s+of\s+([^,\.\n]+)',
    r'chair\s+of\s+([^,\.\n]+)',
    r'head\s+of\s+([^,\.\n]+)',
    r'coordinator\s+of\s+([^,\.\n]+)',
    r'leads?\s+the\s+([^,\.\n]+(?:lab|center|institute|program|initiative))',
    r'founded?\s+the\s+([^,\.\n]+(?:lab|center|institute|program))',
]

# Patterns for lab/center affiliations
LAB_PATTERNS = [
    r'([A-Z][^,\.\n]*(?:Lab|Laboratory|Center|Institute|Consortium|Initiative))',
    r'member\s+of\s+([^,\.\n]+)',
    r'affiliated\s+with\s+([^,\.\n]+)',
]


def parse_faculty_page(url: str) -> dict:
    """Deep parse a faculty web page for roles and affiliations"""
    if not url:
        return {}
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(' ', strip=True).lower()
        full_text = soup.get_text(' ', strip=True)  # Keep case for lab names
        
        result = {
            'labs': [],
            'centers': [],
            'leadership_roles': [],
            'committees': [],
        }
        
        # Find leadership roles
        for pattern in LEADERSHIP_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                role = match.strip()
                if len(role) > 3 and len(role) < 100:
                    result['leadership_roles'].append(role)
        
        # Find lab/center affiliations (case-sensitive for proper names)
        for pattern in LAB_PATTERNS:
            matches = re.findall(pattern, full_text)
            for match in matches:
                name = match.strip()
                if len(name) > 3 and len(name) < 100:
                    if 'lab' in name.lower():
                        result['labs'].append(name)
                    elif any(x in name.lower() for x in ['center', 'institute', 'consortium']):
                        result['centers'].append(name)
        
        # Dedupe
        result['labs'] = list(set(result['labs']))[:10]
        result['centers'] = list(set(result['centers']))[:10]
        result['leadership_roles'] = list(set(result['leadership_roles']))[:10]
        
        # Check for specific keywords that indicate leadership
        result['mentions_directing'] = 'direct' in text and ('lab' in text or 'center' in text)
        result['mentions_founding'] = 'found' in text and ('lab' in text or 'center' in text)
        result['has_grad_students'] = 'graduate student' in text or 'ph.d. student' in text or 'doctoral student' in text
        result['has_grants'] = 'nsf' in text or 'nih' in text or 'grant' in text or 'funded' in text
        
        # Extract bio if present
        bio_section = soup.select_one('.bio, #bio, .about, .biography, [class*="bio"]')
        if bio_section:
            bio_text = bio_section.get_text(' ', strip=True)[:1000]
            result['bio_extracted'] = bio_text
        
        return result
        
    except Exception as e:
        return {'error': str(e)}


def main():
    print("=== CC2: Faculty Page Deep Parser ===\n")
    
    # Load faculty
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        faculty = json.load(f)
    
    # Filter to those with profile URLs
    with_urls = [(i, f) for i, f in enumerate(faculty) if f.get('profile_url')]
    print(f"Loaded {len(faculty)} faculty, {len(with_urls)} have profile URLs")
    
    # Check progress
    start_idx = 0
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_idx = progress.get('last_index', 0)
            if start_idx > 0:
                print(f"Resuming from index {start_idx}")
    
    enriched = 0
    with_labs = 0
    with_leadership = 0
    
    for j, (i, f) in enumerate(with_urls):
        if j < start_idx:
            continue
            
        name = f.get('name', '')
        url = f.get('profile_url', '')
        
        print(f"[{j+1}/{len(with_urls)}] {name}...", end=' ')
        
        # Parse page
        info = parse_faculty_page(url)
        
        if info and 'error' not in info:
            # Merge info
            if info.get('labs'):
                faculty[i]['labs'] = info['labs']
                with_labs += 1
            if info.get('centers'):
                faculty[i]['centers'] = info['centers']
            if info.get('leadership_roles'):
                faculty[i]['leadership_roles'] = info['leadership_roles']
                with_leadership += 1
            if info.get('bio_extracted'):
                faculty[i]['bio'] = info['bio_extracted']
            
            faculty[i]['mentions_directing'] = info.get('mentions_directing', False)
            faculty[i]['has_grad_students'] = info.get('has_grad_students', False)
            faculty[i]['has_grants'] = info.get('has_grants', False)
            
            enriched += 1
            
            labs_str = f"labs:{len(info.get('labs', []))}" if info.get('labs') else ""
            lead_str = f"lead:{len(info.get('leadership_roles', []))}" if info.get('leadership_roles') else ""
            print(f"OK {labs_str} {lead_str}".strip() or "OK")
        else:
            print(f"X - {info.get('error', 'failed')[:30]}")
        
        # Save progress every 50
        if (j + 1) % 50 == 0:
            with open(PROGRESS_FILE, 'w') as pf:
                json.dump({'last_index': j + 1, 'enriched': enriched}, pf)
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as of:
                json.dump(faculty, of, indent=2)
            print(f"  [Checkpoint: {enriched} parsed, {with_labs} with labs, {with_leadership} with leadership]")
        
        # Rate limit
        time.sleep(random.uniform(0.3, 0.8))
    
    # Final save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(faculty, f, indent=2)
    
    print(f"\n=== Complete ===")
    print(f"Pages parsed: {enriched}")
    print(f"With labs: {with_labs}")
    print(f"With leadership roles: {with_leadership}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
