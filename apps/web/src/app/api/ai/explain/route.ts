import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';

const prisma = new PrismaClient();
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'gemma3:4b';

// Data loading for enrichment
const DATA_PATHS = [
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_api_enriched.json',
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_library.json',
];

interface JsonResearcher {
  email?: string;
  name?: string;
  department?: string;
  college?: string;
  scholar?: {
    interests?: string[];
    publications?: Array<{ title: string; year?: number }>;
  };
}

function loadJsonData(): JsonResearcher[] {
  for (const dataPath of DATA_PATHS) {
    try {
      if (fs.existsSync(dataPath)) {
        return JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
      }
    } catch (e) {
      console.error('Error loading ' + dataPath + ':', e);
    }
  }
  return [];
}

function cleanField(field?: string): string {
  if (!field) return 'Unknown';
  return field.split('\n')[0].trim();
}

async function generateWithOllama(prompt: string): Promise<string> {
  const response = await fetch(OLLAMA_BASE_URL + '/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      prompt,
      stream: false,
      options: {
        temperature: 0.7,
        num_predict: 500,
      },
    }),
  });

  if (!response.ok) {
    throw new Error('Ollama request failed: ' + response.statusText);
  }

  const data = await response.json();
  return data.response;
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { researcherId, matchedResearcherId } = body;

    if (!researcherId || !matchedResearcherId) {
      return NextResponse.json(
        { error: 'Both researcherId and matchedResearcherId are required' },
        { status: 400 }
      );
    }

    // Get both researchers from database
    const [dbResearcher, dbMatched] = await Promise.all([
      prisma.researcher.findUnique({
        where: { id: researcherId },
        include: {
          department: { include: { college: true } },
          user: { select: { email: true } }
        }
      }),
      prisma.researcher.findUnique({
        where: { id: matchedResearcherId },
        include: {
          department: { include: { college: true } },
          user: { select: { email: true } }
        }
      })
    ]);

    if (!dbResearcher || !dbMatched) {
      return NextResponse.json(
        { error: 'One or both researchers not found' },
        { status: 404 }
      );
    }

    // Load JSON enrichment data
    const jsonData = loadJsonData();
    const researcherJson = jsonData.find(r => r.email?.toLowerCase() === dbResearcher.user?.email?.toLowerCase());
    const matchedJson = jsonData.find(r => r.email?.toLowerCase() === dbMatched.user?.email?.toLowerCase());

    // Build context for the AI
    const researcherName = (dbResearcher.firstName || '') + ' ' + (dbResearcher.lastName || '');
    const matchedName = (dbMatched.firstName || '') + ' ' + (dbMatched.lastName || '');
    
    const researcherInterests = researcherJson?.scholar?.interests?.join(', ') || 'Not specified';
    const matchedInterests = matchedJson?.scholar?.interests?.join(', ') || 'Not specified';

    const researcherPubs = researcherJson?.scholar?.publications?.slice(0, 5)
      .map(p => p.title).join('; ') || 'No publications listed';
    const matchedPubs = matchedJson?.scholar?.publications?.slice(0, 5)
      .map(p => p.title).join('; ') || 'No publications listed';

    const prompt = 'You are IRIS, an AI research collaboration assistant at Kennesaw State University. Your role is to explain why two researchers might benefit from collaborating.\n\nAnalyze these two researcher profiles and provide a thoughtful, detailed explanation of potential collaboration opportunities:\n\nRESEARCHER 1:\n- Name: ' + researcherName + '\n- Title: ' + (dbResearcher.title || 'Faculty') + '\n- Department: ' + cleanField(dbResearcher.department?.name) + '\n- College: ' + cleanField(dbResearcher.department?.college?.name) + '\n- Research Interests: ' + researcherInterests + '\n- Recent Publications: ' + researcherPubs + '\n\nRESEARCHER 2:\n- Name: ' + matchedName + '\n- Title: ' + (dbMatched.title || 'Faculty') + '\n- Department: ' + cleanField(dbMatched.department?.name) + '\n- College: ' + cleanField(dbMatched.department?.college?.name) + '\n- Research Interests: ' + matchedInterests + '\n- Recent Publications: ' + matchedPubs + '\n\nProvide a thoughtful analysis that includes:\n1. Specific overlapping research themes or methodologies\n2. Complementary expertise that could lead to innovative work\n3. Potential joint research directions or grant opportunities\n4. Why this collaboration could be mutually beneficial\n\nBe specific, reference their actual research areas, and suggest concrete collaboration ideas. Keep your response focused and professional (3-4 paragraphs).';

    const aiResponse = await generateWithOllama(prompt);

    return NextResponse.json({
      success: true,
      researcher: {
        name: researcherName.trim(),
        department: cleanField(dbResearcher.department?.name),
      },
      matched: {
        name: matchedName.trim(),
        department: cleanField(dbMatched.department?.name),
      },
      reasoning: aiResponse.trim(),
      model: OLLAMA_MODEL,
      generatedAt: new Date().toISOString(),
    });

  } catch (error) {
    console.error('AI explanation error:', error);

    // Check if Ollama is not running
    if (error instanceof Error && error.message.includes('fetch')) {
      return NextResponse.json(
        {
          error: 'AI service unavailable',
          message: 'Ollama is not running. Start it with: ollama serve',
        },
        { status: 503 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to generate AI explanation' },
      { status: 500 }
    );
  }
}
