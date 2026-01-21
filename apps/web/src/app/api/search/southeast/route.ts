import { NextRequest, NextResponse } from 'next/server';

const SEARCH_API = process.env.NEXT_PUBLIC_API_URL || 'https://project-iris-production.up.railway.app';

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get('q');
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '20');
  const minH = parseInt(request.nextUrl.searchParams.get('min_h') || '0');
  const institution = request.nextUrl.searchParams.get('institution') || '';
  const hWeight = parseFloat(request.nextUrl.searchParams.get('h_weight') || '0.3');

  if (!query) {
    return NextResponse.json({ error: 'Missing query parameter ?q=' }, { status: 400 });
  }

  try {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
      min_h_index: minH.toString(),
      h_weight: hWeight.toString(),
    });
    
    if (institution) {
      params.append('institution', institution);
    }

    const response = await fetch(`${SEARCH_API}/search?${params}`, {
      headers: { 'Accept': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Search API error: ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json({
      query: data.query,
      total_indexed: data.total_indexed,
      count: data.results.length,
      search_time_ms: data.search_time_ms,
      results: data.results.map((r: any) => ({
        name: r.name,
        institution: r.institution,
        field: r.field,
        subfield: r.subfield,
        h_index: r.h_index,
        citations: r.citations,
        works_count: r.works_count,
        openalex_id: r.openalex_id,
        orcid: r.orcid,
        score: r.weighted_score,
        semantic_score: r.semantic_score,
      })),
    });
  } catch (error: any) {
    console.error('Southeast search error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
