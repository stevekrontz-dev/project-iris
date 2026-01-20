'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { PotentialCollaborators } from '@/components/iris/PotentialCollaborators';

// KSU Brand Colors
const KSU_GOLD = '#FDBB30';
const KSU_BLACK = '#0B1315';

// Types
interface Publication {
  title: string;
  authors?: string[];
  journal?: string;
  conference?: string;
  book?: string;
  year?: number;
  date?: string;
  volume?: string;
  issue?: string;
  pages?: string;
  publisher?: string;
  abstract?: string;
  citations?: number;
  doi?: string;
  article_url?: string;
}

interface ScholarData {
  name: string;
  affiliation?: string;
  interests?: string[];
  h_index?: number;
  i10_index?: number;
  citedby?: number;
  scholar_id?: string;
  profile_url?: string;
  publications?: Publication[];
  publication_count?: number;
}

interface Researcher {
  id: string;
  name: string;
  firstName?: string;
  lastName?: string;
  title?: string;
  department?: string;
  college?: string;
  email?: string;
  phone?: string;
  office?: string;
  photoUrl?: string; // Updated from photo_url
  bio?: string;
  profile_url?: string;

  // Metrics
  h_index?: number;
  citation_count?: number;
  works_count?: number;

  // External IDs
  googleScholarId?: string;
  openalexId?: string;
  orcidId?: string;

  // Data
  publications?: Publication[];
  interests?: string[];
}

// Helper to clean department/college strings (remove extra info after newline)
function cleanField(field?: string): string | undefined {
  if (!field) return undefined;
  return field.split('\n')[0].trim();
}

