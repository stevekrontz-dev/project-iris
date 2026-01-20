'use client';

import { useEffect, useState, useCallback } from 'react';
import { API_URL, EMAIL_API_URL } from '@/lib/api';

interface Grant {
  source: string;
  id: string;
  title: string;
  agency: string;
  keywords: string[];
  amount_range?: string;
  duration?: string;
  deadline?: string;
  team_size?: string;
  description?: string;
  url?: string;
  requirements?: string[];
  why_unconventional?: string;
}

interface GrantsData {
  categories: string[];
  opportunities: Grant[];
}

interface Researcher {
  name: string;
  institution: string;
  field: string;
  subfield?: string;
  h_index: number;
  citations: number;
  openalex_id?: string;
  orcid?: string;
  semantic_score?: number;
}

interface TeamMember extends Researcher {
  role: string;
  matchedKeywords: string[];
  score: number;
}

const INSTITUTIONS = [
  'Kennesaw State University',
  'Georgia Institute of Technology',
  'Emory University',
  'Georgia State University',
  'University of Georgia',
  'Duke University',
  'University of North Carolina',
  'Vanderbilt University',
  'University of Florida',
  'Auburn University',
];

// Category colors and icons
const CATEGORY_CONFIG: Record<string, { color: string; icon: string; short: string }> = {
  'Patient Advocacy & Disease Foundations': { color: '#EC4899', icon: '💗', short: 'Patient Advocacy' },
  'Decentralized Science (DeSci) & DAOs': { color: '#8B5CF6', icon: '🔗', short: 'DeSci/Crypto' },
  'International & Foreign Government': { color: '#3B82F6', icon: '🌍', short: 'International' },
  'Corporate & Industry Partnerships': { color: '#F59E0B', icon: '🏢', short: 'Corporate' },
  'State & Regional Programs': { color: '#10B981', icon: '🗺️', short: 'State/Regional' },
  'Private Foundations (Obscure)': { color: '#6366F1', icon: '🏛️', short: 'Foundations' },
  'Defense & Intelligence (Non-DARPA)': { color: '#EF4444', icon: '🎖️', short: 'Defense/Intel' },
  'Cryptocurrency & Web3': { color: '#A855F7', icon: '₿', short: 'Web3' },
};

// Map sources to categories
const SOURCE_TO_CATEGORY: Record<string, string> = {
  'VitaDAO': 'Decentralized Science (DeSci) & DAOs',
  'ARIA': 'International & Foreign Government',
  'Michael J Fox Foundation': 'Patient Advocacy & Disease Foundations',
  'APDA': 'Patient Advocacy & Disease Foundations',
  'ALS Association': 'Patient Advocacy & Disease Foundations',
  'Japan JST': 'International & Foreign Government',
  'Korea NRF': 'International & Foreign Government',
  'Tether/Crypto': 'Cryptocurrency & Web3',
  'ResearchHub': 'Decentralized Science (DeSci) & DAOs',
  'Georgia FAST': 'State & Regional Programs',
  'Launch Tennessee': 'State & Regional Programs',
  'VA': 'Defense & Intelligence (Non-DARPA)',
  'DOD CDMRP': 'Defense & Intelligence (Non-DARPA)',
  'Wellcome Trust': 'International & Foreign Government',
  'Templeton': 'Private Foundations (Obscure)',
  'Keck': 'Private Foundations (Obscure)',
  'Moore': 'Private Foundations (Obscure)',
  'Sloan': 'Private Foundations (Obscure)',
  'Intel': 'Corporate & Industry Partnerships',
  'Microsoft': 'Corporate & Industry Partnerships',
  'OpenAI': 'Corporate & Industry Partnerships',
  'Gitcoin': 'Decentralized Science (DeSci) & DAOs',
  'Protocol Labs': 'Decentralized Science (DeSci) & DAOs',
  'Ethereum': 'Cryptocurrency & Web3',
  'IARPA': 'Defense & Intelligence (Non-DARPA)',
  'Appalachian Regional': 'State & Regional Programs',
  'EDA': 'State & Regional Programs',
  'CDC': 'Patient Advocacy & Disease Foundations',
  'Reeve': 'Patient Advocacy & Disease Foundations',
  'Craig H. Neilsen': 'Patient Advocacy & Disease Foundations',
  'Helmsley': 'Private Foundations (Obscure)',
  'Arnold': 'Private Foundations (Obscure)',
  'Simons': 'Private Foundations (Obscure)',
  'Schmidt': 'Private Foundations (Obscure)',
};

