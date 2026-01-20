"""
AUTONOMOUS MEGA SWARM v2 - ALL GEORGIA UNIVERSITIES
====================================================
Better parsing, error recovery, continuous operation
Logs to Boswell, handles network issues gracefully
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone
from typing import Dict, List

THALAMUS_URL = 'http://localhost:3000'
LOG_FILE = 'data/consortium/swarm_log.txt'

# All directory sources
SOURCES = [
    # GT
    {'name': 'GT-Aerospace', 'url': 'https://ae.gatech.edu/people/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-Biology', 'url': 'https://biology.gatech.edu/people/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-ChBE', 'url': 'https://chbe.gatech.edu/people/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-Chemistry', 'url': 'https://chemistry.gatech.edu/people/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-CEE', 'url': 'https://ce.gatech.edu/people/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-CS', 'url': 'https://scs.gatech.edu/people', 'inst': 'Georgia Tech'},
    {'name': 'GT-CSE', 'url': 'https://cse.gatech.edu/people', 'inst': 'Georgia Tech'},
    {'name': 'GT-EAS', 'url': 'https://eas.gatech.edu/people/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-ECE', 'url': 'https://ece.gatech.edu/directory', 'inst': 'Georgia Tech'},
    {'name': 'GT-ISyE', 'url': 'https://isye.gatech.edu/faculty-staff/directory', 'inst': 'Georgia Tech'},
    {'name': 'GT-Math', 'url': 'https://math.gatech.edu/people', 'inst': 'Georgia Tech'},
    {'name': 'GT-ME', 'url': 'https://me.gatech.edu/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-MSE', 'url': 'https://mse.gatech.edu/people', 'inst': 'Georgia Tech'},
    {'name': 'GT-NRE', 'url': 'https://nre.gatech.edu/people', 'inst': 'Georgia Tech'},
    {'name': 'GT-Physics', 'url': 'https://physics.gatech.edu/people/faculty', 'inst': 'Georgia Tech'},
    {'name': 'GT-Psychology', 'url': 'https://psychology.gatech.edu/people', 'inst': 'Georgia Tech'},
    {'name': 'GT-Scheller', 'url': 'https://scheller.gatech.edu/directory/', 'inst': 'Georgia Tech'},
    # Emory
    {'name': 'Emory-Neurology', 'url': 'https://med.emory.edu/departments/neurology/faculty/', 'inst': 'Emory'},
    {'name': 'Emory-Psychiatry', 'url': 'https://med.emory.edu/departments/psychiatry/faculty/', 'inst': 'Emory'},
    {'name': 'Emory-Radiology', 'url': 'https://med.emory.edu/departments/radiology/faculty/', 'inst': 'Emory'},
    {'name': 'Emory-Surgery', 'url': 'https://med.emory.edu/departments/surgery/faculty/', 'inst': 'Emory'},
    {'name': 'Emory-Pediatrics', 'url': 'https://med.emory.edu/departments/pediatrics/faculty/', 'inst': 'Emory'},
    {'name': 'Emory-PublicHealth', 'url': 'https://sph.emory.edu/faculty/', 'inst': 'Emory'},
    # GSU
    {'name': 'GSU-Neuroscience', 'url': 'https://neuroscience.gsu.edu/directory/', 'inst': 'GSU'},
    {'name': 'GSU-Psychology', 'url': 'https://psychology.gsu.edu/directory/', 'inst': 'GSU'},
    {'name': 'GSU-Biology', 'url': 'https://biology.gsu.edu/directory/', 'inst': 'GSU'},
    {'name': 'GSU-Chemistry', 'url': 'https://chemistry.gsu.edu/directory/', 'inst': 'GSU'},
    {'name': 'GSU-CS', 'url': 'https://cs.gsu.edu/directory/', 'inst': 'GSU'},
    {'name': 'GSU-Robinson', 'url': 'https://robinson.gsu.edu/directory/', 'inst': 'GSU'},
    # UGA
    {'name': 'UGA-Neuroscience', 'url': 'https://neuroscience.uga.edu/faculty/', 'inst': 'UGA'},
    {'name': 'UGA-Psychology', 'url': 'https://psychology.uga.edu/directory/', 'inst': 'UGA'},
    {'name': 'UGA-Chemistry', 'url': 'https://www.chem.uga.edu/directory/', 'inst': 'UGA'},
    {'name': 'UGA-CS', 'url': 'https://cs.uga.edu/directory/', 'inst': 'UGA'},
    {'name': 'UGA-Genetics', 'url': 'https://genetics.uga.edu/directory/', 'inst': 'UGA'},
    {'name': 'UGA-VetMed', 'url': 'https://vet.uga.edu/directory/', 'inst': 'UGA'},
    {'name': 'UGA-Forestry', 'url': 'https://warnell.uga.edu/directory/', 'inst': 'UGA'},
]


def log(msg: str):
    """Log to file and print"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f'[{timestamp}] {msg}'
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def is_valid_name(name: str) -> bool:
    """Strict name validation"""
    if not name or len(name) < 5 or len(name) > 50:
        return False
    parts = name.split()
    if len(parts) < 2:
        return False
    garbage = ['page', 'menu', 'next', 'previous', 'directory', 'faculty', 
               'staff', 'department', 'college', 'school', 'university',
               'professor', 'research', 'contact', 'email', 'phone',
               'office', 'news', 'events', 'home', 'about', 'skip']
    name_lower = name.lower()
    for g in garbage:
        if name_lower.startswith(g):
            return False
    return True


