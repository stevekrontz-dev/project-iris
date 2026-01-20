'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface MatchFactor {
  factor: string;
  weight: number;
  description: string;
}

interface MatchedResearcher {
  net_id: string;
  name: string;
  title?: string;
  department?: string;
  college?: string;
  photo_url?: string;
  h_index?: number;
  citation_count?: number;
  interests?: string[];
}

interface Match {
  researcher: MatchedResearcher;
  matchScore: number;
  matchType: 'COLLABORATOR' | 'CROSS_DISCIPLINARY' | 'METHODOLOGY';
  explanation: string;
  factors: MatchFactor[];
}

interface AIReasoning {
  reasoning: string;
  generatedAt: string;
}

interface PotentialCollaboratorsProps {
  researcherId: string;
  limit?: number;
}

export function PotentialCollaborators({ researcherId, limit = 5 }: PotentialCollaboratorsProps) {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [crossDisciplinary, setCrossDisciplinary] = useState(false);

  // AI reasoning state
  const [aiReasonings, setAiReasonings] = useState<Record<string, AIReasoning>>({});
  const [loadingAI, setLoadingAI] = useState<string | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams({
      limit: limit.toString(),
      crossDisciplinary: crossDisciplinary.toString(),
    });

    fetch(`/api/researcher/${researcherId}/matches?${params}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load matches');
        return res.json();
      })
      .then(data => {
        setMatches(data.matches || []);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [researcherId, limit, crossDisciplinary]);

  const getMatchTypeLabel = (type: Match['matchType']) => {
    switch (type) {
      case 'CROSS_DISCIPLINARY':
        return { label: 'Cross-Disciplinary', bg: 'bg-purple-100', text: 'text-purple-700' };
      case 'METHODOLOGY':
        return { label: 'Methodology', bg: 'bg-blue-100', text: 'text-blue-700' };
      default:
        return { label: 'Collaborator', bg: 'bg-green-100', text: 'text-green-700' };
    }
  };

  const askIRIS = async (matchedResearcherId: string) => {
    // Don't refetch if we already have it
    if (aiReasonings[matchedResearcherId]) return;

    setLoadingAI(matchedResearcherId);
    setAiError(null);

    try {
      const response = await fetch('/api/ai/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          researcherId,
          matchedResearcherId,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to get AI reasoning');
      }

      const data = await response.json();
      setAiReasonings(prev => ({
        ...prev,
        [matchedResearcherId]: {
          reasoning: data.reasoning,
          generatedAt: data.generatedAt,
        },
      }));
    } catch (err) {
      setAiError(err instanceof Error ? err.message : 'Failed to get AI reasoning');
    } finally {
      setLoadingAI(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 bg-[#0B1315] rounded flex items-center justify-center flex-shrink-0">
            <div className="w-4 h-4 bg-[#FDBB30] rounded-sm animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#0B1315] uppercase tracking-wide">IRIS Collaborator Suggestions</h3>
            <p className="text-xs text-gray-500">Powered by AI matching</p>
          </div>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gray-200 rounded"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
                  <div className="h-3 bg-gray-100 rounded w-48"></div>
                </div>
                <div className="h-8 w-12 bg-gray-200 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-500">
          <p>Unable to load collaborator suggestions</p>
        </div>
      </div>
    );
  }

  if (matches.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 bg-[#0B1315] rounded flex items-center justify-center flex-shrink-0">
            <div className="w-4 h-4 bg-[#FDBB30] rounded-sm" />
          </div>
          <h3 className="text-sm font-semibold text-[#0B1315] uppercase tracking-wide">IRIS Collaborator Suggestions</h3>
        </div>
        <p className="text-gray-500 text-sm">
          No collaborator suggestions available yet. IRIS needs more research data to make meaningful recommendations.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#0B1315] rounded flex items-center justify-center flex-shrink-0">
              <div className="w-4 h-4 bg-[#FDBB30] rounded-sm" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#0B1315] uppercase tracking-wide">IRIS Collaborator Suggestions</h3>
              <p className="text-xs text-gray-500">AI-powered research matching</p>
            </div>
          </div>
          <button
            onClick={() => setCrossDisciplinary(!crossDisciplinary)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              crossDisciplinary
                ? 'bg-purple-50 border-purple-200 text-purple-700'
                : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
            }`}
          >
            {crossDisciplinary ? 'Cross-disciplinary only' : 'All matches'}
          </button>
        </div>
      </div>

      {/* Matches List */}
      <div className="divide-y divide-gray-100">
        {matches.map((match) => {
          const { researcher } = match;
          const typeStyle = getMatchTypeLabel(match.matchType);
          const isExpanded = expandedId === researcher.net_id;
          const scorePercent = Math.round(match.matchScore * 100);
          const aiReasoning = aiReasonings[researcher.net_id];
          const isLoadingThis = loadingAI === researcher.net_id;

          return (
            <div key={researcher.net_id} className="hover:bg-gray-50 transition-colors">
              {/* Main Row */}
              <div className="p-4">
                <div className="flex items-start gap-3">
                  {/* Photo */}
                  <Link href={`/researcher/${researcher.net_id}`} className="flex-shrink-0">
                    {researcher.photo_url ? (
                      <img
                        src={researcher.photo_url}
                        alt={researcher.name}
                        className="w-12 h-12 rounded object-cover border border-gray-200"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded bg-gray-100 flex items-center justify-center border border-gray-200">
                        <span className="text-sm font-medium text-gray-500">
                          {researcher.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </span>
                      </div>
                    )}
                  </Link>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link
                          href={`/researcher/${researcher.net_id}`}
                          className="font-medium text-[#0B1315] hover:text-[#FDBB30] transition-colors"
                        >
                          {researcher.name}
                        </Link>
                        <p className="text-sm text-gray-500 truncate">
                          {researcher.department || researcher.college}
                        </p>
                        {researcher.h_index && (
                          <span className="inline-block mt-1 text-xs px-1.5 py-0.5 bg-[#0B1315] text-white rounded font-medium">
                            h-index: {researcher.h_index}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${typeStyle.bg} ${typeStyle.text}`}>
                          {typeStyle.label}
                        </span>
                        <div className="text-right">
                          <div className="text-lg font-bold text-[#0B1315]">{scorePercent}%</div>
                          <div className="text-[10px] text-gray-400 uppercase">Match</div>
                        </div>
                      </div>
                    </div>

                    {/* Research Interests */}
                    {researcher.interests && researcher.interests.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {researcher.interests.slice(0, 3).map((interest, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                            {interest}
                          </span>
                        ))}
                        {researcher.interests.length > 3 && (
                          <span className="text-xs text-gray-400">+{researcher.interests.length - 3}</span>
                        )}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-3 mt-2">
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : researcher.net_id)}
                        className="text-xs text-gray-500 hover:text-[#0B1315] flex items-center gap-1"
                      >
                        {isExpanded ? 'Hide' : 'View'} analysis
                        <svg
                          className={`w-3 h-3 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      {/* Ask IRIS Button */}
                      <button
                        onClick={() => {
                          if (!isExpanded) setExpandedId(researcher.net_id);
                          askIRIS(researcher.net_id);
                        }}
                        disabled={isLoadingThis}
                        className={`text-xs px-3 py-1 rounded-full font-medium transition-all flex items-center gap-1.5 ${
                          aiReasoning
                            ? 'bg-purple-100 text-purple-700 border border-purple-200'
                            : 'bg-purple-600 text-white hover:bg-purple-700 shadow-sm hover:shadow'
                        } ${isLoadingThis ? 'opacity-75 cursor-wait' : ''}`}
                      >
                        {isLoadingThis ? (
                          <>
                            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Thinking...
                          </>
                        ) : aiReasoning ? (
                          <>
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                            IRIS Analyzed
                          </>
                        ) : (
                          <>
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                            Ask IRIS
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Expanded Analysis */}
              {isExpanded && (
                <div className="px-4 pb-4">
                  <div className="ml-15 pl-3 border-l-2 border-[#FDBB30]">
                    {/* AI Deep Analysis - Show if available */}
                    {aiReasoning && (
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-3">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-6 h-6 bg-purple-600 rounded flex items-center justify-center">
                            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                          </div>
                          <div className="text-xs font-semibold text-purple-800 uppercase tracking-wide">IRIS Deep Analysis</div>
                        </div>
                        <div className="text-sm text-purple-900 leading-relaxed whitespace-pre-wrap">
                          {aiReasoning.reasoning}
                        </div>
                        <div className="text-[10px] text-purple-500 mt-2">
                          Generated by IRIS AI on {new Date(aiReasoning.generatedAt).toLocaleString()}
                        </div>
                      </div>
                    )}

                    {/* AI Error */}
                    {aiError && loadingAI === null && !aiReasoning && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                        <p className="text-sm text-red-700">{aiError}</p>
                        <p className="text-xs text-red-500 mt-1">Make sure Ollama is running: <code className="bg-red-100 px-1 rounded">ollama serve</code></p>
                      </div>
                    )}

                    {/* Basic Explanation */}
                    <div className="bg-gray-50 rounded p-3 mb-3">
                      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Quick Summary</div>
                      <p className="text-sm text-gray-700">{match.explanation}</p>
                    </div>

                    {/* Factors */}
                    {match.factors.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs text-gray-500 uppercase tracking-wide">Match Factors</div>
                        {match.factors.map((factor, i) => (
                          <div key={i} className="flex items-center gap-3">
                            <div className="flex-1">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="font-medium text-gray-700">{factor.factor}</span>
                                <span className="text-gray-500">{Math.round(factor.weight * 100)}%</span>
                              </div>
                              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-[#FDBB30] rounded-full transition-all"
                                  style={{ width: `${factor.weight * 100}%` }}
                                />
                              </div>
                              <p className="text-xs text-gray-500 mt-1">{factor.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Metrics */}
                    {(researcher.h_index || researcher.citation_count) && (
                      <div className="flex gap-4 mt-3 pt-3 border-t border-gray-100">
                        {researcher.h_index && (
                          <div className="text-center">
                            <div className="text-lg font-semibold text-[#0B1315]">{researcher.h_index}</div>
                            <div className="text-[10px] text-gray-500 uppercase">h-index</div>
                          </div>
                        )}
                        {researcher.citation_count && (
                          <div className="text-center">
                            <div className="text-lg font-semibold text-[#0B1315]">{researcher.citation_count.toLocaleString()}</div>
                            <div className="text-[10px] text-gray-500 uppercase">Citations</div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action */}
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <Link
                        href={`/researcher/${researcher.net_id}`}
                        className="inline-flex items-center gap-2 text-sm font-medium text-[#0B1315] hover:text-[#FDBB30] transition-colors"
                      >
                        View full profile
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-3 bg-gray-50 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-xs">All AI analysis performed locally on KSU infrastructure</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PotentialCollaborators;
