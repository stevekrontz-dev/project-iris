import { NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://project-iris-production.up.railway.app';

interface ExternalResearcher {
  rank: number;
  name: string;
  institution: string;
  field: string;
  subfield: string | null;
  h_index: number;
  citations: number;
  works_count: number;
  openalex_id: string;
  orcid: string | null;
  semantic_score: number;
  weighted_score: number;
}

interface SearchResponse {
  query: string;
  total_indexed: number;
  query_time_ms: number;
  results: ExternalResearcher[];
}

// Extract just the ID from OpenAlex URL (e.g., "https://openalex.org/A1234567890" -> "A1234567890")
function extractOpenAlexId(url: string): string {
  if (!url) return '';
  const match = url.match(/\/([A-Z]\d+)$/);
  return match ? match[1] : url.replace(/[^a-zA-Z0-9]/g, '_');
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q') || '';
  const limit = parseInt(searchParams.get('limit') || '50');
  const hasScholar = searchParams.get('hasScholar');

  try {
    // If no search query, return top researchers by h-index
    const searchQuery = query || 'research';
    const apiUrl = `${API_URL}/search?q=${encodeURIComponent(searchQuery)}&limit=${limit}`;

    const res = await fetch(apiUrl);
    if (!res.ok) {
      throw new Error(`API responded with status ${res.status}`);
    }

    const data: SearchResponse = await res.json();

    // Transform to match frontend expected format
    const formatted = data.results.map((r, index) => {
      const cleanId = extractOpenAlexId(r.openalex_id) || `researcher-${index}`;
      return {
        id: cleanId,
        net_id: cleanId,
        name: r.name,
        title: r.field,
        department: r.subfield || r.field,
        college: r.institution,
        photo_url: null,
        h_index: r.h_index,
        citation_count: r.citations,
        interests: r.field ? [r.field, r.subfield].filter(Boolean) : [],
        publications: [],
        has_scholar: true,
        orcidId: r.orcid,
        works_count: r.works_count,
        semantic_score: r.semantic_score,
        openalex_url: r.openalex_id, // Keep the full URL for reference
      };
    });

    return NextResponse.json({
      researchers: formatted,
      total: data.total_indexed,
      offset: 0,
      limit
    });

  } catch (error) {
    console.error('Error fetching researchers:', error);
    return NextResponse.json({ error: 'Failed to fetch researchers' }, { status: 500 });
  }
}
