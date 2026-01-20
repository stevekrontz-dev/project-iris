#!/usr/bin/env python3
"""
MEGA ENRICHMENT SWARM LAUNCHER
Runs all enrichment scrapers in sequence

Phase 1: CC5 - Find social profile URLs (LinkedIn, GitHub, Twitter, ResearchGate)
Phase 2: CC6 - Deep scrape LinkedIn profiles (requires VPN)
Phase 3: Merge all data back into master file
"""

import subprocess
import sys
import time
from pathlib import Path

SCRAPER_DIR = Path(r'C:\dev\research\project-iris\apps\scraper')

def run_phase(name: str, script: str, description: str) -> bool:
    """Run a scraper phase"""
    print(f"\n{'='*60}")
    print(f"  PHASE: {name}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    
    script_path = SCRAPER_DIR / script
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            timeout=7200  # 2 hour max
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {name} took too long")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    print("="*60)
    print("  MEGA ENRICHMENT SWARM")
    print("  Enriching 2,978 KSU people with social profiles")
    print("="*60)
    
    print("\nPhases:")
    print("  1. CC5: Find LinkedIn, GitHub, Twitter, ResearchGate URLs")
    print("  2. CC6: Deep scrape LinkedIn profiles (VPN required)")
    print("\nEstimated time: 2-4 hours (with rate limiting)")
    print("\n" + "-"*60)
    
    input("Press Enter to start Phase 1 (Social Discovery)...")
    
    # Phase 1: Social URL discovery
    success = run_phase(
        "Social Discovery",
        "cc5_social_enrichment.py",
        "Finding LinkedIn, GitHub, Twitter, ResearchGate URLs via search"
    )
    
    if not success:
        print("\nPhase 1 incomplete. Check progress file and restart.")
        return
    
    print("\n" + "="*60)
    print("  Phase 1 Complete!")
    print("="*60)
    
    print("\nPhase 2 requires VPN to scrape LinkedIn profiles.")
    print("1. Open NordVPN app")
    print("2. Connect to a US server")
    print("3. Press Enter when ready")
    input("\nPress Enter to start Phase 2 (LinkedIn Scraping)...")
    
    # Phase 2: LinkedIn deep scrape
    success = run_phase(
        "LinkedIn Scraping", 
        "cc6_linkedin_scrape.py",
        "Scraping LinkedIn profiles for skills, experience, education"
    )
    
    print("\n" + "="*60)
    print("  MEGA ENRICHMENT COMPLETE")
    print("="*60)
    print("\nOutput files:")
    print("  - ksu_enriched_social.json (profile URLs)")
    print("  - ksu_linkedin_enriched.json (full profiles)")
    print("\nNext: Merge with faculty embeddings and update search!")


if __name__ == "__main__":
    main()
