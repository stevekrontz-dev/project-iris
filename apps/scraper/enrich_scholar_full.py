#!/usr/bin/env python3
"""
Google Scholar Full Enrichment - Captures complete publication library.
Clicks into each publication to get full details.
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
logger.add("output/scholar_full.log", level="DEBUG", rotation="10 MB")


def parse_int(text):
    """Parse integer from text, handling commas and special chars."""
    clean = re.sub(r'[^\d]', '', text or '0')
    return int(clean) if clean else 0


def get_publication_details(page, pub_link) -> dict:
    """Click into a publication and extract full details."""
    try:
        pub_link.click()
        time.sleep(random.uniform(1.5, 2.5))

        pub = {}

        # Title
        title_el = page.locator('#gsc_oci_title')
        if title_el.count() > 0:
            pub['title'] = title_el.inner_text().strip()

        # Get all the field rows
        fields = page.locator('.gs_scl')
        for i in range(fields.count()):
            field = fields.nth(i)
            label_el = field.locator('.gsc_oci_field')
            value_el = field.locator('.gsc_oci_value')

            if label_el.count() > 0 and value_el.count() > 0:
                label = label_el.inner_text().strip().lower()
                value = value_el.inner_text().strip()

                if 'authors' in label:
                    # Split authors into list
                    pub['authors'] = [a.strip() for a in value.split(',')]
                elif 'publication date' in label:
                    pub['date'] = value
                    # Extract year
                    year_match = re.search(r'(\d{4})', value)
                    if year_match:
                        pub['year'] = int(year_match.group(1))
                elif 'journal' in label:
                    pub['journal'] = value
                elif 'volume' in label:
                    pub['volume'] = value
                elif 'issue' in label:
                    pub['issue'] = value
                elif 'pages' in label:
                    pub['pages'] = value
                elif 'publisher' in label:
                    pub['publisher'] = value
                elif 'description' in label or 'abstract' in label:
                    pub['abstract'] = value
                elif 'total citations' in label:
                    # Just get the first number (total), ignore yearly breakdown
                    first_num = re.search(r'^\d+', value.replace(',', ''))
                    pub['citations'] = int(first_num.group(0)) if first_num else 0
                elif 'conference' in label:
                    pub['conference'] = value
                elif 'book' in label:
                    pub['book'] = value

        # Try to get DOI or article link
        article_link = page.locator('.gsc_oci_title_link')
        if article_link.count() > 0:
            href = article_link.get_attribute('href')
            if href:
                pub['article_url'] = href
                # Extract DOI if present
                doi_match = re.search(r'10\.\d{4,}/[^\s]+', href)
                if doi_match:
                    pub['doi'] = doi_match.group(0)

        # Go back to profile
        page.go_back()
        time.sleep(random.uniform(1, 2))

        return pub

    except Exception as e:
        logger.debug(f"Error getting pub details: {e}")
        try:
            page.go_back()
            time.sleep(1)
        except:
            pass
        return None


def extract_scholar_data(page, name: str, max_pubs: int = 0) -> dict | None:
    """Search Google Scholar and extract full author data with publications."""
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
        if author_link.count() == 0:
            logger.debug(f"No profile found for {name}")
            return None

        author_link.click()
        time.sleep(random.uniform(2, 3))

        data = {}

        # Name
        name_el = page.locator('#gsc_prf_in')
        if name_el.count() > 0:
            data['name'] = name_el.inner_text()

        # Affiliation
        aff_el = page.locator('.gsc_prf_il')
        if aff_el.count() > 0:
            data['affiliation'] = aff_el.first.inner_text()

        # Interests/keywords
        interests = page.locator('#gsc_prf_int a')
        data['interests'] = [i.inner_text() for i in interests.all()]

        # Citation metrics
        metrics = page.locator('#gsc_rsb_st td.gsc_rsb_std')
        if metrics.count() >= 3:
            data['citedby'] = parse_int(metrics.nth(0).inner_text())
            data['h_index'] = parse_int(metrics.nth(2).inner_text())
            data['i10_index'] = parse_int(metrics.nth(4).inner_text())

        # Scholar ID from URL
        url = page.url
        match = re.search(r'user=([^&]+)', url)
        if match:
            data['scholar_id'] = match.group(1)
            data['profile_url'] = f"https://scholar.google.com/citations?user={match.group(1)}"

        # Load more publications if available (click "Show more" button)
        for _ in range(3):  # Try up to 3 times to load more
            show_more = page.locator('#gsc_bpf_more')
            if show_more.count() > 0 and show_more.is_enabled():
                show_more.click()
                time.sleep(random.uniform(1, 2))
            else:
                break

        # Get ALL publications with full details
        publications = []
        pub_rows = page.locator('#gsc_a_b .gsc_a_tr')
        pub_count = pub_rows.count() if max_pubs == 0 else min(max_pubs, pub_rows.count())

        logger.info(f"    Extracting {pub_count} publications...")

        for i in range(pub_count):
            # Re-query the rows each time (DOM might have changed)
            pub_rows = page.locator('#gsc_a_b .gsc_a_tr')
            if i >= pub_rows.count():
                break

            row = pub_rows.nth(i)
            title_link = row.locator('.gsc_a_at')

            if title_link.count() > 0:
                # Get basic info first
                basic_title = title_link.inner_text()
                cite_el = row.locator('.gsc_a_c')
                year_el = row.locator('.gsc_a_y')

                # Click into publication for full details
                pub = get_publication_details(page, title_link)

                if pub:
                    # Add citation count from list view if not in details
                    if 'citations' not in pub and cite_el.count() > 0:
                        pub['citations'] = parse_int(cite_el.inner_text())
                    if 'year' not in pub and year_el.count() > 0:
                        year_text = year_el.inner_text().strip()
                        if year_text:
                            pub['year'] = parse_int(year_text)
                    publications.append(pub)
                else:
                    # Fallback to basic info
                    publications.append({
                        'title': basic_title,
                        'citations': parse_int(cite_el.inner_text()) if cite_el.count() > 0 else 0,
                        'year': parse_int(year_el.inner_text()) if year_el.count() > 0 else None
                    })

            # Small delay between publications
            if i < pub_count - 1:
                time.sleep(random.uniform(0.5, 1))

        data['publications'] = publications
        data['publication_count'] = len(publications)

        return data

    except PlaywrightTimeout:
        logger.warning(f"Timeout searching for {name}")
        return None
    except Exception as e:
        logger.warning(f"Error searching for {name}: {e}")
        return None


def enrich_faculty(input_file: str, output_file: str, start_idx: int = 0, max_count: int = 0, max_pubs: int = 0):
    """Enrich faculty data with full publication library."""
    logger.info(f"Loading faculty data from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        faculty_data = json.load(f)

    total = len(faculty_data)
    end_idx = total if max_count == 0 else min(start_idx + max_count, total)

    logger.info(f"Processing profiles {start_idx} to {end_idx}")
    logger.info(f"Max publications per researcher: {max_pubs}")

    enriched = 0
    not_found = 0
    errors = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=50
        )
        context = browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        for i in range(start_idx, end_idx):
            faculty = faculty_data[i]

            # Build name
            name = faculty.get('name', '')
            if not name or name == 'KSU' or len(name.split()) < 2:
                first = faculty.get('first_name', '')
                last = faculty.get('last_name', '')
                if first and last:
                    name = f"{first} {last}"

            if not name or len(name) < 3:
                not_found += 1
                continue

            # Skip if already has full enrichment
            if faculty.get('scholar') and len(faculty.get('scholar', {}).get('publications', [])) > 5:
                if faculty['scholar']['publications'][0].get('authors'):
                    logger.debug(f"[{i+1}/{end_idx}] Skipping {name} - already fully enriched")
                    continue

            logger.info(f"[{i+1}/{end_idx}] Searching: {name}")

            try:
                scholar_data = extract_scholar_data(page, name, max_pubs)

                if scholar_data and scholar_data.get('h_index', 0) > 0:
                    faculty['scholar'] = scholar_data
                    faculty['h_index'] = scholar_data.get('h_index', 0)
                    faculty['citation_count'] = scholar_data.get('citedby', 0)
                    faculty['google_scholar_id'] = scholar_data.get('scholar_id')
                    enriched += 1
                    pub_count = len(scholar_data.get('publications', []))
                    logger.success(f"  Found: h={scholar_data.get('h_index')}, citations={scholar_data.get('citedby')}, pubs={pub_count}")
                else:
                    not_found += 1
                    logger.debug(f"  Not found")

                # Delay between researchers
                time.sleep(random.uniform(2, 5))

            except Exception as e:
                errors += 1
                logger.error(f"  Error: {e}")
                time.sleep(5)

            # Save progress every 10 profiles (more frequent due to more data)
            if (i + 1) % 10 == 0:
                logger.info(f"Saving progress... ({enriched} enriched)")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(faculty_data, f, indent=2, ensure_ascii=False)

        browser.close()

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(faculty_data, f, indent=2, ensure_ascii=False)

    logger.info("=" * 50)
    logger.info("FULL ENRICHMENT COMPLETE")
    logger.info(f"  Processed: {end_idx - start_idx}")
    logger.info(f"  Enriched: {enriched}")
    logger.info(f"  Not found: {not_found}")
    logger.info(f"  Errors: {errors}")
    logger.info("=" * 50)


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'output/faculty_fixed.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output/faculty_enriched.json'
    start_idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    max_count = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    max_pubs = int(sys.argv[5]) if len(sys.argv) > 5 else 50

    enrich_faculty(input_file, output_file, start_idx, max_count, max_pubs)
