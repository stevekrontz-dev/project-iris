'use client';

import { useState } from 'react';

interface SearchResult {
  net_id: string;
  name: string;
  title?: string;
  department?: string;
  college?: string;
  email?: string;
  photo_url?: string;
  h_index?: number;
  citations?: number;
  works_count?: number;
  topics?: string[];
  score: number;
}

export default function SemanticSearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchedQuery, setSearchedQuery] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setSearchedQuery(query);

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#0B1315] border-b border-gray-800">
        <div className="max-w-5xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-[#FDBB30] rounded flex items-center justify-center">
                <span className="text-[#0B1315] font-bold text-sm">KSU</span>
              </div>
              <div>
                <h1 className="text-white text-lg font-semibold">IRIS Semantic Search</h1>
                <p className="text-xs text-gray-400">Find researchers by concept, not just keywords</p>
              </div>
            </div>
            <nav className="flex items-center space-x-6 text-sm">
              <a href="/" className="text-gray-400 hover:text-white">Home</a>
              <a href="/discover" className="text-gray-400 hover:text-white">Discover</a>
              <a href="/search" className="text-white">Search</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Search Box */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe what you're looking for... (e.g., 'machine learning for medical diagnosis')"
              className="flex-1 px-5 py-4 text-lg text-gray-900 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#FDBB30] focus:border-transparent outline-none shadow-sm placeholder:text-gray-400"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="px-8 py-4 bg-[#FDBB30] text-[#0B1315] font-semibold rounded-xl hover:bg-[#e5a826] transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Try: "brain computer interface" • "climate policy economics" • "polymer surface chemistry"
          </p>
        </form>

        {/* Results */}
        {searchedQuery && (
          <div className="mb-4 text-gray-600">
            {results.length > 0 ? (
              <span>Found <strong>{results.length}</strong> researchers for "<strong>{searchedQuery}</strong>"</span>
            ) : (
              <span>No results for "{searchedQuery}"</span>
            )}
          </div>
        )}

        <div className="space-y-4">
          {results.map((r, idx) => (
            <div
              key={r.net_id}
              className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-4">
                {/* Rank */}
                <div className="w-8 h-8 bg-[#0B1315] text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                  {idx + 1}
                </div>

                {/* Photo */}
                <div className="w-16 h-16 rounded-full bg-gray-100 flex-shrink-0 overflow-hidden">
                  {r.photo_url ? (
                    <img src={r.photo_url} alt={r.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400 font-bold">
                      {r.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-bold text-[#0B1315]">{r.name}</h3>
                      {r.title && <p className="text-sm text-gray-600">{r.title}</p>}
                      <p className="text-sm text-gray-500">{r.department} • {r.college}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-2xl font-bold text-[#FDBB30]">{(r.score * 100).toFixed(0)}%</div>
                      <div className="text-xs text-gray-500">match</div>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="mt-3 flex gap-4 text-sm">
                    {r.h_index && (
                      <span className="px-2 py-1 bg-[#0B1315] text-white rounded font-medium">
                        h-index: {r.h_index}
                      </span>
                    )}
                    {r.citations && (
                      <span className="text-gray-600">{r.citations.toLocaleString()} citations</span>
                    )}
                    {r.works_count && (
                      <span className="text-gray-600">{r.works_count} publications</span>
                    )}
                  </div>

                  {/* Topics */}
                  {r.topics && r.topics.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {r.topics.map((topic, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-700"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Contact */}
                  {r.email && (
                    <div className="mt-3">
                      <a
                        href={`mailto:${r.email}`}
                        className="text-sm text-[#FDBB30] hover:underline"
                      >
                        {r.email}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Privacy Notice */}
        <div className="mt-12 p-4 bg-gray-100 rounded-lg border border-gray-200">
          <div className="flex items-center gap-3 text-gray-600">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-sm">
              Semantic search powered by local AI (Ollama). Your queries stay on KSU infrastructure.
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}
