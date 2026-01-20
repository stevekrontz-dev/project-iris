// IRIS - Intelligent Research Information System
// AI Matching Engine for KSU Research Platform
// Supports both local (Ollama) and cloud (OpenAI) inference

import { AI_NAME, AI_FULL_NAME, MATCH_THRESHOLDS } from '@ksu-research/shared';

export { AI_NAME, AI_FULL_NAME };

// ============================================
// CONFIGURATION
// ============================================

export type AIProvider = 'ollama' | 'openai';

export interface IRISConfig {
  provider: AIProvider;
  ollamaBaseUrl?: string;
  ollamaEmbedModel?: string;
  ollamaLLMModel?: string;
  openaiApiKey?: string;
  openaiEmbedModel?: string;
}

const defaultConfig: IRISConfig = {
  provider: 'ollama', // Default to local
  ollamaBaseUrl: 'http://localhost:11434',
  ollamaEmbedModel: 'nomic-embed-text',
  ollamaLLMModel: 'gemma3:4b',
  openaiEmbedModel: 'text-embedding-3-small',
};

let config: IRISConfig = { ...defaultConfig };

export function configureIRIS(newConfig: Partial<IRISConfig>): void {
  config = { ...config, ...newConfig };
}

// ============================================
// OLLAMA CLIENT
// ============================================

interface OllamaEmbedResponse {
  embedding: number[];
}

interface OllamaGenerateResponse {
  response: string;
  done: boolean;
}

async function ollamaEmbed(text: string): Promise<number[]> {
  const response = await fetch(`${config.ollamaBaseUrl}/api/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: config.ollamaEmbedModel,
      prompt: text,
    }),
  });

  if (!response.ok) {
    throw new Error(`Ollama embedding failed: ${response.statusText}`);
  }

  const data: OllamaEmbedResponse = await response.json();
  return data.embedding;
}

async function ollamaGenerate(prompt: string): Promise<string> {
  const response = await fetch(`${config.ollamaBaseUrl}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: config.ollamaLLMModel,
      prompt,
      stream: false,
    }),
  });

  if (!response.ok) {
    throw new Error(`Ollama generate failed: ${response.statusText}`);
  }

  const data: OllamaGenerateResponse = await response.json();
  return data.response;
}

// ============================================
// EMBEDDING GENERATION
// ============================================

export interface EmbeddingInput {
  text: string;
  metadata?: Record<string, unknown>;
}

export interface EmbeddingResult {
  embedding: number[];
  model: string;
  provider: AIProvider;
}

/**
 * Generate embeddings for text
 * Uses Ollama locally or OpenAI in cloud
 */
export async function generateEmbedding(input: EmbeddingInput): Promise<EmbeddingResult> {
  if (config.provider === 'ollama') {
    const embedding = await ollamaEmbed(input.text);
    return {
      embedding,
      model: config.ollamaEmbedModel!,
      provider: 'ollama',
    };
  }

  // OpenAI implementation
  if (!config.openaiApiKey) {
    throw new Error('OpenAI API key required for cloud embeddings');
  }

  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.openaiApiKey}`,
    },
    body: JSON.stringify({
      model: config.openaiEmbedModel,
      input: input.text,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI embedding failed: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    embedding: data.data[0].embedding,
    model: config.openaiEmbedModel!,
    provider: 'openai',
  };
}

/**
 * Generate text using LLM (for explanations)
 */
export async function generateText(prompt: string): Promise<string> {
  if (config.provider === 'ollama') {
    return ollamaGenerate(prompt);
  }

  // OpenAI implementation
  if (!config.openaiApiKey) {
    throw new Error('OpenAI API key required for cloud generation');
  }

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.openaiApiKey}`,
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 500,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI generation failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}

/**
 * Check if Ollama is running and models are available
 */
export async function checkOllamaHealth(): Promise<{
  running: boolean;
  embedModel: boolean;
  llmModel: boolean;
}> {
  try {
    // Check if Ollama is running
    const tagsResponse = await fetch(`${config.ollamaBaseUrl}/api/tags`);
    if (!tagsResponse.ok) {
      return { running: false, embedModel: false, llmModel: false };
    }

    const tags = await tagsResponse.json();
    const models = tags.models?.map((m: { name: string }) => m.name) || [];

    return {
      running: true,
      embedModel: models.some((m: string) => m.includes(config.ollamaEmbedModel!)),
      llmModel: models.some((m: string) => m.includes(config.ollamaLLMModel!)),
    };
  } catch {
    return { running: false, embedModel: false, llmModel: false };
  }
}

// ============================================
// MATCH SCORING
// ============================================

export interface MatchCandidate {
  researcherId: string;
  embedding: number[];
  metadata: {
    name: string;
    department?: string;
    researchAreas: string[];
  };
}

export interface MatchResult {
  researcherId: string;
  matchedResearcherId: string;
  score: number;
  matchType: 'COLLABORATOR' | 'METHODOLOGY' | 'EQUIPMENT' | 'GRANT' | 'CROSS_DISCIPLINARY';
  explanation: string;
  factors: MatchFactor[];
}

