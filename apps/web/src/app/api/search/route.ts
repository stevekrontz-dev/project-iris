import { NextRequest, NextResponse } from 'next/server';

const OLLAMA_URL = 'http://localhost:11434/api/embeddings';
const MODEL = 'nomic-embed-text';
const DATA_PATH = 'C:/dev/research/project-iris/apps/scraper/output/faculty_with_embeddings.json';

// Cache faculty data in memory
let facultyCache: any[] | null = null;

async function loadFaculty() {
  if (facultyCache) return facultyCache;
  
  const fs = await import('fs/promises');
  const data = await fs.readFile(DATA_PATH, 'utf-8');
  facultyCache = JSON.parse(data);
  return facultyCache;
}

async function getEmbedding(text: string): Promise<number[]> {
  const res = await fetch(OLLAMA_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: MODEL, prompt: text.slice(0, 4000) })
  });
  
  if (!res.ok) throw new Error(`Ollama error: ${res.status}`);
  const data = await res.json();
  return data.embedding;
}

function cosineSimilarity(a: number[], b: number[]): number {
  if (!a || !b || a.length !== b.length) return 0;
  
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get('q');
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '10');
  
  if (!query) {
    return NextResponse.json({ error: 'Missing query parameter ?q=' }, { status: 400 });
  }
  
  try {
    // Load faculty data
    const faculty = await loadFaculty();
    
    // Get query embedding
    const queryEmbedding = await getEmbedding(query);
    
    // Score all faculty
    const scored = (faculty || [])
      .filter((f: any) => f.embedding && f.embedding.length > 0)
      .map((f: any) => ({
        net_id: f.net_id,
        name: f.name,
        title: f.title,
        department: f.department?.split('\n')[0],
        college: f.college?.split('\n')[0],
        email: f.email,
        photo_url: f.photo_url,
        h_index: f.openalex_h_index || f.h_index,
        citations: f.openalex_cited_by_count || f.citation_count,
        works_count: f.openalex_works_count,
        topics: f.openalex_topics?.slice(0, 5) || [],
        score: cosineSimilarity(queryEmbedding, f.embedding)
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
    
    return NextResponse.json({
      query,
      count: scored.length,
      results: scored
    });
    
  } catch (error: any) {
    console.error('Semantic search error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
