"""
IRIS SEARCH API
===============
FastAPI server for semantic researcher search
Weighted ranking: semantic similarity + h-index + citations
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import urllib.request
import os

# Install dependencies
import subprocess
import sys

def ensure_deps():
    deps = ['fastapi', 'uvicorn', 'sentence-transformers', 'faiss-cpu']
    for dep in deps:
        try:
            __import__(dep.replace('-', '_').split('[')[0])
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep,
                                  '--break-system-packages', '-q'])

ensure_deps()

# GitHub Release download URLs for LFS files
RELEASE_BASE_URL = "https://github.com/stevekrontz-dev/project-iris/releases/download/v1.0.0"
FAISS_INDEX_URL = f"{RELEASE_BASE_URL}/southeast_researchers.index"
LOOKUP_URL = f"{RELEASE_BASE_URL}/researcher_lookup.json"
METADATA_URL = f"{RELEASE_BASE_URL}/metadata.json"


def is_lfs_pointer(file_path: Path) -> bool:
    """Check if a file is a Git LFS pointer (not actual content)."""
    if not file_path.exists():
        return True  # Treat missing as needing download
    with open(file_path, 'rb') as f:
        header = f.read(20)
    return header.startswith(b'version ')


def ensure_file_downloaded(file_path: Path, url: str, name: str) -> bool:
    """Download a file from GitHub Releases if missing or LFS pointer."""
    if not file_path.exists():
        print(f"  {name} not found, downloading...")
        return download_file(file_path, url, name)

    if is_lfs_pointer(file_path):
        print(f"  {name} is LFS pointer, downloading actual file...")
        return download_file(file_path, url, name)

    print(f"  {name} exists and valid ({file_path.stat().st_size / 1e6:.2f} MB)")
    return True


def download_file(file_path: Path, url: str, name: str) -> bool:
    """Download a file from GitHub Releases (handles redirects)."""
    try:
        print(f"  Downloading {name}...")
        print(f"  URL: {url}")

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check for GitHub token (needed for private repos)
        github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')

        # Use subprocess with curl for reliable downloads with redirects
        import shutil
        if shutil.which('curl'):
            print(f"  Using curl for download...")
            cmd = ['curl', '-L', '-o', str(file_path), '--progress-bar']
            if github_token:
                cmd.extend(['-H', f'Authorization: token {github_token}'])
            cmd.extend(['-H', 'Accept: application/octet-stream', url])
            result = subprocess.run(cmd, capture_output=False)
            if result.returncode == 0 and file_path.exists() and file_path.stat().st_size > 100:
                print(f"  Download complete: {file_path.stat().st_size / 1e6:.2f} MB")
                return True
            else:
                print(f"  curl download failed")
                return False

        print(f"  ERROR: curl not available")
        return False

    except Exception as e:
        print(f"  ERROR downloading {name}: {e}")
        import traceback
        traceback.print_exc()
        return False

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import faiss

# Paths - support both local and deployed environments
import os
BASE_DIR = Path(os.getenv('DATA_DIR', r'C:\dev\research\project-iris\apps\scraper\src\consortium'))
INDEX_DIR = BASE_DIR / 'data' / 'consortium' / 'vector_index'
INDEX_PATH = INDEX_DIR / 'southeast_researchers.index'
LOOKUP_PATH = INDEX_DIR / 'researcher_lookup.json'
METADATA_PATH = INDEX_DIR / 'metadata.json'

# Global state
model = None
index = None
lookup = None
metadata = None


class SearchResult(BaseModel):
    rank: int
    name: str
    institution: str
    field: Optional[str]
    subfield: Optional[str]
    h_index: int
    citations: int
    works_count: int
    openalex_id: Optional[str]
    orcid: Optional[str]
    semantic_score: float
    weighted_score: float


class SearchResponse(BaseModel):
    query: str
    total_indexed: int
    results: List[SearchResult]
    search_time_ms: float


def load_resources():
    global model, index, lookup, metadata

    print('Loading resources...')

    # Load model
    print('  Loading embedding model...')
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Ensure all LFS files are downloaded
    print('  Checking data files...')
    if not ensure_file_downloaded(INDEX_PATH, FAISS_INDEX_URL, "FAISS index"):
        raise RuntimeError("Failed to load or download FAISS index")
    if not ensure_file_downloaded(LOOKUP_PATH, LOOKUP_URL, "researcher lookup"):
        raise RuntimeError("Failed to load or download researcher lookup")
    if not ensure_file_downloaded(METADATA_PATH, METADATA_URL, "metadata"):
        raise RuntimeError("Failed to load or download metadata")

    # Load FAISS index
    print('  Loading FAISS index...')
    index = faiss.read_index(str(INDEX_PATH))
    index.nprobe = 50  # Search more clusters for better recall

    # Load lookup
    print('  Loading researcher lookup...')
    with open(LOOKUP_PATH, 'r', encoding='utf-8') as f:
        lookup = json.load(f)
    # Convert string keys to int
    lookup = {int(k): v for k, v in lookup.items()}

    # Load metadata
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)
    
    print(f'  Loaded {len(lookup):,} researchers')
    print('Resources ready!')


# Create FastAPI app
app = FastAPI(
    title="IRIS Research Search API",
    description="Semantic search across 208K Southeast R1/R2 researchers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    load_resources()


@app.get("/")
async def root():
    return {
        "service": "IRIS Research Search API",
        "version": "1.0.0",
        "total_researchers": len(lookup) if lookup else 0,
        "status": "ready" if index else "loading"
    }


@app.get("/health")
async def health():
    """Health check endpoint for Railway."""
    return {"status": "healthy", "index_loaded": index is not None}


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    min_h_index: int = Query(0, ge=0, description="Minimum h-index filter"),
    institution: Optional[str] = Query(None, description="Filter by institution (partial match)"),
    h_weight: float = Query(0.3, ge=0, le=1, description="Weight for h-index in ranking"),
    citation_weight: float = Query(0.1, ge=0, le=1, description="Weight for citations in ranking")
):
    """
    Semantic search for researchers with weighted ranking.
    
    Ranking formula:
    weighted_score = semantic_score * (1 - h_weight - citation_weight) 
                   + normalized_h_index * h_weight
                   + normalized_citations * citation_weight
    """
    import time
    start = time.time()
    
    # Get more candidates for filtering/reranking
    fetch_limit = min(limit * 10, 500)
    
    # Encode query
    query_vec = model.encode([q], convert_to_numpy=True).astype('float32')
    faiss.normalize_L2(query_vec)
    
    # Search
    D, I = index.search(query_vec, fetch_limit)
    
    # Build results with filtering and weighted ranking
    candidates = []
    
    # Get max values for normalization
    max_h = max((lookup.get(int(i), {}).get('h_index', 0) for i in I[0]), default=1) or 1
    max_c = max((lookup.get(int(i), {}).get('citations', 0) for i in I[0]), default=1) or 1
    
    for idx, score in zip(I[0], D[0]):
        r = lookup.get(int(idx), {})
        if not r:
            continue
        
        h = r.get('h_index', 0)
        c = r.get('citations', 0)
        inst = r.get('institution', '')
        
        # Apply filters
        if h < min_h_index:
            continue
        if institution and institution.lower() not in inst.lower():
            continue
        
        # Calculate weighted score
        semantic_weight = 1.0 - h_weight - citation_weight
        normalized_h = h / max_h
        normalized_c = c / max_c
        
        weighted = (score * semantic_weight + 
                   normalized_h * h_weight + 
                   normalized_c * citation_weight)
        
        candidates.append({
            'idx': idx,
            'semantic_score': float(score),
            'weighted_score': float(weighted),
            'researcher': r
        })
    
    # Sort by weighted score
    candidates.sort(key=lambda x: -x['weighted_score'])
    
    # Build response
    results = []
    for rank, c in enumerate(candidates[:limit], 1):
        r = c['researcher']
        results.append(SearchResult(
            rank=rank,
            name=r.get('name', ''),
            institution=r.get('institution', ''),
            field=r.get('field'),
            subfield=r.get('subfield'),
            h_index=r.get('h_index', 0),
            citations=r.get('citations', 0),
            works_count=r.get('works_count', 0),
            openalex_id=r.get('openalex_id'),
            orcid=r.get('orcid'),
            semantic_score=c['semantic_score'],
            weighted_score=c['weighted_score']
        ))
    
    elapsed = (time.time() - start) * 1000
    
    return SearchResponse(
        query=q,
        total_indexed=len(lookup),
        results=results,
        search_time_ms=round(elapsed, 2)
    )


@app.get("/stats")
async def stats():
    """Get index statistics"""
    if not lookup:
        return {"error": "Index not loaded"}
    
    researchers = list(lookup.values())
    
    # Institution counts
    inst_counts = {}
    for r in researchers:
        inst = r.get('institution', 'Unknown')
        inst_counts[inst] = inst_counts.get(inst, 0) + 1
    
    # Top institutions
    top_inst = sorted(inst_counts.items(), key=lambda x: -x[1])[:15]
    
    # h-index distribution
    h_indices = [r.get('h_index', 0) for r in researchers]
    
    return {
        "total_researchers": len(researchers),
        "total_citations": sum(r.get('citations', 0) for r in researchers),
        "avg_h_index": round(np.mean(h_indices), 2),
        "max_h_index": max(h_indices),
        "h_index_percentiles": {
            "50th": int(np.percentile(h_indices, 50)),
            "75th": int(np.percentile(h_indices, 75)),
            "90th": int(np.percentile(h_indices, 90)),
            "99th": int(np.percentile(h_indices, 99)),
        },
        "top_institutions": dict(top_inst),
        "index_metadata": metadata
    }


@app.get("/researcher/{idx}")
async def get_researcher(idx: int):
    """Get researcher by index"""
    if idx not in lookup:
        return {"error": "Researcher not found"}
    return lookup[idx]


@app.get("/name")
async def search_by_name(
    q: str = Query(..., description="Name to search for"),
    limit: int = Query(20, ge=1, le=100)
):
    """Search researchers by name (handles first + last, partial matches)"""
    terms = q.lower().split()
    matches = []
    
    for idx, r in lookup.items():
        name = r.get('name', '').lower()
        
        # Check if ALL search terms appear in name
        if all(term in name for term in terms):
            matches.append({
                'name': r.get('name', ''),
                'institution': r.get('institution', ''),
                'field': r.get('field'),
                'subfield': r.get('subfield'),
                'h_index': r.get('h_index', 0),
                'citations': r.get('citations', 0),
                'works_count': r.get('works_count', 0),
                'openalex_id': r.get('openalex_id'),
                'orcid': r.get('orcid'),
            })
    
    # Sort by h-index descending
    matches.sort(key=lambda x: -x['h_index'])
    
    return {
        'query': q,
        'count': len(matches[:limit]),
        'results': matches[:limit]
    }


@app.get("/top")
async def top_researchers(
    limit: int = Query(50, ge=1, le=500),
    institution: Optional[str] = Query(None),
    field: Optional[str] = Query(None)
):
    """Get top researchers by h-index"""
    candidates = []
    
    for idx, r in lookup.items():
        if institution and institution.lower() not in r.get('institution', '').lower():
            continue
        if field and field.lower() not in (r.get('field', '') + ' ' + r.get('subfield', '')).lower():
            continue
        candidates.append(r)
    
    # Sort by h-index
    candidates.sort(key=lambda x: -x.get('h_index', 0))
    
    return {
        "total_matched": len(candidates),
        "researchers": candidates[:limit]
    }


if __name__ == '__main__':
    import uvicorn
    print('Starting IRIS Search API on http://localhost:8000')
    uvicorn.run(app, host='0.0.0.0', port=8000)
