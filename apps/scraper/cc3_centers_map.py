#!/usr/bin/env python3
"""
CC3: KSU Research Centers Scraper
Maps all research centers/labs to their directors and members
"""

import json
import requests
from bs4 import BeautifulSoup
import re
import time
from pathlib import Path

OUTPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_centers.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# KSU Research pages to scrape
RESEARCH_URLS = [
    'https://research.kennesaw.edu/centers/index.php',
    'https://research.kennesaw.edu/institutes/index.php',
    'https://research.kennesaw.edu/labs/index.php',
]

# Known important centers/labs to ensure we capture
KNOWN_CENTERS = [
    {
        'name': 'The BrainLab',
        'url': 'https://thebrainlab.kennesaw.edu/',
        'type': 'lab',
    },
    {
        'name': 'A-PRIME (Analytics and Programming for Impactful Machine-Learning and Empirical Research)',
        'url': None,
        'type': 'center',
    },
]


def scrape_research_page(url: str) -> list:
    """Scrape a KSU research listing page for centers/labs"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        centers = []
        
        # Look for links to center pages
        for link in soup.select('a[href*="center"], a[href*="institute"], a[href*="lab"]'):
            href = link.get('href', '')
            name = link.get_text(strip=True)
            
            if name and len(name) > 3 and len(name) < 200:
                centers.append({
                    'name': name,
                    'url': href if href.startswith('http') else f"https://research.kennesaw.edu{href}",
                    'source': url,
                })
        
        # Also look for structured listings
        for item in soup.select('.center-item, .institute-item, .lab-item, .listing-item, li'):
            name_el = item.select_one('a, h3, h4, strong')
            if name_el:
                name = name_el.get_text(strip=True)
                href = name_el.get('href', '') if name_el.name == 'a' else ''
                
                if name and any(x in name.lower() for x in ['center', 'institute', 'lab', 'consortium', 'initiative']):
                    centers.append({
                        'name': name,
                        'url': href if href.startswith('http') else (f"https://research.kennesaw.edu{href}" if href else None),
                        'source': url,
                    })
        
        return centers
        
    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return []


def scrape_center_details(center: dict) -> dict:
    """Scrape a center's page for director and member info"""
    if not center.get('url'):
        return center
    
    try:
        resp = requests.get(center['url'], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(' ', strip=True)
        
        # Find director
        director_patterns = [
            r'director[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'directed\s+by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'led\s+by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        for pattern in director_patterns:
            match = re.search(pattern, text)
            if match:
                center['director'] = match.group(1)
                break
        
        # Find members/faculty list
        members = []
        for link in soup.select('a[href*="faculty"], a[href*="people"], a[href*="member"]'):
            name = link.get_text(strip=True)
            if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', name):
                members.append(name)
        
        if members:
            center['members'] = list(set(members))[:20]
        
        # Get description
        desc_el = soup.select_one('.description, .about, .overview, p')
        if desc_el:
            center['description'] = desc_el.get_text(strip=True)[:500]
        
        return center
        
    except Exception as e:
        center['error'] = str(e)
        return center


def main():
    print("=== CC3: KSU Research Centers Mapper ===\n")
    
    all_centers = []
    
    # Scrape research listing pages
    for url in RESEARCH_URLS:
        print(f"Scraping {url}...")
        centers = scrape_research_page(url)
        print(f"  Found {len(centers)} items")
        all_centers.extend(centers)
        time.sleep(1)
    
    # Add known centers
    all_centers.extend(KNOWN_CENTERS)
    
    # Dedupe by name
    seen = set()
    unique_centers = []
    for c in all_centers:
        name_key = c['name'].lower().strip()
        if name_key not in seen:
            seen.add(name_key)
            unique_centers.append(c)
    
    print(f"\nTotal unique centers/labs: {len(unique_centers)}")
    
    # Get details for each center
    print("\nFetching center details...")
    for i, center in enumerate(unique_centers):
        if center.get('url'):
            print(f"  [{i+1}/{len(unique_centers)}] {center['name'][:50]}...", end=' ')
            center = scrape_center_details(center)
            unique_centers[i] = center
            
            if center.get('director'):
                print(f"Director: {center['director']}")
            else:
                print("(no director found)")
            
            time.sleep(0.5)
    
    # Save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_centers, f, indent=2)
    
    # Summary
    with_directors = sum(1 for c in unique_centers if c.get('director'))
    with_members = sum(1 for c in unique_centers if c.get('members'))
    
    print(f"\n=== Complete ===")
    print(f"Total centers/labs: {len(unique_centers)}")
    print(f"With directors: {with_directors}")
    print(f"With member lists: {with_members}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
