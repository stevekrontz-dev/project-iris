#!/usr/bin/env python3
"""
Google Scholar Enrichment Script for Project IRIS

Enriches faculty data with Google Scholar metrics:
- h-index
- Citation count
- Recent publications

Usage:
    python enrich_scholar.py input.json output.json [--max-pubs 20] [--delay 2]
"""

import json
import argparse
import time
import sys
from pathlib import Path
from typing import Optional

try:
    from scholarly import scholarly
except ImportError:
    print("Installing scholarly library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scholarly"])
    from scholarly import scholarly

from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add("output/enrichment.log", level="DEBUG", rotation="10 MB")


def search_scholar(name: str, affiliation: str = "Kennesaw State") -> Optional[dict]:
    """
    Search Google Scholar for a faculty member.
    Returns scholar data or None if not found.
    """
    try:
        # Search with name and affiliation
        query = f"{name} {affiliation}"
        search_query = scholarly.search_author(query)

        # Get first result
        author = next(search_query, None)
        if not author:
            return None

        # Fill in detailed info
        author = scholarly.fill(author, sections=['basics', 'indices', 'publications'])

        return {
            'scholar_id': author.get('scholar_id'),
            'name': author.get('name'),
            'affiliation': author.get('affiliation', ''),
            'interests': author.get('interests', []),
            'citedby': author.get('citedby', 0),
            'h_index': author.get('hindex', 0),
            'i10_index': author.get('i10index', 0),
            'publications': [
                {
                    'title': pub.get('bib', {}).get('title', ''),
                    'year': pub.get('bib', {}).get('pub_year', ''),
                    'citations': pub.get('num_citations', 0),
                    'venue': pub.get('bib', {}).get('venue', ''),
                }
                for pub in author.get('publications', [])[:20]  # Limit publications
            ]
        }
    except StopIteration:
        return None
    except Exception as e:
        logger.warning(f"Scholar search error for {name}: {e}")
        return None


def enrich_faculty(input_file: str, output_file: str, max_pubs: int = 20, delay: float = 2.0):
    """
    Enrich faculty data with Google Scholar information.
    """
    # Load input data
    logger.info(f"Loading faculty data from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        faculty_data = json.load(f)

    total = len(faculty_data)
    logger.info(f"Processing {total} faculty profiles")

    enriched = 0
    not_found = 0
    errors = 0

    for i, faculty in enumerate(faculty_data):
        # Build name for search
        name = faculty.get('name', '')
        if not name or name == 'KSU':
            first = faculty.get('first_name', '')
            last = faculty.get('last_name', '')
            if first and last:
                name = f"{first} {last}"

        if not name or len(name) < 3:
            not_found += 1
            continue

        logger.info(f"[{i+1}/{total}] Searching: {name}")

        try:
            scholar_data = search_scholar(name)

            if scholar_data:
                faculty['scholar'] = scholar_data
                faculty['h_index'] = scholar_data.get('h_index', 0)
                faculty['citation_count'] = scholar_data.get('citedby', 0)
                faculty['google_scholar_id'] = scholar_data.get('scholar_id')
                enriched += 1
                logger.success(f"  Found: h-index={scholar_data.get('h_index')}, citations={scholar_data.get('citedby')}")
            else:
                not_found += 1
                logger.debug(f"  Not found on Google Scholar")

            # Rate limiting
            time.sleep(delay)

        except Exception as e:
            errors += 1
            logger.error(f"  Error: {e}")
            time.sleep(delay * 2)  # Extra delay on error

        # Save progress every 50 profiles
        if (i + 1) % 50 == 0:
            logger.info(f"Saving progress... ({enriched} enriched so far)")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(faculty_data, f, indent=2, ensure_ascii=False)

    # Final save
    logger.info(f"Saving final output to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(faculty_data, f, indent=2, ensure_ascii=False)

    # Summary
    logger.info("=" * 50)
    logger.info("ENRICHMENT COMPLETE")
    logger.info(f"  Total profiles: {total}")
    logger.info(f"  Enriched: {enriched}")
    logger.info(f"  Not found: {not_found}")
    logger.info(f"  Errors: {errors}")
    logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description='Enrich faculty data with Google Scholar info')
    parser.add_argument('input', help='Input JSON file')
    parser.add_argument('output', help='Output JSON file')
    parser.add_argument('--max-pubs', type=int, default=20, help='Max publications per faculty')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')

    args = parser.parse_args()

    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    enrich_faculty(args.input, args.output, args.max_pubs, args.delay)


if __name__ == '__main__':
    main()
