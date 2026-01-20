"""
GT BME Full Profile Scraper
Scrapes all 90 faculty from index pages, then visits each profile for full details
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime

THALAMUS_URL = 'http://localhost:3000'

async def get_page_names(session, page_num):
    """Get faculty names from one index page"""
    url = f'https://bme.gatech.edu/our-people/our-faculty?page={page_num}'
    
    perceive = {
        'method': 'tools/call',
        'params': {
            'name': 'thalamus_perceive',
            'arguments': {'url': url, 'maxElements': 200}
        },
        'id': f'gt-page-{page_num}'
    }
    async with session.post(THALAMUS_URL + '/mcp', json=perceive, timeout=aiohttp.ClientTimeout(total=30)) as resp:
        await resp.json()
    
    await asyncio.sleep(2)
    
    get_text = {
        'method': 'tools/call',
        'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 50000}},
        'id': f'gt-text-{page_num}'
    }
    async with session.post(THALAMUS_URL + '/mcp', json=get_text, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        result = await resp.json()
        content = result['result']['content'][0]['text']
        text_data = json.loads(content)
    
    title_words = ['professor', 'director', 'chair', 'fellow', 'associate', 'senior', 
                   'lecturer', 'scholar', 'emeritus', 'professorship', 'distinguished',
                   'academic', 'professional', 'coordinator', 'specialist', 'services',
                   'faculty', 'biomedical', 'engineering', 'results', 'page', 'previous',
                   'next', 'current', 'about', 'news', 'events', 'giving', 'students']
    
    names = []
    for block in text_data.get('content', []):
        text = block.get('text', '').strip()
        if not text or len(text) < 5 or len(text) > 50:
            continue
        text_lower = text.lower()
        if any(tw in text_lower for tw in title_words):
            continue
        if ' ' not in text:
            continue
        words = text.replace('(', ' ').replace(')', ' ').split()
        if len(words) < 2 or len(words) > 5:
            continue
        cap_words = sum(1 for w in words if w and w[0].isupper())
        if cap_words >= len(words) * 0.5:
            names.append(text)
    
    return names


async def get_profile_details(session, name):
    """Get full details from a faculty profile page"""
    # Convert name to URL slug
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', name).lower().replace(' ', '-')
    profile_url = f'https://bme.gatech.edu/bio/{slug}'
    
    perceive = {
        'method': 'tools/call',
        'params': {
            'name': 'thalamus_perceive',
            'arguments': {'url': profile_url, 'maxElements': 100}
        },
        'id': f'profile-{slug}'
    }
    
    try:
        async with session.post(THALAMUS_URL + '/mcp', json=perceive, timeout=aiohttp.ClientTimeout(total=25)) as resp:
            result = await resp.json()
            if result.get('error'):
                return None
        
        await asyncio.sleep(1.5)
        
        get_text = {
            'method': 'tools/call',
            'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 30000}},
            'id': f'profile-text-{slug}'
        }
        async with session.post(THALAMUS_URL + '/mcp', json=get_text, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            result = await resp.json()
            content = result['result']['content'][0]['text']
            profile_data = json.loads(content)
        
        # Extract details from profile
        position = ''
        email = ''
        phone = ''
        research_areas = []
        
        blocks = profile_data.get('content', [])
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            block_type = block.get('type', '')
            
            # Position is usually right after h1 name
            if block_type == 'div' and i < 5 and ('professor' in text.lower() or 'chair' in text.lower()):
                position = text
            
            # Email pattern
            if '@' in text and 'gatech.edu' in text:
                email = text
            
            # Phone pattern
            phone_match = re.search(r'\d{3}[.-]\d{3}[.-]\d{4}', text)
            if phone_match:
                phone = phone_match.group()
            
            # Research areas often in lists after "AREAS OF RESEARCH"
            if 'Biomaterials' in text or 'Cardiovascular' in text or 'Imaging' in text or 'Informatics' in text:
                research_areas.append(text)
        
        return {
            'position': position,
            'email': email,
            'phone': phone,
            'research_areas': research_areas,
            'profile_url': profile_url
        }
        
    except Exception as e:
        print(f'    Error scraping {name}: {e}')
        return None


async def main():
    print('=' * 60)
    print('GT BME FULL FACULTY SCRAPER')
    print('=' * 60)
    
    all_names = []
    faculty = []
    
    async with aiohttp.ClientSession() as session:
        # Phase 1: Get all names from all 4 pages
        print('\nPhase 1: Scraping index pages for faculty names...')
        for page in range(4):
            names = await get_page_names(session, page)
            print(f'  Page {page + 1}: {len(names)} names')
            for n in names:
                if n not in all_names:
                    all_names.append(n)
            await asyncio.sleep(1)
        
        print(f'\nTotal unique names: {len(all_names)}')
        
        # Phase 2: Visit each profile (limit to first 10 for testing)
        print('\nPhase 2: Scraping individual profiles...')
        for i, name in enumerate(all_names[:15]):  # Test first 15
            print(f'  [{i+1}/{min(15, len(all_names))}] {name}...', end=' ')
            
            details = await get_profile_details(session, name)
            
            if details:
                faculty.append({
                    'id': f'gatech-bme-{i}',
                    'name': name,
                    'institution': 'Georgia Tech BME',
                    'institution_slug': 'gatech-bme',
                    'department': 'Biomedical Engineering',
                    'position': details['position'],
                    'email': details['email'],
                    'phone': details['phone'],
                    'research_areas': details['research_areas'],
                    'profile_url': details['profile_url']
                })
                print(f'OK ({details["position"][:30]}...)' if details['position'] else 'OK')
            else:
                print('FAILED')
            
            await asyncio.sleep(0.5)
    
    # Save results
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'institution': 'Georgia Tech BME',
        'total_names_found': len(all_names),
        'profiles_scraped': len(faculty),
        'faculty': faculty
    }
    
    with open('data/consortium/gt_bme_faculty.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f'\n✓ Saved {len(faculty)} faculty profiles to gt_bme_faculty.json')
    print('\nSample profiles:')
    for f in faculty[:3]:
        print(f'  - {f["name"]}: {f["position"]}')
        if f['research_areas']:
            print(f'    Research: {", ".join(f["research_areas"][:2])}')


if __name__ == '__main__':
    asyncio.run(main())
