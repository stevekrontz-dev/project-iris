'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { IRISThinking } from '@/components/iris/IRISThinking';
import { IRISMatchExplainer } from '@/components/iris/IRISMatchExplainer';
import { Navigation } from '@/components/Navigation';

interface Publication {
  title: string;
  year?: number;
}

interface Researcher {
  net_id: string;
  name: string;
  first_name?: string;
  last_name?: string;
  title?: string;
  department?: string;
  college?: string;
  photo_url?: string;
  h_index?: number;
  citation_count?: number;
  interests?: string[];
  publications?: Publication[];
  has_scholar?: boolean;
}

interface MatchFactor {
  factor: string;
  weight: number;
  description: string;
  icon: string;
}

interface Match {
  researcher: Researcher;
  matchScore: number;
  matchType: string;
  explanation: string;
  factors: MatchFactor[];
}

export default function DiscoverPage() {
  const [researchers, setResearchers] = useState<Researcher[]>([]);
  const [filteredResearchers, setFilteredResearchers] = useState<Researcher[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedResearcher, setSelectedResearcher] = useState<Researcher | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isMatching, setIsMatching] = useState(false);
  const [matchStage, setMatchStage] = useState<'analyzing' | 'matching' | 'explaining' | 'complete'>('analyzing');
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'h_index' | 'citations' | 'name'>('h_index');

  // Helper to clean department names (removes extra lines from multi-line strings)
  const cleanDept = (dept?: string) => dept ? dept.split(/[\n\r]/)[0] : '';

  // Sort and filter researchers
  const sortedResearchers = useMemo(() => {
    const sorted = [...filteredResearchers];
    switch (sortBy) {
      case 'h_index':
        return sorted.sort((a, b) => (b.h_index || 0) - (a.h_index || 0));
      case 'citations':
        return sorted.sort((a, b) => (b.citation_count || 0) - (a.citation_count || 0));
      case 'name':
        return sorted.sort((a, b) => a.name.localeCompare(b.name));
      default:
        return sorted;
    }
  }, [filteredResearchers, sortBy]);

  // Fetch researchers on mount
  useEffect(() => {
    async function fetchResearchers() {
      try {
        const res = await fetch('/api/researchers?hasScholar=true&limit=100');
        const data = await res.json();
        setResearchers(data.researchers || []);
        setFilteredResearchers(data.researchers || []);
      } catch (err) {
        setError('Failed to load researchers');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchResearchers();
  }, []);

  // Filter researchers by search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredResearchers(researchers);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = researchers.filter(r => {
      const searchFields = [
        r.name,
        r.department,
        r.college,
        ...(r.interests || []),
      ].filter(Boolean).join(' ').toLowerCase();
      return searchFields.includes(query);
    });
    setFilteredResearchers(filtered);
  }, [searchQuery, researchers]);

  // Find matches for selected researcher
  const findMatches = useCallback(async (researcher: Researcher) => {
    setSelectedResearcher(researcher);
    setIsMatching(true);
    setMatches([]);
    setMatchStage('analyzing');

    // Progress through stages
    setTimeout(() => setMatchStage('matching'), 2000);
    setTimeout(() => setMatchStage('explaining'), 4000);

    try {
      const res = await fetch(`/api/researcher/${researcher.net_id}/matches?limit=5`);
      const data = await res.json();

      setTimeout(() => {
        setMatchStage('complete');
        setTimeout(() => {
          setIsMatching(false);
          setMatches(data.matches || []);
        }, 1000);
      }, 5500);
    } catch (err) {
      console.error('Match finding error:', err);
      setIsMatching(false);
      setError('Failed to find matches');
    }
  }, []);

  const clearSelection = () => {
    setSelectedResearcher(null);
    setMatches([]);
    setIsMatching(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation variant="dark" />

      <main className="max-w-6xl mx-auto px-6 lg:px-8 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h2 className="text-3xl font-serif font-bold text-[#0B1315]">Discover Collaborators</h2>
          <p className="text-gray-600 mt-2">
            Search for researchers and let IRIS find potential collaboration opportunities
          </p>
        </div>

        {/* Two Column Layout */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Search & Results */}
          <div>
            {/* Search Box */}
            <div className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by name, department, or research interest..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#FDBB30] focus:border-transparent outline-none"
                />
                <svg
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Results List */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  {sortedResearchers.length} researchers
                </span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'h_index' | 'citations' | 'name')}
                  className="text-sm text-gray-700 border border-gray-300 rounded px-2 py-1 bg-white focus:ring-2 focus:ring-[#FDBB30] focus:border-transparent outline-none cursor-pointer"
                >
                  <option value="h_index">Sort by H-Index</option>
                  <option value="citations">Sort by Citations</option>
                  <option value="name">Sort by Name (A-Z)</option>
                </select>
              </div>

              {isLoading ? (
                <div className="p-8 text-center text-gray-500">Loading researchers...</div>
              ) : error ? (
                <div className="p-8 text-center text-red-500">{error}</div>
              ) : (
                <div className="max-h-[600px] overflow-y-auto p-3 grid grid-cols-2 gap-3">
                  {sortedResearchers.map((researcher) => (
                    <button
                      key={researcher.net_id}
                      onClick={() => findMatches(researcher)}
                      className={`w-full h-[140px] text-left rounded-lg border overflow-hidden transition-all hover:shadow-lg hover:-translate-y-0.5 ${
                        selectedResearcher?.net_id === researcher.net_id
                          ? 'ring-2 ring-[#FDBB30] border-[#FDBB30] shadow-lg'
                          : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {/* Gold accent bar */}
                      <div className="h-1 bg-gradient-to-r from-[#FDBB30] to-[#e5a826]" />
                      <div className="p-2.5 flex flex-col h-[calc(100%-4px)]">
                        <div className="flex items-start gap-2">
                          <div className="w-11 h-11 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex-shrink-0 flex items-center justify-center overflow-hidden shadow-sm">
                            {researcher.photo_url ? (
                              <img
                                src={researcher.photo_url}
                                alt={researcher.name}
                                className="w-11 h-11 object-cover rounded-full"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                            ) : (
                              <span className="text-sm font-bold text-gray-400">
                                {researcher.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                              </span>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="text-sm font-bold text-[#0B1315] leading-tight line-clamp-1">
                              {researcher.name}
                            </h3>
                            {researcher.title && (
                              <p className="text-[11px] text-[#0B1315]/70 font-medium line-clamp-1">{researcher.title}</p>
                            )}
                            <p className="text-[10px] text-gray-500 line-clamp-1">{cleanDept(researcher.department)}</p>
                          </div>
                        </div>
                        {/* Metrics row */}
                        <div className="flex gap-3 mt-1.5 text-[10px]">
                          {researcher.h_index && (
                            <span className="px-1.5 py-0.5 bg-[#0B1315] text-white rounded font-medium">h-index: {researcher.h_index}</span>
                          )}
                          {researcher.citation_count && (
                            <span className="text-gray-600">{researcher.citation_count.toLocaleString()} citations</span>
                          )}
                        </div>
                        {/* Interests */}
                        {researcher.interests && researcher.interests.length > 0 && (
                          <div className="mt-auto pt-1 flex flex-wrap gap-1">
                            {researcher.interests.slice(0, 2).map((interest, i) => (
                              <span
                                key={i}
                                className="px-1.5 py-0.5 bg-gray-100 rounded text-[9px] text-gray-600 truncate max-w-[80px]"
                              >
                                {interest}
                              </span>
                            ))}
                            {researcher.interests.length > 2 && (
                              <span className="text-[9px] text-gray-400">+{researcher.interests.length - 2}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Match Results */}
          <div>
            {!selectedResearcher && !isMatching && matches.length === 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-8 text-center shadow-sm">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-lg flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-[#0B1315] mb-2">Select a Researcher</h3>
                <p className="text-gray-600 text-sm">
                  Click on a researcher from the list to discover potential collaborators based on shared research interests
                </p>
              </div>
            )}

            {isMatching && (
              <div className="mb-6">
                <IRISThinking
                  isActive={isMatching}
                  stage={matchStage}
                  researcherName={selectedResearcher?.name}
                />
              </div>
            )}

            {!isMatching && selectedResearcher && matches.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-[#0B1315]">
                    Matches for {selectedResearcher.name}
                  </h3>
                  <button
                    onClick={clearSelection}
                    className="text-sm text-gray-500 hover:text-[#0B1315] transition-colors"
                  >
                    Clear
                  </button>
                </div>

                <div className="space-y-4">
                  {matches.map((match, index) => (
                    <IRISMatchExplainer
                      key={match.researcher.net_id}
                      matchScore={match.matchScore}
                      matchedResearcher={{
                        name: match.researcher.name,
                        department: match.researcher.department || 'Unknown Department',
                        photoUrl: match.researcher.photo_url,
                      }}
                      factors={match.factors}
                      explanation={match.explanation}
                    />
                  ))}
                </div>

                {matches.length === 0 && (
                  <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
                    <p className="text-gray-600">
                      No matches found. This researcher may have unique research interests.
                    </p>
                  </div>
                )}
              </div>
            )}

            {!isMatching && selectedResearcher && matches.length === 0 && !isLoading && (
              <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
                <p className="text-gray-600">
                  Analyzing research profile... If no matches appear, this researcher may have unique research interests with limited overlap.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Privacy Notice */}
        <div className="mt-12 p-4 bg-gray-100 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3 text-gray-600">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-sm">
              All matching is performed locally on KSU infrastructure. Research data never leaves university servers.
            </span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#0B1315] mt-16">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <p>&copy; 2025 Kennesaw State University</p>
            <p>IRIS - Intelligent Research Information System</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
