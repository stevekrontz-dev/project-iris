"""
LIVE GRANT OPPORTUNITIES SCRAPER
================================
Pulls real grants from Grants.gov API (no auth required)
Filters for research/science/neuroscience opportunities
"""
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta

OUTPUT_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\grants')

GRANTS_GOV_SEARCH = 'https://api.grants.gov/v1/api/search2'
GRANTS_GOV_DETAIL = 'https://api.grants.gov/v1/api/fetchOpportunity'

# Research-relevant keywords
SEARCH_KEYWORDS = [
    'neuroscience',
    'brain',
    'neural',
    'brain computer interface',
    'artificial intelligence',
    'machine learning',
    'biomedical engineering',
    'cognitive science',
    'rehabilitation',
    'assistive technology',
    'ALS',
    'neurodegenerative',
    'mental health',
]

# Relevant agencies
RELEVANT_AGENCIES = ['HHS', 'NSF', 'DOD', 'DOE', 'ED', 'NASA']


async def search_grants(session: aiohttp.ClientSession, keyword: str) -> list:
    """Search Grants.gov for opportunities"""
    try:
        payload = {
            'keyword': keyword,
            'oppStatuses': 'posted|forecasted',  # Open or upcoming
            'rows': 50,
        }
        
        async with session.post(
            GRANTS_GOV_SEARCH,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('oppHits', [])
            else:
                print(f'  Error {resp.status} for "{keyword}"')
                return []
    except Exception as e:
        print(f'  Exception for "{keyword}": {e}')
        return []


async def fetch_opportunity_detail(session: aiohttp.ClientSession, opp_id: str) -> dict:
    """Fetch full details for an opportunity"""
    try:
        payload = {'oppId': opp_id}
        
        async with session.post(
            GRANTS_GOV_DETAIL,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception as e:
        pass
    return {}


def parse_opportunity(hit: dict) -> dict:
    """Parse a grant opportunity from search results"""
    # Extract deadline
    close_date = hit.get('closeDate')
    if close_date:
        try:
            deadline = datetime.strptime(close_date, '%m/%d/%Y').strftime('%B %d, %Y')
        except:
            deadline = close_date
    else:
        deadline = 'Rolling/TBD'
    
    return {
        'source': hit.get('agencyCode', 'Federal'),
        'id': hit.get('id') or hit.get('number', ''),
        'number': hit.get('number', ''),
        'title': hit.get('title', ''),
        'agency': hit.get('agency', hit.get('agencyCode', '')),
        'agency_code': hit.get('agencyCode', ''),
        'status': hit.get('oppStatus', ''),
        'deadline': deadline,
        'close_date': close_date,
        'open_date': hit.get('openDate'),
        'description': hit.get('synopsis', '')[:500] if hit.get('synopsis') else '',
        'url': f"https://www.grants.gov/search-results-detail/{hit.get('id')}" if hit.get('id') else '',
        'award_ceiling': hit.get('awardCeiling'),
        'award_floor': hit.get('awardFloor'),
        'cfda': hit.get('cfdaNumber'),
        'keywords': [],  # Will be populated based on search
    }


async def main():
    print('=' * 70)
    print('LIVE GRANTS.GOV SCRAPER')
    print('=' * 70)
    print(f'Started: {datetime.now().isoformat()}')
    print(f'Keywords: {len(SEARCH_KEYWORDS)}')
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_opportunities = {}  # Dedupe by ID
    
    async with aiohttp.ClientSession() as session:
        for keyword in SEARCH_KEYWORDS:
            print(f'Searching: "{keyword}"...')
            hits = await search_grants(session, keyword)
            print(f'  Found: {len(hits)} opportunities')
            
            for hit in hits:
                opp = parse_opportunity(hit)
                opp_id = opp['id'] or opp['number']
                
                if opp_id:
                    if opp_id in all_opportunities:
                        # Add keyword to existing
                        if keyword not in all_opportunities[opp_id]['keywords']:
                            all_opportunities[opp_id]['keywords'].append(keyword)
                    else:
                        opp['keywords'] = [keyword]
                        all_opportunities[opp_id] = opp
            
            await asyncio.sleep(0.5)  # Rate limit
    
    # Convert to list
    opportunities = list(all_opportunities.values())
    
    # Sort by deadline (soonest first, with TBD at end)
    def sort_key(o):
        if o['close_date']:
            try:
                return datetime.strptime(o['close_date'], '%m/%d/%Y')
            except:
                pass
        return datetime(2099, 12, 31)
    
    opportunities.sort(key=sort_key)
    
    # Filter for upcoming (not past deadline)
    today = datetime.now()
    upcoming = []
    for o in opportunities:
        if o['close_date']:
            try:
                close = datetime.strptime(o['close_date'], '%m/%d/%Y')
                if close >= today:
                    upcoming.append(o)
            except:
                upcoming.append(o)
        else:
            upcoming.append(o)  # Keep TBD/rolling
    
    print()
    print(f'Total unique opportunities: {len(opportunities)}')
    print(f'Upcoming (not expired): {len(upcoming)}')
    
    # Save
    output_file = OUTPUT_DIR / 'grant_opportunities.json'
    output_data = {
        'updated': datetime.now().isoformat(),
        'source': 'Grants.gov API',
        'count': len(upcoming),
        'search_keywords': SEARCH_KEYWORDS,
        'opportunities': upcoming
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f'\nSaved: {output_file}')
    
    # Summary by agency
    by_agency = {}
    for o in upcoming:
        agency = o['agency_code'] or o['source']
        by_agency[agency] = by_agency.get(agency, 0) + 1
    
    print('\nBy Agency:')
    for agency, count in sorted(by_agency.items(), key=lambda x: -x[1])[:10]:
        print(f'  {agency}: {count}')
    
    # Show first few
    print('\nSample Opportunities:')
    for o in upcoming[:5]:
        print(f'  [{o["source"]}] {o["title"][:60]}...')
        print(f'    Deadline: {o["deadline"]}')
        print(f'    Keywords: {", ".join(o["keywords"][:3])}')
        print()


if __name__ == '__main__':
    asyncio.run(main())
