#!/usr/bin/env python3
"""
SWARM LAUNCHER: Role Enrichment
Runs CC1, CC2, CC3 in parallel to enrich faculty with role/position data
"""

import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRAPER_DIR = Path(r'C:\dev\research\project-iris\apps\scraper')

SCRIPTS = [
    ('CC1', 'cc1_directory_scrape.py', 'KSU Directory - official titles'),
    ('CC2', 'cc2_faculty_pages.py', 'Faculty pages - labs & leadership'),
    ('CC3', 'cc3_centers_map.py', 'Research centers - directors'),
]


def run_script(name: str, script: str, description: str) -> tuple:
    """Run a scraper script and capture output"""
    script_path = SCRAPER_DIR / script
    
    print(f"\n{'='*60}")
    print(f"[{name}] Starting: {description}")
    print(f"{'='*60}")
    
    start = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour max
        )
        
        elapsed = time.time() - start
        
        # Print output
        if result.stdout:
            for line in result.stdout.split('\n')[-20:]:  # Last 20 lines
                print(f"[{name}] {line}")
        
        if result.returncode != 0:
            print(f"[{name}] ERROR: {result.stderr[-500:]}")
            return (name, False, elapsed, result.stderr[-200:])
        
        return (name, True, elapsed, "Success")
        
    except subprocess.TimeoutExpired:
        return (name, False, 3600, "Timeout")
    except Exception as e:
        return (name, False, 0, str(e))


def main():
    print("="*60)
    print("  IRIS ROLE ENRICHMENT SWARM")
    print("="*60)
    print(f"\nLaunching {len(SCRIPTS)} parallel scrapers...")
    print("  CC1: KSU Directory (official titles)")
    print("  CC2: Faculty web pages (labs, leadership)")
    print("  CC3: Research centers (directors, members)")
    print("\n" + "="*60)
    
    start_time = time.time()
    results = []
    
    # Run in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_script, name, script, desc): name
            for name, script, desc in SCRIPTS
        }
        
        for future in as_completed(futures):
            name, success, elapsed, msg = future.result()
            results.append((name, success, elapsed, msg))
            
            status = "✓ COMPLETE" if success else "✗ FAILED"
            print(f"\n[{name}] {status} in {elapsed:.1f}s")
    
    # Summary
    total_time = time.time() - start_time
    successful = sum(1 for _, s, _, _ in results if s)
    
    print("\n" + "="*60)
    print("  SWARM COMPLETE")
    print("="*60)
    print(f"\nResults: {successful}/{len(SCRIPTS)} successful")
    print(f"Total time: {total_time:.1f}s")
    
    for name, success, elapsed, msg in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}: {elapsed:.1f}s - {msg[:50]}")
    
    print("\nOutput files:")
    print("  - faculty_directory_enriched.json (CC1)")
    print("  - faculty_labs_enriched.json (CC2)")
    print("  - ksu_centers.json (CC3)")
    
    print("\nNext: Run merge script to combine all enrichments")


if __name__ == "__main__":
    main()
