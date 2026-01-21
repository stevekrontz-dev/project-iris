import { NextRequest, NextResponse } from 'next/server';

interface Grant {
  title: string;
  description?: string;
  keywords: string[];
  source: string;
  agency: string;
}

interface Researcher {
  name: string;
  institution: string;
  field: string;
  subfield?: string;
  h_index: number;
  matchedKeywords: string[];
}

interface MatchExplanationRequest {
  grant: Grant;
  researcher: Researcher;
}

export async function POST(request: NextRequest) {
  try {
    const body: MatchExplanationRequest = await request.json();
    const { grant, researcher } = body;

    if (!grant || !researcher) {
      return NextResponse.json(
        { error: 'Missing grant or researcher data' },
        { status: 400 }
      );
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;

    if (!apiKey) {
      // Return a fallback explanation if no API key is configured
      const fallbackExplanation = generateFallbackExplanation(grant, researcher);
      return NextResponse.json({
        explanation: fallbackExplanation,
        source: 'fallback'
      });
    }

    const prompt = `You are an expert at explaining why researchers are good fits for grant opportunities. Be specific and actionable.

Given this grant opportunity:
Title: ${grant.title}
Source: ${grant.source}
Agency: ${grant.agency}
Description: ${grant.description || 'Not provided'}
Keywords: ${grant.keywords.join(', ')}

Explain in 2-3 sentences why this researcher is a good fit:
Name: ${researcher.name}
Institution: ${researcher.institution}
Field: ${researcher.field}${researcher.subfield ? ` / ${researcher.subfield}` : ''}
H-index: ${researcher.h_index}
Matched Keywords: ${researcher.matchedKeywords.join(', ')}

Focus on:
1. How their expertise aligns with the grant's goals
2. What unique contribution they could make to the team
3. Any institutional or methodological strengths

Keep it concise, professional, and actionable. Do not use generic phrases.`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-3-5-haiku-latest',
        max_tokens: 200,
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Anthropic API error:', errorText);

      // Return fallback on API error
      const fallbackExplanation = generateFallbackExplanation(grant, researcher);
      return NextResponse.json({
        explanation: fallbackExplanation,
        source: 'fallback'
      });
    }

    const data = await response.json();
    const explanation = data.content?.[0]?.text || generateFallbackExplanation(grant, researcher);

    return NextResponse.json({
      explanation,
      source: 'claude-haiku'
    });

  } catch (error) {
    console.error('Match explanation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate explanation' },
      { status: 500 }
    );
  }
}

function generateFallbackExplanation(grant: Grant, researcher: Researcher): string {
  const keywordCount = researcher.matchedKeywords.length;
  const totalKeywords = grant.keywords.length;
  const coverage = Math.round((keywordCount / totalKeywords) * 100);

  const expertiseMatch = keywordCount > 2
    ? 'strong multi-area expertise'
    : keywordCount > 1
      ? 'solid cross-disciplinary knowledge'
      : 'specialized expertise';

  const hIndexComment = researcher.h_index >= 30
    ? 'extensive publication record'
    : researcher.h_index >= 15
      ? 'solid research track record'
      : 'growing research portfolio';

  return `${researcher.name} brings ${expertiseMatch} matching ${coverage}% of the grant's focus areas (${researcher.matchedKeywords.slice(0, 3).join(', ')}). Their ${hIndexComment} at ${researcher.institution} positions them to contribute meaningfully to ${grant.source}'s objectives in ${researcher.field}.`;
}
