#!/usr/bin/env python3
"""
MEGA ENRICHMENT SWARM - LinkedIn + Social Discovery
Enriches 2,978 KSU people with LinkedIn profiles, skills, GitHub, social media

Strategy:
1. First pass: Find LinkedIn URLs via Google search (name + "kennesaw" + "linkedin")
2. Second pass: Scrape LinkedIn public profiles with VPN rotation
3. Third pass: GitHub, Twitter, other socials
"""

import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from pathlib import Path
from urllib.parse import quote_plus
import subprocess

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_full_directory.json')
OUTPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_enriched_social.json')
PROGRESS_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\social_enrichment_progress.json')

# Rotate user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
    }


def search_duckduckgo(query: str) -> list:
    """Search DuckDuckGo (doesn't block like Google)"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        resp = requests.get(url, headers=get_headers(), timeout=15)
        
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []
        
        for link in soup.select('a.result__a'):
            href = link.get('href', '')
            title = link.get_text(strip=True)
            results.append({'url': href, 'title': title})
        
        return results[:10]
    except Exception as e:
        return []


def find_linkedin_url(name: str, title: str = '') -> dict:
    """Find LinkedIn profile URL for a person"""
    # Clean name
    clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
    
    # Search query
    query = f'{clean_name} kennesaw state university linkedin'
    
    results = search_duckduckgo(query)
    
    for r in results:
        url = r.get('url', '')
        if 'linkedin.com/in/' in url:
            # Extract LinkedIn username
            match = re.search(r'linkedin\.com/in/([^/?]+)', url)
            if match:
                return {
                    'linkedin_url': f"https://www.linkedin.com/in/{match.group(1)}",
                    'linkedin_username': match.group(1),
                    'found_via': 'duckduckgo'
                }
    
    return {}


def find_github_profile(name: str, email: str = '') -> dict:
    """Find GitHub profile"""
    try:
        # Try by email username first
        if email:
            username = email.split('@')[0]
            url = f"https://api.github.com/users/{username}"
            resp = requests.get(url, headers={'Accept': 'application/vnd.github.v3+json'}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'github_url': data.get('html_url'),
                    'github_username': data.get('login'),
                    'github_repos': data.get('public_repos', 0),
                    'github_followers': data.get('followers', 0),
                    'github_bio': data.get('bio'),
                }
        
        # Search by name
        clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
        query = f'{clean_name} kennesaw'
        url = f"https://api.github.com/search/users?q={quote_plus(query)}"
        resp = requests.get(url, headers={'Accept': 'application/vnd.github.v3+json'}, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('items'):
                user = data['items'][0]
                # Get full profile
                profile_resp = requests.get(user['url'], timeout=10)
                if profile_resp.status_code == 200:
                    profile = profile_resp.json()
                    return {
                        'github_url': profile.get('html_url'),
                        'github_username': profile.get('login'),
                        'github_repos': profile.get('public_repos', 0),
                        'github_followers': profile.get('followers', 0),
                        'github_bio': profile.get('bio'),
                    }
        
        return {}
    except:
        return {}


def find_twitter_profile(name: str) -> dict:
    """Search for Twitter/X profile (limited without API)"""
    clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
    query = f'{clean_name} kennesaw twitter OR x.com'
    
    results = search_duckduckgo(query)
    
    for r in results:
        url = r.get('url', '')
        if 'twitter.com/' in url or 'x.com/' in url:
            match = re.search(r'(?:twitter|x)\.com/([^/?]+)', url)
            if match and match.group(1) not in ['search', 'hashtag', 'i', 'intent']:
                return {
                    'twitter_url': url,
                    'twitter_username': match.group(1),
                }
    
    return {}


def find_researchgate(name: str) -> dict:
    """Find ResearchGate profile"""
    clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
    query = f'{clean_name} kennesaw researchgate'
    
    results = search_duckduckgo(query)
    
    for r in results:
        url = r.get('url', '')
        if 'researchgate.net/profile/' in url:
            return {
                'researchgate_url': url,
            }
    
    return {}


def enrich_person(person: dict) -> dict:
    """Enrich a single person with social profiles"""
    name = person.get('name', '')
    email = person.get('email', '')
    title = person.get('title', '')
    
    enriched = {}
    
    # LinkedIn
    linkedin = find_linkedin_url(name, title)
    if linkedin:
        enriched.update(linkedin)
    
    time.sleep(random.uniform(1, 2))
    
    # GitHub (only for likely technical roles)
    technical_keywords = ['professor', 'lecturer', 'instructor', 'analyst', 'engineer', 
                         'developer', 'data', 'computing', 'technology', 'it ', 'software']
    if any(kw in title.lower() for kw in technical_keywords):
        github = find_github_profile(name, email)
        if github:
            enriched.update(github)
        time.sleep(random.uniform(0.5, 1))
    
    # Twitter
    twitter = find_twitter_profile(name)
    if twitter:
        enriched.update(twitter)
    
    time.sleep(random.uniform(1, 2))
    
    # ResearchGate (only for faculty/researchers)
    if person.get('category') in ['faculty', 'dean', 'chair', 'director']:
        rg = find_researchgate(name)
        if rg:
            enriched.update(rg)
    
    return enriched


def main():
    print("=" * 60)
    print("  MEGA ENRICHMENT SWARM - Social Profile Discovery")
    print("=" * 60)
    
    # Load directory
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    people = data.get('all_people', [])
    print(f"\nLoaded {len(people)} people to enrich")
    
    # Load progress
    start_idx = 0
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_idx = progress.get('last_idx', 0)
            # Update people with existing enrichment
            enriched_map = {p['name']: p for p in progress.get('people', [])}
            for i, person in enumerate(people):
                if person['name'] in enriched_map:
                    people[i].update(enriched_map[person['name']])
            print(f"Resuming from index {start_idx}")
    
    stats = {
        'linkedin': 0,
        'github': 0,
        'twitter': 0,
        'researchgate': 0,
    }
    
    print(f"\nStarting enrichment...\n")
    
    for i in range(start_idx, len(people)):
        person = people[i]
        name = person.get('name', '')
        
        print(f"[{i+1}/{len(people)}] {name[:35]:35s}", end=' ', flush=True)
        
        # Enrich
        enrichment = enrich_person(person)
        
        if enrichment:
            people[i].update(enrichment)
            
            found = []
            if enrichment.get('linkedin_url'):
                stats['linkedin'] += 1
                found.append('LI')
            if enrichment.get('github_url'):
                stats['github'] += 1
                found.append('GH')
            if enrichment.get('twitter_url'):
                stats['twitter'] += 1
                found.append('TW')
            if enrichment.get('researchgate_url'):
                stats['researchgate'] += 1
                found.append('RG')
            
            print(f"-> {', '.join(found)}" if found else "-> -")
        else:
            print("-> -")
        
        # Checkpoint every 25
        if (i + 1) % 25 == 0:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'last_idx': i + 1, 'people': people, 'stats': stats}, f)
            print(f"  [Checkpoint: LI:{stats['linkedin']} GH:{stats['github']} TW:{stats['twitter']} RG:{stats['researchgate']}]")
        
        # Rate limiting - be nice
        time.sleep(random.uniform(2, 4))
    
    # Final save
    output_data = {
        'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_people': len(people),
        'enrichment_stats': stats,
        'all_people': people,
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"  ENRICHMENT COMPLETE")
    print(f"{'=' * 60}")
    print(f"\nProfiles found:")
    print(f"  LinkedIn:     {stats['linkedin']}")
    print(f"  GitHub:       {stats['github']}")
    print(f"  Twitter/X:    {stats['twitter']}")
    print(f"  ResearchGate: {stats['researchgate']}")
    print(f"\nOutput: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
