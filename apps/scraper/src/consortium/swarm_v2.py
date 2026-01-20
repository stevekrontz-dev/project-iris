"""
CONSORTIUM SWARM v2 - COMPLETE ATLANTA FACULTY SCRAPER
======================================================
Validated schemas for GSU, Emory, GT BME
Uses Thalamus for directory pages, web_fetch for GT BME profiles
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone

THALAMUS_URL = 'http://localhost:3000'
BOSWELL_URL = 'http://localhost:8787'

# ============================================================================
# GT BME - Complete Faculty Profile URLs (discovered via web search)
# ============================================================================
GT_BME_PROFILES = [
    # Discovered via multiple web searches
    'https://bme.gatech.edu/bio/lakshmi-prasad-dasi',
    'https://bme.gatech.edu/bio/jaydev-p-desai',
    'https://bme.gatech.edu/bio/gabe-kwong',
    'https://bme.gatech.edu/bio/ahmet-f-coskun',
    'https://bme.gatech.edu/bio/erin-m-buckley',
    'https://bme.gatech.edu/bio/andres-j-garcia',
    'https://bme.gatech.edu/bio/zachary-danziger',
    'https://bme.gatech.edu/bio/amir-pourmorteza',
    'https://bme.gatech.edu/bio/philip-j-santangelo',
    'https://bme.gatech.edu/bio/tara-deans',
    'https://bme.gatech.edu/bio/sung-jin-park',
    'https://bme.gatech.edu/bio/vince-calhoun',
    'https://bme.gatech.edu/bio/marian-ackun-farmmer',
    'https://bme.gatech.edu/bio/vahid-serpooshan',
    'https://bme.gatech.edu/bio/alex-abramson',
    'https://bme.gatech.edu/bio/james-dahlman',
    'https://bme.gatech.edu/bio/andrew-j-feola',
    'https://bme.gatech.edu/bio/greg-myer',
    'https://bme.gatech.edu/bio/rachael-pitts-hall',
    'https://bme.gatech.edu/bio/simone-a-douglas-green',
    'https://bme.gatech.edu/bio/julia-babensee',
    'https://bme.gatech.edu/bio/edward-botchwey',
    'https://bme.gatech.edu/bio/leslie-chan',
    'https://bme.gatech.edu/bio/michael-davis',
    'https://bme.gatech.edu/bio/stanislav-emelianov',
    'https://bme.gatech.edu/bio/c-ross-ethier',
    'https://bme.gatech.edu/bio/susan-margulies',
    'https://bme.gatech.edu/bio/may-wang',
    'https://bme.gatech.edu/bio/manu-platt',
    'https://bme.gatech.edu/bio/craig-forest',
    'https://bme.gatech.edu/bio/rafael-v-davalos',
    'https://bme.gatech.edu/bio/cheng-zhu',
    'https://bme.gatech.edu/bio/hanjoong-jo',
    'https://bme.gatech.edu/bio/manoj-bhasin',
    'https://bme.gatech.edu/bio/susan-thomas',
    'https://bme.gatech.edu/bio/machelle-pardue',
    'https://bme.gatech.edu/bio/timothy-cope',
    'https://bme.gatech.edu/bio/frank-hammond',
    'https://bme.gatech.edu/bio/denis-tsygankov',
    'https://bme.gatech.edu/bio/ravi-kane',
    'https://bme.gatech.edu/bio/costas-arvanitis',
    'https://bme.gatech.edu/bio/yue-chen',
    'https://bme.gatech.edu/bio/j-brandon-dixon',
    'https://bme.gatech.edu/bio/zachary-bercu',
    'https://bme.gatech.edu/bio/michael-girard',
]


# ============================================================================
# INSTITUTION CONFIGS
# ============================================================================
INSTITUTIONS = {
    'gsu_neuro': {
        'name': 'GSU Neuroscience Institute',
        'url': 'https://neuroscience.gsu.edu/directory/',
        'method': 'thalamus_text',
        'parser': 'gsu_directory',
    },
    'emory_neuro': {
        'name': 'Emory Neurology', 
        'url': 'https://med.emory.edu/departments/neurology/faculty-and-research/index.html',
        'method': 'thalamus_text',
        'parser': 'gsu_directory',  # Same format
    },
    'gatech_bme': {
        'name': 'Georgia Tech BME',
        'url': 'https://bme.gatech.edu/our-people/our-faculty',
        'method': 'profile_urls',
        'profile_urls': GT_BME_PROFILES,
        'parser': 'gt_bme_profile',
    },
}


# ============================================================================
# PARSERS
# ============================================================================
def parse_gsu_directory(text_data: dict, inst: dict) -> list:
    """Parse GSU/Emory directory format"""
    faculty = []
    content_blocks = text_data.get('content', [])
    
    skip_patterns = ['skip to', 'copyright', 'privacy', 'profile directory', 
                     'georgia state', 'faculty & staff', 'twitter', 'facebook']
    
    i = 0
    while i < len(content_blocks):
        block = content_blocks[i]
        text = block.get('text', '').strip()
        block_type = block.get('type', '')
        
        if any(skip in text.lower() for skip in skip_patterns):
            i += 1
            continue
        
        # Name pattern: "Last, First" or "Last, First Middle"
        name_match = re.match(r'^([A-Z][a-zA-Z\'\-]+),\s+([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]*)?)$', text)
        
        if name_match and block_type == 'p':
            person = {
                'id': f"{inst['slug']}-{len(faculty)}",
                'name': text,
                'institution': inst['name'],
                'institution_slug': inst['slug'],
                'department': inst.get('department', ''),
                'position': '',
                'email': '',
                'research_interests': '',
            }
            
            # Look ahead for details
            for j in range(i+1, min(i+6, len(content_blocks))):
                next_block = content_blocks[j]
                next_text = next_block.get('text', '').strip()
                next_type = next_block.get('type', '')
                
                # Check if we hit next person
                if re.match(r'^([A-Z][a-zA-Z\'\-]+),\s+([A-Z][a-zA-Z\'\-]+)', next_text) and next_type == 'p':
                    break
                
                # Email
                if '@' in next_text:
                    person['email'] = next_text
                # Position
                elif next_type == 'div' and any(kw in next_text.lower() for kw in ['professor', 'director', 'chair']):
                    person['position'] = next_text
                # Department 
                elif next_type == 'p' and len(next_text) < 100 and any(d in next_text for d in ['Neuroscience', 'Psychology', 'Biology']):
                    person['department'] = next_text
                # Research interests
                elif next_type == 'p' and len(next_text) > 50 and '@' not in next_text:
                    person['research_interests'] = next_text[:200]
            
            faculty.append(person)
        i += 1
    
    return faculty


async def scrape_gt_bme_profile(session, url: str) -> dict:
    """Scrape a single GT BME profile page via Thalamus"""
    slug = url.split('/')[-1]
    
    perceive = {
        'method': 'tools/call',
        'params': {
            'name': 'thalamus_perceive',
            'arguments': {'url': url, 'maxElements': 100}
        },
        'id': f'gt-{slug}'
    }
    
    try:
        async with session.post(f'{THALAMUS_URL}/mcp', json=perceive, 
                                timeout=aiohttp.ClientTimeout(total=25)) as resp:
            result = await resp.json()
            if result.get('error'):
                return None
        
        await asyncio.sleep(1)
        
        get_text = {
            'method': 'tools/call',
            'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 20000}},
            'id': f'gt-text-{slug}'
        }
        async with session.post(f'{THALAMUS_URL}/mcp', json=get_text,
                                timeout=aiohttp.ClientTimeout(total=15)) as resp:
            result = await resp.json()
            content = result['result']['content'][0]['text']
            data = json.loads(content)
        
        # Parse profile
        person = {
            'id': f'gatech-bme-{slug}',
            'name': '',
            'institution': 'Georgia Tech BME',
            'institution_slug': 'gatech-bme',
            'department': 'Biomedical Engineering',
            'position': '',
            'email': '',
            'phone': '',
            'research_areas': [],
            'google_scholar': '',
            'lab': '',
            'profile_url': url,
        }
        
        blocks = data.get('content', [])
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            btype = block.get('type', '')
            
            # Name is usually h1
            if btype == 'h1' and not person['name']:
                person['name'] = text.title()
            
            # Position after name
            if i < 5 and any(kw in text.lower() for kw in ['professor', 'chair', 'director']):
                if not person['position']:
                    person['position'] = text
            
            # Research areas
            if 'Biomaterials' in text or 'Cardiovascular' in text or 'Neuroengineering' in text:
                if text not in person['research_areas']:
                    person['research_areas'].append(text)
            
            # Phone
            phone_match = re.search(r'\d{3}\.\d{3}\.\d{4}', text)
            if phone_match and not person['phone']:
                person['phone'] = phone_match.group()
            
            # Email
            email_match = re.search(r'[\w.-]+@(?:gatech|emory)\.edu', text)
            if email_match and not person['email']:
                person['email'] = email_match.group()
        
        return person
        
    except Exception as e:
        print(f'    Error: {e}')
        return None


async def scrape_institution_thalamus(session, inst: dict) -> list:
    """Scrape institution via Thalamus text extraction"""
    faculty = []
    
    perceive = {
        'method': 'tools/call',
        'params': {
            'name': 'thalamus_perceive',
            'arguments': {'url': inst['url'], 'maxElements': 300}
        },
        'id': f"perceive-{inst['slug']}"
    }
    
    try:
        async with session.post(f'{THALAMUS_URL}/mcp', json=perceive,
                                timeout=aiohttp.ClientTimeout(total=30)) as resp:
            result = await resp.json()
            if result.get('error'):
                print(f'    ✗ Perceive error: {result.get("error")}')
                return []
        
        await asyncio.sleep(2)
        
        get_text = {
            'method': 'tools/call',
            'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 100000}},
            'id': f"text-{inst['slug']}"
        }
        async with session.post(f'{THALAMUS_URL}/mcp', json=get_text,
                                timeout=aiohttp.ClientTimeout(total=20)) as resp:
            result = await resp.json()
            if result.get('error'):
                print(f'    ✗ Text error: {result.get("error")}')
                return []
            content = result['result']['content'][0]['text']
            text_data = json.loads(content)
        
        # Parse based on institution type
        if inst['parser'] == 'gsu_directory':
            faculty = parse_gsu_directory(text_data, inst)
        
        print(f'    ✓ Extracted {len(faculty)} faculty')
        
    except Exception as e:
        print(f'    ✗ Error: {e}')
    
    return faculty


async def scrape_gt_bme_all(session) -> list:
    """Scrape all GT BME profiles"""
    faculty = []
    
    print(f'  Scraping {len(GT_BME_PROFILES)} GT BME profiles...')
    
    for i, url in enumerate(GT_BME_PROFILES):
        slug = url.split('/')[-1]
        print(f'    [{i+1}/{len(GT_BME_PROFILES)}] {slug}...', end=' ', flush=True)
        
        person = await scrape_gt_bme_profile(session, url)
        if person and person.get('name'):
            faculty.append(person)
            print(f'OK')
        else:
            print(f'SKIP')
        
        await asyncio.sleep(0.5)
    
    return faculty


async def main():
    print('=' * 70)
    print('ATLANTA CONSORTIUM SWARM v2')
    print('=' * 70)
    print(f'Started: {datetime.now(timezone.utc).isoformat()}')
    
    all_faculty = []
    
    async with aiohttp.ClientSession() as session:
        # Phase 1: GSU Neuroscience
        print('\n[1/3] GSU NEUROSCIENCE INSTITUTE')
        print('-' * 40)
        inst = INSTITUTIONS['gsu_neuro']
        inst['slug'] = 'gsu-neuro'
        gsu_faculty = await scrape_institution_thalamus(session, inst)
        all_faculty.extend(gsu_faculty)
        print(f'  Total: {len(gsu_faculty)} faculty')
        
        await asyncio.sleep(2)
        
        # Phase 2: Emory Neurology  
        print('\n[2/3] EMORY NEUROLOGY')
        print('-' * 40)
        inst = INSTITUTIONS['emory_neuro']
        inst['slug'] = 'emory-neuro'
        emory_faculty = await scrape_institution_thalamus(session, inst)
        all_faculty.extend(emory_faculty)
        print(f'  Total: {len(emory_faculty)} faculty')
        
        await asyncio.sleep(2)
        
        # Phase 3: GT BME
        print('\n[3/3] GEORGIA TECH BME')
        print('-' * 40)
        gt_faculty = await scrape_gt_bme_all(session)
        all_faculty.extend(gt_faculty)
        print(f'  Total: {len(gt_faculty)} faculty')
    
    # Save results
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'consortium': 'Atlanta Neuroscience',
        'total_faculty': len(all_faculty),
        'by_institution': {
            'GSU Neuroscience': len(gsu_faculty),
            'Emory Neurology': len(emory_faculty),
            'Georgia Tech BME': len(gt_faculty),
        },
        'faculty': all_faculty
    }
    
    outfile = f'data/consortium/atlanta_consortium_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(outfile, 'w') as f:
        json.dump(output, f, indent=2)
    
    print('\n' + '=' * 70)
    print('SWARM COMPLETE')
    print('=' * 70)
    print(f'Total Faculty: {len(all_faculty)}')
    print(f'  - GSU Neuroscience: {len(gsu_faculty)}')
    print(f'  - Emory Neurology: {len(emory_faculty)}')
    print(f'  - Georgia Tech BME: {len(gt_faculty)}')
    print(f'\n✓ Saved to: {outfile}')


if __name__ == '__main__':
    asyncio.run(main())
