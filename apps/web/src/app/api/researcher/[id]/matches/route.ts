import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';

const prisma = new PrismaClient();

// Data loading for enrichment data - prioritize most complete file
const DATA_PATHS = [
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_api_enriched.json',
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_library.json',
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_enriched.json',
];

interface JsonResearcher {
  net_id: string;
  name: string;
  email?: string;
  department?: string;
  college?: string;
  photo_url?: string;
  h_index?: number;
  citation_count?: number;
  scholar?: {
    interests?: string[];
    h_index?: number;
    citedby?: number;
    publications?: Array<{ title: string }>;
  };
}

function loadJsonData(): JsonResearcher[] {
  for (const dataPath of DATA_PATHS) {
    try {
      if (fs.existsSync(dataPath)) {
        console.log('Loading JSON from:', dataPath);
        return JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
      }
    } catch (e) {
      console.error('Error loading ' + dataPath + ':', e);
    }
  }
  return [];
}

function interestSimilarity(a: string[], b: string[]): number {
  if (!a.length || !b.length) return 0;
  const setA = new Set(a.map(i => i.toLowerCase()));
  const setB = new Set(b.map(i => i.toLowerCase()));
  let matches = 0;
  for (const interest of setA) {
    for (const other of setB) {
      if (interest === other || interest.includes(other) || other.includes(interest)) {
        matches++;
        break;
      }
    }
  }
  return matches / new Set([...setA, ...setB]).size;
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get('limit') || '5');

  try {
    // Get researcher from database
    const dbResearcher = await prisma.researcher.findUnique({
      where: { id },
      include: { user: { select: { email: true } } }
    });

    if (!dbResearcher) {
      return NextResponse.json({ error: 'Researcher not found' }, { status: 404 });
    }

    // Load JSON data for enrichment info
    const jsonData = loadJsonData();
    const targetEmail = dbResearcher.user?.email?.toLowerCase();
    const targetJson = jsonData.find(r => r.email?.toLowerCase() === targetEmail);
    const targetInterests = targetJson?.scholar?.interests || [];

    console.log('Target email:', targetEmail);
    console.log('Target interests:', targetInterests);
    console.log('JSON data loaded:', jsonData.length, 'researchers');

    // Get all other researchers from database  
    const allResearchers = await prisma.researcher.findMany({
      where: { id: { not: id } },
      include: {
        department: { include: { college: true } },
        user: { select: { email: true } }
      },
      take: 200
    });

    // Calculate matches
    const matches = allResearchers.map(candidate => {
      const candidateEmail = candidate.user?.email?.toLowerCase();
      const candidateJson = jsonData.find(r => r.email?.toLowerCase() === candidateEmail);
      const candidateInterests = candidateJson?.scholar?.interests || [];
      const score = interestSimilarity(targetInterests, candidateInterests);

      return {
        researcher: {
          net_id: candidate.id,
          name: (candidate.firstName || '') + ' ' + (candidate.lastName || ''),
          department: candidate.department?.name,
          photo_url: candidate.photoUrl,
          h_index: candidateJson?.h_index || candidateJson?.scholar?.h_index,
          interests: candidateInterests.slice(0, 5),
        },
        matchScore: score,
        matchType: 'COLLABORATOR' as const,
        explanation: 'Shared research interests identified',
        factors: [{ factor: 'Shared Interests', weight: score, description: 'Research area overlap', icon: 'RO' }]
      };
    }).filter(m => m.matchScore > 0.05).sort((a, b) => b.matchScore - a.matchScore).slice(0, limit);

    return NextResponse.json({ matches, total: matches.length });
  } catch (error) {
    console.error('Match error:', error);
    return NextResponse.json({ error: 'Failed to find matches' }, { status: 500 });
  }
}