def extract_faculty(text: str) -> List[Dict]:
    """Extract faculty from text"""
    faculty = []
    
    # Pattern: "Last, First"
    for match in re.finditer(r'([A-Z][a-z]+),\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?)', text):
        name = f'{match.group(2)} {match.group(1)}'
        if is_valid_name(name):
            faculty.append({'name': name})
    
    # Pattern: Email hints
    for match in re.finditer(r'([a-z]+)\.([a-z]+)@(?:gatech|emory|gsu|uga)\.edu', text.lower()):
        name = f'{match.group(1).title()} {match.group(2).title()}'
        email = match.group(0)
        if is_valid_name(name):
            faculty.append({'name': name, 'email': email})
    
    return faculty


async def scrape_source(session, source: Dict) -> List[Dict]:
    """Scrape one source with Thalamus"""
    name = source['name']
    url = source['url']
    
    try:
        # Perceive page
        req = {
            'method': 'tools/call',
            'params': {'name': 'thalamus_perceive', 'arguments': {'url': url, 'maxElements': 500}},
            'id': f'p-{name}'
        }
        async with session.post(f'{THALAMUS_URL}/mcp', json=req,
                               timeout=aiohttp.ClientTimeout(total=45)) as resp:
            result = await resp.json()
            if result.get('error'):
                log(f'  {name}: PERCEIVE ERROR - {result.get("error", {}).get("message", "unknown")[:30]}')
                return []
        
        await asyncio.sleep(1.5)
        
        # Get text
        req = {
            'method': 'tools/call',
            'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 150000}},
            'id': f't-{name}'
        }
        async with session.post(f'{THALAMUS_URL}/mcp', json=req,
                               timeout=aiohttp.ClientTimeout(total=30)) as resp:
            result = await resp.json()
            if result.get('error'):
                log(f'  {name}: TEXT ERROR')
                return []
            
            content = result['result']['content'][0]['text']
            data = json.loads(content)
            full_text = '\n'.join(b.get('text', '') for b in data.get('content', []))
            
            faculty = extract_faculty(full_text)
            for f in faculty:
                f['department'] = name
                f['institution'] = source['inst']
                f['source_url'] = url
            
            return faculty
            
    except asyncio.TimeoutError:
        log(f'  {name}: TIMEOUT')
    except Exception as e:
        log(f'  {name}: ERROR - {str(e)[:40]}')
    
    return []


async def check_thalamus() -> bool:
    """Check if Thalamus is responsive"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{THALAMUS_URL}/health', timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
    except:
        return False


async def main():
    log('=' * 60)
    log('AUTONOMOUS SWARM v2 STARTED')
    log('=' * 60)
    
    # Check Thalamus
    if not await check_thalamus():
        log('ERROR: Thalamus not responding! Check Chrome/extension.')
        return
    
    log(f'Thalamus OK. Sources: {len(SOURCES)}')
    
    all_faculty = []
    stats = {}
    errors = []
    
    async with aiohttp.ClientSession() as session:
        for i, source in enumerate(SOURCES, 1):
            log(f'[{i}/{len(SOURCES)}] {source["name"]}...')
            
            faculty = await scrape_source(session, source)
            
            if faculty:
                all_faculty.extend(faculty)
                stats[source['name']] = len(faculty)
                log(f'  -> {len(faculty)} faculty extracted')
            else:
                errors.append(source['name'])
            
            await asyncio.sleep(3)
    
    # Dedupe
    seen = set()
    unique = []
    for f in all_faculty:
        key = f.get('name', '').lower().replace(' ', '')
        if key and key not in seen:
            seen.add(key)
            unique.append(f)
    
    # Save
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': 'autonomous-v2',
        'total_raw': len(all_faculty),
        'total_unique': len(unique),
        'stats': stats,
        'errors': errors,
        'faculty': unique
    }
    
    outfile = f'data/consortium/autonomous_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    log('=' * 60)
    log('SWARM COMPLETE')
    log(f'Total unique faculty: {len(unique)}')
    log(f'Sources with errors: {len(errors)}')
    log(f'Output: {outfile}')
    log('=' * 60)


if __name__ == '__main__':
    asyncio.run(main())
