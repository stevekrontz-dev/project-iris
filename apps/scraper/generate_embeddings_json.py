#!/usr/bin/env python3
"""
Generate embeddings for enriched faculty data using Ollama.
Reads from faculty_openalex_enriched.json, writes to faculty_with_embeddings.json
"""

import json
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"
INPUT_FILE = Path(__file__).parent / "output" / "faculty_openalex_enriched.json"
OUTPUT_FILE = Path(__file__).parent / "output" / "faculty_with_embeddings.json"
PROGRESS_FILE = Path(__file__).parent / "output" / "embedding_progress.json"
BATCH_SIZE = 10
MAX_WORKERS = 4

def get_embedding(text: str) -> list[float]:
    """Get embedding from Ollama"""
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": text[:4000]  # Limit text length
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["embedding"]

def build_text(faculty: dict) -> str:
    """Build text for embedding from faculty data"""
    parts = [
        faculty.get("name", ""),
        faculty.get("department", ""),
        faculty.get("college", ""),
    ]
    
    # Add OpenAlex topics
    topics = faculty.get("openalex_topics", [])
    if topics:
        parts.extend(topics[:10])
    
    # Add OpenAlex concepts
    concepts = faculty.get("openalex_concepts", [])
    if concepts:
        parts.extend(concepts[:10])
    
    # Add research interests
    interests = faculty.get("research_interests", [])
    if interests:
        parts.extend(interests[:10])
    
    # Add publication titles
    works = faculty.get("openalex_works", [])
    for w in works[:5]:
        if w.get("title"):
            parts.append(w["title"])
    
    # Clean and join
    clean_parts = [str(p).strip() for p in parts if p]
    return " ".join(clean_parts)

def process_faculty(idx: int, faculty: dict) -> tuple[int, dict, list[float] | None]:
    """Process a single faculty member"""
    text = build_text(faculty)
    if len(text) < 10:
        return idx, faculty, None
    
    try:
        embedding = get_embedding(text)
        return idx, faculty, embedding
    except Exception as e:
        print(f"  Error for {faculty.get('name', 'unknown')}: {e}")
        return idx, faculty, None

def main():
    print(f"=== Embedding Generation ===")
    print(f"Model: {MODEL}")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    
    # Load faculty data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        faculty_list = json.load(f)
    
    print(f"Loaded {len(faculty_list)} faculty members")
    
    # Check for existing progress
    start_idx = 0
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            start_idx = progress.get("last_index", 0)
            if start_idx > 0:
                print(f"Resuming from index {start_idx}")
    
    # Process in batches
    processed = 0
    errors = 0
    start_time = time.time()
    
    for batch_start in range(start_idx, len(faculty_list), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(faculty_list))
        batch = [(i, faculty_list[i]) for i in range(batch_start, batch_end)]
        
        # Process batch with thread pool
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_faculty, idx, fac) for idx, fac in batch]
            
            for future in as_completed(futures):
                idx, faculty, embedding = future.result()
                if embedding:
                    faculty_list[idx]["embedding"] = embedding
                    processed += 1
                else:
                    errors += 1
        
        # Progress update
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        remaining = (len(faculty_list) - batch_end) / rate if rate > 0 else 0
        
        print(f"Batch {batch_start}-{batch_end}: {processed} done, {errors} errors, "
              f"{rate:.1f}/sec, ~{remaining/60:.1f}min remaining")
        
        # Save progress
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({"last_index": batch_end, "processed": processed, "errors": errors}, f)
        
        # Save intermediate results every 100
        if batch_end % 100 == 0:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(faculty_list, f, indent=2)
    
    # Final save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(faculty_list, f, indent=2)
    
    elapsed = time.time() - start_time
    print(f"\n=== Complete ===")
    print(f"Processed: {processed}")
    print(f"Errors: {errors}")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
