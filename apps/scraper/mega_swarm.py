#!/usr/bin/env python3
"""
MEGA SWARM - Parallel Social Enrichment
Splits 2,978 people into chunks and runs parallel workers

Each worker:
- Searches DuckDuckGo for LinkedIn, GitHub, Twitter, ResearchGate
- Saves to its own output file
- Final merge combines all results
"""

import json
import subprocess
import sys
import time
import math
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_full_directory.json')
OUTPUT_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\output\swarm_chunks')
FINAL_OUTPUT = Path(r'C:\dev\research\project-iris\apps\scraper\output\ksu_mega_enriched.json')
WORKER_SCRIPT = Path(r'C:\dev\research\project-iris\apps\scraper\swarm_worker.py')

NUM_WORKERS = 8  # Parallel workers


def create_chunks(people: list, num_chunks: int) -> list:
    """Split people into chunks"""
    chunk_size = math.ceil(len(people) / num_chunks)
    return [people[i:i + chunk_size] for i in range(0, len(people), chunk_size)]


def run_worker(worker_id: int, chunk_file: Path) -> dict:
    """Run a single worker process"""
    output_file = OUTPUT_DIR / f'enriched_chunk_{worker_id}.json'
    
    result = subprocess.run(
        [sys.executable, str(WORKER_SCRIPT), str(chunk_file), str(output_file)],
        capture_output=True,
        text=True,
        timeout=7200  # 2 hour max per worker
    )
    
    return {
        'worker_id': worker_id,
        'success': result.returncode == 0,
        'output_file': str(output_file),
        'stdout': result.stdout[-500:] if result.stdout else '',
        'stderr': result.stderr[-500:] if result.stderr else '',
    }


def merge_results():
    """Merge all chunk outputs into final file"""
    all_people = []
    stats = {'linkedin': 0, 'github': 0, 'twitter': 0, 'researchgate': 0}
    
    for chunk_file in OUTPUT_DIR.glob('enriched_chunk_*.json'):
        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_people.extend(data.get('people', []))
            
            chunk_stats = data.get('stats', {})
            for key in stats:
                stats[key] += chunk_stats.get(key, 0)
    
    output = {
        'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_people': len(all_people),
        'enrichment_stats': stats,
        'all_people': all_people,
    }
    
    with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    return stats


def main():
    print("=" * 70)
    print("  MEGA SWARM - Parallel Social Enrichment")
    print("  8 Workers × ~370 people each = MAXIMUM SPEED")
    print("=" * 70)
    
    # Load directory
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    people = data.get('all_people', [])
    print(f"\nLoaded {len(people)} people")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Split into chunks
    chunks = create_chunks(people, NUM_WORKERS)
    print(f"Split into {len(chunks)} chunks of ~{len(chunks[0])} people each\n")
    
    # Save chunk files
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_file = OUTPUT_DIR / f'chunk_{i}.json'
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump({'people': chunk}, f)
        chunk_files.append(chunk_file)
        print(f"  Chunk {i}: {len(chunk)} people -> {chunk_file.name}")
    
    print(f"\n{'=' * 70}")
    print(f"  LAUNCHING {NUM_WORKERS} PARALLEL WORKERS")
    print(f"{'=' * 70}\n")
    
    start_time = time.time()
    
    # Launch workers in parallel
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {
            executor.submit(run_worker, i, chunk_files[i]): i 
            for i in range(len(chunks))
        }
        
        for future in as_completed(futures):
            worker_id = futures[future]
            try:
                result = future.result()
                status = "OK" if result['success'] else "FAILED"
                print(f"  Worker {worker_id}: {status}")
                if not result['success']:
                    print(f"    Error: {result['stderr'][:200]}")
            except Exception as e:
                print(f"  Worker {worker_id}: EXCEPTION - {e}")
    
    elapsed = time.time() - start_time
    
    print(f"\n{'=' * 70}")
    print(f"  MERGING RESULTS")
    print(f"{'=' * 70}\n")
    
    stats = merge_results()
    
    print(f"\n{'=' * 70}")
    print(f"  MEGA SWARM COMPLETE")
    print(f"{'=' * 70}")
    print(f"\nTime: {elapsed/60:.1f} minutes")
    print(f"\nProfiles Found:")
    print(f"  LinkedIn:     {stats['linkedin']}")
    print(f"  GitHub:       {stats['github']}")
    print(f"  Twitter/X:    {stats['twitter']}")
    print(f"  ResearchGate: {stats['researchgate']}")
    print(f"\nOutput: {FINAL_OUTPUT}")


if __name__ == "__main__":
    main()
