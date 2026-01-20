"""
OPENALEX SOUTHEAST R1/R2 MEGA SCRAPER
=====================================
All R1/R2 universities within 500 miles of Atlanta
Including KSU and expanding outward
"""
import asyncio
import aiohttp
import json
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

OPENALEX_API = 'https://api.openalex.org'

# R1/R2 Universities within ~500 miles of Atlanta
# Organized by distance from Atlanta
INSTITUTIONS = [
    # GEORGIA (Core)
    {'name': 'Georgia Institute of Technology', 'id': 'I130701444', 'short': 'GT', 'state': 'GA'},
    {'name': 'Emory University', 'id': 'I95457486', 'short': 'Emory', 'state': 'GA'},
    {'name': 'Georgia State University', 'id': 'I181565077', 'short': 'GSU', 'state': 'GA'},
    {'name': 'University of Georgia', 'id': 'I165733156', 'short': 'UGA', 'state': 'GA'},
    {'name': 'Kennesaw State University', 'id': 'I172980758', 'short': 'KSU', 'state': 'GA'},
    {'name': 'Georgia Southern University', 'id': 'I165169599', 'short': 'GASouth', 'state': 'GA'},
    {'name': 'Augusta University', 'id': 'I4210158657', 'short': 'Augusta', 'state': 'GA'},
    {'name': 'Mercer University', 'id': 'I110815073', 'short': 'Mercer', 'state': 'GA'},
    
    # FLORIDA (R1s within range)
    {'name': 'University of Florida', 'id': 'I33213144', 'short': 'UF', 'state': 'FL'},
    {'name': 'Florida State University', 'id': 'I4210158401', 'short': 'FSU', 'state': 'FL'},
    {'name': 'University of South Florida', 'id': 'I184775466', 'short': 'USF', 'state': 'FL'},
    {'name': 'University of Central Florida', 'id': 'I100733427', 'short': 'UCF', 'state': 'FL'},
    
    # NORTH CAROLINA
    {'name': 'Duke University', 'id': 'I170897317', 'short': 'Duke', 'state': 'NC'},
    {'name': 'University of North Carolina at Chapel Hill', 'id': 'I114027177', 'short': 'UNC', 'state': 'NC'},
    {'name': 'North Carolina State University', 'id': 'I137902535', 'short': 'NCSU', 'state': 'NC'},
    {'name': 'Wake Forest University', 'id': 'I193662353', 'short': 'WakeForest', 'state': 'NC'},
    {'name': 'University of North Carolina at Charlotte', 'id': 'I153012026', 'short': 'UNCC', 'state': 'NC'},
    
    # SOUTH CAROLINA
    {'name': 'University of South Carolina', 'id': 'I204641592', 'short': 'USC', 'state': 'SC'},
    {'name': 'Clemson University', 'id': 'I8078737', 'short': 'Clemson', 'state': 'SC'},
    {'name': 'Medical University of South Carolina', 'id': 'I4210108100', 'short': 'MUSC', 'state': 'SC'},
    
    # TENNESSEE
    {'name': 'Vanderbilt University', 'id': 'I200719446', 'short': 'Vandy', 'state': 'TN'},
    {'name': 'University of Tennessee', 'id': 'I29351846', 'short': 'UTK', 'state': 'TN'},
    
    # ALABAMA
    {'name': 'University of Alabama at Birmingham', 'id': 'I32389192', 'short': 'UAB', 'state': 'AL'},
    {'name': 'University of Alabama', 'id': 'I4210088090', 'short': 'UA', 'state': 'AL'},
    {'name': 'Auburn University', 'id': 'I82497590', 'short': 'Auburn', 'state': 'AL'},
    
    # VIRGINIA (edge of range)
    {'name': 'Virginia Tech', 'id': 'I859038795', 'short': 'VT', 'state': 'VA'},
    {'name': 'University of Virginia', 'id': 'I51556381', 'short': 'UVA', 'state': 'VA'},
    
    # KENTUCKY
    {'name': 'University of Kentucky', 'id': 'I4210113988', 'short': 'UK', 'state': 'KY'},
    {'name': 'University of Louisville', 'id': 'I4210164101', 'short': 'UofL', 'state': 'KY'},
]


