#!/usr/bin/env python3
"""
OpenAlex Enrichment Script for Project IRIS

Enriches faculty data with OpenAlex metrics:
- h-index
- Citation count
- Recent publications
- Works count

Usage:
    python enrich_openalex.py input.json output.json [--limit 10]
"""

import json
import argparse
import time
import sys
import requests
from pathlib import Path
from typing import Optional, List, Dict
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add("output/openalex_enrichment.log", level="DEBUG", rotation="10 MB")

KSU_INSTITUTION_ID = "I165506023"  # Kennesaw State University

def search_openalex_author(name: str) -> Optional[Dict]:
    """
    Search OpenAlex for a faculty member at KSU.
    """
    try:
        # Search for author by name and affiliation
        url = "https://api.openalex.org/authors"
        params = {
            "search": name,
            "filter": f"affiliations.institution.id:{KSU_INSTITUTION_ID}"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        if not results:
            return None
            
        # Return the first result (usually best match due to relevance sorting)
        return results[0]
        
    except Exception as e:
        logger.warning(f"OpenAlex search error for {name}: {e}")
        return None

def get_author_works(author_id: str) -> List[Dict]:
    """
    Get recent works for an author.
    """
    try:
        url = "https://api.openalex.org/works"
        params = {
            "filter": f"author.id:{author_id}",
            "sort": "publication_date:desc",
            "per_page": 20
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return [
            {
                'title': work.get('title'),
                'year': work.get('publication_year'),
                'citations': work.get('cited_by_count'),
                'venue': work.get('primary_location', {}).get('source', {}).get('display_name'),
                'doi': work.get('doi'),
                'landing_page_url': work.get('landing_page_url')
            }
            for work in data.get('results', [])
        ]
        
    except Exception as e:
        logger.warning(f"OpenAlex works error for {author_id}: {e}")
        return []

def enrich_faculty(input_file: str, output_file: str, limit: int = 0):
    """
    Enrich faculty data with OpenAlex information.
    """
    logger.info(f"Loading faculty data from {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        faculty_data = json.load(f)

    total = len(faculty_data)
    if limit > 0:
        total = min(total, limit)
        faculty_data = faculty_data[:total]
        
    logger.info(f"Processing {total} faculty profiles")

    enriched = 0
    not_found = 0
    
    for i, faculty in enumerate(faculty_data):
        name = faculty.get('name', '')
        if not name:
             # Try first/last construction
             first = faculty.get('first_name', '')
             last = faculty.get('last_name', '')
             if first and last:
                 name = f"{first} {last}"
        
        if not name:
            continue

        logger.info(f"[{i+1}/{total}] Searching: {name}")
        
        # Add delay to respect API limits (though OpenAlex is generous)
        time.sleep(0.1) 
        
        author_data = search_openalex_author(name)
        
        if author_data:
            enriched += 1
            
            # Basic metrics
            faculty['openalex'] = {
                'id': author_data.get('id'),
                'display_name': author_data.get('display_name'),
                'works_count': author_data.get('works_count'),
                'cited_by_count': author_data.get('cited_by_count'),
                'h_index': author_data.get('summary_stats', {}).get('h_index'),
                'i10_index': author_data.get('summary_stats', {}).get('i10_index'),
                'topics': [t.get('display_name') for t in author_data.get('topics', [])[:5]]
            }
            
            # Map top-level fields for easy access
            faculty['h_index'] = faculty['openalex']['h_index']
            faculty['citation_count'] = faculty['openalex']['cited_by_count']
            
            logger.success(f"  Found: h-index={faculty['h_index']}, works={faculty['openalex']['works_count']}")
            
            # Get Works
            works = get_author_works(author_data['id'])
            faculty['publications'] = works
            
        else:
            not_found += 1
            logger.debug("  Not found on OpenAlex")

        # Save periodically
        if (i + 1) % 50 == 0:
             with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(faculty_data, f, indent=2)

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(faculty_data, f, indent=2)

    logger.info("=" * 50)
    logger.info(f"Enriched: {enriched}")
    logger.info(f"Not found: {not_found}")
    logger.info("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='output/faculty_fixed.json')
    parser.add_argument('--output', default='output/faculty_openalex.json')
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    
    enrich_faculty(args.input, args.output, args.limit)
