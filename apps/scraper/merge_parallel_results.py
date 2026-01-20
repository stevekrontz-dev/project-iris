#!/usr/bin/env python3
"""
Merge parallel enrichment results into a single file.
Combines faculty_enriched_agent1.json, faculty_enriched_agent2.json, etc.
"""

import json
import os
import glob
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')
BASE_FILE = os.path.join(OUTPUT_DIR, 'faculty_fixed.json')
MERGED_FILE = os.path.join(OUTPUT_DIR, 'faculty_library.json')

def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{timestamp} | {msg}")

def main():
    log("Loading base faculty data...")
    with open(BASE_FILE, 'r', encoding='utf-8') as f:
        base_data = json.load(f)

    log(f"Base file has {len(base_data)} faculty members")

    # Find all enriched files
    enriched_files = glob.glob(os.path.join(OUTPUT_DIR, 'faculty_enriched_*.json'))
    log(f"Found {len(enriched_files)} enriched files: {[os.path.basename(f) for f in enriched_files]}")

    if not enriched_files:
        log("No enriched files found!")
        return

    # Merge enriched data
    total_enriched = 0

    for enriched_file in enriched_files:
        agent_name = os.path.basename(enriched_file).replace('faculty_enriched_', '').replace('.json', '')

        with open(enriched_file, 'r', encoding='utf-8') as f:
            enriched_data = json.load(f)

        # Figure out which range this file covers
        # Each file contains a subset of faculty
        file_enriched = 0

        for enriched_person in enriched_data:
            if enriched_person.get('scholar') and enriched_person['scholar'].get('publications'):
                # Find matching person in base data by net_id
                net_id = enriched_person.get('net_id')
                for i, base_person in enumerate(base_data):
                    if base_person.get('net_id') == net_id:
                        base_data[i] = enriched_person
                        file_enriched += 1
                        break

        log(f"  {agent_name}: {file_enriched} enriched profiles merged")
        total_enriched += file_enriched

    # Count total with scholar data
    total_with_scholar = sum(1 for p in base_data if p.get('scholar') and p['scholar'].get('publications'))

    log(f"Total enriched: {total_with_scholar}")

    # Save merged file
    log(f"Saving merged data to {MERGED_FILE}...")
    with open(MERGED_FILE, 'w', encoding='utf-8') as f:
        json.dump(base_data, f, indent=2, ensure_ascii=False)

    log("Done!")
    log(f"Merged file: {MERGED_FILE}")
    log(f"Total faculty: {len(base_data)}")
    log(f"With Scholar data: {total_with_scholar}")

if __name__ == '__main__':
    main()
