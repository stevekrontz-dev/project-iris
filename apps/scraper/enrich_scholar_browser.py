#!/usr/bin/env python3
"""
Google Scholar Enrichment using Playwright (Browser Automation)
Bypasses anti-bot protection by using a real browser.
"""

import json
import re
import time
import sys
import random
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add("output/scholar_browser.log", level="DEBUG", rotation="10 MB")


def extract_scholar_data(page, name: str) -> dict | None:
    """Search Google Scholar and extract author data."""
    try:
        # Go to Google Scholar
        page.goto("https://scholar.google.com/", wait_until="networkidle", timeout=30000)
        time.sleep(random.uniform(1, 2))

        # Search for author
        search_query = f'author:"{name}" Kennesaw State'
        search_box = page.locator('input[name="q"]')
        search_box.fill(search_query)
        search_box.press("Enter")

        time.sleep(random.uniform(2, 4))

        # Look for author profile link
        author_link = page.locator('h4.gs_rt2 a').first
        if author_link.count() > 0:
            author_link.click()
            time.sleep(random.uniform(2, 3))

            # Extract data from profile page
            data = {}

            # Name
            name_el = page.locator('#gsc_prf_in')
            if name_el.count() > 0:
                data['name'] = name_el.inner_text()

            # Affiliation
            aff_el = page.locator('.gsc_prf_il')
            if aff_el.count() > 0:
                data['affiliation'] = aff_el.first.inner_text()

            # Interests
            interests = page.locator('#gsc_prf_int a')
            data['interests'] = [i.inner_text() for i in interests.all()]

            # Citation metrics (h-index, i10-index, total citations)
            metrics = page.locator('#gsc_rsb_st td.gsc_rsb_std')
            if metrics.count() >= 3:
                def parse_int(text):
                    # Remove commas, asterisks, newlines, and other non-numeric chars
                    clean = re.sub(r'[^\d]', '', text or '0')
                    return int(clean) if clean else 0
                data['citedby'] = parse_int(metrics.nth(0).inner_text())
                data['h_index'] = parse_int(metrics.nth(2).inner_text())
                data['i10_index'] = parse_int(metrics.nth(4).inner_text())

            # Get scholar ID from URL
            url = page.url
            match = re.search(r'user=([^&]+)', url)
            if match:
                data['scholar_id'] = match.group(1)

            # Get top publications
            pubs = []
            pub_rows = page.locator('#gsc_a_b .gsc_a_tr')
            for i in range(min(10, pub_rows.count())):
                row = pub_rows.nth(i)
                title_el = row.locator('.gsc_a_at')
                cite_el = row.locator('.gsc_a_c')
                year_el = row.locator('.gsc_a_y')

                pub = {
                    'title': title_el.inner_text() if title_el.count() > 0 else '',
                    'citations': int(cite_el.inner_text() or 0) if cite_el.count() > 0 else 0,
                    'year': year_el.inner_text() if year_el.count() > 0 else ''
                }
                if pub['title']:
                    pubs.append(pub)

            data['publications'] = pubs
            return data

        # No profile found, try to get data from search results
        logger.debug(f"No profile found for {name}, checking search results")
        return None

    except PlaywrightTimeout:
        logger.warning(f"Timeout searching for {name}")
        return None
    except Exception as e:
        logger.warning(f"Error searching for {name}: {e}")
        return None


def enrich_faculty(input_file: str, output_file: str, start_idx: int = 0, max_count: int = 0):
    """Enrich faculty data using browser automation."""
    logger.info(f"Loading faculty data from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        faculty_data = json.load(f)

    total = len(faculty_data)
    if max_count > 0:
        total = min(start_idx + max_count, total)

    logger.info(f"Processing profiles {start_idx} to {total}")

    enriched = 0
    not_found = 0
    errors = 0

    with sync_playwright() as p:
        # Launch browser (non-headless to look more human)
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100  # Slow down actions to look human
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        for i in range(start_idx, total):
            faculty = faculty_data[i]

            # Build name for search
            name = faculty.get('name', '')
            if not name or name == 'KSU' or len(name.split()) < 2:
                first = faculty.get('first_name', '')
                last = faculty.get('last_name', '')
                if first and last:
                    name = f"{first} {last}"

            if not name or len(name) < 3:
                not_found += 1
                continue

            # Skip if already enriched
            if faculty.get('scholar') and faculty.get('h_index', 0) > 0:
                logger.debug(f"[{i+1}/{total}] Skipping {name} - already enriched")
                continue

            logger.info(f"[{i+1}/{total}] Searching: {name}")

            try:
                scholar_data = extract_scholar_data(page, name)

                if scholar_data and scholar_data.get('h_index', 0) > 0:
                    faculty['scholar'] = scholar_data
                    faculty['h_index'] = scholar_data.get('h_index', 0)
                    faculty['citation_count'] = scholar_data.get('citedby', 0)
                    faculty['google_scholar_id'] = scholar_data.get('scholar_id')
                    enriched += 1
                    logger.success(f"  Found: h-index={scholar_data.get('h_index')}, citations={scholar_data.get('citedby')}")
                else:
                    not_found += 1
                    logger.debug(f"  Not found on Google Scholar")

                # Random delay between searches (3-8 seconds)
                delay = random.uniform(3, 8)
                time.sleep(delay)

            except Exception as e:
                errors += 1
                logger.error(f"  Error: {e}")
                time.sleep(5)

            # Save progress every 25 profiles
            if (i + 1) % 25 == 0:
                logger.info(f"Saving progress... ({enriched} enriched so far)")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(faculty_data, f, indent=2, ensure_ascii=False)

        browser.close()

    # Final save
    logger.info(f"Saving final output to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(faculty_data, f, indent=2, ensure_ascii=False)

    # Summary
    logger.info("=" * 50)
    logger.info("ENRICHMENT COMPLETE")
    logger.info(f"  Processed: {total - start_idx}")
    logger.info(f"  Enriched: {enriched}")
    logger.info(f"  Not found: {not_found}")
    logger.info(f"  Errors: {errors}")
    logger.info("=" * 50)


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'output/faculty_fixed.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output/faculty_enriched.json'
    start_idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    max_count = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    enrich_faculty(input_file, output_file, start_idx, max_count)
