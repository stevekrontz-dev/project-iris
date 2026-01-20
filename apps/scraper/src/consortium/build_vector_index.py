"""
IRIS VECTOR INDEX BUILDER
=========================
Creates searchable vector embeddings for 208K+ researchers
Uses sentence-transformers for embeddings, FAISS for similarity search
"""
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Check dependencies
try:
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "sentence-transformers", "faiss-cpu", "--break-system-packages", "-q"])
    from sentence_transformers import SentenceTransformer
    import faiss

# Paths
DATA_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\consortium')
INPUT_FILE = DATA_DIR / 'southeast_r1r2_20260114_041911.json'
OUTPUT_DIR = Path(r'C:\dev\research\project-iris\data\vectors')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Model - all-MiniLM-L6-v2 is fast and good for semantic search
MODEL_NAME = 'all-MiniLM-L6-v2'

def create_researcher_text(r: dict) -> str:
    """Create searchable text from researcher record"""
    parts = [
        r.get('name', ''),
        r.get('institution', ''),
        r.get('field', ''),
        r.get('subfield', ''),
    ]
    # Add h-index context
    h = r.get('h_index', 0)
    if h > 100:
        parts.append('highly cited researcher prominent expert')
    elif h > 50:
        parts.append('established researcher senior scientist')
    elif h > 20:
        parts.append('active researcher')
    
    return ' '.join(p for p in parts if p)


def main():
    print('=' * 70)
    print('IRIS VECTOR INDEX BUILDER')
    print('=' * 70)
    
    # Load data
    print(f'\nLoading data from {INPUT_FILE.name}...')
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    researchers = data.get('researchers', [])
    print(f'Loaded {len(researchers):,} researchers')
    
    # Load model
    print(f'\nLoading model: {MODEL_NAME}...')
    model = SentenceTransformer(MODEL_NAME)
    embedding_dim = model.get_sentence_embedding_dimension()
    print(f'Embedding dimension: {embedding_dim}')
    
    # Create texts for embedding
    print('\nCreating search texts...')
    texts = [create_researcher_text(r) for r in researchers]
    
    # Show sample
    print('\nSample texts:')
    for i in range(min(3, len(texts))):
        print(f'  {i+1}. {texts[i][:80]}...')
    
    # Generate embeddings in batches
    print(f'\nGenerating embeddings for {len(texts):,} researchers...')
    batch_size = 512
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
        all_embeddings.append(embeddings)
        
        progress = min(i + batch_size, len(texts))
        pct = progress / len(texts) * 100
        print(f'  Progress: {progress:,}/{len(texts):,} ({pct:.1f}%)')
    
    # Combine embeddings
    embeddings_array = np.vstack(all_embeddings).astype('float32')
    print(f'\nEmbeddings shape: {embeddings_array.shape}')
    
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings_array)
    
    # Create FAISS index
    print('\nBuilding FAISS index...')
    
    # Use IVF for faster search on large datasets
    nlist = min(1000, len(researchers) // 100)  # Number of clusters
    quantizer = faiss.IndexFlatIP(embedding_dim)  # Inner product (cosine after normalization)
    index = faiss.IndexIVFFlat(quantizer, embedding_dim, nlist, faiss.METRIC_INNER_PRODUCT)
    
    # Train index
    print(f'  Training with {nlist} clusters...')
    index.train(embeddings_array)
    
    # Add vectors
    print('  Adding vectors...')
    index.add(embeddings_array)
    
    print(f'  Index size: {index.ntotal:,} vectors')
    
    # Save index
    index_file = OUTPUT_DIR / 'iris_researchers.index'
    print(f'\nSaving index to {index_file}...')
    faiss.write_index(index, str(index_file))
    
    # Save metadata (for lookup after search)
    metadata = []
    for i, r in enumerate(researchers):
        metadata.append({
            'id': i,
            'name': r.get('name', ''),
            'institution': r.get('institution', ''),
            'h_index': r.get('h_index', 0),
            'citations': r.get('citations', 0),
            'field': r.get('field', ''),
            'openalex_id': r.get('openalex_id', ''),
        })
    
    metadata_file = OUTPUT_DIR / 'iris_metadata.json'
    print(f'Saving metadata to {metadata_file}...')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f)
    
    # Test search
    print('\n' + '=' * 70)
    print('TESTING SEARCH')
    print('=' * 70)
    
    test_queries = [
        'brain computer interface neural engineering',
        'machine learning artificial intelligence',
        'cancer immunotherapy treatment',
        'climate change environmental science',
        'robotics automation control systems',
    ]
    
    index.nprobe = 50  # Search more clusters for accuracy
    
    for query in test_queries:
        print(f'\nQuery: "{query}"')
        query_vec = model.encode([query], convert_to_numpy=True).astype('float32')
        faiss.normalize_L2(query_vec)
        
        D, I = index.search(query_vec, 5)  # Top 5 results
        
        for rank, (idx, score) in enumerate(zip(I[0], D[0]), 1):
            r = researchers[idx]
            print(f'  {rank}. {r["name"][:35]:<35} h={r["h_index"]:3} | {r["institution"][:20]} | score={score:.3f}')
    
    # Summary
    print('\n' + '=' * 70)
    print('VECTORIZATION COMPLETE')
    print('=' * 70)
    print(f'Researchers indexed: {len(researchers):,}')
    print(f'Index file: {index_file} ({index_file.stat().st_size / 1024 / 1024:.1f} MB)')
    print(f'Metadata file: {metadata_file}')
    print(f'Model: {MODEL_NAME}')
    print(f'Embedding dim: {embedding_dim}')


if __name__ == '__main__':
    main()
