#!/usr/bin/env python3
"""
Parallel Google Scholar Enrichment Script
Run multiple instances with different IP addresses (VPN/Proxy)

Usage:
  python enrich_scholar_parallel.py --start 0 --end 300 --id agent1
  python enrich_scholar_parallel.py --start 301 --end 600 --id agent2
  etc.
"""

import json
import time
import random
import re
import argparse
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Parse arguments
parser = argparse.ArgumentParser(description='Parallel Scholar Enrichment')
parser.add_argument('--start', type=int, default=0, help='Start index')
parser.add_argument('--end', type=int, default=None, help='End index')
parser.add_argument('--id', type=str, default='agent', help='Agent identifier')
parser.add_argument('--proxy', type=str, default=None, help='Proxy URL (e.g., http://user:pass@proxy:port)')
parser.add_argument('--delay-min', type=int, default=8, help='Minimum delay between searches (seconds)')
parser.add_argument('--delay-max', type=int, default=15, help='Maximum delay between searches (seconds)')
parser.add_argument('--max-pubs', type=int, default=30, help='Max publications per researcher')
args = parser.parse_args()

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, 'output', 'faculty_fixed.json')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'output', f'faculty_enriched_{args.id}.json')
PROGRESS_FILE = os.path.join(SCRIPT_DIR, 'output', f'progress_{args.id}.json')

def log(level, msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{args.id}] {timestamp} | {level} | {msg}")

def random_delay():
    delay = random.uniform(args.delay_min, args.delay_max)
    time.sleep(delay)

def get_publication_details(page, pub_link) -> dict:
    """Click into a publication and extract full details."""
    try:
        pub_link.click()
        time.sleep(1.5 + random.random())

        details = {
            'title': '',
            'authors': [],
            'journal': '',
            'year': None,
            'volume': '',
            'issue': '',
            'pages': '',
            'publisher': '',
            'abstract': '',
            'citations': 0,
            'doi': '',
            'article_url': ''
        }

        # Title
        title_el = page.query_selector('#gsc_oci_title')
        if title_el:
            details['title'] = title_el.inner_text().strip()

            # Check for link
            link_el = title_el.query_selector('a')
            if link_el:
                details['article_url'] = link_el.get_attribute('href') or ''

        # Get all field rows
        fields = page.query_selector_all('.gs_scl')
        for field in fields:
            label_el = field.query_selector('.gsc_oci_field')
            value_el = field.query_selector('.gsc_oci_value')

            if not label_el or not value_el:
                continue

            label = label_el.inner_text().strip().lower()
            value = value_el.inner_text().strip()

            if 'authors' in label:
                details['authors'] = [a.strip() for a in value.split(',')]
            elif 'journal' in label or 'conference' in label or 'book' in label:
                details['journal'] = value
            elif 'volume' in label:
                details['volume'] = value
            elif 'issue' in label:
                details['issue'] = value
            elif 'pages' in label:
                details['pages'] = value
            elif 'publisher' in label:
                details['publisher'] = value
            elif 'description' in label:
                details['abstract'] = value[:2000]
            elif 'total citations' in label:
                first_num = re.search(r'^\d+', value.replace(',', ''))
                if first_num:
                    details['citations'] = int(first_num.group())

        # Try to get DOI from links
        links = page.query_selector_all('.gsc_oci_title_ggi a, .gsc_oci_value a')
        for link in links:
            href = link.get_attribute('href') or ''
            if 'doi.org' in href:
                doi_match = re.search(r'doi\.org/(.+?)(?:\?|$)', href)
                if doi_match:
                    details['doi'] = doi_match.group(1)
                break

        # Publication date/year
        date_field = page.query_selector('.gsc_oci_value')
        all_text = page.inner_text()
        year_match = re.search(r'\b(19|20)\d{2}\b', all_text)
        if year_match:
            details['year'] = int(year_match.group())

        # Go back
        page.go_back()
        time.sleep(1 + random.random())

        return details

    except Exception as e:
        log('ERROR', f"Error getting publication details: {e}")
        try:
            page.go_back()
            time.sleep(1)
        except:
            pass
        return None