export default function GrantsPage() {
  const [grants, setGrants] = useState<Grant[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [selectedGrant, setSelectedGrant] = useState<Grant | null>(null);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchScope, setSearchScope] = useState<'single' | 'cross'>('single');
  const [primaryInstitution, setPrimaryInstitution] = useState('Kennesaw State University');
  const [minHIndex, setMinHIndex] = useState(0);
  const [teamSize, setTeamSize] = useState(5);
  const [keywordFilter, setKeywordFilter] = useState('');
  
  // Email briefing state
  const [showBriefingModal, setShowBriefingModal] = useState(false);
  const [briefingPreview, setBriefingPreview] = useState<string | null>(null);
  const [senderName, setSenderName] = useState('Steve Krontz');
  const [senderEmail, setSenderEmail] = useState('stevekrontz@gmail.com');
  const [senderInstitution, setSenderInstitution] = useState('Kennesaw State University - The BrainLab');
  const [customMessage, setCustomMessage] = useState('');
  const [sendingBriefing, setSendingBriefing] = useState(false);
  const [briefingResult, setBriefingResult] = useState<any>(null);

  // Load grants
  useEffect(() => {
    fetch('/grants.json')
      .then(r => r.json())
      .then((data: GrantsData) => {
        setGrants(data.opportunities || []);
        setCategories(data.categories || []);
      })
      .catch(console.error);
  }, []);

  // Filter grants by category and keyword
  const filteredGrants = grants.filter(grant => {
    // Category filter
    if (selectedCategories.size > 0) {
      const grantCategory = SOURCE_TO_CATEGORY[grant.source] || 'Other';
      if (!selectedCategories.has(grantCategory)) return false;
    }
    
    // Keyword filter
    if (keywordFilter) {
      const search = keywordFilter.toLowerCase();
      const matchesTitle = grant.title.toLowerCase().includes(search);
      const matchesKeywords = grant.keywords.some(k => k.toLowerCase().includes(search));
      const matchesSource = grant.source.toLowerCase().includes(search);
      const matchesDesc = grant.description?.toLowerCase().includes(search);
      if (!matchesTitle && !matchesKeywords && !matchesSource && !matchesDesc) return false;
    }
    
    return true;
  });

  // Toggle category selection
  const toggleCategory = (category: string) => {
    const newSelected = new Set(selectedCategories);
    if (newSelected.has(category)) {
      newSelected.delete(category);
    } else {
      newSelected.add(category);
    }
    setSelectedCategories(newSelected);
  };

  // Get category for a grant
  const getGrantCategory = (grant: Grant) => {
    return SOURCE_TO_CATEGORY[grant.source] || 'Other';
  };

  // Build team for selected grant
  const buildTeam = useCallback(async () => {
    if (!selectedGrant) return;
    
    setLoading(true);
    setTeam([]);
    
    try {
      const allCandidates: Map<string, { researcher: Researcher; keywords: string[]; totalScore: number }> = new Map();
      
      for (const keyword of selectedGrant.keywords) {
        const params = new URLSearchParams({
          q: keyword,
          limit: '30',
          min_h_index: minHIndex.toString(),
        });
        
        if (searchScope === 'single') {
          params.append('institution', primaryInstitution);
        }
        
        const res = await fetch(`${API_URL}/search?${params}`);
        const data = await res.json();
        
        for (const r of data.results || []) {
          const key = r.openalex_id || r.name;
          if (allCandidates.has(key)) {
            const existing = allCandidates.get(key)!;
            existing.keywords.push(keyword);
            existing.totalScore += r.semantic_score || 0;
          } else {
            allCandidates.set(key, {
              researcher: r,
              keywords: [keyword],
              totalScore: r.semantic_score || 0,
            });
          }
        }
      }
      
      const candidates = Array.from(allCandidates.values());
      const maxH = Math.max(...candidates.map(c => c.researcher.h_index)) || 1;
      
      const scoredCandidates = candidates.map(c => {
        const keywordCoverage = c.keywords.length / selectedGrant.keywords.length;
        const avgSemantic = c.totalScore / c.keywords.length;
        const hBonus = c.researcher.h_index / maxH;
        
        return {
          ...c.researcher,
          matchedKeywords: c.keywords,
          score: keywordCoverage * 0.4 + avgSemantic * 0.4 + hBonus * 0.2,
          role: c.keywords.length > 1 ? 'Multi-area Expert' : `${c.keywords[0]} Specialist`,
        };
      });
      
      scoredCandidates.sort((a, b) => b.score - a.score);
      
      const selectedTeam: TeamMember[] = [];
      const coveredKeywords = new Set<string>();
      
      for (const candidate of scoredCandidates) {
        if (selectedTeam.length >= teamSize) break;
        const newKeywords = candidate.matchedKeywords.filter(k => !coveredKeywords.has(k));
        if (newKeywords.length > 0 || selectedTeam.length < 2) {
          selectedTeam.push(candidate);
          candidate.matchedKeywords.forEach(k => coveredKeywords.add(k));
        }
      }
      
      for (const candidate of scoredCandidates) {
        if (selectedTeam.length >= teamSize) break;
        if (!selectedTeam.some(t => t.name === candidate.name)) {
          selectedTeam.push(candidate);
        }
      }
      
      setTeam(selectedTeam);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [selectedGrant, searchScope, primaryInstitution, minHIndex, teamSize]);

  useEffect(() => {
    if (selectedGrant) {
      buildTeam();
    }
  }, [buildTeam]);

  const keywordCoverage = selectedGrant ? 
    new Set(team.flatMap(t => t.matchedKeywords)).size / selectedGrant.keywords.length * 100 : 0;

  const previewBriefing = async () => {
    if (!selectedGrant || team.length === 0) return;
    try {
      const res = await fetch(`${EMAIL_API_URL}/preview-briefing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant: selectedGrant,
          team: team,
          sender_name: senderName,
          sender_email: senderEmail,
          sender_institution: senderInstitution,
          custom_message: customMessage || null,
        }),
      });
      const data = await res.json();
      setBriefingPreview(data.html);
      setShowBriefingModal(true);
    } catch (e) {
      console.error(e);
      alert('Error generating preview. Is the email service running on port 8001?');
    }
  };

  const sendBriefings = async () => {
    if (!selectedGrant || team.length === 0) return;
    
    setSendingBriefing(true);
    
    const teamList = team.map((m, i) => 
      `${i+1}. ${m.name} (${m.institution}) - ${m.role}, h-index: ${m.h_index}`
    ).join('%0A');
    
    const subject = encodeURIComponent(`Research Collaboration Opportunity: ${selectedGrant.title}`);
    
    const bodyParts = [
      'Hello,',
      '',
      'I am reaching out because IRIS (Intelligent Research Information System) has identified you as an excellent potential collaborator for an upcoming grant opportunity.',
      '',
    ];
    
    if (customMessage) {
      bodyParts.push(`Personal Note: ${customMessage}`, '');
    }
    
    bodyParts.push(
      '═══════════════════════════════════════',
      'GRANT OPPORTUNITY',
      '═══════════════════════════════════════',
      `${selectedGrant.source}: ${selectedGrant.title}`,
      '',
      `Agency: ${selectedGrant.agency}`,
      `Funding: ${selectedGrant.amount_range || 'See announcement'}`,
      `Duration: ${selectedGrant.duration || 'Varies'}`,
      `Deadline: ${selectedGrant.deadline || 'Rolling'}`,
      '',
      selectedGrant.description || '',
      '',
      `Key Research Areas: ${selectedGrant.keywords.join(', ')}`,
      '',
      selectedGrant.url ? `Full Announcement: ${selectedGrant.url}` : '',
      '',
      '═══════════════════════════════════════',
      'PROPOSED RESEARCH TEAM',
      '═══════════════════════════════════════',
    );
    
    team.forEach((m, i) => {
      bodyParts.push(`${i+1}. ${m.name} (${m.institution})`);
      bodyParts.push(`   Role: ${m.role} | h-index: ${m.h_index}`);
      bodyParts.push(`   Expertise: ${m.matchedKeywords.join(', ')}`);
      bodyParts.push('');
    });
    
    bodyParts.push(
      `Combined h-index: ${team.reduce((sum, m) => sum + m.h_index, 0)}`,
      '',
      '═══════════════════════════════════════',
      'NEXT STEPS', 
      '═══════════════════════════════════════',
      '1. Review the grant announcement',
      '2. Let me know if you are interested in participating',
      '3. We will schedule a brief call to discuss roles and timeline',
      '',
      'I would love to discuss this opportunity with you.',
      '',
      'Best regards,',
      senderName,
      senderInstitution,
      '',
      '---',
      'This collaboration opportunity was identified by IRIS',
      'Kennesaw State University | The BrainLab'
    );
    
    const body = encodeURIComponent(bodyParts.join('\n'));
    const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&su=${subject}&body=${body}`;
    
    window.open(gmailUrl, '_blank');
    
    setSendingBriefing(false);
    setBriefingResult({ 
      success: true, 
      message: 'Gmail opened! Add recipient emails and click Send.' 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <header className="bg-black/50 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-emerald-600 rounded-lg flex items-center justify-center text-xl">
                💰
              </div>
              <div>
                <h1 className="text-white text-xl font-bold">Grant Team Builder</h1>
                <p className="text-gray-400 text-sm">Unconventional funding sources nobody else knows about</p>
              </div>
            </div>
            <nav className="flex gap-4">
              <a href="/" className="text-gray-400 hover:text-white text-sm">KSU IRIS</a>
              <a href="/network" className="text-gray-400 hover:text-white text-sm">Network</a>
              <a href="/consortium" className="text-gray-400 hover:text-white text-sm">Search</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Category Filter Bar */}
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-white font-bold">Filter by Category</h2>
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">{filteredGrants.length} of {grants.length} opportunities</span>
              {selectedCategories.size > 0 && (
                <button 
                  onClick={() => setSelectedCategories(new Set())}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  Clear filters
                </button>
              )}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2 mb-4">
            {categories.map(category => {
              const config = CATEGORY_CONFIG[category] || { color: '#666', icon: '📋', short: category };
              const isSelected = selectedCategories.has(category);
              const count = grants.filter(g => SOURCE_TO_CATEGORY[g.source] === category).length;
              
              return (
                <button
                  key={category}
                  onClick={() => toggleCategory(category)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    isSelected 
                      ? 'ring-2 ring-offset-2 ring-offset-gray-900' 
                      : 'opacity-70 hover:opacity-100'
                  }`}
                  style={{ 
                    backgroundColor: isSelected ? config.color : `${config.color}30`,
                    color: isSelected ? 'white' : config.color,
                    '--tw-ring-color': config.color
                  } as React.CSSProperties}
                >
                  <span>{config.icon}</span>
                  <span>{config.short}</span>
                  <span className={`px-1.5 py-0.5 rounded text-xs ${isSelected ? 'bg-white/20' : 'bg-black/20'}`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
          
          {/* Keyword search */}
          <div className="relative">
            <input
              type="text"
              value={keywordFilter}
              onChange={e => setKeywordFilter(e.target.value)}
              placeholder="Search by keyword, source, or description..."
              className="w-full px-4 py-2 pl-10 rounded-lg bg-gray-900 border border-gray-600 text-white text-sm placeholder-gray-500"
            />
            <span className="absolute left-3 top-2.5 text-gray-500">🔍</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Grant Selection */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700 mb-4">
              <h2 className="text-white font-bold mb-4">1. Select Grant Opportunity</h2>
              
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {filteredGrants.map((grant, i) => {
                  const category = getGrantCategory(grant);
                  const config = CATEGORY_CONFIG[category] || { color: '#666', icon: '📋', short: category };
                  
                  return (
                    <button
                      key={i}
                      onClick={() => setSelectedGrant(grant)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        selectedGrant?.id === grant.id
                          ? 'bg-green-500/20 border-green-500'
                          : 'bg-gray-900/50 border-gray-700 hover:border-gray-600'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span 
                              className="px-2 py-0.5 rounded text-xs font-bold flex items-center gap-1"
                              style={{ 
                                backgroundColor: `${config.color}20`,
                                color: config.color
                              }}
                            >
                              <span>{config.icon}</span>
                              {grant.source}
                            </span>
                          </div>
                          <h3 className="text-white font-medium text-sm truncate">{grant.title}</h3>
                          <p className="text-gray-400 text-xs mt-1">{grant.amount_range}</p>
                          {grant.why_unconventional && (
                            <p className="text-yellow-500/80 text-xs mt-1 truncate">💡 {grant.why_unconventional}</p>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })}
                
                {filteredGrants.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No grants match your filters
                  </div>
                )}
              </div>
            </div>

            {/* Settings */}
            <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
              <h2 className="text-white font-bold mb-4">2. Team Settings</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-gray-400 text-sm block mb-2">Search Scope</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSearchScope('single')}
                      className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        searchScope === 'single'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Single University
                    </button>
                    <button
                      onClick={() => setSearchScope('cross')}
                      className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        searchScope === 'cross'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Cross-University
                    </button>
                  </div>
                </div>

                {searchScope === 'single' && (
                  <div>
                    <label className="text-gray-400 text-sm block mb-2">Institution</label>
                    <select
                      value={primaryInstitution}
                      onChange={e => setPrimaryInstitution(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-600 text-white text-sm"
                    >
                      {INSTITUTIONS.map(inst => (
                        <option key={inst} value={inst}>{inst}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div>
                  <label className="text-gray-400 text-sm block mb-2">Team Size: {teamSize}</label>
                  <input
                    type="range"
                    value={teamSize}
                    onChange={e => setTeamSize(parseInt(e.target.value))}
                    min="3"
                    max="10"
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="text-gray-400 text-sm block mb-2">Min h-index: {minHIndex}</label>
                  <input
                    type="range"
                    value={minHIndex}
                    onChange={e => setMinHIndex(parseInt(e.target.value))}
                    min="0"
                    max="30"
                    className="w-full"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Grant Details & Team */}
          <div className="lg:col-span-2">
            {selectedGrant ? (
              <>
                {/* Grant Info */}
                <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700 mb-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        {(() => {
                          const category = getGrantCategory(selectedGrant);
                          const config = CATEGORY_CONFIG[category] || { color: '#666', icon: '📋', short: category };
                          return (
                            <span 
                              className="px-3 py-1 rounded-lg text-sm font-bold flex items-center gap-2"
                              style={{ 
                                backgroundColor: `${config.color}20`,
                                color: config.color
                              }}
                            >
                              <span>{config.icon}</span>
                              {selectedGrant.source}
                            </span>
                          );
                        })()}
                        <span className="text-gray-500">{selectedGrant.id}</span>
                      </div>
                      <h2 className="text-white text-xl font-bold">{selectedGrant.title}</h2>
                      <p className="text-gray-400 mt-1">{selectedGrant.agency}</p>
                    </div>
                    {selectedGrant.url && (
                      <a 
                        href={selectedGrant.url} 
                        target="_blank" 
                        className="text-blue-400 text-sm hover:underline"
                      >
                        View Details →
                      </a>
                    )}
                  </div>

                  {selectedGrant.why_unconventional && (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mb-4">
                      <p className="text-yellow-400 text-sm">
                        <span className="font-bold">💡 Why This is Unconventional: </span>
                        {selectedGrant.why_unconventional}
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    {selectedGrant.amount_range && (
                      <div className="bg-green-500/10 rounded-lg p-3">
                        <div className="text-green-400 font-bold">{selectedGrant.amount_range}</div>
                        <div className="text-gray-500 text-xs">Funding</div>
                      </div>
                    )}
                    {selectedGrant.duration && (
                      <div className="bg-blue-500/10 rounded-lg p-3">
                        <div className="text-blue-400 font-bold">{selectedGrant.duration}</div>
                        <div className="text-gray-500 text-xs">Duration</div>
                      </div>
                    )}
                    {selectedGrant.deadline && (
                      <div className="bg-red-500/10 rounded-lg p-3">
                        <div className="text-red-400 font-bold">{selectedGrant.deadline}</div>
                        <div className="text-gray-500 text-xs">Deadline</div>
                      </div>
                    )}
                    {selectedGrant.team_size && (
                      <div className="bg-purple-500/10 rounded-lg p-3">
                        <div className="text-purple-400 font-bold">{selectedGrant.team_size}</div>
                        <div className="text-gray-500 text-xs">Team Size</div>
                      </div>
                    )}
                  </div>

                  {selectedGrant.description && (
                    <p className="text-gray-300 text-sm mb-4">{selectedGrant.description}</p>
                  )}

                  <div className="flex flex-wrap gap-2">
                    {selectedGrant.keywords.map((kw, i) => {
                      const covered = team.some(t => t.matchedKeywords.includes(kw));
                      return (
                        <span 
                          key={i}
                          className={`px-3 py-1 rounded-full text-sm ${
                            covered 
                              ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                              : 'bg-gray-700 text-gray-400'
                          }`}
                        >
                          {covered && '✓ '}{kw}
                        </span>
                      );
                    })}
                  </div>

                  {selectedGrant.requirements && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <h4 className="text-gray-400 text-sm mb-2">Requirements:</h4>
                      <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
                        {selectedGrant.requirements.map((req, i) => (
                          <li key={i}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Team Results */}
                <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-white font-bold text-lg">
                      {searchScope === 'single' ? `${primaryInstitution} Team` : 'Cross-University Team'}
                    </h2>
                    <div className="flex items-center gap-4">
                      <div className="text-sm">
                        <span className="text-gray-400">Keyword Coverage: </span>
                        <span className={`font-bold ${keywordCoverage === 100 ? 'text-green-400' : keywordCoverage > 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                          {keywordCoverage.toFixed(0)}%
                        </span>
                      </div>
                      {loading && (
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-green-500 border-t-transparent"></div>
                      )}
                    </div>
                  </div>

                  {team.length > 0 ? (
                    <div className="space-y-3">
                      {team.map((member, i) => (
                        <div 
                          key={i}
                          className="bg-gray-900/50 rounded-lg p-4 border border-gray-700"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-yellow-500 font-bold">#{i + 1}</span>
                                <h3 className="text-white font-medium">{member.name}</h3>
                                <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
                                  {member.role}
                                </span>
                              </div>
                              <p className="text-blue-400 text-sm">{member.institution}</p>
                              <p className="text-gray-500 text-xs mt-1">{member.field}</p>
                            </div>
                            <div className="text-right">
                              <div className="text-purple-400 font-bold">h={member.h_index}</div>
                              <div className="text-gray-500 text-xs">{member.citations.toLocaleString()} cites</div>
                              <div className="text-green-400 text-xs">Score: {(member.score * 100).toFixed(0)}</div>
                            </div>
                          </div>
                          <div className="mt-3 flex flex-wrap gap-1">
                            {member.matchedKeywords.map((kw, j) => (
                              <span key={j} className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                                {kw}
                              </span>
                            ))}
                          </div>
                          <div className="mt-2 flex gap-2">
                            {member.orcid && (
                              <a href={member.orcid} target="_blank" className="text-green-400 text-xs hover:underline">ORCID</a>
                            )}
                            {member.openalex_id && (
                              <a href={member.openalex_id} target="_blank" className="text-orange-400 text-xs hover:underline">OpenAlex</a>
                            )}
                          </div>
                        </div>
                      ))}
                      
                      {/* Send Briefing Section */}
                      <div className="mt-6 pt-6 border-t border-gray-700">
                        <h3 className="text-white font-bold mb-4">📧 Send Team Briefing</h3>
                        
                        <div className="space-y-3 mb-4">
                          <div>
                            <label className="text-gray-400 text-xs block mb-1">Your Name</label>
                            <input
                              type="text"
                              value={senderName}
                              onChange={e => setSenderName(e.target.value)}
                              className="w-full px-3 py-2 rounded bg-gray-900 border border-gray-600 text-white text-sm"
                            />
                          </div>
                          <div>
                            <label className="text-gray-400 text-xs block mb-1">Your Email</label>
                            <input
                              type="email"
                              value={senderEmail}
                              onChange={e => setSenderEmail(e.target.value)}
                              className="w-full px-3 py-2 rounded bg-gray-900 border border-gray-600 text-white text-sm"
                            />
                          </div>
                          <div>
                            <label className="text-gray-400 text-xs block mb-1">Your Institution</label>
                            <input
                              type="text"
                              value={senderInstitution}
                              onChange={e => setSenderInstitution(e.target.value)}
                              className="w-full px-3 py-2 rounded bg-gray-900 border border-gray-600 text-white text-sm"
                            />
                          </div>
                          <div>
                            <label className="text-gray-400 text-xs block mb-1">Personal Message (optional)</label>
                            <textarea
                              value={customMessage}
                              onChange={e => setCustomMessage(e.target.value)}
                              placeholder="Add a personal note to your briefing..."
                              className="w-full px-3 py-2 rounded bg-gray-900 border border-gray-600 text-white text-sm h-20 resize-none"
                            />
                          </div>
                        </div>
                        
                        <div className="flex gap-2">
                          <button
                            onClick={previewBriefing}
                            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium text-sm"
                          >
                            👁 Preview HTML
                          </button>
                          <button
                            onClick={sendBriefings}
                            disabled={sendingBriefing}
                            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg font-medium text-sm"
                          >
                            {sendingBriefing ? '⏳...' : '📨 Open in Gmail'}
                          </button>
                        </div>
                        
                        <p className="text-gray-500 text-xs mt-2 text-center">
                          Opens Gmail compose - add recipients manually
                        </p>
                        
                        {briefingResult && (
                          <div className={`mt-3 p-3 rounded-lg text-sm ${briefingResult.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                            {briefingResult.success ? (
                              <>✓ {briefingResult.message}</>
                            ) : (
                              <>✗ {briefingResult.error}</>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : loading ? (
                    <div className="text-center py-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-4 border-green-500 border-t-transparent mx-auto"></div>
                      <p className="text-gray-400 mt-4">Building optimal team...</p>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      No researchers found matching grant criteria
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="bg-gray-800/50 rounded-xl p-12 border border-gray-700 text-center">
                <div className="text-6xl mb-4">💰</div>
                <h2 className="text-white text-xl font-bold mb-2">Select a Grant Opportunity</h2>
                <p className="text-gray-400 mb-6">Choose a grant from the list to find the optimal research team</p>
                
                {/* Category legend */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-2xl mx-auto">
                  {categories.slice(0, 8).map(category => {
                    const config = CATEGORY_CONFIG[category] || { color: '#666', icon: '📋', short: category };
                    const count = grants.filter(g => SOURCE_TO_CATEGORY[g.source] === category).length;
                    
                    return (
                      <div 
                        key={category}
                        className="p-3 rounded-lg text-left"
                        style={{ backgroundColor: `${config.color}15` }}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span>{config.icon}</span>
                          <span className="text-white text-sm font-medium">{config.short}</span>
                        </div>
                        <p className="text-gray-400 text-xs">{count} opportunities</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      
      {/* Briefing Preview Modal */}
      {showBriefingModal && briefingPreview && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-gray-100 px-6 py-4 flex items-center justify-between border-b">
              <h3 className="font-bold text-gray-800">📧 Email Preview</h3>
              <button 
                onClick={() => setShowBriefingModal(false)}
                className="text-gray-500 hover:text-gray-800 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <iframe
                srcDoc={briefingPreview}
                className="w-full h-full min-h-[600px]"
                title="Email Preview"
              />
            </div>
            <div className="bg-gray-100 px-6 py-4 flex justify-end gap-2 border-t">
              <button
                onClick={() => setShowBriefingModal(false)}
                className="px-4 py-2 bg-gray-300 hover:bg-gray-400 text-gray-800 rounded-lg font-medium"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowBriefingModal(false);
                  sendBriefings();
                }}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium"
              >
                📨 Open in Gmail
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
