#!/usr/bin/env python3
"""
Google Scholar Enrichment with NordVPN Server Rotation
Automatically rotates through different VPN servers to avoid rate limiting.
"""

import json
import time
import random
import re
import subprocess
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, 'output', 'faculty_fixed.json')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'output', 'faculty_library.json')
PROGRESS_FILE = os.path.join(SCRIPT_DIR, 'output', 'progress_vpn.json')
SCREENSHOTS_DIR = os.path.join(SCRIPT_DIR, 'output', 'screenshots')

NORDVPN_PATH = r"C:\Program Files\NordVPN\NordVPN.exe"

# Rotate through these locations
VPN_LOCATIONS = [
    "United States",
    "Canada",
    "United Kingdom",
    "Germany",
    "Netherlands",
    "France",
    "Switzerland",
    "Sweden",
    "Australia",
    "Japan"
]

# Settings
ROTATE_EVERY = 30  # Switch VPN every N searches
DELAY_MIN = 10
DELAY_MAX = 18
MAX_PUBS = 30
CAPTCHA_WAIT = 120  # Seconds to wait when CAPTCHA detected

def log(level, msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{timestamp} | {level} | {msg}")


def ensure_screenshots_dir():
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)
        log('INFO', f'Created screenshots directory: {SCREENSHOTS_DIR}')

def sanitize_filename(name):
    return re.sub(r'[<>:"/\|?*]', '_', name)[:50]

def take_screenshot(page, name, screenshot_type):
    try:
        ensure_screenshots_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = sanitize_filename(name)
        filename = f"{timestamp}_{screenshot_type}_{safe_name}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        page.screenshot(path=filepath, full_page=True)
        log('SCREENSHOT', f'Saved: {filename}')
        return filepath
    except Exception as e:
        log('ERROR', f'Screenshot failed: {e}')
        return None

def connect_vpn(location):
    """Connect to NordVPN server in specified location."""
    log('VPN', f'Connecting to {location}...')
    try:
        # Disconnect first
        subprocess.run([NORDVPN_PATH, '-d'], capture_output=True, timeout=10)
        time.sleep(3)

        # Connect to new location
        result = subprocess.run(
            [NORDVPN_PATH, '-c', '-g', location],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Wait for connection
        time.sleep(8)
        log('VPN', f'Connected to {location}')
        return True

    except subprocess.TimeoutExpired:
        log('ERROR', f'VPN connection timeout')
        return False
    except Exception as e:
        log('ERROR', f'VPN error: {e}')
        return False

def disconnect_vpn():
    """Disconnect from NordVPN."""
    try:
        subprocess.run([NORDVPN_PATH, '-d'], capture_output=True, timeout=10)
        log('VPN', 'Disconnected')
    except:
        pass

def random_delay():
    delay = random.uniform(DELAY_MIN, DELAY_MAX)
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

        # DOI
        links = page.query_selector_all('.gsc_oci_title_ggi a, .gsc_oci_value a')
        for link in links:
            href = link.get_attribute('href') or ''
            if 'doi.org' in href:
                doi_match = re.search(r'doi\.org/(.+?)(?:\?|$)', href)
                if doi_match:
                    details['doi'] = doi_match.group(1)
                break

        # Year
        all_text = page.inner_text()
        year_match = re.search(r'\b(19|20)\d{2}\b', all_text)
        if year_match:
            details['year'] = int(year_match.group())

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

def check_for_captcha(page):
    """Check if page shows CAPTCHA."""
    if 'sorry' in page.url.lower():
        return True
    if page.query_selector('form[action*="sorry"]'):
        return True
    if page.query_selector('#captcha-form'):
        return True
    return False

def search_scholar(page, name: str) -> dict:
    """Search for a researcher on Google Scholar."""
    try:
        search_url = f"https://scholar.google.com/scholar?q=author:%22{name.replace(' ', '+')}%22"
        page.goto(search_url, timeout=30000)
        time.sleep(2 + random.random())

        # Check for CAPTCHA
        if check_for_captcha(page):
            take_screenshot(page, name, 'captcha')
            return 'CAPTCHA'

        # Look for author profile link
        profile_links = page.query_selector_all('a[href*="/citations?user="]')

        if not profile_links:
            return None

        # Click first profile
        profile_link = profile_links[0]
        profile_link.click()
        time.sleep(2 + random.random())

        # Check for CAPTCHA again
        if check_for_captcha(page):
            take_screenshot(page, name, 'captcha')
            return 'CAPTCHA'

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
        num_pubs = min(len(pub_links), MAX_PUBS)

        if num_pubs > 0:
            log('INFO', f"    Extracting {num_pubs} publications...")

        for i in range(num_pubs):
            try:
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
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_index': -1, 'enriched_count': 0, 'vpn_index': 0}

def save_progress(index, enriched_count, vpn_index):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'last_index': index, 'enriched_count': enriched_count, 'vpn_index': vpn_index}, f)

