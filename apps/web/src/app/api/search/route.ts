import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://project-iris-production.up.railway.app';

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get('q');
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '10');

  if (!query) {
    return NextResponse.json({ error: 'Missing query parameter ?q=' }, { status: 400 });
  }

  try {
    // Call external search API
    const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}&limit=${limit}`);

    if (!response.ok) {
      throw new Error(`Search API error: ${response.status}`);
    }

    const data = await response.json();

    // Transform to expected format
    const results = data.results.map((r: any) => ({
      net_id: r.openalex_id,
      name: r.name,
      title: r.field,
      department: r.subfield || r.field,
      college: r.institution,
      email: null,
      photo_url: null,
      h_index: r.h_index,
      citations: r.citations,
      works_count: r.works_count,
      topics: [r.field, r.subfield].filter(Boolean),
      score: r.semantic_score
    }));

    return NextResponse.json({
      query,
      count: results.length,
      results
    });

  } catch (error: any) {
    console.error('Semantic search error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
