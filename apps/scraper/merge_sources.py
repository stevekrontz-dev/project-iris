#!/usr/bin/env python3
"""
Merge all enrichment sources into a single faculty dataset.
Combines: Google Scholar (VPN scraper) + OpenAlex + Semantic Scholar + ORCID
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')

# Source files
GOOGLE_SCHOLAR_FILE = os.path.join(OUTPUT_DIR, 'faculty_library.json')
API_ENRICHED_FILE = os.path.join(OUTPUT_DIR, 'faculty_api_enriched.json')
MERGED_OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'faculty_merged.json')


def log(msg: str):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{timestamp} | {msg}")


def dedupe_publications(pubs: List[Dict]) -> List[Dict]:
    """Remove duplicate publications by DOI or title."""
    seen_dois = set()
    seen_titles = set()
    unique = []

    for pub in pubs:
        doi = pub.get('doi')
        title = (pub.get('title') or '').lower().strip()

        # Skip if we've seen this DOI
        if doi and doi in seen_dois:
            continue

        # Skip if we've seen this title (fuzzy match)
        if title and any(title in t or t in title for t in seen_titles):
            continue

        unique.append(pub)
        if doi:
            seen_dois.add(doi)
        if title:
            seen_titles.add(title)

    return unique


def merge_faculty_record(base: Dict, overlay: Dict) -> Dict:
    """Merge two faculty records, taking best data from each."""
    merged = base.copy()

    # Take higher h-index
    base_h = base.get('h_index') or base.get('scholar', {}).get('h_index') or 0
    overlay_h = overlay.get('h_index') or overlay.get('scholar', {}).get('h_index') or 0
    merged['h_index'] = max(base_h, overlay_h)

    # Take higher citation count
    base_cites = base.get('citation_count') or base.get('scholar', {}).get('total_citations') or 0
    overlay_cites = overlay.get('citation_count') or overlay.get('scholar', {}).get('total_citations') or 0
    merged['citation_count'] = max(base_cites, overlay_cites)

    # Merge scholar objects
    base_scholar = base.get('scholar') or {}
    overlay_scholar = overlay.get('scholar') or {}

    if base_scholar or overlay_scholar:
        merged_scholar = {}

        # Take non-empty values, preferring higher metrics
        for key in ['scholar_id', 'name', 'affiliation']:
            merged_scholar[key] = overlay_scholar.get(key) or base_scholar.get(key) or ''

        # Merge interests
        base_interests = set(base_scholar.get('interests') or [])
        overlay_interests = set(overlay_scholar.get('interests') or [])
        merged_scholar['interests'] = list(base_interests | overlay_interests)[:15]

        # Take higher metrics
        merged_scholar['h_index'] = max(
            base_scholar.get('h_index') or 0,
            overlay_scholar.get('h_index') or 0
        )
        merged_scholar['i10_index'] = max(
            base_scholar.get('i10_index') or 0,
            overlay_scholar.get('i10_index') or 0
        )
        merged_scholar['total_citations'] = max(
            base_scholar.get('total_citations') or base_scholar.get('citedby') or 0,
            overlay_scholar.get('total_citations') or overlay_scholar.get('citedby') or 0
        )

        # Merge publications
        base_pubs = base_scholar.get('publications') or []
        overlay_pubs = overlay_scholar.get('publications') or []
        all_pubs = base_pubs + overlay_pubs

        # Sort by citations, then year
        all_pubs.sort(key=lambda p: (-(p.get('citations') or 0), -(p.get('year') or 0)))

        # Dedupe and limit
        merged_scholar['publications'] = dedupe_publications(all_pubs)[:50]
        merged_scholar['publication_count'] = len(merged_scholar['publications'])

        merged['scholar'] = merged_scholar

    # Track all sources
    base_sources = set(base.get('api_sources') or [])
    overlay_sources = set(overlay.get('api_sources') or [])

    # Check for Google Scholar data
    if base.get('google_scholar_id') or base_scholar.get('scholar_id', '').startswith('uk'):
        base_sources.add('google_scholar')
    if overlay.get('google_scholar_id') or overlay_scholar.get('scholar_id', '').startswith('uk'):
        overlay_sources.add('google_scholar')

    merged['sources'] = list(base_sources | overlay_sources)

    return merged


def load_json_safe(filepath: str) -> List[Dict]:
    """Load JSON file, return empty list if not found."""
    if not os.path.exists(filepath):
        log(f"File not found: {filepath}")
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading {filepath}: {e}")
        return []


def main():
    log("=" * 60)
    log("IRIS Faculty Data Merger")
    log("=" * 60)

    # Load all sources
    log(f"Loading Google Scholar data: {GOOGLE_SCHOLAR_FILE}")
    gs_data = load_json_safe(GOOGLE_SCHOLAR_FILE)
    log(f"  Loaded {len(gs_data)} records")

    log(f"Loading API enriched data: {API_ENRICHED_FILE}")
    api_data = load_json_safe(API_ENRICHED_FILE)
    log(f"  Loaded {len(api_data)} records")

    if not gs_data and not api_data:
        log("ERROR: No data to merge!")
        sys.exit(1)

    # Use larger dataset as base
    if len(gs_data) >= len(api_data):
        base_data = gs_data
        overlay_data = api_data
        log("Using Google Scholar as base")
    else:
        base_data = api_data
        overlay_data = gs_data
        log("Using API enriched as base")

    # Build lookup by net_id
    overlay_by_id = {r.get('net_id'): r for r in overlay_data if r.get('net_id')}

    # Merge records
    merged_data = []
    stats = {
        'total': 0,
        'with_scholar': 0,
        'with_publications': 0,
        'sources': {}
    }

    for record in base_data:
        net_id = record.get('net_id')
        overlay = overlay_by_id.get(net_id, {})

        merged = merge_faculty_record(record, overlay)
        merged_data.append(merged)

        # Track stats
        stats['total'] += 1
        if merged.get('scholar'):
            stats['with_scholar'] += 1
            if merged['scholar'].get('publications'):
                stats['with_publications'] += 1

        for src in merged.get('sources', []):
            stats['sources'][src] = stats['sources'].get(src, 0) + 1

    # Sort by h-index descending
    merged_data.sort(key=lambda r: -(r.get('h_index') or 0))

    # Save merged output
    log(f"Saving merged data to: {MERGED_OUTPUT_FILE}")
    with open(MERGED_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    # Print summary
    log("=" * 60)
    log("MERGE COMPLETE")
    log("=" * 60)
    log(f"Total faculty: {stats['total']}")
    log(f"With scholar data: {stats['with_scholar']} ({100*stats['with_scholar']/stats['total']:.1f}%)")
    log(f"With publications: {stats['with_publications']} ({100*stats['with_publications']/stats['total']:.1f}%)")
    log("")
    log("Data sources:")
    for src, count in sorted(stats['sources'].items(), key=lambda x: -x[1]):
        log(f"  {src}: {count}")

    log("")
    log(f"Output: {MERGED_OUTPUT_FILE}")


if __name__ == '__main__':
    main()
