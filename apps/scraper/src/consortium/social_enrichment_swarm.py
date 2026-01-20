"""
SOCIAL ENRICHMENT SWARM
=======================
Parallel workers to enrich 208K researchers with social profiles
Sources: LinkedIn, Twitter/X, GitHub, Google Scholar, ResearchGate
"""
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
import sys
import re
from urllib.parse import quote_plus

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\consortium\southeast_r1r2_20260114_041911.json')
OUTPUT_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\consortium\enriched')

NUM_WORKERS = 8
BATCH_SIZE = 100
RATE_LIMIT_DELAY = 0.5  # seconds between requests per worker


async def search_google_scholar(session: aiohttp.ClientSession, name: str, institution: str) -> dict:
    """Search Google Scholar for profile"""
    try:
        query = quote_plus(f'{name} {institution}')
        url = f'https://scholar.google.com/citations?view_op=search_authors&mauthors={query}'
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                text = await resp.text()
                # Look for profile link
                match = re.search(r'href="/citations\?user=([^"&]+)', text)
                if match:
                    user_id = match.group(1)
                    return {
                        'google_scholar_id': user_id,
                        'google_scholar_url': f'https://scholar.google.com/citations?user={user_id}'
                    }
    except Exception as e:
        pass
    return {}


async def search_semantic_scholar(session: aiohttp.ClientSession, name: str) -> dict:
    """Search Semantic Scholar API"""
    try:
        url = f'https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(name)}&limit=1'
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get('data'):
                    author = data['data'][0]
                    return {
                        'semantic_scholar_id': author.get('authorId'),
                        'semantic_scholar_url': f'https://www.semanticscholar.org/author/{author.get("authorId")}'
                    }
    except Exception as e:
        pass
    return {}


async def search_github(session: aiohttp.ClientSession, name: str) -> dict:
    """Search GitHub for user profile"""
    try:
        # Try name as username (hyphenated)
        username_guess = name.lower().replace(' ', '-').replace('.', '')
        url = f'https://api.github.com/users/{username_guess}'
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    'github_username': data.get('login'),
                    'github_url': data.get('html_url'),
                    'github_repos': data.get('public_repos', 0)
                }
    except Exception as e:
        pass
    return {}


async def search_dblp(session: aiohttp.ClientSession, name: str) -> dict:
    """Search DBLP for computer science publications"""
    try:
        url = f'https://dblp.org/search/author/api?q={quote_plus(name)}&format=json&h=1'
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                hits = data.get('result', {}).get('hits', {}).get('hit', [])
                if hits:
                    author = hits[0].get('info', {})
                    return {
                        'dblp_url': author.get('url'),
                        'dblp_name': author.get('author')
                    }
    except Exception as e:
        pass
    return {}


async def enrich_researcher(session: aiohttp.ClientSession, researcher: dict) -> dict:
    """Enrich a single researcher with social profiles"""
    name = researcher.get('name', '')
    institution = researcher.get('institution', '')
    
    if not name:
        return researcher
    
    # Run searches in parallel
    tasks = [
        search_semantic_scholar(session, name),
        search_dblp(session, name),
        # search_google_scholar(session, name, institution),  # Often rate-limited
        # search_github(session, name),  # Low hit rate for academics
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Merge results
    enriched = dict(researcher)
    enriched['socials'] = {}
    
    for result in results:
        if isinstance(result, dict):
            enriched['socials'].update(result)
    
    return enriched


async def worker(worker_id: int, queue: asyncio.Queue, results: list, progress: dict):
    """Worker that processes researchers from queue"""
    async with aiohttp.ClientSession(headers={'User-Agent': 'IRIS Research Bot/1.0'}) as session:
        while True:
            try:
                batch = await asyncio.wait_for(queue.get(), timeout=5.0)
            except asyncio.TimeoutError:
                break
            
            for researcher in batch:
                try:
                    enriched = await enrich_researcher(session, researcher)
                    results.append(enriched)
                    progress['done'] += 1
                    
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                except Exception as e:
                    results.append(researcher)  # Keep original on error
                    progress['errors'] += 1
            
            queue.task_done()
            
            # Progress update
            if progress['done'] % 500 == 0:
                pct = progress['done'] / progress['total'] * 100
                print(f'  W{worker_id}: {progress["done"]:,}/{progress["total"]:,} ({pct:.1f}%) - {progress["errors"]} errors')


async def main():
    print('=' * 70)
    print('SOCIAL ENRICHMENT SWARM')
    print('=' * 70)
    print(f'Started: {datetime.now().isoformat()}')
    print(f'Workers: {NUM_WORKERS}')
    print()
    
    # Load data
    print('Loading researcher data...')
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    researchers = data.get('researchers', [])
    print(f'Total researchers: {len(researchers):,}')
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create queue and load batches
    queue = asyncio.Queue()
    for i in range(0, len(researchers), BATCH_SIZE):
        batch = researchers[i:i+BATCH_SIZE]
        await queue.put(batch)
    
    print(f'Batches created: {queue.qsize()}')
    
    # Progress tracking
    progress = {'done': 0, 'errors': 0, 'total': len(researchers)}
    results = []
    
    # Start workers
    print(f'\nStarting {NUM_WORKERS} workers...')
    start_time = datetime.now()
    
    workers = [
        asyncio.create_task(worker(i, queue, results, progress))
        for i in range(NUM_WORKERS)
    ]
    
    # Progress reporter
    async def report_progress():
        while progress['done'] < progress['total']:
            await asyncio.sleep(30)
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = progress['done'] / elapsed if elapsed > 0 else 0
            eta = (progress['total'] - progress['done']) / rate / 60 if rate > 0 else 0
            print(f'Progress: {progress["done"]:,}/{progress["total"]:,} ({progress["done"]/progress["total"]*100:.1f}%) - {rate:.1f}/sec - ETA: {eta:.1f}min')
    
    reporter = asyncio.create_task(report_progress())
    
    # Wait for completion
    await asyncio.gather(*workers)
    reporter.cancel()
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Save results
    print(f'\nSaving {len(results):,} enriched researchers...')
    
    output_file = OUTPUT_DIR / f'southeast_enriched_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    output_data = {
        'metadata': {
            'source': str(INPUT_FILE),
            'enriched_at': datetime.now().isoformat(),
            'total_researchers': len(results),
            'errors': progress['errors'],
            'elapsed_seconds': elapsed,
        },
        'researchers': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False)
    
    print(f'Saved: {output_file}')
    
    # Stats
    socials_found = sum(1 for r in results if r.get('socials'))
    semantic_scholar = sum(1 for r in results if r.get('socials', {}).get('semantic_scholar_id'))
    dblp = sum(1 for r in results if r.get('socials', {}).get('dblp_url'))
    
    print('\n' + '=' * 70)
    print('ENRICHMENT COMPLETE')
    print('=' * 70)
    print(f'Total processed: {len(results):,}')
    print(f'Socials found: {socials_found:,}')
    print(f'  - Semantic Scholar: {semantic_scholar:,}')
    print(f'  - DBLP: {dblp:,}')
    print(f'Errors: {progress["errors"]:,}')
    print(f'Time: {elapsed/60:.1f} minutes')
    print(f'Rate: {len(results)/elapsed:.1f} researchers/sec')


if __name__ == '__main__':
    asyncio.run(main())
