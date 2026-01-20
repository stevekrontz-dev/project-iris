"""
Synapse Live Harvest - Single Query Test
Pulls real data from Synapse via MCP, generates embeddings, saves to IRIS data dir.

Usage: Run from Claude with Synapse MCP connected - pass results to this script.
"""

import json
import os
import re
import httpx
from pathlib import Path
from datetime import datetime, timezone

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
OUTPUT_DIR = Path("C:/dev/research/project-iris/data/synapse")
OUTPUT_DIR.mkdir(exist_ok=True)

def clean_description(desc: str) -> str:
    """Strip markdown/HTML formatting, normalize whitespace."""
    if not desc:
        return ""
    desc = re.sub(r'\$\{image\?[^}]+\}', '', desc)
    desc = re.sub(r'\$\{buttonlink\?[^}]+\}', '', desc)
    desc = re.sub(r'\$\{[^}]+\}', '', desc)
    desc = re.sub(r'<[^>]+>', '', desc)
    desc = re.sub(r'[#*_`|]', '', desc)
    desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc[:2000] if len(desc) > 2000 else desc

def get_embedding(text: str) -> list[float]:
    """Generate OpenAI embedding for text."""
    if not text or not OPENAI_API_KEY:
        return []
    
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

def process_synapse_results(results: list[dict]) -> list[dict]:
    """Process raw Synapse results into clean format."""
    processed = []
    
    for item in results:
        synapse_id = item.get("id", "")
        name = item.get("name", "")
        description = item.get("description", "")
        node_type = item.get("node_type", "")
        
        clean_desc = clean_description(description)
        embed_text = f"{name}. {clean_desc}" if clean_desc else name
        
        processed.append({
            "synapse_id": synapse_id,
            "name": name,
            "node_type": node_type,
            "description_clean": clean_desc,
            "embed_text": embed_text,
            "url": f"https://www.synapse.org/#!Synapse:{synapse_id}",
        })
    
    return processed

def generate_embeddings_batch(datasets: list[dict]) -> list[dict]:
    """Add embeddings to processed datasets."""
    print(f"Generating embeddings for {len(datasets)} datasets...")
    
    for i, ds in enumerate(datasets):
        if ds.get("embed_text"):
            try:
                ds["embedding"] = get_embedding(ds["embed_text"])
                print(f"  [{i+1}/{len(datasets)}] {ds['synapse_id']}: {ds['name'][:40]}... OK ({len(ds['embedding'])} dims)")
            except Exception as e:
                print(f"  [{i+1}/{len(datasets)}] {ds['synapse_id']}: FAILED - {e}")
                ds["embedding"] = []
        else:
            ds["embedding"] = []
    
    return datasets

def save_results(datasets: list[dict], query: str):
    """Save harvested data."""
    query_slug = query.lower().replace(' ', '_')
    
    output = {
        "query": query,
        "harvested_at": datetime.now(timezone.utc).isoformat(),
        "total": len(datasets),
        "with_embeddings": sum(1 for d in datasets if d.get("embedding")),
        "datasets": datasets
    }
    
    output_file = OUTPUT_DIR / f"live_{query_slug}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to {output_file}")
    print(f"  Total: {output['total']}")
    print(f"  With embeddings: {output['with_embeddings']}")
    
    return output_file

def run_harvest(synapse_results: list[dict], query: str):
    """Main entry point - pass Synapse MCP results here."""
    print(f"\n{'='*60}")
    print(f"SYNAPSE LIVE HARVEST: {query}")
    print(f"{'='*60}")
    
    # Process
    processed = process_synapse_results(synapse_results)
    print(f"\nProcessed {len(processed)} results")
    
    # Embed
    if OPENAI_API_KEY:
        processed = generate_embeddings_batch(processed)
    else:
        print("WARNING: No OPENAI_API_KEY - skipping embeddings")
    
    # Save
    output_file = save_results(processed, query)
    
    print(f"\n{'='*60}")
    print("HARVEST COMPLETE")
    print(f"{'='*60}")
    
    return output_file

if __name__ == "__main__":
    # When run directly, load from stdin or test
    print("This script is designed to be called with Synapse MCP results.")
    print("Use: run_harvest(synapse_results, query)")
