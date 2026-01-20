#!/usr/bin/env python3
"""
Fix faculty names by re-scraping from profile URLs.
"""

import json
import re
import time
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

def extract_name_from_page(url: str) -> tuple[str, str, str]:
    """Extract name from faculty profile page."""
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'lxml')

        # Try h1 or h2 with name
        for tag in soup.find_all(['h1', 'h2']):
            text = tag.get_text(strip=True)
            # Remove Dr., Prof., etc.
            text = re.sub(r'^(Dr\.?|Prof\.?|Professor)\s*', '', text, flags=re.I)
            # Check if it looks like a name (2+ words, no common page titles)
            if text and len(text.split()) >= 2 and 'KSU' not in text and 'Kennesaw' not in text:
                parts = text.split()
                first = parts[0]
                last = parts[-1] if len(parts) > 1 else ''
                return text, first, last

        # Try title tag
        title = soup.find('title')
        if title:
            text = title.get_text(strip=True)
            text = re.sub(r'^(Dr\.?|Prof\.?|Professor)\s*', '', text, flags=re.I)
            text = re.sub(r'\s*[-|]\s*.*$', '', text)  # Remove after dash or pipe
            if text and len(text.split()) >= 2 and 'KSU' not in text:
                parts = text.split()
                first = parts[0]
                last = parts[-1] if len(parts) > 1 else ''
                return text, first, last

        return None, None, None
    except Exception as e:
        logger.debug(f"Error fetching {url}: {e}")
        return None, None, None


def fix_names(input_file: str, output_file: str):
    """Fix names in faculty data."""
    logger.info(f"Loading {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)
    fixed = 0
    failed = 0

    for i, profile in enumerate(data):
        current_name = profile.get('name', '')

        # Skip if name already looks good
        if current_name and current_name != 'KSU' and len(current_name.split()) >= 2:
            continue

        url = profile.get('profile_url')
        if not url:
            failed += 1
            continue

        logger.info(f"[{i+1}/{total}] Fetching: {url}")
        name, first, last = extract_name_from_page(url)

        if name:
            profile['name'] = name
            profile['first_name'] = first
            profile['last_name'] = last
            fixed += 1
            logger.success(f"  -> {name}")
        else:
            failed += 1
            logger.warning(f"  -> Could not extract name")

        # Rate limit
        time.sleep(0.3)

        # Save progress every 100
        if (i + 1) % 100 == 0:
            logger.info(f"Saving progress... ({fixed} fixed)")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info("=" * 50)
    logger.info(f"Fixed: {fixed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Output: {output_file}")


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'output/faculty_all.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output/faculty_fixed.json'
    fix_names(input_file, output_file)
