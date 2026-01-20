"""
OPENALEX INSTITUTION SCRAPER
============================
Pull ALL faculty directly from OpenAlex by institution
This bypasses HTML scraping entirely - gets clean data with h-index
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timezone

OPENALEX_API = 'https://api.openalex.org'

# OpenAlex institution IDs for Georgia universities
INSTITUTIONS = [
    {
        'name': 'Georgia Institute of Technology',
        'openalex_id': 'I64462195',
        'short': 'GT'
    },
    {
        'name': 'Emory University', 
        'openalex_id': 'I95457486',
        'short': 'Emory'
    },
    {
        'name': 'Georgia State University',
        'openalex_id': 'I29425537',
        'short': 'GSU'
    },
    {
        'name': 'University of Georgia',
        'openalex_id': 'I168971618',
        'short': 'UGA'
    },
]


async def fetch_institution_authors(session, inst: dict, cursor: str = '*') -> tuple:
    """Fetch authors from an institution using OpenAlex API"""
    params = {
        'filter': f'last_known_institutions.id:{inst["openalex_id"]}',
        'per_page': 200,
        'cursor': cursor,
        'select': 'id,display_name,orcid,works_count,cited_by_count,summary_stats,last_known_institutions,topics'
    }
    
    url = f'{OPENALEX_API}/authors'
    
    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        if resp.status != 200:
            return [], None
        
        data = await resp.json()
        results = data.get('results', [])
        next_cursor = data.get('meta', {}).get('next_cursor')
        
        return results, next_cursor


def process_author(author: dict, inst_name: str) -> dict:
    """Process OpenAlex author into our format"""
    summary = author.get('summary_stats', {})
    
    # Get primary topic/field
    topics = author.get('topics', [])
    primary_field = topics[0].get('display_name', '') if topics else ''
    
    return {
        'name': author.get('display_name', ''),
        'openalex_id': author.get('id', ''),
        'orcid': author.get('orcid', ''),
        'institution': inst_name,
        'h_index': summary.get('h_index', 0),
        'i10_index': summary.get('i10_index', 0),
        'citations': author.get('cited_by_count', 0),
        'works_count': author.get('works_count', 0),
        'primary_field': primary_field,
    }


async def scrape_institution(session, inst: dict, max_pages: int = 50) -> list:
    """Scrape all authors from an institution"""
    all_authors = []
    cursor = '*'
    page = 0
    
    while cursor and page < max_pages:
        page += 1
        print(f'  Page {page}...', end=' ', flush=True)
        
        authors, cursor = await fetch_institution_authors(session, inst, cursor)
        
        if not authors:
            print('done')
            break
        
        for author in authors:
            processed = process_author(author, inst['name'])
            if processed['h_index'] > 0:  # Only keep researchers with h-index
                all_authors.append(processed)
        
        print(f'{len(authors)} fetched, {len(all_authors)} with h-index')
        await asyncio.sleep(0.1)  # Rate limit
    
    return all_authors


async def main():
    print('=' * 70)
    print('OPENALEX INSTITUTION SCRAPER')
    print('=' * 70)
    print(f'Started: {datetime.now(timezone.utc).isoformat()}')
    print()
    
    all_faculty = []
    stats = {}
    
    async with aiohttp.ClientSession() as session:
        for inst in INSTITUTIONS:
            print(f'\n[{inst["short"]}] {inst["name"]}')
            print('-' * 50)
            
            authors = await scrape_institution(session, inst)
            all_faculty.extend(authors)
            stats[inst['name']] = len(authors)
            
            print(f'Total for {inst["short"]}: {len(authors)} researchers with h-index')
    
    # Sort by h-index
    all_faculty.sort(key=lambda x: -x['h_index'])
    
    # Calculate stats
    total_citations = sum(f['citations'] for f in all_faculty)
    avg_hindex = sum(f['h_index'] for f in all_faculty) / len(all_faculty) if all_faculty else 0
    
    print('\n' + '=' * 70)
    print('OPENALEX SCRAPE COMPLETE')
    print('=' * 70)
    print(f'Total researchers with h-index: {len(all_faculty)}')
    print(f'Total citations: {total_citations:,}')
    print(f'Average h-index: {avg_hindex:.1f}')
    print()
    print('By institution:')
    for inst, count in stats.items():
        print(f'  {inst}: {count}')
    
    print('\nTOP 20 RESEARCHERS:')
    for i, f in enumerate(all_faculty[:20], 1):
        print(f'{i:2}. h={f["h_index"]:3} c={f["citations"]:>8,} | {f["name"][:40]} | {f["institution"][:15]}')
    
    # Save
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'source': 'OpenAlex API',
        'version': '7.0-openalex-direct',
        'total_researchers': len(all_faculty),
        'total_citations': total_citations,
        'avg_hindex': round(avg_hindex, 2),
        'by_institution': stats,
        'researchers': all_faculty
    }
    
    outfile = f'data/consortium/openalex_georgia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f'\nSaved to: {outfile}')


if __name__ == '__main__':
    asyncio.run(main())
