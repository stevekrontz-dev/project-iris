'use client';

import { useState, useEffect } from 'react';

interface Leader {
  name: string;
  title: string;
  department?: string;
  college?: string;
  unit?: string;
  level: number;
  category: string;
}

interface OrgData {
  generated: string;
  total_leaders: number;
  by_category: Record<string, Leader[]>;
  all_leaders: Leader[];
}

const LEVEL_COLORS: Record<number, string> = {
  1: '#991B1B',  // President - deep red
  2: '#B91C1C',  // Provost
  3: '#DC2626',  // VP
  4: '#EF4444',  // Vice Provost
  5: '#F59E0B',  // Dean - gold
  6: '#FBBF24',  // Associate Dean
  7: '#FCD34D',  // Assistant Dean
  8: '#10B981',  // Chair - green
  9: '#34D399',  // Director
  10: '#6EE7B7', // Coordinator
  11: '#3B82F6', // Faculty - blue
};

const LEVEL_NAMES: Record<number, string> = {
  1: 'President',
  2: 'Provost',
  3: 'Vice President',
  4: 'Vice Provost',
  5: 'Dean',
  6: 'Associate Dean',
  7: 'Assistant Dean',
  8: 'Chair',
  9: 'Director',
  10: 'Coordinator',
  11: 'Faculty',
};

export default function OrgChartPage() {
  const [data, setData] = useState<OrgData | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedColleges, setExpandedColleges] = useState<Set<string>>(new Set(['Office of the President', 'Office of Research']));

  useEffect(() => {
    fetch('/api/org-chart')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  const toggleCollege = (college: string) => {
    setExpandedColleges(prev => {
      const next = new Set(prev);
      if (next.has(college)) next.delete(college);
      else next.add(college);
      return next;
    });
  };

  const filteredLeaders = data?.all_leaders.filter(leader => {
    if (selectedLevel !== null && leader.level !== selectedLevel) return false;
    if (selectedCategory && leader.category !== selectedCategory) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        leader.name.toLowerCase().includes(q) ||
        leader.title.toLowerCase().includes(q) ||
        leader.department?.toLowerCase().includes(q)
      );
    }
    return true;
  }) || [];

  // Group by college/office
  const byCollege: Record<string, Leader[]> = {};
  filteredLeaders.forEach(leader => {
    const college = leader.college || leader.department?.split(' - ')[0] || 'Other';
    if (!byCollege[college]) byCollege[college] = [];
    byCollege[college].push(leader);
  });

  // Sort colleges by highest-ranking member
  const sortedColleges = Object.entries(byCollege).sort((a, b) => {
    const minA = Math.min(...a[1].map(l => l.level));
    const minB = Math.min(...b[1].map(l => l.level));
    return minA - minB;
  });

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-[#0B1315] border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[#FDBB30]">KSU Leadership Map</h1>
              <p className="text-sm text-gray-400">
                {data ? `${data.total_leaders} leaders` : 'Loading...'}
                {data && ` | Generated ${data.generated}`}
              </p>
            </div>
            <nav className="flex gap-4 text-sm">
              <a href="/" className="text-gray-400 hover:text-white">Home</a>
              <a href="/search" className="text-gray-400 hover:text-white">Search</a>
              <a href="/org-chart" className="text-white">Org Chart</a>
            </nav>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <input
            type="text"
            placeholder="Search name, title, department..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 min-w-[300px] px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-[#FDBB30] focus:border-transparent"
          />
          
          <select
            value={selectedLevel ?? ''}
            onChange={(e) => setSelectedLevel(e.target.value ? parseInt(e.target.value) : null)}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          >
            <option value="">All Levels</option>
            {Object.entries(LEVEL_NAMES).map(([level, name]) => (
              <option key={level} value={level}>{name}</option>
            ))}
          </select>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-2 mb-6">
          {Object.entries(LEVEL_NAMES).map(([level, name]) => (
            <button
              key={level}
              onClick={() => setSelectedLevel(selectedLevel === parseInt(level) ? null : parseInt(level))}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                selectedLevel === parseInt(level) ? 'ring-2 ring-white' : 'opacity-80 hover:opacity-100'
              }`}
              style={{ backgroundColor: LEVEL_COLORS[parseInt(level)] }}
            >
              {name}
            </button>
          ))}
        </div>

        <div className="mb-4 text-gray-400 text-sm">
          Showing {filteredLeaders.length} leaders
        </div>

        {/* Org Chart */}
        <div className="space-y-3">
          {sortedColleges.map(([college, leaders]) => (
            <div key={college} className="bg-gray-800 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleCollege(college)}
                className="w-full px-4 py-3 flex items-center justify-between bg-gray-700 hover:bg-gray-600 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <span className="font-semibold">{college}</span>
                  <span className="text-sm text-gray-400">({leaders.length})</span>
                </div>
                <span className="text-gray-400">{expandedColleges.has(college) ? '−' : '+'}</span>
              </button>

              {expandedColleges.has(college) && (
                <div className="p-3 space-y-2">
                  {leaders.sort((a, b) => a.level - b.level).map((leader, idx) => (
                    <div
                      key={`${leader.name}-${idx}`}
                      className="flex items-center gap-3 p-3 bg-gray-900 rounded-lg"
                      style={{ marginLeft: `${Math.min((leader.level - 1) * 12, 60)}px` }}
                    >
                      <div
                        className="w-2 h-8 rounded-full flex-shrink-0"
                        style={{ backgroundColor: LEVEL_COLORS[leader.level] }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium">{leader.name}</div>
                        <div className="text-sm text-gray-400 truncate">{leader.title}</div>
                      </div>
                      <span
                        className="px-2 py-1 rounded text-xs font-medium flex-shrink-0"
                        style={{ 
                          backgroundColor: LEVEL_COLORS[leader.level] + '30', 
                          color: LEVEL_COLORS[leader.level] 
                        }}
                      >
                        L{leader.level}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {!data && (
          <div className="text-center py-12 text-gray-500">Loading org chart data...</div>
        )}
      </div>
    </div>
  );
}
