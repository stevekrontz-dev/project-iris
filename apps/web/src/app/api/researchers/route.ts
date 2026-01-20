import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';

const prisma = new PrismaClient();

const DATA_PATHS = [
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_api_enriched.json',
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_library.json',
];

interface JsonResearcher {
  email?: string;
  h_index?: number;
  citation_count?: number;
  scholar?: {
    interests?: string[];
    h_index?: number;
    citedby?: number;
    publications?: Array<{ title: string; year?: number }>;
  };
}

let cachedData: JsonResearcher[] | null = null;

function loadJsonData(): JsonResearcher[] {
  if (cachedData) return cachedData;
  for (const p of DATA_PATHS) {
    try {
      if (fs.existsSync(p)) {
        cachedData = JSON.parse(fs.readFileSync(p, 'utf-8'));
        return cachedData!;
      }
    } catch { /* skip */ }
  }
  return [];
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q')?.toLowerCase();
  const limit = parseInt(searchParams.get('limit') || '50');
  const offset = parseInt(searchParams.get('offset') || '0');

  try {
    const where: any = {};
    if (query) {
      where.OR = [
        { firstName: { contains: query, mode: 'insensitive' } },
        { lastName: { contains: query, mode: 'insensitive' } },
        { bio: { contains: query, mode: 'insensitive' } },
        { position: { contains: query, mode: 'insensitive' } },
      ];
    }

    const total = await prisma.researcher.count({ where });
    const researchers = await prisma.researcher.findMany({
      where,
      include: {
        department: { include: { college: true } },
        user: { select: { email: true } }
      },
      take: limit,
      skip: offset,
      orderBy: { lastName: 'asc' }
    });

    const jsonData = loadJsonData();

    const formatted = researchers.map((r: typeof researchers[number]) => {
      const email = r.user?.email?.toLowerCase();
      const enrichment = jsonData.find(j => j.email?.toLowerCase() === email);

      return {
        id: r.id,
        net_id: r.id,
        firstName: r.firstName,
        lastName: r.lastName,
        name: (r.firstName || '') + ' ' + (r.lastName || ''),
        title: r.title,
        position: r.position,
        bio: r.bio,
        photoUrl: r.photoUrl,
        photo_url: r.photoUrl,
        department: r.department?.name || null,
        college: r.department?.college?.name || null,
        email: r.user?.email || null,
        orcidId: r.orcidId,
        googleScholarId: r.googleScholarId,
        profileStatus: r.profileStatus,
        hasEmbedding: r.embeddingUpdatedAt !== null,
        has_scholar: r.embeddingUpdatedAt !== null,
        h_index: enrichment?.h_index || enrichment?.scholar?.h_index || null,
        citation_count: enrichment?.citation_count || enrichment?.scholar?.citedby || null,
        interests: enrichment?.scholar?.interests || [],
        publications: enrichment?.scholar?.publications?.slice(0, 3) || [],
      };
    });

    return NextResponse.json({ researchers: formatted, total, offset, limit });

  } catch (error) {
    console.error('Error fetching researchers:', error);
    return NextResponse.json({ error: 'Failed to fetch researchers' }, { status: 500 });
  }
}