def main():
    log('INFO', f'Loading faculty data from {INPUT_FILE}')

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        faculty = json.load(f)

    # Load existing output or use input as base
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
    else:
        output_data = faculty.copy()

    # Load progress
    progress = load_progress()
    start_from = progress['last_index'] + 1
    enriched_count = progress['enriched_count']
    vpn_index = progress['vpn_index']

    log('INFO', f'Total profiles: {len(faculty)}')
    log('INFO', f'Starting from: {start_from}')
    log('INFO', f'Already enriched: {enriched_count}')
    log('INFO', f'Rotating VPN every {ROTATE_EVERY} searches')

    # Initial VPN connection
    current_location = VPN_LOCATIONS[vpn_index % len(VPN_LOCATIONS)]
    if not connect_vpn(current_location) and False:
        log('ERROR', 'Failed to connect to VPN. Please connect manually.')
        return

    searches_since_rotate = 0
    captcha_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox'
            ]
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            for i in range(start_from, len(faculty)):
                person = faculty[i]
                name = person.get('name', '')

                log('INFO', f'[{i+1}/{len(faculty)}] Searching: {name}')

                # Skip if already has scholar data
                if output_data[i].get('scholar') and output_data[i]['scholar'].get('publications'):
                    log('INFO', f'  Already enriched, skipping')
                    continue

                # Search
                scholar_data = search_scholar(page, name)

                # Handle CAPTCHA
                if scholar_data == 'CAPTCHA':
                    log('WARNING', f'CAPTCHA detected! Rotating VPN...')
                    captcha_count += 1

                    # Close browser, rotate VPN, reopen
                    browser.close()

                    vpn_index += 1
                    current_location = VPN_LOCATIONS[vpn_index % len(VPN_LOCATIONS)]

                    if not connect_vpn(current_location) and False:
                        log('ERROR', 'VPN rotation failed. Waiting...')
                        time.sleep(CAPTCHA_WAIT)
                        connect_vpn(current_location)

                    # Reopen browser
                    browser = p.chromium.launch(
                        headless=False,
                        args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                    )
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    )
                    page = context.new_page()

                    searches_since_rotate = 0

                    # Retry this search
                    time.sleep(5)
                    scholar_data = search_scholar(page, name)
                    if scholar_data == 'CAPTCHA':
                        log('ERROR', 'Still getting CAPTCHA. Skipping...')
                        scholar_data = None

                if scholar_data and scholar_data != 'CAPTCHA':
                    output_data[i]['scholar'] = scholar_data
                    output_data[i]['h_index'] = scholar_data.get('h_index', 0)
                    output_data[i]['citation_count'] = scholar_data.get('total_citations', 0)
                    enriched_count += 1

                    log('SUCCESS', f"  Found: h={scholar_data.get('h_index', 0)}, citations={scholar_data.get('total_citations', 0)}, pubs={len(scholar_data.get('publications', []))}")

                searches_since_rotate += 1

                # Rotate VPN periodically
                if searches_since_rotate >= ROTATE_EVERY:
                    log('VPN', f'Rotating VPN (every {ROTATE_EVERY} searches)...')

                    browser.close()

                    vpn_index += 1
                    current_location = VPN_LOCATIONS[vpn_index % len(VPN_LOCATIONS)]
                    connect_vpn(current_location)

                    browser = p.chromium.launch(
                        headless=False,
                        args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                    )
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    )
                    page = context.new_page()

                    searches_since_rotate = 0

                # Save progress
                if (i + 1) % 10 == 0:
                    log('INFO', f'Saving progress... ({enriched_count} enriched, {captcha_count} CAPTCHAs)')
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)
                    save_progress(i, enriched_count, vpn_index)

                random_delay()

        except KeyboardInterrupt:
            log('INFO', 'Interrupted by user')
        except Exception as e:
            log('ERROR', f'Fatal error: {e}')
        finally:
            log('INFO', f'Final save... ({enriched_count} enriched)')
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            save_progress(i if 'i' in dir() else start_from, enriched_count, vpn_index)

            browser.close()
            disconnect_vpn()

    log('INFO', f'Done! {enriched_count} researchers enriched')
    log('INFO', f'CAPTCHAs encountered: {captcha_count}')

if __name__ == '__main__':
    main()