def search_scholar(page, name: str) -> dict:
    """Search for a researcher on Google Scholar."""
    try:
        search_url = f"https://scholar.google.com/scholar?q=author:%22{name.replace(' ', '+')}%22"
        page.goto(search_url, timeout=30000)
        time.sleep(2 + random.random())

        # Check for CAPTCHA
        if 'sorry' in page.url.lower() or page.query_selector('form[action*="sorry"]'):
            log('WARNING', 'CAPTCHA detected! Waiting 60 seconds...')
            time.sleep(60)
            return None

        # Look for author profile link
        profile_links = page.query_selector_all('a[href*="/citations?user="]')

        if not profile_links:
            return None

        # Click first profile
        profile_link = profile_links[0]
        profile_link.click()
        time.sleep(2 + random.random())

        # Extract profile data
        scholar_data = {
            'scholar_id': '',
            'name': '',
            'affiliation': '',
            'interests': [],
            'h_index': 0,
            'i10_index': 0,
            'total_citations': 0,
            'publications': []
        }

        # Get Scholar ID from URL
        url_match = re.search(r'user=([^&]+)', page.url)
        if url_match:
            scholar_data['scholar_id'] = url_match.group(1)

        # Name
        name_el = page.query_selector('#gsc_prf_in')
        if name_el:
            scholar_data['name'] = name_el.inner_text().strip()

        # Affiliation
        aff_el = page.query_selector('.gsc_prf_il')
        if aff_el:
            scholar_data['affiliation'] = aff_el.inner_text().strip()

        # Interests
        interest_els = page.query_selector_all('#gsc_prf_int a')
        scholar_data['interests'] = [el.inner_text().strip() for el in interest_els]

        # Citation metrics
        metrics = page.query_selector_all('#gsc_rsb_st td.gsc_rsb_std')
        if len(metrics) >= 2:
            try:
                scholar_data['total_citations'] = int(metrics[0].inner_text().replace(',', ''))
            except:
                pass

        index_cells = page.query_selector_all('#gsc_rsb_st tr')
        for row in index_cells:
            cells = row.query_selector_all('td')
            if len(cells) >= 2:
                label = cells[0].inner_text().lower()
                try:
                    value = int(cells[1].inner_text().replace(',', ''))
                    if 'h-index' in label:
                        scholar_data['h_index'] = value
                    elif 'i10-index' in label:
                        scholar_data['i10_index'] = value
                except:
                    pass

        # Get publications
        pub_links = page.query_selector_all('a.gsc_a_at')
        num_pubs = min(len(pub_links), args.max_pubs)

        if num_pubs > 0:
            log('INFO', f"    Extracting {num_pubs} publications...")

        for i in range(num_pubs):
            try:
                # Re-query since page might have changed
                pub_links = page.query_selector_all('a.gsc_a_at')
                if i >= len(pub_links):
                    break

                pub_details = get_publication_details(page, pub_links[i])
                if pub_details and pub_details.get('title'):
                    scholar_data['publications'].append(pub_details)

                time.sleep(0.5 + random.random())

            except Exception as e:
                log('ERROR', f"Error on publication {i}: {e}")
                continue

        return scholar_data

    except PlaywrightTimeout:
        log('ERROR', f"Timeout searching for {name}")
        return None
    except Exception as e:
        log('ERROR', f"Error searching for {name}: {e}")
        return None

def load_progress():
    """Load progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_index': args.start - 1, 'enriched_count': 0}

def save_progress(index, enriched_count):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'last_index': index, 'enriched_count': enriched_count}, f)

def main():
    log('INFO', f'Loading faculty data from {INPUT_FILE}')

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        faculty = json.load(f)

    # Determine range
    end_idx = args.end if args.end is not None else len(faculty)
    end_idx = min(end_idx, len(faculty))

    log('INFO', f'Processing profiles {args.start} to {end_idx}')
    log('INFO', f'Delay range: {args.delay_min}-{args.delay_max} seconds')
    log('INFO', f'Max publications per researcher: {args.max_pubs}')
    if args.proxy:
        log('INFO', f'Using proxy: {args.proxy[:30]}...')

    # Load existing output or start fresh
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
    else:
        output_data = faculty[args.start:end_idx]

    # Load progress
    progress = load_progress()
    start_from = progress['last_index'] + 1
    enriched_count = progress['enriched_count']

    if start_from > args.start:
        log('INFO', f'Resuming from index {start_from} ({enriched_count} already enriched)')

    # Browser setup
    browser_args = {
        'headless': False,
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage'
        ]
    }

    if args.proxy:
        browser_args['proxy'] = {'server': args.proxy}

    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_args)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            for i in range(start_from, end_idx):
                relative_idx = i - args.start
                person = faculty[i]
                name = person.get('name', '')

                log('INFO', f'[{i+1}/{end_idx}] Searching: {name}')

                # Skip if already has scholar data
                if person.get('scholar') and person['scholar'].get('publications'):
                    log('INFO', f'  Already enriched, skipping')
                    continue

                # Search
                scholar_data = search_scholar(page, name)

                if scholar_data:
                    output_data[relative_idx]['scholar'] = scholar_data
                    output_data[relative_idx]['h_index'] = scholar_data.get('h_index', 0)
                    output_data[relative_idx]['citation_count'] = scholar_data.get('total_citations', 0)
                    enriched_count += 1

                    log('SUCCESS', f"  Found: h={scholar_data.get('h_index', 0)}, citations={scholar_data.get('total_citations', 0)}, pubs={len(scholar_data.get('publications', []))}")

                # Save progress periodically
                if (i + 1) % 10 == 0:
                    log('INFO', f'Saving progress... ({enriched_count} enriched)')
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)
                    save_progress(i, enriched_count)

                # Random delay
                random_delay()

        except KeyboardInterrupt:
            log('INFO', 'Interrupted by user')
        except Exception as e:
            log('ERROR', f'Fatal error: {e}')
        finally:
            # Final save
            log('INFO', f'Final save... ({enriched_count} enriched)')
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            save_progress(i if 'i' in dir() else args.start, enriched_count)

            browser.close()

    log('INFO', f'Done! {enriched_count} researchers enriched')
    log('INFO', f'Output saved to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
