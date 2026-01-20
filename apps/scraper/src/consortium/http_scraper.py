"""
AUTONOMOUS HTTP SCRAPER - NO BROWSER REQUIRED
==============================================
Uses aiohttp directly, no Thalamus/browser tabs
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone
from typing import List, Dict

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# Directory URLs - focus on ones with good HTML structure
SOURCES = [
    # GSU - clean HTML structure
    {'name': 'GSU Neuroscience', 'url': 'https://neuroscience.gsu.edu/directory/', 'inst': 'Georgia State University'},
    {'name': 'GSU Psychology', 'url': 'https://psychology.gsu.edu/directory/', 'inst': 'Georgia State University'},
    {'name': 'GSU Biology', 'url': 'https://biology.gsu.edu/directory/', 'inst': 'Georgia State University'},
    {'name': 'GSU Chemistry', 'url': 'https://chemistry.gsu.edu/directory/', 'inst': 'Georgia State University'},
    
    # UGA - clean HTML
    {'name': 'UGA Neuroscience', 'url': 'https://neuroscience.uga.edu/faculty/', 'inst': 'University of Georgia'},
    {'name': 'UGA Psychology', 'url': 'https://psychology.uga.edu/directory/faculty', 'inst': 'University of Georgia'},
    {'name': 'UGA Genetics', 'url': 'https://genetics.uga.edu/people/faculty/', 'inst': 'University of Georgia'},
    {'name': 'UGA Chemistry', 'url': 'https://www.chem.uga.edu/people/faculty', 'inst': 'University of Georgia'},
    
    # Emory - structured pages
    {'name': 'Emory Neurology', 'url': 'https://med.emory.edu/departments/neurology/faculty/index.html', 'inst': 'Emory University'},
    {'name': 'Emory Psychiatry', 'url': 'https://med.emory.edu/departments/psychiatry/faculty/index.html', 'inst': 'Emory University'},
]


def extract_faculty_from_html(html: str, source: Dict) -> List[Dict]:
    """Extract faculty from HTML using multiple patterns"""
    faculty = []
    
    # Pattern 1: Links with names (common pattern)
    # <a href="...">First Last</a>
    name_links = re.findall(r'<a[^>]+href="([^"]*)"[^>]*>([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)</a>', html)
    for url, name in name_links:
        if is_valid_name(name):
            faculty.append({
                'name': clean_name(name),
                'profile_url': make_absolute(url, source['url']),
                'institution': source['inst'],
                'department': source['name'],
            })
    
    # Pattern 2: Name, Title format in divs/spans
    # "John Smith, Professor"
    name_title = re.findall(r'>([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+),?\s*(Professor|Director|Chair|Associate|Assistant)[^<]*<', html)
    for name, title in name_title:
        if is_valid_name(name):
            faculty.append({
                'name': clean_name(name),
                'position': title,
                'institution': source['inst'],
                'department': source['name'],
            })
    
    # Pattern 3: Email-based extraction
    emails = re.findall(r'([a-zA-Z][a-zA-Z0-9.]+)@(gatech|emory|gsu|uga)\.edu', html)
    for local, domain in emails:
        # Try to find associated name nearby
        if '.' in local:
            parts = local.split('.')
            if len(parts) >= 2:
                name = f"{parts[0].title()} {parts[1].title()}"
                if is_valid_name(name):
                    faculty.append({
                        'name': name,
                        'email': f'{local}@{domain}.edu',
                        'institution': source['inst'],
                        'department': source['name'],
                    })
    
    # Pattern 4: h2/h3/h4 headers with names
    headers = re.findall(r'<h[234][^>]*>([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)</h[234]>', html)
    for name in headers:
        if is_valid_name(name):
            faculty.append({
                'name': clean_name(name),
                'institution': source['inst'],
                'department': source['name'],
            })
    
    # Pattern 5: Photo alt text
    photos = re.findall(r'<img[^>]+alt="(?:Photo of |Image of )?([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)"[^>]+src="([^"]+)"', html)
    for name, photo_url in photos:
        if is_valid_name(name):
            faculty.append({
                'name': clean_name(name),
                'photo_url': make_absolute(photo_url, source['url']),
                'institution': source['inst'],
                'department': source['name'],
            })
    
    return faculty


def is_valid_name(name: str) -> bool:
    """Check if string is a valid person name"""
    if not name or len(name) < 4 or len(name) > 50:
        return False
    
    parts = name.split()
    if len(parts) < 2:
        return False
    
    # Reject garbage
    garbage = ['page', 'menu', 'next', 'previous', 'directory', 'faculty', 'staff',
               'department', 'college', 'school', 'university', 'contact', 'email',
               'phone', 'office', 'news', 'events', 'home', 'about', 'research',
               'professor', 'associate', 'assistant', 'chair', 'dean', 'director']
    
    first_word = parts[0].lower()
    if first_word in garbage:
        return False
    
    # Check alphabetic
    for part in parts:
        clean = re.sub(r'[,.\-\'\s]', '', part)
        if clean and not clean.isalpha():
            return False
    
    return True


def clean_name(name: str) -> str:
    """Clean and normalize name"""
    name = re.sub(r'\s+', ' ', name.strip())
    name = re.sub(r',\s*$', '', name)
    return name


def make_absolute(url: str, base: str) -> str:
    """Convert relative URL to absolute"""
    if url.startswith('http'):
        return url
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        match = re.match(r'(https?://[^/]+)', base)
        if match:
            return match.group(1) + url
    return url


def deduplicate(faculty: List[Dict]) -> List[Dict]:
    """Remove duplicates by name"""
    seen = {}
    for f in faculty:
        key = f.get('name', '').lower().replace(' ', '').replace('.', '')
        if key and key not in seen:
            seen[key] = f
        elif key in seen:
            # Merge data
            existing = seen[key]
            for k, v in f.items():
                if v and not existing.get(k):
                    existing[k] = v
    return list(seen.values())


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch a single page"""
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                return await resp.text()
    except Exception as e:
        print(f'    Fetch error: {str(e)[:40]}')
    return ''


async def main():
    print('=' * 70)
    print('AUTONOMOUS HTTP SCRAPER - NO BROWSER')
    print('=' * 70)
    print(f'Started: {datetime.now(timezone.utc).isoformat()}')
    print(f'Sources: {len(SOURCES)}')
    print()
    
    all_faculty = []
    
    async with aiohttp.ClientSession() as session:
        for i, source in enumerate(SOURCES, 1):
            print(f'[{i}/{len(SOURCES)}] {source["name"]}...', end=' ', flush=True)
            
            html = await fetch_page(session, source['url'])
            if html:
                faculty = extract_faculty_from_html(html, source)
                all_faculty.extend(faculty)
                print(f'{len(faculty)} extracted')
            else:
                print('FAILED')
            
            await asyncio.sleep(1)
    
    # Deduplicate
    unique = deduplicate(all_faculty)
    
    print(f'\n{"="*70}')
    print(f'Total extracted: {len(all_faculty)}')
    print(f'After dedup: {len(unique)}')
    
    # Save
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': 'http-scraper-v1',
        'total': len(unique),
        'faculty': unique
    }
    
    outfile = f'data/consortium/http_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f'Saved: {outfile}')
    
    return unique


if __name__ == '__main__':
    asyncio.run(main())