export interface MatchFactor {
  factor: string;
  weight: number;
  description: string;
}

/**
 * Calculate cosine similarity between two embedding vectors
 */
export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) {
    throw new Error('Embedding vectors must have the same length');
  }

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

/**
 * Find potential matches for a researcher based on embedding similarity
 */
export function findMatches(
  researcher: MatchCandidate,
  candidates: MatchCandidate[],
  options: {
    minScore?: number;
    maxResults?: number;
    excludeSameDepartment?: boolean;
  } = {}
): MatchResult[] {
  const {
    minScore = MATCH_THRESHOLDS.low,
    maxResults = 10,
    excludeSameDepartment = false,
  } = options;

  const results: MatchResult[] = [];

  for (const candidate of candidates) {
    // Skip self
    if (candidate.researcherId === researcher.researcherId) continue;

    // Skip same department if requested
    if (excludeSameDepartment && candidate.metadata.department === researcher.metadata.department) {
      continue;
    }

    const score = cosineSimilarity(researcher.embedding, candidate.embedding);

    if (score >= minScore) {
      results.push({
        researcherId: researcher.researcherId,
        matchedResearcherId: candidate.researcherId,
        score,
        matchType: determineMatchType(researcher, candidate, score),
        explanation: generateExplanation(researcher, candidate, score),
        factors: identifyMatchFactors(researcher, candidate),
      });
    }
  }

  // Sort by score descending and limit results
  return results
    .sort((a, b) => b.score - a.score)
    .slice(0, maxResults);
}

/**
 * Determine the type of match based on researcher profiles
 */
function determineMatchType(
  researcher: MatchCandidate,
  candidate: MatchCandidate,
  score: number
): MatchResult['matchType'] {
  // If different departments with high score, likely cross-disciplinary
  if (researcher.metadata.department !== candidate.metadata.department && score > MATCH_THRESHOLDS.high) {
    return 'CROSS_DISCIPLINARY';
  }

  // Default to collaborator match
  return 'COLLABORATOR';
}

/**
 * Generate human-readable explanation for why IRIS suggested this match
 * This is key for transparency - users should understand WHY they're being matched
 */
function generateExplanation(
  researcher: MatchCandidate,
  candidate: MatchCandidate,
  score: number
): string {
  const scorePercent = Math.round(score * 100);
  const sharedAreas = researcher.metadata.researchAreas.filter(area =>
    candidate.metadata.researchAreas.includes(area)
  );

  let explanation = `IRIS identified a ${scorePercent}% research alignment between your profile and ${candidate.metadata.name}`;

  if (sharedAreas.length > 0) {
    explanation += `. You share interest in: ${sharedAreas.join(', ')}`;
  }

  if (researcher.metadata.department !== candidate.metadata.department) {
    explanation += `. This cross-disciplinary connection between ${researcher.metadata.department} and ${candidate.metadata.department} may offer unique collaboration opportunities.`;
  }

  return explanation;
}

/**
 * Identify specific factors that contributed to the match
 */
function identifyMatchFactors(
  researcher: MatchCandidate,
  candidate: MatchCandidate
): MatchFactor[] {
  const factors: MatchFactor[] = [];

  // Shared research areas
  const sharedAreas = researcher.metadata.researchAreas.filter(area =>
    candidate.metadata.researchAreas.includes(area)
  );

  if (sharedAreas.length > 0) {
    factors.push({
      factor: 'Shared Research Areas',
      weight: 0.4,
      description: `Both researchers work in: ${sharedAreas.join(', ')}`,
    });
  }

  // Cross-disciplinary bonus
  if (researcher.metadata.department !== candidate.metadata.department) {
    factors.push({
      factor: 'Cross-Disciplinary Potential',
      weight: 0.2,
      description: `Different departments may bring complementary perspectives`,
    });
  }

  return factors;
}

// ============================================
// TRANSPARENCY HELPERS
// ============================================

/**
 * Get a summary of how IRIS works - for the transparency page
 */
export function getIRISExplanation(): string {
  return `
${AI_NAME} (${AI_FULL_NAME}) analyzes your research profile to find meaningful connections.

HOW IT WORKS:
1. Profile Analysis: IRIS reads your publications, research interests, and grants to understand your work.
2. Semantic Understanding: Using AI, IRIS creates a "fingerprint" of your research that captures meaning, not just keywords.
3. Match Discovery: IRIS compares your fingerprint with other researchers to find complementary work.
4. Transparent Recommendations: Every match includes an explanation of WHY IRIS thinks you'd work well together.

YOUR DATA:
- You control what IRIS can see via your privacy settings
- IRIS never shares your data externally
- You can opt out of AI matching at any time

WHAT IRIS DOESN'T DO:
- IRIS doesn't claim ownership of your ideas or IP
- IRIS doesn't share pre-publication research without your consent
- IRIS doesn't make decisions for you - it only suggests
  `.trim();
}
