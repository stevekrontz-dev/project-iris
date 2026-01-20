#!/usr/bin/env python3
"""
CC6: LinkedIn Profile Scraper
Scrapes public LinkedIn profiles to extract skills, experience, education

REQUIRES: VPN connection to avoid rate limiting
When you see "BLOCKED - Switch VPN", manually change server in NordVPN app

Run after cc5_social_enrichment.py has found LinkedIn URLs
"""

import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from pathlib import Path

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_enriched_social.json')
OUTPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_linkedin_enriched.json')
PROGRESS_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\linkedin_scrape_progress.json')

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]


def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def scrape_linkedin_profile(url: str) -> dict:
    """Scrape public LinkedIn profile"""
    try:
        resp = requests.get(url, headers=get_headers(), timeout=20, allow_redirects=True)
        
        # Check for blocks
        if resp.status_code == 999 or 'authwall' in resp.url:
            return {'error': 'authwall', 'blocked': True}
        
        if resp.status_code == 429:
            return {'error': 'rate_limited', 'blocked': True}
        
        if resp.status_code != 200:
            return {'error': f'status_{resp.status_code}'}
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        profile = {}
        
        # Headline
        headline = soup.select_one('.top-card-layout__headline')
        if headline:
            profile['linkedin_headline'] = headline.get_text(strip=True)
        
        # Location
        location = soup.select_one('.top-card-layout__first-subline')
        if location:
            profile['linkedin_location'] = location.get_text(strip=True)
        
        # About/Summary
        about = soup.select_one('.core-section-container__content p')
        if about:
            profile['linkedin_about'] = about.get_text(strip=True)[:500]
        
        # Experience
        experiences = []
        for exp in soup.select('.experience-item'):
            title_el = exp.select_one('.experience-item__title')
            company_el = exp.select_one('.experience-item__subtitle')
            duration_el = exp.select_one('.experience-item__duration')
            
            if title_el:
                experiences.append({
                    'title': title_el.get_text(strip=True),
                    'company': company_el.get_text(strip=True) if company_el else '',
                    'duration': duration_el.get_text(strip=True) if duration_el else '',
                })
        
        if experiences:
            profile['linkedin_experience'] = experiences[:5]  # Top 5
        
        # Education
        education = []
        for edu in soup.select('.education__list-item'):
            school_el = edu.select_one('.education__item--school-name')
            degree_el = edu.select_one('.education__item--degree-info')
            
            if school_el:
                education.append({
                    'school': school_el.get_text(strip=True),
                    'degree': degree_el.get_text(strip=True) if degree_el else '',
                })
        
        if education:
            profile['linkedin_education'] = education[:3]
        
        # Skills (from skills section)
        skills = []
        for skill in soup.select('.skill-categories-card li'):
            skill_text = skill.get_text(strip=True)
            if skill_text:
                skills.append(skill_text)
        
        if skills:
            profile['linkedin_skills'] = skills[:20]
        
        # Certifications
        certs = []
        for cert in soup.select('.certifications__list-item'):
            cert_name = cert.select_one('.certifications__item-title')
            if cert_name:
                certs.append(cert_name.get_text(strip=True))
        
        if certs:
            profile['linkedin_certifications'] = certs[:10]
        
        return profile
        
    except requests.exceptions.Timeout:
        return {'error': 'timeout'}
    except Exception as e:
        return {'error': str(e)[:50]}


def main():
    print("=" * 60)
    print("  CC6: LinkedIn Profile Scraper")
    print("=" * 60)
    print("\n  IMPORTANT: Have NordVPN connected!")
    print("  When you see 'BLOCKED', switch VPN server manually.\n")
    
    # Load enriched data
    if not INPUT_FILE.exists():
        print(f"ERROR: Run cc5_social_enrichment.py first!")
        print(f"Missing: {INPUT_FILE}")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    people = data.get('all_people', [])
    
    # Filter to those with LinkedIn URLs
    with_linkedin = [(i, p) for i, p in enumerate(people) if p.get('linkedin_url')]
    print(f"Found {len(with_linkedin)} people with LinkedIn URLs\n")
    
    if not with_linkedin:
        print("No LinkedIn URLs found. Run cc5_social_enrichment.py first!")
        return
    
    # Load progress
    start_idx = 0
    blocked_count = 0
    
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_idx = progress.get('last_idx', 0)
            print(f"Resuming from index {start_idx}")
    
    scraped = 0
    errors = 0
    
    for j, (i, person) in enumerate(with_linkedin):
        if j < start_idx:
            continue
        
        name = person.get('name', '')
        url = person.get('linkedin_url', '')
        
        print(f"[{j+1}/{len(with_linkedin)}] {name[:30]:30s}", end=' ', flush=True)
        
        profile = scrape_linkedin_profile(url)
        
        if profile.get('blocked'):
            blocked_count += 1
            print(f"BLOCKED ({blocked_count}/3)")
            
            if blocked_count >= 3:
                print("\n" + "!" * 60)
                print("  BLOCKED - SWITCH VPN SERVER NOW!")
                print("  Open NordVPN app and connect to a different server.")
                print("  Press Enter when ready to continue...")
                print("!" * 60)
                input()
                blocked_count = 0
                continue
        
        elif profile.get('error'):
            errors += 1
            print(f"Error: {profile.get('error')}")
        
        else:
            # Merge profile data
            people[i].update(profile)
            scraped += 1
            
            skills_count = len(profile.get('linkedin_skills', []))
            exp_count = len(profile.get('linkedin_experience', []))
            print(f"OK - {skills_count} skills, {exp_count} jobs")
        
        # Save progress every 10
        if (j + 1) % 10 == 0:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'last_idx': j + 1, 'scraped': scraped, 'errors': errors}, f)
            
            # Also save main output
            data['all_people'] = people
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"  [Saved: {scraped} scraped, {errors} errors]")
        
        # Rate limiting
        time.sleep(random.uniform(3, 6))
    
    # Final save
    data['all_people'] = people
    data['linkedin_scrape_stats'] = {'scraped': scraped, 'errors': errors}
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"  COMPLETE")
    print(f"{'=' * 60}")
    print(f"\nScraped: {scraped}")
    print(f"Errors: {errors}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
