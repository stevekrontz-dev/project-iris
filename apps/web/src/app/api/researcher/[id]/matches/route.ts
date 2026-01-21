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

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get('limit') || '5');

  try {
    // The id contains the researcher info - parse the field from it
    // For external API researchers, the id format is the openalex_id
    // We'll use the field info that was passed, or default to searching by similar fields

    // First, try to find the original researcher's field by searching
    // We'll extract a search term from the ID or use a default
    let searchQuery = 'research collaboration';

    // If the ID looks like an OpenAlex ID, extract field info differently
    // For now, use a simple heuristic - the frontend should pass field info
    const fieldParam = searchParams.get('field');
    if (fieldParam) {
      searchQuery = fieldParam;
    }

    // Search for similar researchers
    const apiUrl = `${API_URL}/search?q=${encodeURIComponent(searchQuery)}&limit=${limit + 1}`;
    const res = await fetch(apiUrl);

    if (!res.ok) {
      throw new Error(`API responded with status ${res.status}`);
    }

    const data: SearchResponse = await res.json();

    // Filter out the original researcher and transform results
    const matches = data.results
      .filter(r => r.openalex_id !== id)
      .slice(0, limit)
      .map((r, index) => {
        // Calculate a match score based on semantic similarity
        const matchScore = Math.max(0.5, 1 - (index * 0.1)); // Higher rank = higher score

        return {
          researcher: {
            net_id: r.openalex_id,
            name: r.name,
            department: r.field,
            institution: r.institution,
            photo_url: null,
            h_index: r.h_index,
            citation_count: r.citations,
            interests: [r.field, r.subfield].filter(Boolean) as string[],
          },
          matchScore,
          matchType: 'COLLABORATOR' as const,
          explanation: `Researches ${r.field}${r.subfield ? ` with focus on ${r.subfield}` : ''}. Has ${r.works_count} publications with ${r.citations.toLocaleString()} citations.`,
          factors: [
            {
              factor: 'Research Area',
              weight: matchScore * 0.6,
              description: `Both work in ${r.field}`,
              icon: '🔬'
            },
            {
              factor: 'Citation Impact',
              weight: Math.min(r.h_index / 100, 0.3),
              description: `h-index: ${r.h_index}`,
              icon: '📊'
            },
          ]
        };
      });

    return NextResponse.json({ matches, total: matches.length });
  } catch (error) {
    console.error('Match error:', error);
    return NextResponse.json({ error: 'Failed to find matches' }, { status: 500 });
  }
}
