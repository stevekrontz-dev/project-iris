#!/usr/bin/env python3
"""
SWARM WORKER - Individual enrichment worker
Called by mega_swarm.py with chunk file and output file

Usage: python swarm_worker.py <input_chunk.json> <output_chunk.json>
"""

import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import sys
from pathlib import Path
from urllib.parse import quote_plus

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }


def search_duckduckgo(query: str) -> list:
    """Search DuckDuckGo"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        resp = requests.get(url, headers=get_headers(), timeout=15)
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []
        for link in soup.select('a.result__a'):
            href = link.get('href', '')
            results.append({'url': href})
        return results[:10]
    except:
        return []


def find_linkedin(name: str) -> dict:
    clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
    results = search_duckduckgo(f'{clean_name} kennesaw state linkedin')
    for r in results:
        url = r.get('url', '')
        if 'linkedin.com/in/' in url:
            match = re.search(r'linkedin\.com/in/([^/?]+)', url)
            if match:
                return {'linkedin_url': f"https://www.linkedin.com/in/{match.group(1)}"}
    return {}


def find_github(name: str, email: str = '') -> dict:
    try:
        if email:
            username = email.split('@')[0]
            resp = requests.get(f"https://api.github.com/users/{username}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'github_url': data.get('html_url'),
                    'github_repos': data.get('public_repos', 0),
                    'github_bio': data.get('bio'),
                }
        
        clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
        resp = requests.get(f"https://api.github.com/search/users?q={quote_plus(clean_name + ' kennesaw')}", timeout=10)
        if resp.status_code == 200 and resp.json().get('items'):
            user = resp.json()['items'][0]
            profile = requests.get(user['url'], timeout=10).json()
            return {
                'github_url': profile.get('html_url'),
                'github_repos': profile.get('public_repos', 0),
                'github_bio': profile.get('bio'),
            }
    except:
        pass
    return {}


def find_twitter(name: str) -> dict:
    clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
    results = search_duckduckgo(f'{clean_name} kennesaw twitter OR x.com')
    for r in results:
        url = r.get('url', '')
        if 'twitter.com/' in url or 'x.com/' in url:
            match = re.search(r'(?:twitter|x)\.com/([^/?]+)', url)
            if match and match.group(1) not in ['search', 'hashtag', 'i', 'intent']:
                return {'twitter_url': url, 'twitter_username': match.group(1)}
    return {}


def find_researchgate(name: str) -> dict:
    clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
    results = search_duckduckgo(f'{clean_name} kennesaw researchgate')
    for r in results:
        url = r.get('url', '')
        if 'researchgate.net/profile/' in url:
            return {'researchgate_url': url}
    return {}


def find_orcid(name: str) -> dict:
    """Search ORCID API"""
    try:
        clean_name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
        parts = clean_name.split()
        if len(parts) >= 2:
            query = f"family-name:{parts[-1]}+AND+given-names:{parts[0]}"
            resp = requests.get(
                f"https://pub.orcid.org/v3.0/search/?q={query}",
                headers={'Accept': 'application/json'},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('result'):
                    orcid_id = data['result'][0].get('orcid-identifier', {}).get('path')
                    if orcid_id:
                        return {'orcid_id': orcid_id, 'orcid_url': f"https://orcid.org/{orcid_id}"}
    except:
        pass
    return {}


def enrich_person(person: dict) -> dict:
    name = person.get('name', '')
    email = person.get('email', '')
    title = person.get('title', '').lower()
    category = person.get('category', '')
    
    enriched = {}
    
    # LinkedIn - everyone
    enriched.update(find_linkedin(name))
    time.sleep(random.uniform(0.5, 1.5))
    
    # GitHub - technical roles
    tech_keywords = ['professor', 'lecturer', 'analyst', 'engineer', 'developer', 
                    'data', 'computing', 'technology', 'it ', 'software', 'research']
    if any(kw in title for kw in tech_keywords):
        enriched.update(find_github(name, email))
        time.sleep(random.uniform(0.3, 0.8))
    
    # Twitter - everyone
    enriched.update(find_twitter(name))
    time.sleep(random.uniform(0.5, 1.5))
    
    # ResearchGate + ORCID - academics
    if category in ['faculty', 'dean', 'chair', 'director', 'executive']:
        enriched.update(find_researchgate(name))
        time.sleep(random.uniform(0.5, 1))
        enriched.update(find_orcid(name))
        time.sleep(random.uniform(0.3, 0.8))
    
    return enriched


def main():
    if len(sys.argv) != 3:
        print("Usage: python swarm_worker.py <input.json> <output.json>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    people = data.get('people', [])
    worker_id = input_file.stem.split('_')[-1]
    
    print(f"Worker {worker_id}: Processing {len(people)} people")
    
    stats = {'linkedin': 0, 'github': 0, 'twitter': 0, 'researchgate': 0, 'orcid': 0}
    
    for i, person in enumerate(people):
        enrichment = enrich_person(person)
        
        if enrichment:
            people[i].update(enrichment)
            if enrichment.get('linkedin_url'): stats['linkedin'] += 1
            if enrichment.get('github_url'): stats['github'] += 1
            if enrichment.get('twitter_url'): stats['twitter'] += 1
            if enrichment.get('researchgate_url'): stats['researchgate'] += 1
            if enrichment.get('orcid_id'): stats['orcid'] += 1
        
        if (i + 1) % 50 == 0:
            print(f"Worker {worker_id}: {i+1}/{len(people)} done")
        
        time.sleep(random.uniform(1, 2))
    
    output = {
        'worker_id': worker_id,
        'people': people,
        'stats': stats,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"Worker {worker_id}: Complete - LI:{stats['linkedin']} GH:{stats['github']} TW:{stats['twitter']} RG:{stats['researchgate']} OR:{stats['orcid']}")


if __name__ == "__main__":
    main()
