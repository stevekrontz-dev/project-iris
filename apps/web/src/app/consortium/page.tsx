'use client';

import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/api';
import { Navigation } from '@/components/Navigation';

interface Researcher {
  name: string;
  institution: string;
  field: string;
  subfield: string;
  h_index: number;
  citations: number;
  works_count: number;
  openalex_id: string;
  orcid: string;
  score: number;
  semantic_score: number;
}

interface SearchResult {
  query: string;
  total_indexed: number;
  count: number;
  search_time_ms: number;
  results: Researcher[];
}

const INSTITUTIONS = [
  'Georgia Institute of Technology',
  'Emory University',
  'Duke University',
  'University of North Carolina',
  'University of Florida',
  'Vanderbilt University',
  'Virginia Tech',
  'Auburn University',
  'Clemson University',
  'University of Georgia',
  'Wake Forest University',
  'North Carolina State University',
  'Georgia State University',
  'University of Alabama at Birmingham',
  'University of Virginia',
];

export default function ConsortiumPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [minH, setMinH] = useState(0);
  const [institution, setInstitution] = useState('');
  const [hWeight, setHWeight] = useState(0.3);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    // Load stats on mount
    fetch(`${API_URL}/stats`)
      .then(r => r.json())
      .then(setStats)
      .catch(console.error);
  }, []);

  const search = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: query,
        limit: '30',
        min_h: minH.toString(),
        h_weight: hWeight.toString(),
      });
      if (institution) params.append('institution', institution);
      
      const res = await fetch(`/api/search/southeast?${params}`);
      const data = await res.json();
      setResults(data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') search();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Navigation variant="dark" />

      {/* Page Header */}
      <div className="bg-black/30 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-blue-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SE</span>
            </div>
            <div>
              <h2 className="text-white text-lg sm:text-xl font-bold">Southeast Research Consortium</h2>
              <p className="text-gray-400 text-xs sm:text-sm">
                {stats ? `${stats.total_researchers.toLocaleString()} researchers` : 'Loading...'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Search Box */}
        <div className="max-w-3xl mx-auto mb-8">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search by research area, expertise, or name..."
              className="w-full px-6 py-4 rounded-xl bg-gray-800/50 border border-gray-700 text-white text-lg placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
            <button
              onClick={search}
              disabled={loading}
              className="absolute right-2 top-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-medium text-white transition-colors"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <label className="text-gray-400">Min h-index:</label>
              <input
                type="number"
                value={minH}
                onChange={(e) => setMinH(parseInt(e.target.value) || 0)}
                min="0"
                className="w-20 px-3 py-1 rounded bg-gray-800 border border-gray-700 text-white"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-gray-400">Institution:</label>
              <select
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
                className="px-3 py-1 rounded bg-gray-800 border border-gray-700 text-white max-w-[200px]"
              >
                <option value="">All</option>
                {INSTITUTIONS.map(inst => (
                  <option key={inst} value={inst}>{inst}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-gray-400">h-index weight:</label>
              <input
                type="range"
                value={hWeight}
                onChange={(e) => setHWeight(parseFloat(e.target.value))}
                min="0"
                max="0.5"
                step="0.1"
                className="w-24"
              />
              <span className="text-gray-400 w-8">{hWeight}</span>
            </div>
          </div>
        </div>

        {/* Stats Bar */}
        {results && (
          <div className="max-w-3xl mx-auto mb-6 p-4 rounded-lg bg-gray-800/30">
            <div className="flex justify-between text-sm text-gray-400">
              <span>{results.count} results from {results.total_indexed.toLocaleString()} researchers</span>
              <span>{results.search_time_ms.toFixed(1)}ms</span>
            </div>
          </div>
        )}

        {/* Results */}
        <div className="space-y-4">
          {results?.results.map((r, i) => (
            <div
              key={i}
              className="p-6 rounded-xl bg-gray-800/50 border border-gray-700 hover:border-gray-600 transition-all hover:transform hover:translate-y-[-2px]"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl font-bold text-gray-500">#{i + 1}</span>
                    <h3 className="text-xl font-semibold text-white">{r.name}</h3>
                  </div>
                  <p className="text-blue-400 mb-2">{r.institution}</p>
                  {r.field && (
                    <p className="text-gray-400 text-sm">
                      {r.field}{r.subfield ? ` → ${r.subfield}` : ''}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-purple-400">h={r.h_index}</div>
                  <div className="text-sm text-gray-400">{r.citations.toLocaleString()} citations</div>
                  <div className="text-sm text-gray-500">{r.works_count} works</div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between items-center text-xs text-gray-500">
                <div className="flex gap-4">
                  <span>Semantic: {(r.semantic_score * 100).toFixed(1)}%</span>
                  <span>Weighted: {(r.score * 100).toFixed(1)}%</span>
                </div>
                <div className="flex gap-3">
                  {r.orcid && (
                    <a href={r.orcid} target="_blank" rel="noopener" className="text-green-400 hover:underline">
                      ORCID
                    </a>
                  )}
                  {r.openalex_id && (
                    <a href={r.openalex_id} target="_blank" rel="noopener" className="text-orange-400 hover:underline">
                      OpenAlex
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Searches */}
        {!results && (
          <div className="max-w-3xl mx-auto mt-12">
            <h3 className="text-gray-400 mb-4 text-center">Quick searches:</h3>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                'brain computer interface',
                'machine learning neural networks',
                'cancer immunotherapy',
                'climate change',
                'neuroscience cognition',
                'robotics automation',
                'quantum computing',
                'genetics genomics CRISPR',
              ].map(q => (
                <button
                  key={q}
                  onClick={() => { setQuery(q); search(); }}
                  className="px-4 py-2 rounded-full bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Institution Stats */}
        {stats && !results && (
          <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-green-400 mb-4">Top Institutions</h3>
              <div className="space-y-2">
                {Object.entries(stats.top_institutions || {}).slice(0, 10).map(([name, count]: [string, any]) => (
                  <div key={name} className="flex justify-between text-sm">
                    <span className="text-gray-300 truncate">{name}</span>
                    <span className="text-gray-500">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-blue-400 mb-4">H-Index Distribution</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Average</span>
                  <span className="text-white font-bold">{stats.avg_h_index}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Maximum</span>
                  <span className="text-white font-bold">{stats.max_h_index}</span>
                </div>
                {stats.h_index_percentiles && Object.entries(stats.h_index_percentiles).map(([pct, val]: [string, any]) => (
                  <div key={pct} className="flex justify-between">
                    <span className="text-gray-400">{pct} percentile</span>
                    <span className="text-gray-300">{val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
