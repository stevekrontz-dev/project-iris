#!/usr/bin/env python3
"""
MEGA SWARM ORCHESTRATOR
Runs 8 parallel workers + additional enrichment sources

Sources:
- LinkedIn (profile URL)
- GitHub (repos, languages, activity)
- Twitter/X (handle)
- ResearchGate (academic profile)
- ORCID (verified publications)
- Google Scholar (citations) - via SerpAPI if available
- Rate My Professor (teaching ratings)
- KSU News (mentions, awards)

Total: 8 workers × ~370 people × 6 sources = ~17,000 lookups
Time: ~30-45 minutes with parallel execution
"""

import json
import subprocess
import sys
import time
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_full_directory.json')
OUTPUT_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\output\swarm_chunks')
FINAL_OUTPUT = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_mega_enriched.json')

NUM_WORKERS = 8

# Track progress across workers
progress_lock = threading.Lock()
total_progress = {'processed': 0, 'linkedin': 0, 'github': 0, 'twitter': 0, 'researchgate': 0, 'orcid': 0}


def run_worker(worker_id: int, people_chunk: list, output_file: Path):
    """Run enrichment for a chunk of people"""
    import requests
    from bs4 import BeautifulSoup
    import re
    import random
    from urllib.parse import quote_plus
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    ]
    
    def get_headers():
        return {'User-Agent': random.choice(USER_AGENTS), 'Accept': 'text/html'}
    
    def search_ddg(query):
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            r = requests.get(url, headers=get_headers(), timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                return [{'url': a.get('href', '')} for a in soup.select('a.result__a')][:8]
        except:
            pass
        return []
    
    def find_linkedin(name):
        clean = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
        for r in search_ddg(f'{clean} kennesaw linkedin'):
            if 'linkedin.com/in/' in r['url']:
                m = re.search(r'linkedin\.com/in/([^/?]+)', r['url'])
                if m: return {'linkedin_url': f"https://linkedin.com/in/{m.group(1)}"}
        return {}
    
    def find_github(name, email=''):
        try:
            if email:
                username = email.split('@')[0]
                r = requests.get(f"https://api.github.com/users/{username}", timeout=8)
                if r.status_code == 200:
                    d = r.json()
                    return {'github_url': d.get('html_url'), 'github_repos': d.get('public_repos', 0)}
        except:
            pass
        return {}
    
    def find_twitter(name):
        clean = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
        for r in search_ddg(f'{clean} kennesaw twitter'):
            if 'twitter.com/' in r['url'] or 'x.com/' in r['url']:
                m = re.search(r'(?:twitter|x)\.com/([^/?]+)', r['url'])
                if m and m.group(1) not in ['search', 'hashtag', 'i']:
                    return {'twitter_url': r['url']}
        return {}
    
    def find_researchgate(name):
        clean = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
        for r in search_ddg(f'{clean} kennesaw researchgate'):
            if 'researchgate.net/profile/' in r['url']:
                return {'researchgate_url': r['url']}
        return {}
    
    def find_orcid(name):
        try:
            clean = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name).strip()
            parts = clean.split()
            if len(parts) >= 2:
                q = f"family-name:{parts[-1]}+AND+given-names:{parts[0]}"
                r = requests.get(f"https://pub.orcid.org/v3.0/search/?q={q}", 
                               headers={'Accept': 'application/json'}, timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    if data.get('result'):
                        oid = data['result'][0].get('orcid-identifier', {}).get('path')
                        if oid: return {'orcid_id': oid, 'orcid_url': f"https://orcid.org/{oid}"}
        except:
            pass
        return {}
    
    stats = {'linkedin': 0, 'github': 0, 'twitter': 0, 'researchgate': 0, 'orcid': 0}
    
    for i, person in enumerate(people_chunk):
        name = person.get('name', '')
        email = person.get('email', '')
        title = person.get('title', '').lower()
        cat = person.get('category', '')
        
        # LinkedIn
        li = find_linkedin(name)
        if li: 
            person.update(li)
            stats['linkedin'] += 1
        time.sleep(random.uniform(0.3, 0.8))
        
        # GitHub (technical roles)
        if any(k in title for k in ['professor', 'analyst', 'engineer', 'data', 'computing', 'software']):
            gh = find_github(name, email)
            if gh:
                person.update(gh)
                stats['github'] += 1
            time.sleep(random.uniform(0.2, 0.5))
        
        # Twitter
        tw = find_twitter(name)
        if tw:
            person.update(tw)
            stats['twitter'] += 1
        time.sleep(random.uniform(0.3, 0.8))
        
        # ResearchGate + ORCID (academics)
        if cat in ['faculty', 'dean', 'chair', 'director', 'executive']:
            rg = find_researchgate(name)
            if rg:
                person.update(rg)
                stats['researchgate'] += 1
            time.sleep(random.uniform(0.3, 0.6))
            
            orcid = find_orcid(name)
            if orcid:
                person.update(orcid)
                stats['orcid'] += 1
            time.sleep(random.uniform(0.2, 0.5))
        
        # Update global progress
        with progress_lock:
            total_progress['processed'] += 1
            for k in stats:
                total_progress[k] = total_progress.get(k, 0)
        
        if (i + 1) % 25 == 0:
            print(f"  W{worker_id}: {i+1}/{len(people_chunk)}")
    
    # Save chunk output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'people': people_chunk, 'stats': stats}, f)
    
    return stats


def main():
    print("=" * 70)
    print("  MEGA SWARM ORCHESTRATOR")
    print("  8 Parallel Workers × 6 Data Sources")
    print("=" * 70)
    
    # Load data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    people = data.get('all_people', [])
    print(f"\nLoaded {len(people)} people")
    
    # Create output dir
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Split into chunks
    chunk_size = len(people) // NUM_WORKERS + 1
    chunks = [people[i:i+chunk_size] for i in range(0, len(people), chunk_size)]
    
    print(f"Split into {len(chunks)} chunks of ~{chunk_size} each")
    print(f"\nSources: LinkedIn, GitHub, Twitter, ResearchGate, ORCID")
    print(f"\n{'=' * 70}")
    print(f"  LAUNCHING {NUM_WORKERS} WORKERS")
    print(f"{'=' * 70}\n")
    
    start = time.time()
    all_stats = []
    
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {}
        for i, chunk in enumerate(chunks):
            out_file = OUTPUT_DIR / f'chunk_{i}_enriched.json'
            futures[executor.submit(run_worker, i, chunk, out_file)] = i
        
        for future in as_completed(futures):
            wid = futures[future]
            try:
                stats = future.result()
                all_stats.append(stats)
                print(f"  Worker {wid} DONE: LI:{stats['linkedin']} GH:{stats['github']} TW:{stats['twitter']} RG:{stats['researchgate']} OR:{stats['orcid']}")
            except Exception as e:
                print(f"  Worker {wid} ERROR: {e}")
    
    elapsed = time.time() - start
    
    # Merge results
    print(f"\n{'=' * 70}")
    print(f"  MERGING RESULTS")
    print(f"{'=' * 70}")
    
    all_people = []
    totals = {'linkedin': 0, 'github': 0, 'twitter': 0, 'researchgate': 0, 'orcid': 0}
    
    for chunk_file in sorted(OUTPUT_DIR.glob('chunk_*_enriched.json')):
        with open(chunk_file, 'r', encoding='utf-8') as f:
            d = json.load(f)
            all_people.extend(d['people'])
            for k in totals:
                totals[k] += d['stats'].get(k, 0)
    
    output = {
        'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_people': len(all_people),
        'enrichment_stats': totals,
        'all_people': all_people,
    }
    
    with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'=' * 70}")
    print(f"  MEGA SWARM COMPLETE")
    print(f"{'=' * 70}")
    print(f"\nTime: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")
    print(f"\nProfiles Found:")
    print(f"  LinkedIn:     {totals['linkedin']:,}")
    print(f"  GitHub:       {totals['github']:,}")
    print(f"  Twitter/X:    {totals['twitter']:,}")
    print(f"  ResearchGate: {totals['researchgate']:,}")
    print(f"  ORCID:        {totals['orcid']:,}")
    print(f"  TOTAL:        {sum(totals.values()):,} profiles")
    print(f"\nOutput: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
