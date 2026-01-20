"""
PROFILE-BASED FACULTY SCRAPER WITH PHOTO CAPTURE
=================================================
Scrapes individual profile pages for clean data extraction
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone

# Profile URL patterns discovered from each institution
PROFILE_SOURCES = {
    # Georgia Tech BME - individual /bio/ pages
    'gt_bme': {
        'name': 'Georgia Tech BME',
        'institution': 'Georgia Institute of Technology',
        'profile_base': 'https://bme.gatech.edu/bio/',
        'faculty_list': [
            'lakshmi-prasad-dasi', 'jaydev-desai', 'gabe-kwong', 'ahmet-coskun',
            'erin-buckley', 'andres-garcia', 'craig-forest', 'manu-platt',
            'susan-margulies', 'ross-ethier', 'hanjoong-jo', 'machelle-pardue'
        ],
        'selectors': {
            'name': 'h1.page-title, h1',
            'position': '.field--name-field-title-position',
            'photo': 'img.headshot, .field--name-field-headshot img',
            'email': 'a[href^="mailto:"]',
            'phone': '.field--name-field-phone',
            'research': '.field--name-field-research-interests',
        }
    },
    
    # GSU - individual profile pages
    'gsu_neuro': {
        'name': 'GSU Neuroscience',
        'institution': 'Georgia State University',
        'profile_base': 'https://neuroscience.gsu.edu/profile/',
        'faculty_list': [],  # Will discover from directory
        'selectors': {
            'name': 'h1.entry-title',
            'position': '.faculty-title',
            'photo': '.faculty-photo img, .profile-image img',
            'email': 'a[href^="mailto:"]',
        }
    },
}


async def fetch_profile(session, url: str) -> dict:
    """Fetch and parse a single profile page"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            html = await resp.text()
            return {'url': url, 'html': html}
    except:
        return None


def extract_from_html(html: str, url: str) -> dict:
    """Extract faculty data from profile HTML"""
    faculty = {
        'name': '',
        'position': '',
        'email': '',
        'phone': '',
        'photo_url': '',
        'profile_url': url,
        'research_interests': '',
        'lab_name': '',
    }
    
    # Extract name from h1
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if h1_match:
        faculty['name'] = h1_match.group(1).strip()
    
    # Extract photo URL
    photo_patterns = [
        r'<img[^>]+class="[^"]*headshot[^"]*"[^>]+src="([^"]+)"',
        r'Headshot[^>]*>.*?<img[^>]+src="([^"]+)"',
        r'<img[^>]+src="([^"]+/files/[^"]+\.(?:jpg|png|webp))"',
        r'<img[^>]+src="([^"]+)"[^>]+alt="[^"]*[Pp]hoto',
    ]
    for pattern in photo_patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            photo = match.group(1)
            # Make absolute
            if photo.startswith('/'):
                base = re.match(r'(https?://[^/]+)', url)
                if base:
                    photo = base.group(1) + photo
            faculty['photo_url'] = photo
            break
    
    # Extract email
    email_match = re.search(r'[\w.-]+@[\w.-]+\.(?:edu|com|org)', html)
    if email_match:
        faculty['email'] = email_match.group()
    
    # Extract phone
    phone_match = re.search(r'(\d{3}[\.\-]\d{3}[\.\-]\d{4})', html)
    if phone_match:
        faculty['phone'] = phone_match.group(1)
    
    # Extract position - look for common patterns
    position_patterns = [
        r'Title/Position[^>]*>([^<]+)',
        r'<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)',
        r'Professor[^<]*</(?:div|span|p)>',
    ]
    for pattern in position_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            pos = match.group(1) if '(' in pattern else match.group()
            pos = re.sub(r'<[^>]+>', '', pos).strip()
            if len(pos) < 200:
                faculty['position'] = pos
                break
    
    # Extract research areas
    research_match = re.search(r'Areas of Research.*?<a[^>]+>([^<]+)', html, re.DOTALL)
    if research_match:
        faculty['research_interests'] = research_match.group(1).strip()
    
    # Extract lab name
    lab_match = re.search(r'([A-Z][^<]*Laboratory|[A-Z][^<]*Lab)</a>', html)
    if lab_match:
        faculty['lab_name'] = lab_match.group(1).strip()
    
    # Google Scholar
    scholar_match = re.search(r'scholar\.google\.com/citations\?[^"]+user=([^"&]+)', html)
    if scholar_match:
        faculty['google_scholar'] = f'https://scholar.google.com/citations?user={scholar_match.group(1)}'
    
    return faculty


async def scrape_profiles(profile_urls: list, institution: str) -> list:
    """Scrape multiple profile pages"""
    faculty = []
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_profile(session, url) for url in profile_urls]
        results = await asyncio.gather(*tasks)
        
        for result in results:
            if result and result.get('html'):
                data = extract_from_html(result['html'], result['url'])
                if data.get('name'):
                    data['institution'] = institution
                    faculty.append(data)
                    print(f"  ✓ {data['name'][:40]} | photo: {'✓' if data.get('photo_url') else '✗'}")
    
    return faculty


async def main():
    print('=' * 70)
    print('PROFILE-BASED SCRAPER WITH PHOTO CAPTURE')
    print('=' * 70)
    
    all_faculty = []
    
    # Scrape GT BME profiles
    print('\n[Georgia Tech BME]')
    gt_urls = [f"https://bme.gatech.edu/bio/{slug}" for slug in PROFILE_SOURCES['gt_bme']['faculty_list']]
    gt_faculty = await scrape_profiles(gt_urls, 'Georgia Institute of Technology')
    all_faculty.extend(gt_faculty)
    
    print(f'\nTotal scraped: {len(all_faculty)}')
    print(f'With photos: {len([f for f in all_faculty if f.get("photo_url")])}')
    
    # Save
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '6.0-profiles',
        'total': len(all_faculty),
        'with_photos': len([f for f in all_faculty if f.get('photo_url')]),
        'faculty': all_faculty
    }
    
    outfile = 'data/consortium/profiles_with_photos.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f'\nSaved to: {outfile}')


if __name__ == '__main__':
    asyncio.run(main())