async def fetch_page(session, inst_id, cursor='*'):
    params = {
        'filter': f'last_known_institutions.id:{inst_id}',
        'per_page': 200,
        'cursor': cursor,
        'select': 'id,display_name,orcid,works_count,cited_by_count,summary_stats,topics'
    }
    try:
        async with session.get(f'{OPENALEX_API}/authors', params=params,
                              timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                return [], None
            data = await resp.json()
            return data.get('results', []), data.get('meta', {}).get('next_cursor')
    except:
        return [], None


def process(author, inst_name):
    s = author.get('summary_stats', {})
    t = author.get('topics', [])
    return {
        'name': author.get('display_name', ''),
        'openalex_id': author.get('id', ''),
        'orcid': author.get('orcid'),
        'institution': inst_name,
        'h_index': s.get('h_index', 0),
        'i10_index': s.get('i10_index', 0),
        'citations': author.get('cited_by_count', 0),
        'works': author.get('works_count', 0),
        'field': t[0].get('display_name', '') if t else '',
    }


async def scrape_inst(session, inst, max_pages=75):
    authors = []
    cursor = '*'
    page = 0
    while cursor and page < max_pages:
        page += 1
        results, cursor = await fetch_page(session, inst['id'], cursor)
        if not results:
            break
        for a in results:
            p = process(a, inst['name'])
            if p['h_index'] > 0:
                authors.append(p)
        if page % 10 == 0:
            print(f'    p{page}: {len(authors)}', end=' ', flush=True)
        await asyncio.sleep(0.05)
    return authors


async def main():
    print('=' * 70)
    print('SOUTHEAST R1/R2 MEGA SCRAPER - 500 MILE RADIUS')
    print('=' * 70)
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Institutions: {len(INSTITUTIONS)}')
    print()
    
    all_researchers = []
    stats = {}
    
    async with aiohttp.ClientSession() as session:
        for i, inst in enumerate(INSTITUTIONS, 1):
            print(f'[{i}/{len(INSTITUTIONS)}] {inst["short"]} ({inst["state"]})...', end=' ', flush=True)
            
            researchers = await scrape_inst(session, inst)
            all_researchers.extend(researchers)
            
            cites = sum(r['citations'] for r in researchers)
            stats[inst['short']] = {'count': len(researchers), 'citations': cites, 'state': inst['state']}
            print(f'-> {len(researchers):,} researchers, {cites:,} citations')
    
    # Sort globally
    all_researchers.sort(key=lambda x: -x['h_index'])
    
    total_cites = sum(r['citations'] for r in all_researchers)
    avg_h = sum(r['h_index'] for r in all_researchers) / len(all_researchers) if all_researchers else 0
    
    print('\n' + '=' * 70)
    print('COMPLETE')
    print('=' * 70)
    print(f'Total researchers: {len(all_researchers):,}')
    print(f'Total citations: {total_cites:,}')
    print(f'Average h-index: {avg_h:.1f}')
    
    print('\nBY STATE:')
    by_state = {}
    for s, d in stats.items():
        st = d['state']
        if st not in by_state:
            by_state[st] = {'count': 0, 'citations': 0, 'schools': []}
        by_state[st]['count'] += d['count']
        by_state[st]['citations'] += d['citations']
        by_state[st]['schools'].append(s)
    
    for st in sorted(by_state.keys()):
        d = by_state[st]
        print(f'  {st}: {d["count"]:,} researchers, {d["citations"]:,} citations ({", ".join(d["schools"])})')
    
    print('\nTOP 50 RESEARCHERS:')
    for i, r in enumerate(all_researchers[:50], 1):
        print(f'{i:2}. h={r["h_index"]:3} c={r["citations"]:>9,} | {r["name"][:32]:<32} | {r["institution"][:20]}')
    
    # Save
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'source': 'OpenAlex API',
        'version': '9.0-southeast-500mi',
        'radius': '500 miles from Atlanta',
        'institutions': len(INSTITUTIONS),
        'total_researchers': len(all_researchers),
        'total_citations': total_cites,
        'by_institution': stats,
        'by_state': by_state,
        'researchers': all_researchers
    }
    
    outfile = f'data/consortium/southeast_r1r2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f'\nSaved: {outfile}')


if __name__ == '__main__':
    asyncio.run(main())
