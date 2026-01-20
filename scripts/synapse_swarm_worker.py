"""
Synapse Swarm Worker - Harvests datasets for a single query term
Paginates through results, extracts metadata, generates embeddings
"""

import json
import os
import re
import sys
import httpx
from pathlib import Path
from datetime import datetime, timezone

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
OUTPUT_DIR = Path("C:/dev/research/project-iris/data/synapse/harvest_raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Synapse API
SYNAPSE_BASE = "https://repo-prod.prod.sagebase.org/repo/v1"

def clean_description(desc: str) -> str:
    if not desc:
        return ""
    desc = re.sub(r'\$\{[^}]+\}', '', desc)
    desc = re.sub(r'<[^>]+>', '', desc)
    desc = re.sub(r'[#*_`|]', '', desc)
    desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc[:2000] if len(desc) > 2000 else desc

def get_embedding(text: str) -> list[float]:
    if not text or not OPENAI_API_KEY:
        return []
    try:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": EMBEDDING_MODEL, "input": text},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"    Embedding error: {e}")
        return []

def search_synapse(query: str, offset: int = 0, limit: int = 100) -> dict:
    """Search Synapse using their search API"""
    try:
        response = httpx.post(
            f"{SYNAPSE_BASE}/search",
            json={
                "queryTerm": [query],
                "start": offset,
                "size": limit,
                "returnFields": ["name", "description", "node_type", "alias"]
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    Search error at offset {offset}: {e}")
        return {"hits": [], "found": 0}

def harvest_query(query: str, worker_id: int, max_results: int = 500) -> list[dict]:
    """Harvest all results for a query term"""
    print(f"[W{worker_id}] Starting harvest: '{query}'")
    
    all_results = []
    offset = 0
    batch_size = 50
    
    while offset < max_results:
        result = search_synapse(query, offset, batch_size)
        hits = result.get("hits", [])
        total_found = result.get("found", 0)
        
        if not hits:
            break
            
        for item in hits:
            synapse_id = item.get("id", "")
            name = item.get("name", "")
            description = item.get("description", "")
            
            clean_desc = clean_description(description)
            embed_text = f"{name}. {clean_desc}" if clean_desc else name
            
            all_results.append({
                "synapse_id": synapse_id,
                "name": name,
                "alias": item.get("alias", ""),
                "node_type": item.get("node_type", ""),
                "description_clean": clean_desc,
                "embed_text": embed_text,
                "url": f"https://www.synapse.org/#!Synapse:{synapse_id}",
                "query_source": query,
                "harvested_at": datetime.now(timezone.utc).isoformat()
            })
        
        print(f"[W{worker_id}] Harvested {len(all_results)}/{min(total_found, max_results)} for '{query}'")
        offset += batch_size
        
        if offset >= total_found:
            break
    
    return all_results

def generate_embeddings_batch(datasets: list[dict], worker_id: int) -> list[dict]:
    """Generate embeddings for all datasets"""
    print(f"[W{worker_id}] Generating embeddings for {len(datasets)} datasets...")
    
    for i, ds in enumerate(datasets):
        if ds["embed_text"]:
            ds["embedding"] = get_embedding(ds["embed_text"])
            if (i + 1) % 10 == 0:
                print(f"[W{worker_id}] Embedded {i+1}/{len(datasets)}")
        else:
            ds["embedding"] = []
    
    return datasets

def save_results(datasets: list[dict], query: str, worker_id: int):
    """Save harvested data"""
    safe_query = re.sub(r'[^\w\-]', '_', query.lower())
    output_file = OUTPUT_DIR / f"{safe_query}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "query": query,
            "worker_id": worker_id,
            "harvested_at": datetime.now(timezone.utc).isoformat(),
            "count": len(datasets),
            "embedded_count": sum(1 for d in datasets if d.get("embedding")),
            "datasets": datasets
        }, f, indent=2)
    
    print(f"[W{worker_id}] Saved {len(datasets)} datasets to {output_file.name}")
    return output_file

def run_worker(query: str, worker_id: int, max_results: int = 500):
    """Main worker execution"""
    print(f"\n{'='*60}")
    print(f"SYNAPSE SWARM WORKER {worker_id}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    # Harvest
    datasets = harvest_query(query, worker_id, max_results)
    
    if not datasets:
        print(f"[W{worker_id}] No results found for '{query}'")
        return
    
    # Embed
    datasets = generate_embeddings_batch(datasets, worker_id)
    
    # Save
    output_file = save_results(datasets, query, worker_id)
    
    print(f"\n[W{worker_id}] COMPLETE: {len(datasets)} datasets harvested and embedded")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python synapse_swarm_worker.py <query> <worker_id> [max_results]")
        sys.exit(1)
    
    query = sys.argv[1]
    worker_id = int(sys.argv[2])
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    
    run_worker(query, worker_id, max_results)
