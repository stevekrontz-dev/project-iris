"""
IRIS VECTOR INDEXER
===================
Vectorize 208K Southeast researchers for semantic search
Uses sentence-transformers for embeddings, FAISS for indexing
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
except ImportError as e:
    print(f"Installing dependencies: {e}")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
                          'sentence-transformers', 'faiss-cpu', '--break-system-packages', '-q'])
    from sentence_transformers import SentenceTransformer
    import faiss

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\consortium\southeast_r1r2_20260114_041911.json')
OUTPUT_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\consortium\vector_index')

# Model for scientific/academic text
MODEL_NAME = 'all-MiniLM-L6-v2'  # Fast, good quality, 384 dimensions
BATCH_SIZE = 512


def create_search_text(researcher: dict) -> str:
    """Create searchable text from researcher record"""
    parts = []
    
    # Name
    if researcher.get('name'):
        parts.append(researcher['name'])
    
    # Institution
    if researcher.get('institution'):
        parts.append(researcher['institution'])
    
    # Field/subfield
    if researcher.get('field'):
        parts.append(researcher['field'])
    if researcher.get('subfield'):
        parts.append(researcher['subfield'])
    
    # Metrics as context
    h = researcher.get('h_index', 0)
    c = researcher.get('citations', 0)
    if h > 50:
        parts.append('highly cited researcher')
    if h > 100:
        parts.append('world leading expert')
    
    return ' | '.join(parts)


def main():
    print('=' * 70)
    print('IRIS VECTOR INDEXER')
    print('=' * 70)
    print(f'Started: {datetime.now().isoformat()}')
    print(f'Model: {MODEL_NAME}')
    print()
    
    # Load data
    print('Loading researcher data...')
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    researchers = data.get('researchers', [])
    print(f'Loaded {len(researchers):,} researchers')
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load model
    print(f'\nLoading embedding model: {MODEL_NAME}')
    model = SentenceTransformer(MODEL_NAME)
    embedding_dim = model.get_sentence_embedding_dimension()
    print(f'Embedding dimension: {embedding_dim}')
    
    # Create search texts
    print('\nCreating search texts...')
    texts = []
    valid_researchers = []
    for r in researchers:
        text = create_search_text(r)
        if text.strip():
            texts.append(text)
            valid_researchers.append(r)
    
    print(f'Valid researchers: {len(valid_researchers):,}')
    
    # Generate embeddings in batches
    print(f'\nGenerating embeddings (batch size: {BATCH_SIZE})...')
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
        
        embeddings = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
        all_embeddings.append(embeddings)
        
        if batch_num % 50 == 0 or batch_num == total_batches:
            print(f'  Batch {batch_num}/{total_batches} ({i + len(batch):,}/{len(texts):,})')
    
    # Combine embeddings
    embeddings_array = np.vstack(all_embeddings).astype('float32')
    print(f'\nEmbeddings shape: {embeddings_array.shape}')
    
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings_array)
    
    # Create FAISS index
    print('\nBuilding FAISS index...')
    
    # Use IVF for faster search on large datasets
    nlist = min(1000, len(valid_researchers) // 100)  # Number of clusters
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
    index_path = OUTPUT_DIR / 'southeast_researchers.index'
    faiss.write_index(index, str(index_path))
    print(f'\nSaved index: {index_path}')
    
    # Save metadata
    metadata = {
        'created': datetime.now().isoformat(),
        'source': str(INPUT_FILE),
        'model': MODEL_NAME,
        'embedding_dim': embedding_dim,
        'num_vectors': len(valid_researchers),
        'nlist': nlist,
        'index_type': 'IVFFlat',
    }
    
    metadata_path = OUTPUT_DIR / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save researcher lookup (id -> researcher data)
    lookup = {i: r for i, r in enumerate(valid_researchers)}
    lookup_path = OUTPUT_DIR / 'researcher_lookup.json'
    with open(lookup_path, 'w', encoding='utf-8') as f:
        json.dump(lookup, f, ensure_ascii=False)
    
    print(f'Saved metadata: {metadata_path}')
    print(f'Saved lookup: {lookup_path}')
    
    # Test search
    print('\n' + '=' * 70)
    print('TEST SEARCHES')
    print('=' * 70)
    
    test_queries = [
        'brain computer interface neural engineering',
        'machine learning artificial intelligence',
        'cancer immunotherapy treatment',
        'materials science nanotechnology',
        'climate change environmental science',
    ]
    
    index.nprobe = 50  # Search more clusters for better recall
    
    for query in test_queries:
        query_vec = model.encode([query], convert_to_numpy=True).astype('float32')
        faiss.normalize_L2(query_vec)
        
        D, I = index.search(query_vec, 5)
        
        print(f'\nQuery: "{query}"')
        for rank, (idx, score) in enumerate(zip(I[0], D[0]), 1):
            r = valid_researchers[idx]
            print(f'  {rank}. {r["name"][:30]:<30} | h={r.get("h_index",0):>3} | {r.get("institution","")[:20]} | score={score:.3f}')
    
    print('\n' + '=' * 70)
    print('VECTORIZATION COMPLETE')
    print('=' * 70)
    print(f'Total vectors: {len(valid_researchers):,}')
    print(f'Index file: {index_path}')
    print(f'Index size: {index_path.stat().st_size / 1024 / 1024:.1f} MB')


if __name__ == '__main__':
    main()
