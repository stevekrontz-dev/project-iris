#!/usr/bin/env python3
"""
Multi-Source Academic Enricher for IRIS
Queries OpenAlex, Semantic Scholar, and ORCID APIs to enrich faculty data.
FIXED: Strict KSU affiliation verification to prevent false matches.
"""

import json
import time
import re
import os
import sys
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import quote

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(SCRIPT_DIR, 'output', 'faculty_library.json')
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, 'output', 'faculty_api_enriched.json')
PROGRESS_FILE = os.path.join(SCRIPT_DIR, 'output', 'api_enricher_progress.json')
LOG_FILE = os.path.join(SCRIPT_DIR, 'output', 'api_enricher.log')

# API endpoints
OPENALEX_API = "https://api.openalex.org"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
ORCID_API = "https://pub.orcid.org/v3.0"

# Rate limiting
REQUEST_DELAY = 1.0  # seconds between API calls
MAX_RETRIES = 3
MAX_PUBLICATIONS = 30

# Session for connection pooling
session = requests.Session()
session.headers.update({
    'User-Agent': 'IRIS-Academic-Enricher/1.0 (Research Project; mailto:research@kennesaw.edu)',
    'Accept': 'application/json'
})


def log(level: str, msg: str):
    """Log message to console and file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"{timestamp} | {level:8} | {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def safe_request(url: str, headers: dict = None, params: dict = None) -> Optional[Dict]:
    """Make HTTP request with retries and error handling."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return None
            elif resp.status_code == 429:  # Rate limited
                wait_time = int(resp.headers.get('Retry-After', 60))
                log('RATE', f"Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
            else:
                log('WARN', f"HTTP {resp.status_code} for {url[:80]}")
        except requests.exceptions.Timeout:
            log('WARN', f"Timeout (attempt {attempt + 1})")
        except requests.exceptions.RequestException as e:
            log('ERROR', f"Request error: {e}")
        time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


# =============================================================================
# Affiliation Verification (NEW)
# =============================================================================

def check_ksu_affiliation(affiliations: List) -> bool:
    """Check if any affiliation contains Kennesaw State University."""
    ksu_keywords = ['kennesaw', 'ksu', 'kennesaw state']
    for aff in affiliations:
        aff_str = ''
        if isinstance(aff, dict):
            aff_str = (aff.get('display_name') or aff.get('name') or '').lower()
        elif isinstance(aff, str):
            aff_str = aff.lower()
        for keyword in ksu_keywords:
            if keyword in aff_str:
                return True
    return False


def names_match(name1: str, name2: str) -> bool:
    """Check if two names are reasonably similar."""
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()
    # Direct containment
    if n1 in n2 or n2 in n1:
        return True
    # Compare last names + first initial
    parts1 = n1.split()
    parts2 = n2.split()
    if parts1 and parts2:
        last1 = parts1[-1]
        last2 = parts2[-1]
        if last1 == last2 and len(parts1[0]) > 0 and len(parts2[0]) > 0:
            if parts1[0][0] == parts2[0][0]:
                return True
    return False


# =============================================================================
# OpenAlex API
# =============================================================================

def search_openalex(name: str, affiliation: str = "Kennesaw") -> Optional[Dict]:
    """Search OpenAlex for an author with VERIFIED KSU affiliation."""
    url = f"{OPENALEX_API}/authors"
    params = {'search': name, 'per-page': 15}

    data = safe_request(url, params=params)
    if not data or not data.get('results'):
        return None

    # STRICT: Only return if we confirm KSU affiliation
    for result in data['results']:
        institutions = result.get('last_known_institutions') or []
        all_affiliations = result.get('affiliations') or []

        if check_ksu_affiliation(institutions) or check_ksu_affiliation(all_affiliations):
            result_name = result.get('display_name') or ''
            if names_match(name, result_name):
                log('INFO', f"    OpenAlex MATCH: {result_name} (KSU verified)")
                return result

    # NO FALLBACK - only return verified KSU affiliates
    return None


def get_openalex_works(author_id: str) -> List[Dict]:
    """Get publications for an OpenAlex author."""
    url = f"{OPENALEX_API}/works"
    params = {
        'filter': f'author.id:{author_id}',
        'per-page': MAX_PUBLICATIONS,
        'sort': 'cited_by_count:desc'
    }

    data = safe_request(url, params=params)
    if not data:
        return []

    publications = []
    for work in data.get('results', []):
        # Handle nested nulls safely
        primary_loc = work.get('primary_location') or {}
        source_info = primary_loc.get('source') or {}

        pub = {
            'title': work.get('title', ''),
            'authors': [a.get('author', {}).get('display_name', '')
                       for a in work.get('authorships', [])[:10]],
            'year': work.get('publication_year'),
            'journal': source_info.get('display_name', ''),
            'abstract': None,
            'citations': work.get('cited_by_count', 0),
            'doi': work.get('doi', '').replace('https://doi.org/', '') if work.get('doi') else None,
            'article_url': primary_loc.get('landing_page_url', ''),
            'source': 'openalex'
        }

        # Try to get abstract from inverted index
        if work.get('abstract_inverted_index'):
            try:
                inv_idx = work['abstract_inverted_index']
                words = [''] * (max(max(positions) for positions in inv_idx.values()) + 1)
                for word, positions in inv_idx.items():
                    for pos in positions:
                        words[pos] = word
                pub['abstract'] = ' '.join(words)[:2000]
            except:
                pass

        publications.append(pub)

    return publications


def enrich_from_openalex(name: str) -> Optional[Dict]:
    """Get full enrichment data from OpenAlex."""
    author = search_openalex(name)
    if not author:
        return None

    author_id = author.get('id', '').replace('https://openalex.org/', '')
    publications = get_openalex_works(author['id'])

    interests = []
    for concept in author.get('x_concepts', [])[:10]:
        if concept.get('level', 0) <= 2:
            interests.append(concept.get('display_name', ''))

    return {
        'scholar_id': f"openalex:{author_id}",
        'name': author.get('display_name', ''),
        'affiliation': (author.get('last_known_institutions') or [{}])[0].get('display_name', ''),
        'interests': interests[:10],
        'h_index': author.get('summary_stats', {}).get('h_index', 0),
        'i10_index': author.get('summary_stats', {}).get('i10_index', 0),
        'total_citations': author.get('cited_by_count', 0),
        'publication_count': author.get('works_count', 0),
        'publications': publications,
        'source': 'openalex',
        'ksu_verified': True
    }


# =============================================================================
# Semantic Scholar API
# =============================================================================

def search_semantic_scholar(name: str) -> Optional[Dict]:
    """Search Semantic Scholar for an author with KSU affiliation check."""
    url = f"{SEMANTIC_SCHOLAR_API}/author/search"
    params = {'query': name, 'limit': 10}

    data = safe_request(url, params=params)
    if not data or not data.get('data'):
        return None

    # Check each result for KSU affiliation
    for author in data['data']:
        author_id = author.get('authorId')
        if not author_id:
            continue

        # Get full details to check affiliation
        details = get_semantic_author_details(author_id)
        if details:
            affiliations = details.get('affiliations', []) or []
            if check_ksu_affiliation(affiliations):
                result_name = details.get('name') or ''
                if names_match(name, result_name):
                    log('INFO', f"    S2 MATCH: {result_name} (KSU verified)")
                    return details

    return None


def get_semantic_papers(author_id: str) -> List[Dict]:
    """Get publications for a Semantic Scholar author."""
    url = f"{SEMANTIC_SCHOLAR_API}/author/{author_id}/papers"
    params = {
        'fields': 'title,authors,year,venue,abstract,citationCount,externalIds,url',
        'limit': MAX_PUBLICATIONS
    }

    data = safe_request(url, params=params)
    if not data:
        return []

    publications = []
    for paper in data.get('data', []):
        pub = {
            'title': paper.get('title', ''),
            'authors': [a.get('name', '') for a in paper.get('authors', [])[:10]],
            'year': paper.get('year'),
            'journal': paper.get('venue', ''),
            'abstract': (paper.get('abstract') or '')[:2000],
            'citations': paper.get('citationCount', 0),
            'doi': paper.get('externalIds', {}).get('DOI'),
            'article_url': paper.get('url', ''),
            'source': 'semantic_scholar'
        }
        publications.append(pub)

    return publications


def get_semantic_author_details(author_id: str) -> Optional[Dict]:
    """Get detailed author info from Semantic Scholar."""
    url = f"{SEMANTIC_SCHOLAR_API}/author/{author_id}"
    params = {'fields': 'name,affiliations,paperCount,citationCount,hIndex'}
    return safe_request(url, params=params)


def enrich_from_semantic_scholar(name: str) -> Optional[Dict]:
    """Get full enrichment data from Semantic Scholar with KSU verification."""
    author = search_semantic_scholar(name)
    if not author:
        return None

    author_id = author.get('authorId')
    if not author_id:
        return None

    publications = get_semantic_papers(author_id)
    affiliations = author.get('affiliations', []) or []

    return {
        'scholar_id': f"s2:{author_id}",
        'name': author.get('name', ''),
        'affiliation': affiliations[0] if affiliations else '',
        'interests': [],
        'h_index': author.get('hIndex', 0),
        'i10_index': 0,
        'total_citations': author.get('citationCount', 0),
        'publication_count': author.get('paperCount', 0),
        'publications': publications,
        'source': 'semantic_scholar',
        'ksu_verified': True
    }


# =============================================================================
# ORCID API
# =============================================================================

def search_orcid(first_name: str, last_name: str) -> Optional[str]:
    """Search ORCID for a researcher with KSU affiliation."""
    url = f"{ORCID_API}/search/"
    # Start with strict KSU search
    query = f'family-name:{last_name} AND given-names:{first_name} AND affiliation-org-name:Kennesaw'
    params = {'q': query}
    headers = {'Accept': 'application/json'}

    data = safe_request(url, headers=headers, params=params)
    if data and data.get('result'):
        first_result = data['result'][0]
        orcid_id = first_result.get('orcid-identifier', {}).get('path')
        if orcid_id:
            log('INFO', f"    ORCID MATCH: {orcid_id} (KSU search)")
            return orcid_id

    # Try broader search but verify affiliation manually
    query = f'family-name:{last_name} AND given-names:{first_name}'
    params = {'q': query}
    data = safe_request(url, headers=headers, params=params)

    if not data or not data.get('result'):
        return None

    # Check each result for KSU affiliation
    for result in data.get('result', [])[:5]:
        orcid_id = result.get('orcid-identifier', {}).get('path')
        if not orcid_id:
            continue

        # Get full record to verify affiliation
        record_url = f"{ORCID_API}/{orcid_id}/record"
        record = safe_request(record_url, headers=headers)
        if record:
            affiliations = record.get('activities-summary', {}).get('employments', {}).get('affiliation-group', [])
            for aff in affiliations:
                summaries = aff.get('summaries', [])
                for summary in summaries:
                    org_name = summary.get('employment-summary', {}).get('organization', {}).get('name', '')
                    if 'kennesaw' in org_name.lower():
                        log('INFO', f"    ORCID MATCH: {orcid_id} (KSU verified)")
                        return orcid_id

    return None


def get_orcid_works(orcid_id: str) -> List[Dict]:
    """Get publications from ORCID profile."""
    url = f"{ORCID_API}/{orcid_id}/works"
    headers = {'Accept': 'application/json'}

    data = safe_request(url, headers=headers)
    if not data or not data.get('group'):
        return []

    publications = []
    for group in data.get('group', [])[:MAX_PUBLICATIONS]:
        work_summary = group.get('work-summary', [{}])[0]

        doi = None
        ext_ids = (work_summary.get('external-ids') or {}).get('external-id') or []
        for ext_id in ext_ids:
            if ext_id.get('external-id-type') == 'doi':
                doi = ext_id.get('external-id-value')
                break

        title_obj = (work_summary.get('title') or {}).get('title') or {}
        pub_date = work_summary.get('publication-date') or {}
        year_obj = pub_date.get('year') or {}
        journal_obj = work_summary.get('journal-title') or {}
        url_obj = work_summary.get('url') or {}

        pub = {
            'title': title_obj.get('value', ''),
            'authors': [],
            'year': year_obj.get('value'),
            'journal': journal_obj.get('value', ''),
            'abstract': None,
            'citations': 0,
            'doi': doi,
            'article_url': url_obj.get('value', ''),
            'source': 'orcid'
        }

        if pub['year']:
            try:
                pub['year'] = int(pub['year'])
            except:
                pub['year'] = None

        publications.append(pub)

    return publications


def enrich_from_orcid(first_name: str, last_name: str) -> Optional[Dict]:
    """Get enrichment data from ORCID with KSU verification."""
    orcid_id = search_orcid(first_name, last_name)
    if not orcid_id:
        return None

    url = f"{ORCID_API}/{orcid_id}/record"
    headers = {'Accept': 'application/json'}
    data = safe_request(url, headers=headers)

    if not data:
        return None

    person = data.get('person', {})
    name_data = person.get('name', {})
    full_name = f"{name_data.get('given-names', {}).get('value', '')} {name_data.get('family-name', {}).get('value', '')}"

    affiliations = data.get('activities-summary', {}).get('employments', {}).get('affiliation-group', [])
    current_affiliation = ''
    for aff in affiliations:
        summaries = aff.get('summaries', [])
        if summaries:
            current_affiliation = summaries[0].get('employment-summary', {}).get('organization', {}).get('name', '')
            break

    publications = get_orcid_works(orcid_id)

    return {
        'scholar_id': f"orcid:{orcid_id}",
        'orcid_id': orcid_id,
        'name': full_name.strip(),
        'affiliation': current_affiliation,
        'interests': [],
        'h_index': 0,
        'i10_index': 0,
        'total_citations': 0,
        'publication_count': len(publications),
        'publications': publications,
        'source': 'orcid',
        'ksu_verified': True
    }


# =============================================================================
# Main Enrichment Logic
# =============================================================================

def merge_scholar_data(existing: Optional[Dict], new_data: Dict) -> Dict:
    """Merge new enrichment data with existing, keeping best values."""
    if not existing:
        return new_data

    merged = existing.copy()

    if new_data.get('h_index', 0) > merged.get('h_index', 0):
        merged['h_index'] = new_data['h_index']

    if new_data.get('total_citations', 0) > merged.get('total_citations', 0):
        merged['total_citations'] = new_data['total_citations']

    existing_interests = set(merged.get('interests', []))
    new_interests = set(new_data.get('interests', []))
    merged['interests'] = list(existing_interests | new_interests)[:15]

    existing_pubs = merged.get('publications', [])
    existing_dois = {p.get('doi') for p in existing_pubs if p.get('doi')}
    existing_titles = {(p.get('title') or '').lower() for p in existing_pubs}

    for pub in new_data.get('publications', []):
        doi = pub.get('doi')
        title = (pub.get('title') or '').lower()

        if doi and doi in existing_dois:
            continue
        if title in existing_titles:
            continue

        existing_pubs.append(pub)
        if doi:
            existing_dois.add(doi)
        existing_titles.add(title)

    merged['publications'] = existing_pubs[:MAX_PUBLICATIONS]

    sources = set(merged.get('sources', []))
    sources.add(new_data.get('source', 'unknown'))
    merged['sources'] = list(sources)
    merged['ksu_verified'] = True

    return merged


def enrich_faculty_member(faculty: Dict) -> Dict:
    """Enrich a single faculty member from all sources."""
    name = faculty.get('name', '')
    first_name = faculty.get('first_name', '')
    last_name = faculty.get('last_name', '')

    if not name:
        return faculty

    enriched = faculty.copy()
    scholar_data = enriched.get('scholar')
    sources_tried = []

    # 1. Try OpenAlex (best for metrics)
    log('INFO', f"  OpenAlex: {name}")
    time.sleep(REQUEST_DELAY)
    openalex_data = enrich_from_openalex(name)
    if openalex_data:
        log('SUCCESS', f"    Found on OpenAlex: h={openalex_data.get('h_index', 0)}")
        scholar_data = merge_scholar_data(scholar_data, openalex_data)
        sources_tried.append('openalex')

    # 2. Try Semantic Scholar
    log('INFO', f"  Semantic Scholar: {name}")
    time.sleep(REQUEST_DELAY)
    s2_data = enrich_from_semantic_scholar(name)
    if s2_data:
        log('SUCCESS', f"    Found on S2: h={s2_data.get('h_index', 0)}")
        scholar_data = merge_scholar_data(scholar_data, s2_data)
        sources_tried.append('semantic_scholar')

    # 3. Try ORCID
    if first_name and last_name:
        log('INFO', f"  ORCID: {first_name} {last_name}")
        time.sleep(REQUEST_DELAY)
        orcid_data = enrich_from_orcid(first_name, last_name)
        if orcid_data:
            log('SUCCESS', f"    Found on ORCID: {orcid_data.get('orcid_id')}")
            scholar_data = merge_scholar_data(scholar_data, orcid_data)
            sources_tried.append('orcid')

    if scholar_data:
        enriched['scholar'] = scholar_data
        enriched['h_index'] = scholar_data.get('h_index', 0)
        enriched['citation_count'] = scholar_data.get('total_citations', 0)
        enriched['api_sources'] = sources_tried
        enriched['ksu_verified'] = True

    return enriched


def load_progress() -> Dict:
    """Load progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_index': -1, 'enriched_count': 0, 'sources_found': {}}


def save_progress(index: int, enriched_count: int, sources_found: Dict):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({
            'last_index': index,
            'enriched_count': enriched_count,
            'sources_found': sources_found,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)


def main():
    """Main enrichment loop."""
    input_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    output_file = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT

    log('INFO', f'Loading faculty data from {input_file}')
    log('INFO', '*** STRICT KSU VERIFICATION ENABLED ***')

    with open(input_file, 'r', encoding='utf-8') as f:
        faculty = json.load(f)

    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
    else:
        output_data = faculty.copy()

    progress = load_progress()
    start_from = progress['last_index'] + 1
    enriched_count = progress['enriched_count']
    sources_found = progress.get('sources_found', {'openalex': 0, 'semantic_scholar': 0, 'orcid': 0})

    log('INFO', f'Total profiles: {len(faculty)}')
    log('INFO', f'Starting from: {start_from}')
    log('INFO', f'Already enriched: {enriched_count}')

    try:
        for i in range(start_from, len(faculty)):
            person = faculty[i]
            name = person.get('name', '')

            log('INFO', f'[{i+1}/{len(faculty)}] Processing: {name}')

            if output_data[i].get('api_sources'):
                log('INFO', f'  Already enriched via API, skipping')
                continue

            enriched = enrich_faculty_member(person)
            output_data[i] = enriched

            if enriched.get('api_sources'):
                enriched_count += 1
                for src in enriched['api_sources']:
                    sources_found[src] = sources_found.get(src, 0) + 1

            if (i + 1) % 10 == 0:
                log('INFO', f'Saving progress... ({enriched_count} enriched)')
                log('INFO', f'  Sources: OpenAlex={sources_found.get("openalex", 0)}, S2={sources_found.get("semantic_scholar", 0)}, ORCID={sources_found.get("orcid", 0)}')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                save_progress(i, enriched_count, sources_found)

    except KeyboardInterrupt:
        log('INFO', 'Interrupted by user')
    except Exception as e:
        log('ERROR', f'Fatal error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        log('INFO', f'Final save... ({enriched_count} enriched)')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        save_progress(i if 'i' in dir() else start_from, enriched_count, sources_found)

    log('INFO', '=' * 50)
    log('INFO', f'Done! {enriched_count} faculty enriched (KSU verified)')
    log('INFO', f'OpenAlex matches: {sources_found.get("openalex", 0)}')
    log('INFO', f'Semantic Scholar matches: {sources_found.get("semantic_scholar", 0)}')
    log('INFO', f'ORCID matches: {sources_found.get("orcid", 0)}')


if __name__ == '__main__':
    main()
