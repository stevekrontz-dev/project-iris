"""
Synapse Harvest Test - Single Query Pipeline Validation
Harvests BCI datasets from Synapse, extracts metadata, generates embeddings,
and prepares for IRIS vector space integration.

Test run: "brain computer interface" query
"""

import json
import os
import re
import httpx
from pathlib import Path
from datetime import datetime

# OpenAI for embeddings (same as IRIS faculty vectors)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dims - matches IRIS

# Synapse MCP endpoint (we'll simulate the harvest structure)
OUTPUT_DIR = Path("C:/dev/research/project-iris/data/synapse")
OUTPUT_DIR.mkdir(exist_ok=True)

def clean_description(desc: str) -> str:
    """Strip markdown/HTML formatting, normalize whitespace."""
    if not desc:
        return ""
    # Remove markdown images
    desc = re.sub(r'\$\{image\?[^}]+\}', '', desc)
    # Remove markdown links but keep text
    desc = re.sub(r'\$\{buttonlink\?[^}]+\}', '', desc)
    # Remove HTML tags
    desc = re.sub(r'<[^>]+>', '', desc)
    # Remove markdown formatting
    desc = re.sub(r'[#*_`]', '', desc)
    # Normalize whitespace
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Truncate to reasonable length for embedding
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
    """Process raw Synapse results into IRIS-compatible format."""
    processed = []
    
    for item in results:
        synapse_id = item.get("id", "")
        name = item.get("name", "")
        description = item.get("description", "")
        node_type = item.get("node_type", "")
        alias = item.get("alias", "")
        
        # Clean and prepare for embedding
        clean_desc = clean_description(description)
        
        # Create embedding text (combine name + description for richer semantics)
        embed_text = f"{name}. {clean_desc}" if clean_desc else name
        
        processed.append({
            "synapse_id": synapse_id,
            "name": name,
            "alias": alias,
            "node_type": node_type,
            "description_raw": description[:500] + "..." if len(description) > 500 else description,
            "description_clean": clean_desc,
            "embed_text": embed_text,
            "url": f"https://www.synapse.org/#!Synapse:{synapse_id}",
            "harvested_at": datetime.utcnow().isoformat()
        })
    
    return processed

def generate_embeddings(datasets: list[dict]) -> list[dict]:
    """Add embeddings to processed datasets."""
    print(f"\nGenerating embeddings for {len(datasets)} datasets...")
    
    for i, ds in enumerate(datasets):
        if ds["embed_text"]:
            try:
                ds["embedding"] = get_embedding(ds["embed_text"])
                print(f"  [{i+1}/{len(datasets)}] {ds['name'][:50]}... OK")
            except Exception as e:
                print(f"  [{i+1}/{len(datasets)}] {ds['name'][:50]}... FAILED: {e}")
                ds["embedding"] = []
        else:
            ds["embedding"] = []
    
    return datasets

def save_harvest(datasets: list[dict], query: str):
    """Save harvested data to JSON."""
    output_file = OUTPUT_DIR / f"harvest_{query.replace(' ', '_')}.json"
    
    # Save full data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "query": query,
            "harvested_at": datetime.utcnow().isoformat(),
            "count": len(datasets),
            "datasets": datasets
        }, f, indent=2)
    
    print(f"\nOK Saved {len(datasets)} datasets to {output_file}")
    
    # Also save embeddings-only file for FAISS import
    embeddings_file = OUTPUT_DIR / f"embeddings_{query.replace(' ', '_')}.json"
    embeddings_data = [
        {
            "id": ds["synapse_id"],
            "name": ds["name"],
            "embedding": ds["embedding"]
        }
        for ds in datasets if ds.get("embedding")
    ]
    
    with open(embeddings_file, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f)
    
    print(f"OK Saved {len(embeddings_data)} embeddings to {embeddings_file}")

# Test data from our Synapse query (simulating MCP response)
TEST_RESULTS = [
    {
        "id": "syn68713182",
        "name": "A multimodal human-computer interaction dataset for neurocognitive user state evaluation",
        "alias": "HCI_SENSE_42",
        "description": "SENSE-42: A multimodal Human-Computer Interaction dataset for Neurocognitive User State Evaluation. 42 participants over 2-hour continuous interaction session. Includes EEG (32-channel BioSemi), ECG, respiration, webcam, and behavioral data. Supports research on attention, mental/physical fatigue, cognitive workload.",
        "node_type": "project"
    },
    {
        "id": "syn11974918",
        "name": "Brain Cancer",
        "description": "Single-Cell RNAseq analysis of diffuse neoplastic infiltrating cells at the migrating front of human glioblastoma. 3,589 cells from 4 patients. Cells from tumor core and surrounding peripheral tissue. Analysis revealed cellular variation in tumor genome and transcriptome.",
        "node_type": "folder"
    },
    {
        "id": "syn26346373",
        "name": "Cortical Brain Organoids",
        "alias": "BrainOrganoids",
        "description": "Autism genes converge on asynchronous development of shared neuron classes. Single-cell multiomics atlas of organoid development. Collaboration between Paola Arlotta, Aviv Regev, and Joshua Levin labs.",
        "node_type": "project"
    },
    {
        "id": "syn22150694",
        "name": "Human Brain Tau Immunoprecipitation",
        "alias": "TauBrainIP",
        "description": "Tau Immunoprecipitation and Human Postmortem Brain Proteomics. Healthy control (n=4) and AD patient (n=4) frontal cortex brain samples. Immunoprecipitation with anti-Tau monoclonal antibody (TAU-5). Mass spectrometry analysis.",
        "node_type": "project"
    },
    {
        "id": "syn12033248",
        "name": "Integrative Analyses of iPSC-derived Brain Organoids",
        "description": "PsychENCODE Consortium iPSC study. Transcriptome and epigenome landscape of human cortical development modeled in organoids. ATACseq, single cell RNAseq, bulk RNAseq, ChIPseq across multiple terminal differentiation timepoints.",
        "node_type": "folder"
    }
]

if __name__ == "__main__":
    print("=" * 60)
    print("SYNAPSE HARVEST TEST - Brain Computer Interface Query")
    print("=" * 60)
    
    # Check for API key
    if not OPENAI_API_KEY:
        print("\n⚠️  OPENAI_API_KEY not set. Running without embeddings.")
    
    # Process results
    print(f"\nProcessing {len(TEST_RESULTS)} test results...")
    processed = process_synapse_results(TEST_RESULTS)
    
    # Show what we extracted
    print("\n--- Processed Datasets ---")
    for ds in processed:
        print(f"\n{ds['synapse_id']}: {ds['name']}")
        print(f"  Type: {ds['node_type']}")
        print(f"  URL: {ds['url']}")
        print(f"  Embed text ({len(ds['embed_text'])} chars): {ds['embed_text'][:100]}...")
    
    # Generate embeddings
    if OPENAI_API_KEY:
        processed = generate_embeddings(processed)
        
        # Verify embedding dimensions
        for ds in processed:
            if ds.get("embedding"):
                print(f"\nOK {ds['synapse_id']}: {len(ds['embedding'])} dimensions")
    
    # Save results
    save_harvest(processed, "brain_computer_interface")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
