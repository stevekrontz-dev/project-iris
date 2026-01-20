"""
GT BME Faculty Scraper - Direct Web Fetch
Uses web_fetch to get profile pages, then parses the HTML structure
"""
import re
import json
from datetime import datetime

# Faculty profile URLs discovered via web search
GT_BME_FACULTY_URLS = [
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
]


def parse_gt_bme_profile(html_content: str, url: str) -> dict:
    """Parse a GT BME faculty profile from HTML"""
    
    # Extract name from h1
    name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else ''
    
    # Extract position (usually after "Title/Position" or in specific div)
    position = ''
    pos_match = re.search(r'Title/Position\s*</?\w+>\s*([^<]+)', html_content)
    if not pos_match:
        pos_match = re.search(r'Professor[^<]*|Chair[^<]*|Director[^<]*', html_content)
    if pos_match:
        position = pos_match.group(1).strip() if hasattr(pos_match, 'group') else pos_match.group(0).strip()
    
    # Extract research areas
    research_areas = re.findall(r'/research/areas-research/([^"]+)"[^>]*>([^<]+)', html_content)
    research = [area[1] for area in research_areas]
    
    # Extract contact info
    email_match = re.search(r'[\w.-]+@(?:gatech|emory)\.edu', html_content)
    email = email_match.group(0) if email_match else ''
    
    phone_match = re.search(r'(\d{3}\.\d{3}\.\d{4})', html_content)
    phone = phone_match.group(1) if phone_match else ''
    
    # Extract Google Scholar
    scholar_match = re.search(r'scholar\.google\.com/citations[^"]+', html_content)
    scholar = 'https://' + scholar_match.group(0) if scholar_match else ''
    
    # Extract lab
    lab_match = re.search(r'\[([^\]]+Lab(?:oratory)?)\]', html_content)
    lab = lab_match.group(1) if lab_match else ''
    
    return {
        'name': name,
        'position': position,
        'research_areas': research,
        'email': email,
        'phone': phone,
        'google_scholar': scholar,
        'lab': lab,
        'profile_url': url,
        'institution': 'Georgia Tech BME',
        'department': 'Biomedical Engineering'
    }


# Example parsed from the web_fetch output:
SAMPLE_PARSED = {
    'name': 'Lakshmi (Prasad) Dasi',
    'position': 'Rozelle Vanda Wesley Professor',
    'research_areas': [
        'Biomaterials & Regenerative Technologies',
        'Biomedical Imaging & Instrumentation',
        'Biomedical Informatics & Systems Modeling', 
        'Cardiovascular Engineering'
    ],
    'email': '',
    'phone': '404.385.1265',
    'google_scholar': 'https://scholar.google.com/citations?hl=en&user=CC7aZdcAAAAJ&view_op=list_works&sortby=pubdate',
    'lab': 'Cardiovascular Fluid Mechanics Laboratory',
    'profile_url': 'https://bme.gatech.edu/bio/lakshmi-prasad-dasi',
    'institution': 'Georgia Tech BME',
    'department': 'Biomedical Engineering'
}

print(f"GT BME faculty URLs to scrape: {len(GT_BME_FACULTY_URLS)}")
print(f"\nSample parsed profile:")
print(json.dumps(SAMPLE_PARSED, indent=2))
