"""
IRIS FAISS Merge - Combines faculty vectors with Synapse dataset vectors
Creates unified search index for cross-matching
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("Warning: FAISS not installed. Will export vectors only.")

# Paths
IRIS_DATA = Path("C:/dev/research/project-iris/data/vectors")
SYNAPSE_DATA = Path("C:/dev/research/project-iris/data/synapse/dedupe")
OUTPUT_DIR = Path("C:/dev/research/project-iris/data/combined")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_synapse_embeddings() -> tuple[list[str], np.ndarray]:
    """Load Synapse dataset embeddings"""
    dedupe_file = SYNAPSE_DATA / "all_datasets_unique.json"
    
    if not dedupe_file.exists():
        print(f"Error: {dedupe_file} not found")
        return [], np.array([])
    
    with open(dedupe_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ids = []
    embeddings = []
    
    for ds in data.get("datasets", []):
        if ds.get("embedding"):
            ids.append(f"syn:{ds['synapse_id']}")
            embeddings.append(ds["embedding"])
    
    if embeddings:
        return ids, np.array(embeddings, dtype=np.float32)
    return [], np.array([])

def load_iris_embeddings() -> tuple[list[str], np.ndarray]:
    """Load existing IRIS faculty embeddings"""
    index_file = IRIS_DATA / "iris_researchers.index"
    metadata_file = IRIS_DATA / "iris_metadata.json"
    
    if not index_file.exists() or not metadata_file.exists():
        print("Warning: IRIS faculty index not found")
        return [], np.array([])
    
    # Load metadata for IDs
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    ids = [f"faculty:{r.get('id', i)}" for i, r in enumerate(metadata.get("researchers", []))]
    
    # Load FAISS index and extract vectors
    if HAS_FAISS:
        index = faiss.read_index(str(index_file))
        n = index.ntotal
        d = index.d
        vectors = np.zeros((n, d), dtype=np.float32)
        for i in range(n):
            vectors[i] = index.reconstruct(i)
        return ids, vectors
    
    return ids, np.array([])

def create_combined_index(faculty_ids: list, faculty_vecs: np.ndarray,
                          synapse_ids: list, synapse_vecs: np.ndarray) -> dict:
    """Create combined FAISS index"""
    
    # Combine
    all_ids = faculty_ids + synapse_ids
    
    if len(faculty_vecs) > 0 and len(synapse_vecs) > 0:
        all_vecs = np.vstack([faculty_vecs, synapse_vecs])
    elif len(synapse_vecs) > 0:
        all_vecs = synapse_vecs
    else:
        all_vecs = faculty_vecs
    
    print(f"\nCombined vectors:")
    print(f"  Faculty: {len(faculty_ids)}")
    print(f"  Synapse: {len(synapse_ids)}")
    print(f"  Total: {len(all_ids)}")
    print(f"  Dimensions: {all_vecs.shape[1] if len(all_vecs) > 0 else 0}")
    
    # Save ID mapping
    id_mapping = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_vectors": len(all_ids),
        "faculty_count": len(faculty_ids),
        "synapse_count": len(synapse_ids),
        "ids": all_ids
    }
    
    mapping_file = OUTPUT_DIR / "combined_id_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(id_mapping, f, indent=2)
    print(f"\nID mapping saved to: {mapping_file}")
    
    # Save raw vectors for portability
    vectors_file = OUTPUT_DIR / "combined_vectors.npy"
    np.save(vectors_file, all_vecs)
    print(f"Vectors saved to: {vectors_file}")
    
    # Create FAISS index
    if HAS_FAISS and len(all_vecs) > 0:
        d = all_vecs.shape[1]
        
        # Use IVF for larger datasets
        if len(all_vecs) > 10000:
            nlist = min(100, len(all_vecs) // 100)
            quantizer = faiss.IndexFlatIP(d)
            index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(all_vecs)
            index.train(all_vecs)
            index.add(all_vecs)
        else:
            index = faiss.IndexFlatIP(d)
            faiss.normalize_L2(all_vecs)
            index.add(all_vecs)
        
        index_file = OUTPUT_DIR / "combined_iris.index"
        faiss.write_index(index, str(index_file))
        print(f"FAISS index saved to: {index_file}")
    
    return id_mapping

def run_merge():
    """Execute the merge"""
    print("="*60)
    print("IRIS FAISS MERGE - Faculty + Synapse Datasets")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("="*60)
    
    # Load Synapse
    print("\nLoading Synapse embeddings...")
    synapse_ids, synapse_vecs = load_synapse_embeddings()
    print(f"  Loaded: {len(synapse_ids)} datasets")
    
    # Load IRIS faculty
    print("\nLoading IRIS faculty embeddings...")
    faculty_ids, faculty_vecs = load_iris_embeddings()
    print(f"  Loaded: {len(faculty_ids)} faculty")
    
    # Merge
    print("\nCreating combined index...")
    stats = create_combined_index(faculty_ids, faculty_vecs, synapse_ids, synapse_vecs)
    
    print("\n" + "="*60)
    print("MERGE COMPLETE")
    print("="*60)
    
    return stats

if __name__ == "__main__":
    run_merge()
