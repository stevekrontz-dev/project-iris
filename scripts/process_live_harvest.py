"""
Process live Synapse harvest and generate embeddings.
"""
import json
import os
import re
import httpx
from pathlib import Path
from datetime import datetime, timezone

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
DATA_DIR = Path("C:/dev/research/project-iris/data/synapse")

def clean_description(desc):
    if not desc:
        return ""
    desc = re.sub(r'\$\{[^}]+\}', '', desc)
    desc = re.sub(r'<[^>]+>', '', desc)
    desc = re.sub(r'[#*_`|]', '', desc)
    desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc[:2000]

def get_embedding(text):
    response = httpx.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={"model": EMBEDDING_MODEL, "input": text},
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

def main():
    # Load raw data
    with open(DATA_DIR / "live_eeg_bci_raw.json") as f:
        datasets = json.load(f)
    
    print(f"Processing {len(datasets)} live Synapse results...")
    print("=" * 60)
    
    results = []
    for i, ds in enumerate(datasets):
        name = ds.get("name", "")
        desc = clean_description(ds.get("description", ""))
        embed_text = f"{name}. {desc}" if desc else name
        
        try:
            embedding = get_embedding(embed_text)
            status = f"OK ({len(embedding)} dims)"
        except Exception as e:
            embedding = []
            status = f"FAILED: {e}"
        
        print(f"[{i+1:2}/{len(datasets)}] {ds['id']}: {name[:45]}... {status}")
        
        results.append({
            "synapse_id": ds["id"],
            "name": name,
            "node_type": ds.get("node_type", ""),
            "description_clean": desc[:300],
            "url": f"https://www.synapse.org/#!Synapse:{ds['id']}",
            "embedding": embedding
        })
    
    # Save results
    output = {
        "query": "EEG brain computer interface",
        "source": "Synapse MCP live",
        "harvested_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "with_embeddings": sum(1 for r in results if r.get("embedding")),
        "datasets": results
    }
    
    output_file = DATA_DIR / "live_eeg_bci_embedded.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print("=" * 60)
    print(f"Saved {output['with_embeddings']}/{output['total']} embedded to {output_file}")

if __name__ == "__main__":
    main()
