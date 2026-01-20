#!/usr/bin/env python3
"""
Google Scholar Second Pass - Gets ALL publications for researchers who already have partial data.
Run this after the first pass to complete the publication library.
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
logger.add("output/scholar_pass2.log", level="DEBUG", rotation="10 MB")


def parse_int(text):
    clean = re.sub(r'[^\d]', '', text or '0')
    return int(clean) if clean else 0


def get_publication_details(page, pub_link) -> dict:
    """Click into a publication and extract full details."""
    try:
        pub_link.click()
        time.sleep(random.uniform(1.5, 2.5))

        pub = {}

        title_el = page.locator('#gsc_oci_title')
        if title_el.count() > 0:
            pub['title'] = title_el.inner_text().strip()

        fields = page.locator('.gs_scl')
        for i in range(fields.count()):
            field = fields.nth(i)
            label_el = field.locator('.gsc_oci_field')
            value_el = field.locator('.gsc_oci_value')

            if label_el.count() > 0 and value_el.count() > 0:
                label = label_el.inner_text().strip().lower()
                value = value_el.inner_text().strip()

                if 'authors' in label:
                    pub['authors'] = [a.strip() for a in value.split(',')]
                elif 'publication date' in label:
                    pub['date'] = value
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
                    first_num = re.search(r'^\d+', value.replace(',', ''))
                    pub['citations'] = int(first_num.group(0)) if first_num else 0
                elif 'conference' in label:
                    pub['conference'] = value
                elif 'book' in label:
                    pub['book'] = value

        article_link = page.locator('.gsc_oci_title_link')
        if article_link.count() > 0:
            href = article_link.get_attribute('href')
            if href:
                pub['article_url'] = href
                doi_match = re.search(r'10\.\d{4,}/[^\s]+', href)
                if doi_match:
                    pub['doi'] = doi_match.group(0)

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


def get_remaining_publications(page, scholar_id: str, existing_count: int) -> list:
    """Go directly to a scholar profile and get publications beyond what we have."""
    try:
        url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en&sortby=pubdate"
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(random.uniform(2, 3))

        # Load more publications
        for _ in range(10):  # Try to load all
            show_more = page.locator('#gsc_bpf_more')
            if show_more.count() > 0 and show_more.is_enabled():
                show_more.click()
                time.sleep(random.uniform(1, 2))
            else:
                break

        pub_rows = page.locator('#gsc_a_b .gsc_a_tr')
        total_pubs = pub_rows.count()

        if total_pubs <= existing_count:
            logger.info(f"    No new publications (have {existing_count}, found {total_pubs})")
            return []

        logger.info(f"    Found {total_pubs} total, getting {total_pubs - existing_count} new ones...")

        # Get publications beyond what we already have
        new_publications = []
        for i in range(existing_count, total_pubs):
            pub_rows = page.locator('#gsc_a_b .gsc_a_tr')
            if i >= pub_rows.count():
                break

            row = pub_rows.nth(i)
            title_link = row.locator('.gsc_a_at')

            if title_link.count() > 0:
                basic_title = title_link.inner_text()
                cite_el = row.locator('.gsc_a_c')
                year_el = row.locator('.gsc_a_y')

                pub = get_publication_details(page, title_link)

                if pub:
                    if 'citations' not in pub and cite_el.count() > 0:
                        pub['citations'] = parse_int(cite_el.inner_text())
                    if 'year' not in pub and year_el.count() > 0:
                        year_text = year_el.inner_text().strip()
                        if year_text:
                            pub['year'] = parse_int(year_text)
                    new_publications.append(pub)

            if i < total_pubs - 1:
                time.sleep(random.uniform(0.5, 1))

        return new_publications

    except Exception as e:
        logger.warning(f"Error getting remaining pubs: {e}")
        return []


def second_pass(input_file: str, output_file: str):
    """Get remaining publications for researchers with partial data."""
    logger.info(f"Loading faculty data from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        faculty_data = json.load(f)

    # Find researchers with scholar data but potentially incomplete pubs
    candidates = [
        (i, f) for i, f in enumerate(faculty_data)
        if f.get('google_scholar_id') and f.get('scholar')
    ]

    logger.info(f"Found {len(candidates)} researchers with Scholar IDs")

    updated = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(
            viewport={'width': 1400, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        for idx, (i, faculty) in enumerate(candidates):
            name = faculty.get('name', 'Unknown')
            scholar_id = faculty['google_scholar_id']
            existing_pubs = len(faculty.get('scholar', {}).get('publications', []))

            logger.info(f"[{idx+1}/{len(candidates)}] {name} (has {existing_pubs} pubs)")

            new_pubs = get_remaining_publications(page, scholar_id, existing_pubs)

            if new_pubs:
                faculty['scholar']['publications'].extend(new_pubs)
                faculty['scholar']['publication_count'] = len(faculty['scholar']['publications'])
                updated += 1
                logger.success(f"    Added {len(new_pubs)} new publications")

            time.sleep(random.uniform(2, 4))

            # Save progress every 10
            if (idx + 1) % 10 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(faculty_data, f, indent=2, ensure_ascii=False)

        browser.close()

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(faculty_data, f, indent=2, ensure_ascii=False)

    logger.info("=" * 50)
    logger.info(f"SECOND PASS COMPLETE - Updated {updated} researchers")
    logger.info("=" * 50)


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'output/faculty_library.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output/faculty_library.json'
    second_pass(input_file, output_file)
