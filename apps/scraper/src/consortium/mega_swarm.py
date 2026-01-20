"""
GEORGIA MEGA SWARM - ALL UNIVERSITIES, ALL COLLEGES, EVERYONE
==============================================================
Captures: name, position, department, email, phone, photo_url, profile_url, research
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict

THALAMUS_URL = 'http://localhost:3000'

# ============================================================================
# UNIVERSITY DIRECTORY SOURCES
# ============================================================================
GEORGIA_UNIVERSITIES = {
    # -------------------------------------------------------------------------
    # GEORGIA TECH - All Schools/Colleges
    # -------------------------------------------------------------------------
    'gatech': {
        'name': 'Georgia Institute of Technology',
        'central_directory': 'https://directory.gatech.edu/',
        'colleges': [
            {
                'name': 'College of Engineering',
                'schools': [
                    {'name': 'BME', 'url': 'https://bme.gatech.edu/our-people/our-faculty', 'profile_pattern': '/bio/'},
                    {'name': 'ECE', 'url': 'https://ece.gatech.edu/directory', 'profile_pattern': '/directory/'},
                    {'name': 'ME', 'url': 'https://me.gatech.edu/faculty', 'profile_pattern': '/'},
                    {'name': 'ChBE', 'url': 'https://chbe.gatech.edu/people/faculty', 'profile_pattern': '/'},
                    {'name': 'CEE', 'url': 'https://ce.gatech.edu/people/faculty', 'profile_pattern': '/'},
                    {'name': 'AE', 'url': 'https://ae.gatech.edu/people/faculty', 'profile_pattern': '/'},
                    {'name': 'MSE', 'url': 'https://mse.gatech.edu/people', 'profile_pattern': '/'},
                    {'name': 'ISyE', 'url': 'https://isye.gatech.edu/faculty-staff/directory', 'profile_pattern': '/'},
                    {'name': 'NRE', 'url': 'https://nre.gatech.edu/people', 'profile_pattern': '/'},
                ]
            },
            {
                'name': 'College of Computing',
                'schools': [
                    {'name': 'CS', 'url': 'https://scs.gatech.edu/people', 'profile_pattern': '/'},
                    {'name': 'CSE', 'url': 'https://cse.gatech.edu/people', 'profile_pattern': '/'},
                    {'name': 'IC', 'url': 'https://ic.gatech.edu/people', 'profile_pattern': '/'},
                ]
            },
            {
                'name': 'College of Sciences',
                'schools': [
                    {'name': 'Physics', 'url': 'https://physics.gatech.edu/people/faculty', 'profile_pattern': '/'},
                    {'name': 'Chemistry', 'url': 'https://chemistry.gatech.edu/people/faculty', 'profile_pattern': '/'},
                    {'name': 'Math', 'url': 'https://math.gatech.edu/people', 'profile_pattern': '/'},
                    {'name': 'Biology', 'url': 'https://biology.gatech.edu/people/faculty', 'profile_pattern': '/'},
                    {'name': 'Psychology', 'url': 'https://psychology.gatech.edu/people', 'profile_pattern': '/'},
                    {'name': 'EAS', 'url': 'https://eas.gatech.edu/people/faculty', 'profile_pattern': '/'},
                ]
            },
            {
                'name': 'Scheller College of Business',
                'schools': [
                    {'name': 'Business', 'url': 'https://scheller.gatech.edu/directory/', 'profile_pattern': '/'},
                ]
            },
            {
                'name': 'Ivan Allen College of Liberal Arts',
                'schools': [
                    {'name': 'Liberal Arts', 'url': 'https://iac.gatech.edu/people', 'profile_pattern': '/'},
                ]
            },
            {
                'name': 'College of Design',
                'schools': [
                    {'name': 'Design', 'url': 'https://design.gatech.edu/people', 'profile_pattern': '/'},
                ]
            },
        ]
    },
    
    # -------------------------------------------------------------------------
    # EMORY UNIVERSITY - Schools
    # -------------------------------------------------------------------------
    'emory': {
        'name': 'Emory University',
        'central_directory': 'https://directory.emory.edu/',
        'schools': [
            {
                'name': 'School of Medicine',
                'departments': [
                    {'name': 'Neurology', 'url': 'https://med.emory.edu/departments/neurology/faculty/', 'done': True},
                    {'name': 'Psychiatry', 'url': 'https://med.emory.edu/departments/psychiatry/faculty/'},
                    {'name': 'Radiology', 'url': 'https://med.emory.edu/departments/radiology/faculty/'},
                    {'name': 'Surgery', 'url': 'https://med.emory.edu/departments/surgery/faculty/'},
                    {'name': 'BMI', 'url': 'https://med.emory.edu/departments/biomedical-informatics/faculty/'},
                    {'name': 'Pediatrics', 'url': 'https://med.emory.edu/departments/pediatrics/faculty/'},
                    {'name': 'Medicine', 'url': 'https://med.emory.edu/departments/medicine/faculty/'},
                ]
            },
            {
                'name': 'Rollins School of Public Health',
                'url': 'https://sph.emory.edu/faculty/'
            },
            {
                'name': 'College of Arts & Sciences',
                'url': 'https://college.emory.edu/people/'
            },
        ]
    },
    
    # -------------------------------------------------------------------------
    # GEORGIA STATE UNIVERSITY - Colleges
    # -------------------------------------------------------------------------
    'gsu': {
        'name': 'Georgia State University',
        'central_directory': 'https://www.gsu.edu/directory/',
        'colleges': [
            {
                'name': 'College of Arts & Sciences',
                'departments': [
                    {'name': 'Neuroscience', 'url': 'https://neuroscience.gsu.edu/directory/', 'done': True},
                    {'name': 'Psychology', 'url': 'https://psychology.gsu.edu/directory/'},
                    {'name': 'Biology', 'url': 'https://biology.gsu.edu/directory/'},
                    {'name': 'Chemistry', 'url': 'https://chemistry.gsu.edu/directory/'},
                    {'name': 'Physics', 'url': 'https://physics.gsu.edu/directory/'},
                    {'name': 'Computer Science', 'url': 'https://cs.gsu.edu/directory/'},
                    {'name': 'Math', 'url': 'https://math.gsu.edu/directory/'},
                ]
            },
            {
                'name': 'Robinson College of Business',
                'url': 'https://robinson.gsu.edu/directory/'
            },
            {
                'name': 'Andrew Young School of Policy',
                'url': 'https://aysps.gsu.edu/directory/'
            },
        ]
    },
    
    # -------------------------------------------------------------------------
    # UNIVERSITY OF GEORGIA - Colleges
    # -------------------------------------------------------------------------
    'uga': {
        'name': 'University of Georgia',
        'central_directory': 'https://peoplesearch.uga.edu/',
        'colleges': [
            {
                'name': 'Franklin College of Arts & Sciences',
                'departments': [
                    {'name': 'Neuroscience', 'url': 'https://neuroscience.uga.edu/faculty/', 'done': True},
                    {'name': 'Psychology', 'url': 'https://psychology.uga.edu/directory/'},
                    {'name': 'Biology', 'url': 'https://www.cellbio.uga.edu/directory/'},
                    {'name': 'Chemistry', 'url': 'https://www.chem.uga.edu/directory/'},
                    {'name': 'Physics', 'url': 'https://www.physast.uga.edu/people/'},
                    {'name': 'Computer Science', 'url': 'https://cs.uga.edu/directory/'},
                    {'name': 'Genetics', 'url': 'https://genetics.uga.edu/directory/'},
                ]
            },
            {
                'name': 'College of Engineering',
                'url': 'https://engineering.uga.edu/faculty/'
            },
            {
                'name': 'College of Veterinary Medicine',
                'url': 'https://vet.uga.edu/directory/'
            },
            {
                'name': 'Warnell School of Forestry',
                'url': 'https://warnell.uga.edu/directory/'
            },
        ]
    },
}


# ============================================================================
# ENHANCED SCHEMA - Now includes photo_url
# ============================================================================
FACULTY_SCHEMA = {
    'id': str,
    'name': str,
    'institution': str,
    'institution_slug': str,
    'college': str,
    'department': str,
    'position': str,
    'email': str,
    'phone': str,
    'photo_url': str,  # NEW!
    'profile_url': str,
    'research_interests': str,
    'lab_name': str,
    'google_scholar': str,
}


def extract_photo_url(html: str, base_url: str) -> Optional[str]:
    """Extract faculty photo URL from HTML"""
    # Common patterns for faculty photos
    patterns = [
        r'<img[^>]+class="[^"]*(?:headshot|profile|faculty)[^"]*"[^>]+src="([^"]+)"',
        r'<img[^>]+src="([^"]+)"[^>]+class="[^"]*(?:headshot|profile|faculty)[^"]*"',
        r'<img[^>]+src="([^"]+(?:headshot|profile|faculty|photo)[^"]*\.(?:jpg|jpeg|png|webp))"',
        r'<img[^>]+src="([^"]+/(?:people|faculty|directory)/[^"]+\.(?:jpg|jpeg|png|webp))"',
        r'<img[^>]+src="([^"]+)"[^>]+alt="[^"]*(?:photo|headshot|profile)',
        r'Headshot[^>]*>.*?<img[^>]+src="([^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            url = match.group(1)
            # Make absolute URL
            if url.startswith('//'):
                return 'https:' + url
            elif url.startswith('/'):
                # Extract base domain
                domain_match = re.match(r'(https?://[^/]+)', base_url)
                if domain_match:
                    return domain_match.group(1) + url
            elif url.startswith('http'):
                return url
    return ''


async def scrape_directory_page(session, url: str, institution: str, dept: str) -> List[Dict]:
    """Scrape a directory page using Thalamus"""
    faculty = []
    
    print(f"    Scraping {dept}...", end=' ', flush=True)
    
    # Use Thalamus to perceive the page
    perceive = {
        'method': 'tools/call',
        'params': {
            'name': 'thalamus_perceive',
            'arguments': {'url': url, 'maxElements': 500}
        },
        'id': f'perceive-{dept}'
    }
    
    try:
        async with session.post(f'{THALAMUS_URL}/mcp', json=perceive,
                                timeout=aiohttp.ClientTimeout(total=45)) as resp:
            result = await resp.json()
            if result.get('error'):
                print(f'ERROR: {result.get("error")}')
                return []
        
        await asyncio.sleep(1.5)
        
        # Get text content
        get_text = {
            'method': 'tools/call',
            'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 150000}},
            'id': f'text-{dept}'
        }
        async with session.post(f'{THALAMUS_URL}/mcp', json=get_text,
                                timeout=aiohttp.ClientTimeout(total=30)) as resp:
            result = await resp.json()
            if result.get('error'):
                print(f'TEXT ERROR')
                return []
            content = result['result']['content'][0]['text']
            data = json.loads(content)
        
        # Parse faculty from content blocks
        blocks = data.get('content', [])
        current_person = None
        
        for i, block in enumerate(blocks):
            text = block.get('text', '').strip()
            btype = block.get('type', '')
            
            # Skip navigation/footer content
            skip_words = ['skip to', 'copyright', 'privacy', 'menu', 'navigation', 
                         'footer', 'contact us', 'home', 'about']
            if any(w in text.lower() for w in skip_words):
                continue
            
            # Detect name patterns (Last, First or First Last with title)
            name_patterns = [
                r'^([A-Z][a-zA-Z\'\-]+),\s+([A-Z][a-zA-Z\'\-\s]+)$',  # Last, First
                r'^([A-Z][a-zA-Z\'\-]+\s+[A-Z][a-zA-Z\'\-]+)$',  # First Last
                r'^(Dr\.\s+)?([A-Z][a-zA-Z\'\-]+\s+[A-Z][a-zA-Z\'\-]+)',  # Dr. First Last
            ]
            
            for pattern in name_patterns:
                match = re.match(pattern, text)
                if match and len(text) < 60:
                    # Save previous person if exists
                    if current_person and current_person.get('name'):
                        faculty.append(current_person)
                    
                    # Start new person
                    name = match.group(0).replace('Dr. ', '').strip()
                    current_person = {
                        'name': name,
                        'institution': institution,
                        'department': dept,
                        'position': '',
                        'email': '',
                        'phone': '',
                        'photo_url': '',
                        'profile_url': url,
                        'research_interests': '',
                    }
                    break
            
            # If we have a current person, look for their details
            if current_person:
                # Email
                email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
                if email_match and not current_person['email']:
                    current_person['email'] = email_match.group()
                
                # Phone
                phone_match = re.search(r'\d{3}[\.-]\d{3}[\.-]\d{4}', text)
                if phone_match and not current_person['phone']:
                    current_person['phone'] = phone_match.group()
                
                # Position
                position_keywords = ['professor', 'director', 'chair', 'dean', 
                                    'lecturer', 'instructor', 'researcher', 'scientist']
                if any(kw in text.lower() for kw in position_keywords):
                    if len(text) < 150 and not current_person['position']:
                        current_person['position'] = text
                
                # Research
                if len(text) > 80 and '@' not in text and not current_person['research_interests']:
                    current_person['research_interests'] = text[:300]
        
        # Don't forget last person
        if current_person and current_person.get('name'):
            faculty.append(current_person)
        
        print(f'{len(faculty)} found')
        
    except asyncio.TimeoutError:
        print('TIMEOUT')
    except Exception as e:
        print(f'ERROR: {str(e)[:50]}')
    
    return faculty


async def main():
    print('=' * 80)
    print('GEORGIA MEGA SWARM - ALL UNIVERSITIES, ALL COLLEGES, EVERYONE')
    print('=' * 80)
    print(f'Started: {datetime.now(timezone.utc).isoformat()}')
    print()
    
    all_faculty = []
    stats = {}
    
    async with aiohttp.ClientSession() as session:
        # Process each university
        for uni_slug, uni_data in GEORGIA_UNIVERSITIES.items():
            print(f'\n{"="*60}')
            print(f'{uni_data["name"].upper()}')
            print(f'{"="*60}')
            
            uni_faculty = []
            
            # Process colleges/schools
            colleges = uni_data.get('colleges', uni_data.get('schools', []))
            
            for college in colleges:
                college_name = college.get('name', 'Unknown')
                print(f'\n  [{college_name}]')
                
                # Process departments/schools within college
                depts = college.get('departments', college.get('schools', []))
                if not depts and college.get('url'):
                    depts = [{'name': college_name, 'url': college['url']}]
                
                for dept in depts:
                    if dept.get('done'):
                        print(f"    {dept['name']}... ALREADY DONE (loading from file)")
                        continue
                    
                    if dept.get('url'):
                        faculty = await scrape_directory_page(
                            session, 
                            dept['url'], 
                            uni_data['name'],
                            dept['name']
                        )
                        
                        # Add institution slug and college
                        for f in faculty:
                            f['institution_slug'] = uni_slug
                            f['college'] = college_name
                            f['id'] = f"{uni_slug}-{dept['name'].lower()}-{len(uni_faculty)}"
                        
                        uni_faculty.extend(faculty)
                        await asyncio.sleep(2)  # Rate limit
            
            all_faculty.extend(uni_faculty)
            stats[uni_data['name']] = len(uni_faculty)
    
    # Save results
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'consortium': 'Georgia Mega Consortium',
        'version': '4.0',
        'total_faculty': len(all_faculty),
        'by_institution': stats,
        'captures_photos': True,
        'faculty': all_faculty
    }
    
    outfile = f'data/consortium/georgia_mega_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print('\n' + '=' * 80)
    print('MEGA SWARM COMPLETE')
    print('=' * 80)
    print(f'Total Faculty: {len(all_faculty)}')
    for uni, count in stats.items():
        print(f'  - {uni}: {count}')
    print(f'\nSaved to: {outfile}')


if __name__ == '__main__':
    asyncio.run(main())
