"""
Synapse Swarm Coordinator - Orchestrates parallel harvest workers
Manages query queue, tracks progress, dedupes results, triggers FAISS merge
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Paths
SCRIPTS_DIR = Path("C:/dev/research/project-iris/scripts")
HARVEST_DIR = Path("C:/dev/research/project-iris/data/synapse/harvest_raw")
DEDUPE_DIR = Path("C:/dev/research/project-iris/data/synapse/dedupe")
HARVEST_DIR.mkdir(parents=True, exist_ok=True)
DEDUPE_DIR.mkdir(parents=True, exist_ok=True)

# Harvest domains - BCI/Neurotech focused
HARVEST_QUERIES = [
    # Core BCI
    "brain computer interface",
    "EEG electroencephalography",
    "neural decoding",
    "motor imagery BCI",
    # Communication  
    "thought to text",
    "locked-in syndrome communication",
    "P300 speller",
    "SSVEP brain",
]

def run_worker(query: str, worker_id: int, max_results: int = 300) -> dict:
    """Run a single worker process"""
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "synapse_swarm_worker.py"),
                query,
                str(worker_id),
                str(max_results)
            ],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        
        elapsed = time.time() - start_time
        success = result.returncode == 0
        
        return {
            "query": query,
            "worker_id": worker_id,
            "success": success,
            "elapsed": elapsed,
            "stdout": result.stdout[-1000:] if result.stdout else "",
            "stderr": result.stderr[-500:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {
            "query": query,
            "worker_id": worker_id,
            "success": False,
            "elapsed": 300,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "query": query,
            "worker_id": worker_id,
            "success": False,
            "elapsed": time.time() - start_time,
            "error": str(e)
        }

def dedupe_results() -> dict:
    """Merge all harvest files and dedupe by synapse_id"""
    print("\n" + "="*60)
    print("DEDUPLICATION PHASE")
    print("="*60 + "\n")
    
    all_datasets = {}
    files_processed = 0
    
    for harvest_file in HARVEST_DIR.glob("*.json"):
        try:
            with open(harvest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for ds in data.get("datasets", []):
                sid = ds.get("synapse_id")
                if sid and sid not in all_datasets:
                    all_datasets[sid] = ds
                elif sid and sid in all_datasets:
                    # Keep the one with embedding if other doesn't have it
                    if ds.get("embedding") and not all_datasets[sid].get("embedding"):
                        all_datasets[sid] = ds
            
            files_processed += 1
            print(f"  Processed {harvest_file.name}: {data.get('count', 0)} datasets")
        except Exception as e:
            print(f"  Error processing {harvest_file.name}: {e}")
    
    # Save deduplicated results
    unique_datasets = list(all_datasets.values())
    embedded_count = sum(1 for d in unique_datasets if d.get("embedding"))
    
    output_file = DEDUPE_DIR / "all_datasets_unique.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "deduped_at": datetime.now(timezone.utc).isoformat(),
            "files_processed": files_processed,
            "total_unique": len(unique_datasets),
            "with_embeddings": embedded_count,
            "datasets": unique_datasets
        }, f, indent=2)
    
    print(f"\nDedupe complete:")
    print(f"  Files processed: {files_processed}")
    print(f"  Unique datasets: {len(unique_datasets)}")
    print(f"  With embeddings: {embedded_count}")
    print(f"  Output: {output_file}")
    
    return {
        "files_processed": files_processed,
        "total_unique": len(unique_datasets),
        "with_embeddings": embedded_count
    }

def run_swarm(max_workers: int = 4, max_results_per_query: int = 300):
    """Run the full swarm harvest"""
    print("="*60)
    print("SYNAPSE HARVEST SWARM - COORDINATOR")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Queries: {len(HARVEST_QUERIES)}")
    print(f"Max workers: {max_workers}")
    print(f"Max results per query: {max_results_per_query}")
    print("="*60 + "\n")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_worker, query, i, max_results_per_query): query
            for i, query in enumerate(HARVEST_QUERIES)
        }
        
        for future in as_completed(futures):
            query = futures[future]
            result = future.result()
            results.append(result)
            
            status = "OK" if result.get("success") else "FAILED"
            elapsed = result.get("elapsed", 0)
            print(f"[{status}] Worker {result.get('worker_id')}: '{query}' ({elapsed:.1f}s)")
            
            if not result.get("success"):
                error = result.get("error") or result.get("stderr", "")[:100]
                print(f"    Error: {error}")
    
    # Summary
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    total_time = sum(r.get("elapsed", 0) for r in results)
    
    print(f"\n{'='*60}")
    print("HARVEST PHASE COMPLETE")
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Failed: {failed}")
    print(f"  Total time: {total_time:.1f}s")
    print(f"{'='*60}")
    
    # Dedupe
    dedupe_stats = dedupe_results()
    
    # Save run summary
    summary_file = DEDUPE_DIR / "swarm_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "queries": len(HARVEST_QUERIES),
            "successful": successful,
            "failed": failed,
            "total_time_seconds": total_time,
            "dedupe_stats": dedupe_stats,
            "worker_results": results
        }, f, indent=2)
    
    print(f"\nSwarm summary saved to: {summary_file}")
    print("\n" + "="*60)
    print("SWARM COMPLETE")
    print("="*60)
    
    return dedupe_stats

if __name__ == "__main__":
    max_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    run_swarm(max_workers, max_results)