export default function ResearcherProfile({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [researcher, setResearcher] = useState<Researcher | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPubs, setExpandedPubs] = useState<Set<number>>(new Set());
  const [showAllPubs, setShowAllPubs] = useState(false);

  useEffect(() => {
    fetch(`/api/researcher/${id}`)
      .then(res => {
        if (!res.ok) throw new Error('Researcher not found');
        return res.json();
      })
      .then(data => {
        setResearcher(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  const togglePub = (index: number) => {
    const newExpanded = new Set(expandedPubs);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedPubs(newExpanded);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-gray-300 border-t-[#FDBB30] rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading researcher profile...</p>
        </div>
      </div>
    );
  }

  if (!researcher) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">Researcher not found</p>
          <Link href="/" className="text-[#FDBB30] hover:underline mt-2 inline-block">
            Return to home
          </Link>
        </div>
      </div>
    );
  }

  const publications = researcher.publications || [];
  const displayedPubs = showAllPubs ? publications : publications.slice(0, 10);
  const department = cleanField(researcher.department);
  const college = cleanField(researcher.college);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#0B1315] border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <div className="py-5 flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-[#FDBB30] rounded flex items-center justify-center">
                <span className="text-[#0B1315] font-bold text-sm">KSU</span>
              </div>
              <div>
                <h1 className="text-white text-lg font-semibold tracking-tight">IRIS v2</h1>
                <p className="text-xs text-gray-400">Intelligent Research Information System</p>
              </div>
            </Link>
            <nav className="flex items-center space-x-6 text-sm">
              <Link href="/" className="text-gray-400 hover:text-white transition-colors">
                Search
              </Link>
              <button className="bg-[#FDBB30] text-[#0B1315] px-4 py-2 rounded font-medium text-sm hover:bg-[#e5a826] transition-colors">
                Sign In
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Profile Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Photo */}
            <div className="flex-shrink-0">
              {researcher.photoUrl ? (
                <img
                  src={researcher.photoUrl}
                  alt={researcher.name}
                  className="w-32 h-32 rounded-lg object-cover border border-gray-200"
                />
              ) : (
                <div className="w-32 h-32 rounded-lg bg-gray-100 flex items-center justify-center border border-gray-200">
                  <span className="text-3xl text-gray-400 font-serif">
                    {researcher.firstName?.[0]}{researcher.lastName?.[0]}
                  </span>
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-grow">
              <h1 className="text-3xl font-serif font-bold text-[#0B1315]">
                {researcher.name}
              </h1>
              {researcher.title && (
                <p className="text-lg text-gray-600 mt-1">{researcher.title}</p>
              )}
              {department && (
                <p className="text-gray-500">{department}</p>
              )}
              {college && (
                <p className="text-gray-400 text-sm">{college}</p>
              )}

              {/* Contact */}
              <div className="flex flex-wrap gap-4 mt-4 text-sm">
                {researcher.email && (
                  <a href={`mailto:${researcher.email}`} className="text-[#0B1315] hover:text-[#FDBB30] flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    {researcher.email}
                  </a>
                )}
                {researcher.phone && (
                  <span className="text-gray-500 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    {researcher.phone}
                  </span>
                )}
                {researcher.googleScholarId && (
                  <a
                    href={`https://scholar.google.com/citations?user=${researcher.googleScholarId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 24a7 7 0 110-14 7 7 0 010 14zm0-24L0 9.5l4.838 3.94A8 8 0 0112 9a8 8 0 017.162 4.44L24 9.5z" />
                    </svg>
                    Google Scholar
                  </a>
                )}
              </div>
            </div>

            {/* Metrics */}
            <div className="flex-shrink-0">
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-4">Research Metrics</h3>
                <div className="grid grid-cols-3 gap-6 text-center">
                  <div>
                    <div className="text-2xl font-bold text-[#0B1315]">{researcher.h_index || '-'}</div>
                    <div className="text-xs text-gray-500 mt-1">h-index</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-[#0B1315]">{researcher.citation_count?.toLocaleString() || '-'}</div>
                    <div className="text-xs text-gray-500 mt-1">Citations</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-[#0B1315]">{researcher.works_count || publications.length || '-'}</div>
                    <div className="text-xs text-gray-500 mt-1">Publications</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="lg:col-span-1 space-y-6">
            {/* Research Interests */}
            {researcher.interests && researcher.interests.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-sm font-semibold text-[#0B1315] uppercase tracking-wide mb-4">Research Interests</h3>
                <div className="flex flex-wrap gap-2">
                  {researcher.interests.map((interest, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full hover:bg-[#FDBB30] hover:text-[#0B1315] transition-colors cursor-pointer"
                    >
                      {interest}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* AI Collaborator Suggestions */}
            <PotentialCollaborators researcherId={id} limit={5} />

            {/* Bio */}
            {researcher.bio && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-sm font-semibold text-[#0B1315] uppercase tracking-wide mb-4">Biography</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{researcher.bio}</p>
              </div>
            )}

            {/* External Links */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-[#0B1315] uppercase tracking-wide mb-4">External Profiles</h3>
              <div className="space-y-2">
                {researcher.profile_url && (
                  <a
                    href={researcher.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-gray-600 hover:text-[#0B1315]"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                    </svg>
                    KSU Faculty Page
                  </a>
                )}
                {researcher.openalexId && (
                  <a
                    href={`https://openalex.org/authors/${researcher.openalexId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-gray-600 hover:text-[#0B1315]"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                    </svg>
                    OpenAlex Profile
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Publications */}
          <div className="lg:col-span-2">
            <div className="bg-white border border-gray-200 rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-[#0B1315]">Publications</h3>
                <span className="text-sm text-gray-500">{publications.length} total</span>
              </div>

              {publications.length === 0 ? (
                <div className="p-8 text-center">
                  <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-gray-500 text-sm">No publication data available yet.</p>
                  <p className="text-gray-400 text-xs mt-1">Publications will appear here once linked to this profile.</p>
                </div>
              ) : (
                <>
                  <div className="divide-y divide-gray-100">
                    {displayedPubs.map((pub, index) => (
                      <div key={index} className="p-6 hover:bg-gray-50 transition-colors">
                        {/* Title */}
                        <h4 className="font-medium text-[#0B1315] leading-snug">
                          {pub.article_url ? (
                            <a href={pub.article_url} target="_blank" rel="noopener noreferrer" className="hover:text-[#FDBB30]">
                              {pub.title}
                            </a>
                          ) : (
                            pub.title
                          )}
                        </h4>

                        {/* Authors */}
                        {pub.authors && pub.authors.length > 0 && (
                          <p className="text-sm text-gray-500 mt-1">
                            {pub.authors.slice(0, 5).join(', ')}
                            {pub.authors.length > 5 && ` +${pub.authors.length - 5} more`}
                          </p>
                        )}

                        {/* Journal/Venue */}
                        <p className="text-sm text-gray-600 mt-2">
                          <span className="italic">{pub.journal || pub.conference || pub.book}</span>
                          {pub.volume && ` ${pub.volume}`}
                          {pub.issue && `(${pub.issue})`}
                          {pub.pages && `, ${pub.pages}`}
                          {pub.year && ` (${pub.year})`}
                        </p>

                        {/* Metrics Row */}
                        <div className="flex items-center gap-4 mt-3 text-xs">
                          {pub.citations !== undefined && (
                            <span className="flex items-center gap-1 text-gray-500">
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                              </svg>
                              {pub.citations} citations
                            </span>
                          )}
                          {pub.doi && (
                            <a
                              href={`https://doi.org/${pub.doi}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline"
                            >
                              DOI: {pub.doi}
                            </a>
                          )}
                          <button
                            onClick={() => togglePub(index)}
                            className="text-gray-500 hover:text-[#0B1315] ml-auto"
                          >
                            {expandedPubs.has(index) ? 'Hide details' : 'Show details'}
                          </button>
                        </div>

                        {/* Expanded Details */}
                        {expandedPubs.has(index) && pub.abstract && (
                          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                            <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Abstract</h5>
                            <p className="text-sm text-gray-700 leading-relaxed">{pub.abstract}</p>
                            {pub.publisher && (
                              <p className="text-xs text-gray-500 mt-3">Publisher: {pub.publisher}</p>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Show More */}
                  {publications.length > 10 && (
                    <div className="px-6 py-4 border-t border-gray-200 text-center">
                      <button
                        onClick={() => setShowAllPubs(!showAllPubs)}
                        className="text-sm text-[#0B1315] font-medium hover:text-[#FDBB30] transition-colors"
                      >
                        {showAllPubs ? 'Show fewer publications' : `Show all ${publications.length} publications`}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#0B1315] mt-16">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <p>&copy; 2025 Kennesaw State University - IRIS</p>
            <Link href="/" className="text-gray-400 hover:text-white transition-colors">
              Back to Search
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
