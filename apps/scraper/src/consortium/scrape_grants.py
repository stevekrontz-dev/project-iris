"""
GRANT OPPORTUNITIES SCRAPER
============================
Scrapes active grant opportunities from NIH, NSF, DOE, etc.
Extracts keywords, funding amounts, deadlines, and requirements
"""
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re

OUTPUT_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\grants')

# NIH Reporter API
NIH_API = 'https://api.reporter.nih.gov/v2/projects/search'

# Grants.gov API
GRANTS_GOV_API = 'https://www.grants.gov/grantsws/rest/opportunities/search'


async def fetch_nih_opportunities(session: aiohttp.ClientSession) -> list:
    """Fetch active NIH funding opportunities"""
    opportunities = []
    
    # Search for active FOAs (Funding Opportunity Announcements)
    keywords = [
        'brain computer interface',
        'neuroscience',
        'artificial intelligence',
        'machine learning',
        'biomedical engineering',
        'neural engineering',
        'rehabilitation',
        'assistive technology',
        'mental health',
        'aging',
    ]
    
    for keyword in keywords:
        try:
            payload = {
                "criteria": {
                    "advanced_text_search": {
                        "operator": "and",
                        "search_field": "all",
                        "search_text": keyword
                    },
                    "fiscal_years": [2025, 2026],
                    "include_active_projects": True
                },
                "limit": 20,
                "offset": 0
            }
            
            async with session.post(NIH_API, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for proj in data.get('results', []):
                        opportunities.append({
                            'source': 'NIH',
                            'id': proj.get('project_num'),
                            'title': proj.get('project_title'),
                            'agency': proj.get('agency_ic_fundings', [{}])[0].get('name', 'NIH'),
                            'keywords': [keyword],
                            'amount': proj.get('award_amount'),
                            'abstract': proj.get('abstract_text', '')[:500],
                        })
        except Exception as e:
            print(f'NIH error for {keyword}: {e}')
    
    return opportunities


async def fetch_nsf_opportunities(session: aiohttp.ClientSession) -> list:
    """Fetch active NSF funding opportunities"""
    opportunities = []
    
    # NSF has a public RSS/search - we'll use known program areas
    nsf_programs = [
        {
            'id': 'NSF-CISE',
            'title': 'Computer and Information Science and Engineering',
            'agency': 'NSF CISE',
            'keywords': ['computer science', 'artificial intelligence', 'machine learning', 'cybersecurity'],
            'amount_range': '$300K - $1.5M',
            'url': 'https://www.nsf.gov/dir/index.jsp?org=CISE',
        },
        {
            'id': 'NSF-BIO',
            'title': 'Biological Sciences',
            'agency': 'NSF BIO',
            'keywords': ['biology', 'neuroscience', 'genomics', 'ecology'],
            'amount_range': '$200K - $2M',
            'url': 'https://www.nsf.gov/dir/index.jsp?org=BIO',
        },
        {
            'id': 'NSF-ENG',
            'title': 'Engineering',
            'agency': 'NSF ENG',
            'keywords': ['engineering', 'biomedical', 'robotics', 'materials'],
            'amount_range': '$300K - $3M',
            'url': 'https://www.nsf.gov/dir/index.jsp?org=ENG',
        },
        {
            'id': 'NSF-CAREER',
            'title': 'Faculty Early Career Development Program (CAREER)',
            'agency': 'NSF',
            'keywords': ['early career', 'research', 'education'],
            'amount_range': '$400K - $800K',
            'deadline': 'July 2025',
            'url': 'https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=503214',
        },
        {
            'id': 'NSF-NRI',
            'title': 'National Robotics Initiative 3.0',
            'agency': 'NSF',
            'keywords': ['robotics', 'human-robot interaction', 'autonomous systems', 'AI'],
            'amount_range': '$250K - $1.5M',
            'url': 'https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=503641',
        },
        {
            'id': 'NSF-BRAIN',
            'title': 'Understanding the Brain (UtB)',
            'agency': 'NSF',
            'keywords': ['neuroscience', 'brain', 'cognition', 'neural circuits'],
            'amount_range': '$300K - $1M',
            'url': 'https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=505132',
        },
    ]
    
    for prog in nsf_programs:
        opportunities.append({
            'source': 'NSF',
            'id': prog['id'],
            'title': prog['title'],
            'agency': prog['agency'],
            'keywords': prog['keywords'],
            'amount_range': prog.get('amount_range'),
            'deadline': prog.get('deadline'),
            'url': prog.get('url'),
        })
    
    return opportunities


def get_curated_opportunities() -> list:
    """Curated list of major grant opportunities"""
    return [
        # NIH
        {
            'source': 'NIH',
            'id': 'R01',
            'title': 'NIH Research Project Grant (R01)',
            'agency': 'NIH',
            'keywords': ['biomedical', 'health', 'disease', 'clinical'],
            'amount_range': '$250K - $500K/year',
            'duration': '3-5 years',
            'deadline': 'Rolling (3 cycles/year)',
            'team_size': '1-5 PIs',
            'description': 'Support discrete, specified, circumscribed projects in areas representing investigators specific interests and competencies.',
            'url': 'https://grants.nih.gov/grants/funding/r01.htm',
            'requirements': ['Preliminary data recommended', 'Institutional support'],
        },
        {
            'source': 'NIH',
            'id': 'R21',
            'title': 'NIH Exploratory/Developmental Research Grant (R21)',
            'agency': 'NIH',
            'keywords': ['exploratory', 'pilot', 'novel', 'high-risk'],
            'amount_range': '$275K total',
            'duration': '2 years',
            'deadline': 'Rolling (3 cycles/year)',
            'team_size': '1-3 PIs',
            'description': 'Support exploratory and developmental research projects. High-risk/high-reward.',
            'url': 'https://grants.nih.gov/grants/funding/r21.htm',
            'requirements': ['No preliminary data required'],
        },
        {
            'source': 'NIH',
            'id': 'U01-BRAIN',
            'title': 'BRAIN Initiative: Research on the Ethical Implications of Advancements in Neurotechnology',
            'agency': 'NIH BRAIN',
            'keywords': ['brain computer interface', 'neurotechnology', 'ethics', 'neural devices', 'BCI'],
            'amount_range': '$500K/year',
            'duration': '4 years',
            'deadline': 'February 2025',
            'team_size': '2-5 PIs',
            'description': 'Support research on ethical implications of emerging neurotechnologies including BCIs.',
            'url': 'https://braininitiative.nih.gov/',
            'requirements': ['Multi-disciplinary team', 'Ethics expertise', 'Neuroscience expertise'],
        },
        {
            'source': 'NIH',
            'id': 'K99-R00',
            'title': 'Pathway to Independence Award (K99/R00)',
            'agency': 'NIH',
            'keywords': ['early career', 'postdoc', 'transition', 'faculty'],
            'amount_range': '$100K/year (K99) + $250K/year (R00)',
            'duration': '2 years K99 + 3 years R00',
            'deadline': 'Rolling',
            'team_size': '1 PI',
            'description': 'Support postdocs transitioning to independent faculty positions.',
            'url': 'https://grants.nih.gov/grants/guide/pa-files/PA-20-188.html',
            'requirements': ['Postdoctoral fellow', 'Strong mentor'],
        },
        # NSF
        {
            'source': 'NSF',
            'id': 'NSF-CAREER',
            'title': 'Faculty Early Career Development Program (CAREER)',
            'agency': 'NSF',
            'keywords': ['early career', 'research', 'education', 'tenure-track'],
            'amount_range': '$400K - $800K',
            'duration': '5 years',
            'deadline': 'July 2025',
            'team_size': '1 PI',
            'description': 'NSF most prestigious award for early-career faculty integrating research and education.',
            'url': 'https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=503214',
            'requirements': ['Tenure-track faculty', 'Strong education plan'],
        },
        {
            'source': 'NSF',
            'id': 'NSF-NRI-3.0',
            'title': 'National Robotics Initiative 3.0: Innovations in Integration of Robotics',
            'agency': 'NSF',
            'keywords': ['robotics', 'human-robot', 'AI', 'automation', 'assistive'],
            'amount_range': '$250K - $1.5M',
            'duration': '3-4 years',
            'deadline': 'March 2025',
            'team_size': '1-4 PIs',
            'description': 'Accelerate realization and deployment of robots that work with humans.',
            'url': 'https://www.nsf.gov/pubs/2023/nsf23529/nsf23529.htm',
            'requirements': ['Cross-disciplinary team encouraged'],
        },
        {
            'source': 'NSF',
            'id': 'NSF-BCS-Neural',
            'title': 'Cognitive Neuroscience Program',
            'agency': 'NSF BCS',
            'keywords': ['neuroscience', 'cognition', 'brain', 'behavior', 'neural'],
            'amount_range': '$200K - $600K',
            'duration': '3-4 years',
            'deadline': 'Rolling',
            'team_size': '1-3 PIs',
            'description': 'Support research on neural and cognitive systems underlying human behavior.',
            'url': 'https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=5316',
            'requirements': ['Human subjects research'],
        },
        {
            'source': 'NSF',
            'id': 'NSF-CISE-IIS',
            'title': 'Information & Intelligent Systems (IIS): Core Programs',
            'agency': 'NSF CISE',
            'keywords': ['AI', 'machine learning', 'human-computer interaction', 'data science'],
            'amount_range': '$200K - $600K',
            'duration': '3 years',
            'deadline': 'Rolling',
            'team_size': '1-3 PIs',
            'description': 'Support research in AI, ML, HCI, and data science.',
            'url': 'https://www.nsf.gov/funding/pgm_summ.jsp?pims_id=13707',
            'requirements': ['Computing focus'],
        },
        # DOD/DARPA
        {
            'source': 'DARPA',
            'id': 'DARPA-N3',
            'title': 'Next-Generation Nonsurgical Neurotechnology (N3)',
            'agency': 'DARPA',
            'keywords': ['BCI', 'brain computer interface', 'non-invasive', 'neural', 'neurotechnology'],
            'amount_range': '$1M - $5M',
            'duration': '4 years',
            'deadline': 'TBD 2025',
            'team_size': '3-10 PIs',
            'description': 'Develop high-resolution, bidirectional brain-machine interfaces without surgery.',
            'url': 'https://www.darpa.mil/program/next-generation-nonsurgical-neurotechnology',
            'requirements': ['Technical expertise in neural interfaces', 'Engineering team'],
        },
        {
            'source': 'DOD',
            'id': 'CDMRP-ALS',
            'title': 'ALS Research Program',
            'agency': 'DOD CDMRP',
            'keywords': ['ALS', 'neurodegenerative', 'motor neuron', 'assistive technology'],
            'amount_range': '$300K - $1.5M',
            'duration': '2-4 years',
            'deadline': 'October 2025',
            'team_size': '1-5 PIs',
            'description': 'Support innovative ALS research including assistive technologies.',
            'url': 'https://cdmrp.health.mil/alsrp/',
            'requirements': ['Relevance to ALS patients'],
        },
        # DOE
        {
            'source': 'DOE',
            'id': 'DOE-ASCR',
            'title': 'Advanced Scientific Computing Research (ASCR)',
            'agency': 'DOE',
            'keywords': ['computing', 'AI', 'scientific computing', 'HPC'],
            'amount_range': '$500K - $2M',
            'duration': '3 years',
            'deadline': 'Rolling',
            'team_size': '1-5 PIs',
            'description': 'Support research in applied mathematics, computer science for scientific discovery.',
            'url': 'https://www.energy.gov/science/ascr',
            'requirements': ['Scientific computing focus'],
        },
        # Private Foundations
        {
            'source': 'Simons Foundation',
            'id': 'Simons-Collab',
            'title': 'Simons Collaborations in Mathematics and Physical Sciences',
            'agency': 'Simons Foundation',
            'keywords': ['mathematics', 'physics', 'theoretical', 'collaboration'],
            'amount_range': '$1M - $2M/year',
            'duration': '4 years',
            'deadline': 'LOI September 2025',
            'team_size': '4-10 PIs',
            'description': 'Support collaborative projects addressing fundamental scientific questions.',
            'url': 'https://www.simonsfoundation.org/funding-opportunities/',
            'requirements': ['Multi-institutional collaboration', 'Theoretical focus'],
        },
        {
            'source': 'Kavli Foundation',
            'id': 'Kavli-Neuro',
            'title': 'Kavli Neural Systems Institute Programs',
            'agency': 'Kavli Foundation',
            'keywords': ['neuroscience', 'neural systems', 'brain', 'research'],
            'amount_range': 'Varies',
            'duration': 'Varies',
            'deadline': 'Rolling',
            'team_size': '1-5 PIs',
            'description': 'Support innovative neuroscience research.',
            'url': 'https://kavlifoundation.org/',
            'requirements': ['Neuroscience focus'],
        },
        {
            'source': 'ALS Association',
            'id': 'ALSA-Research',
            'title': 'ALS Association Research Grants',
            'agency': 'ALS Association',
            'keywords': ['ALS', 'motor neuron disease', 'therapy', 'biomarkers'],
            'amount_range': '$100K - $500K',
            'duration': '2-3 years',
            'deadline': 'March 2025',
            'team_size': '1-3 PIs',
            'description': 'Support research to find treatments and cure for ALS.',
            'url': 'https://www.als.org/research/for-researchers',
            'requirements': ['ALS relevance'],
        },
    ]


async def main():
    print('=' * 70)
    print('GRANT OPPORTUNITIES AGGREGATOR')
    print('=' * 70)
    print(f'Started: {datetime.now().isoformat()}')
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get curated opportunities
    opportunities = get_curated_opportunities()
    
    # Could add live scraping here
    # async with aiohttp.ClientSession() as session:
    #     nih_opps = await fetch_nih_opportunities(session)
    #     nsf_opps = await fetch_nsf_opportunities(session)
    #     opportunities.extend(nih_opps)
    #     opportunities.extend(nsf_opps)
    
    # Deduplicate by ID
    seen = set()
    unique_opps = []
    for opp in opportunities:
        if opp['id'] not in seen:
            seen.add(opp['id'])
            unique_opps.append(opp)
    
    print(f'Total opportunities: {len(unique_opps)}')
    
    # Save
    output_file = OUTPUT_DIR / 'grant_opportunities.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'updated': datetime.now().isoformat(),
            'count': len(unique_opps),
            'opportunities': unique_opps
        }, f, indent=2, ensure_ascii=False)
    
    print(f'Saved: {output_file}')
    
    # Summary by source
    by_source = {}
    for opp in unique_opps:
        src = opp['source']
        by_source[src] = by_source.get(src, 0) + 1
    
    print('\nBy Source:')
    for src, count in sorted(by_source.items()):
        print(f'  {src}: {count}')


if __name__ == '__main__':
    asyncio.run(main())
