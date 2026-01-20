"""
OPENALEX ENRICHER
=================
Add h-index, citations, publications, ORCID to faculty records
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone

OPENALEX_API = 'https://api.openalex.org'

async def search_author(session, name, institution=None):
    """Search OpenAlex for an author by name"""
    clean_name = re.sub(r'\s+', ' ', name.strip())
    clean_name = re.sub(r'[^\w\s\-\']', '', clean_name)
    
    params = {'search': clean_name, 'per_page': 5}
    
    # Add institution filter
    inst_map = {
        'Georgia Institute of Technology': 'Georgia Institute of Technology',
        'Emory University': 'Emory University', 
        'Georgia State University': 'Georgia State University',
        'University of Georgia': 'University of Georgia',
    }
    if institution and institution in inst_map:
        params['filter'] = f'last_known_institutions.display_name:{inst_map[institution]}'
    
    try:
        async with session.get(f'{OPENALEX_API}/authors', params=params, 
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = data.get('results', [])
                if results:
                    return results[0]
    except:
        pass
    return None


def extract_openalex_data(author_data):
    """Extract relevant fields from OpenAlex author data"""
    if not author_data:
        return {}
    
    summary = author_data.get('summary_stats', {})
    return {
        'openalex_id': author_data.get('id', ''),
        'orcid': author_data.get('orcid', ''),
        'h_index': summary.get('h_index', 0),
        'i10_index': summary.get('i10_index', 0),
        'citations_count': author_data.get('cited_by_count', 0),
        'works_count': author_data.get('works_count', 0),
        'openalex_name': author_data.get('display_name', ''),
    }


async def enrich_faculty(faculty_list, max_concurrent=5):
    """Enrich faculty list with OpenAlex data"""
    enriched = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def enrich_one(session, faculty, idx, total):
        async with semaphore:
            name = faculty.get('name_normalized', faculty.get('name', ''))
            institution = faculty.get('institution', '')
            
            print(f'  [{idx+1}/{total}] {name[:40]}...', end=' ', flush=True)
            
            author = await search_author(session, name, institution)
            openalex_data = extract_openalex_data(author)
            
            if openalex_data.get('h_index', 0) > 0:
                faculty.update(openalex_data)
                print(f'h={openalex_data["h_index"]}, c={openalex_data["citations_count"]}')
            else:
                print('not found')
            
            await asyncio.sleep(0.1)  # Rate limit
            return faculty
    
    async with aiohttp.ClientSession() as session:
        tasks = [enrich_one(session, f.copy(), i, len(faculty_list)) 
                 for i, f in enumerate(faculty_list)]
        enriched = await asyncio.gather(*tasks)
    
    return enriched


async def main():
    print('=' * 70)
    print('OPENALEX ENRICHER')
    print('=' * 70)
    
    # Load cleaned data
    with open('data/consortium/georgia_CLEANED.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    faculty = data['faculty']
    print(f'Faculty to enrich: {len(faculty)}')
    
    # Enrich in batches
    batch_size = 100
    all_enriched = []
    
    for i in range(0, len(faculty), batch_size):
        batch = faculty[i:i+batch_size]
        print(f'\nBatch {i//batch_size + 1}/{(len(faculty)-1)//batch_size + 1}')
        enriched = await enrich_faculty(batch)
        all_enriched.extend(enriched)
    
    # Count enriched
    with_hindex = len([f for f in all_enriched if f.get('h_index', 0) > 0])
    total_citations = sum(f.get('citations_count', 0) for f in all_enriched)
    
    print(f'\n{"="*70}')
    print('ENRICHMENT COMPLETE')
    print(f'{"="*70}')
    print(f'Faculty with h-index: {with_hindex}')
    print(f'Total citations: {total_citations:,}')
    
    # Save
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'consortium': 'Georgia Research Consortium - ENRICHED',
        'version': '5.0',
        'total_faculty': len(all_enriched),
        'enrichment_stats': {
            'with_hindex': with_hindex,
            'total_citations': total_citations,
        },
        'faculty': all_enriched
    }
    
    outfile = 'data/consortium/georgia_ENRICHED.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f'Saved to: {outfile}')


if __name__ == '__main__':
    asyncio.run(main())
