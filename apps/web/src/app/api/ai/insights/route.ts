import { NextRequest, NextResponse } from 'next/server';

// Ollama configuration - using local gemma3:4b model
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'gemma3:4b';

interface ResearcherProfile {
  name: string;
  department?: string;
  title?: string;
  interests?: string[];
  publications?: Array<{
    title: string;
    journal?: string;
    year?: number;
    citations?: number;
  }>;
  h_index?: number;
  citation_count?: number;
}

interface InsightRequest {
  type: 'collaboration' | 'innovation' | 'trend' | 'gap';
  researchers?: ResearcherProfile[];
  context?: string;
}

async function generateWithOllama(prompt: string): Promise<string> {
  const response = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: OLLAMA_MODEL,
      prompt,
      stream: false,
      options: {
        temperature: 0.7,
        top_p: 0.9,
        num_predict: 500,
      }
    }),
  });

  if (!response.ok) {
    throw new Error(`Ollama generate failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.response;
}

function buildCollaborationPrompt(researchers: ResearcherProfile[]): string {
  if (researchers.length < 2) {
    throw new Error('Need at least 2 researchers for collaboration analysis');
  }

  const [r1, r2] = researchers;

  const r1Pubs = r1.publications?.slice(0, 5).map(p => `- "${p.title}" (${p.year || 'n/d'})`).join('\n') || 'No publications listed';
  const r2Pubs = r2.publications?.slice(0, 5).map(p => `- "${p.title}" (${p.year || 'n/d'})`).join('\n') || 'No publications listed';

  return `You are IRIS, an AI research collaboration analyst. Analyze these two researchers and explain why they should collaborate.

RESEARCHER 1:
Name: ${r1.name}
Department: ${r1.department || 'Unknown'}
Title: ${r1.title || 'Researcher'}
Research Interests: ${r1.interests?.join(', ') || 'Not specified'}
H-Index: ${r1.h_index || 'N/A'}
Citations: ${r1.citation_count || 'N/A'}
Recent Publications:
${r1Pubs}

RESEARCHER 2:
Name: ${r2.name}
Department: ${r2.department || 'Unknown'}
Title: ${r2.title || 'Researcher'}
Research Interests: ${r2.interests?.join(', ') || 'Not specified'}
H-Index: ${r2.h_index || 'N/A'}
Citations: ${r2.citation_count || 'N/A'}
Recent Publications:
${r2Pubs}

Provide a brief, insightful analysis (3-4 sentences) of:
1. What specific research synergies exist between these two
2. A concrete collaboration idea they could pursue together
3. What unique value each brings to a potential partnership

Be specific and actionable. Reference their actual research areas.`;
}

function buildInnovationPrompt(researcher: ResearcherProfile): string {
  const pubs = researcher.publications?.slice(0, 8).map(p => `- "${p.title}" (${p.year || 'n/d'}, ${p.citations || 0} citations)`).join('\n') || 'No publications';

  return `You are IRIS, an AI research analyst. Analyze this researcher's innovation potential.

RESEARCHER:
Name: ${researcher.name}
Department: ${researcher.department || 'Unknown'}
Research Interests: ${researcher.interests?.join(', ') || 'Not specified'}
H-Index: ${researcher.h_index || 'N/A'}
Total Citations: ${researcher.citation_count || 'N/A'}

Publications:
${pubs}

Provide a brief analysis (3-4 sentences) of:
1. Their research trajectory and impact
2. Emerging themes or directions in their work
3. Potential for breakthrough discoveries

Be specific and reference their actual work.`;
}

export async function POST(request: NextRequest) {
  try {
    const body: InsightRequest = await request.json();
    const { type, researchers, context } = body;

    if (!type) {
      return NextResponse.json({ error: 'Missing insight type' }, { status: 400 });
    }

    let prompt: string;
    let insight: string;

    switch (type) {
      case 'collaboration':
        if (!researchers || researchers.length < 2) {
          return NextResponse.json({ error: 'Need 2 researchers for collaboration analysis' }, { status: 400 });
        }
        prompt = buildCollaborationPrompt(researchers);
        break;

      case 'innovation':
        if (!researchers || researchers.length < 1) {
          return NextResponse.json({ error: 'Need 1 researcher for innovation analysis' }, { status: 400 });
        }
        prompt = buildInnovationPrompt(researchers[0]);
        break;

      case 'trend':
        prompt = `You are IRIS, an AI research analyst. Based on the context: "${context || 'university research'}".
Identify 3 emerging research trends that could lead to breakthrough discoveries. Be specific and actionable.`;
        break;

      case 'gap':
        prompt = `You are IRIS, an AI research analyst. Based on the context: "${context || 'interdisciplinary research'}".
Identify 2-3 research gaps that represent opportunities for new collaboration. Be specific.`;
        break;

      default:
        return NextResponse.json({ error: 'Unknown insight type' }, { status: 400 });
    }

    // Call Ollama
    insight = await generateWithOllama(prompt);

    return NextResponse.json({
      insight,
      type,
      model: OLLAMA_MODEL,
      generated_at: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('AI Insight error:', error);

    // Check if Ollama is not running
    if (error.message?.includes('fetch failed') || error.message?.includes('ECONNREFUSED')) {
      return NextResponse.json(
        { error: 'AI service unavailable. Ensure Ollama is running locally.' },
        { status: 503 }
      );
    }

    return NextResponse.json(
      { error: 'Failed to generate insight' },
      { status: 500 }
    );
  }
}

// Health check endpoint
export async function GET() {
  try {
    const response = await fetch(`${OLLAMA_BASE_URL}/api/tags`);
    if (!response.ok) {
      return NextResponse.json({ status: 'offline', model: OLLAMA_MODEL }, { status: 503 });
    }

    const data = await response.json();
    const models = data.models?.map((m: { name: string }) => m.name) || [];
    const hasModel = models.some((m: string) => m.includes(OLLAMA_MODEL.split(':')[0]));

    return NextResponse.json({
      status: 'online',
      model: OLLAMA_MODEL,
      available: hasModel,
      models
    });
  } catch {
    return NextResponse.json({ status: 'offline', model: OLLAMA_MODEL }, { status: 503 });
  }
}
