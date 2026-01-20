'use client';

import { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import { API_URL } from '@/lib/api';

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

interface Node extends Researcher {
  id: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  isSeed?: boolean;
  seedIndex?: number;
}

interface Edge {
  source: Node | string;
  target: Node | string;
  weight: number;
  type: 'semantic' | 'coauthor';
}

const INSTITUTION_COLORS: Record<string, string> = {
  'Georgia Institute of Technology': '#B3A369',
  'Emory University': '#4169E1',
  'Duke University': '#00539B',
  'University of North Carolina': '#7BAFD4',
  'University of Florida': '#FA4616',
  'Vanderbilt University': '#CFB53B',
  'Virginia Tech': '#861F41',
  'Auburn University': '#DD550C',
  'Clemson University': '#F56600',
  'University of Georgia': '#BA0C2F',
  'Wake Forest University': '#9E7E38',
  'North Carolina State': '#CC0000',
  'Georgia State University': '#0039A6',
  'University of Alabama': '#9E1B32',
  'University of Virginia': '#F84C1E',
  'Kennesaw State University': '#FDBB30',
};

const SEED_COLORS = ['#FFD700', '#FF6B6B', '#4ECDC4', '#A855F7', '#F97316'];

function getInstitutionColor(inst: string): string {
  for (const [key, color] of Object.entries(INSTITUTION_COLORS)) {
    if (inst.includes(key) || key.includes(inst.split(' ')[0])) return color;
  }
  return '#888';
}

export default function NetworkPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState<Researcher[]>([]);
  const [seedResearchers, setSeedResearchers] = useState<Researcher[]>([]);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  
  // Filters
  const [minHIndex, setMinHIndex] = useState(0);
  const [maxResults, setMaxResults] = useState(50);
  const [institutionFilter, setInstitutionFilter] = useState('');
  const [seedInstitutionsOnly, setSeedInstitutionsOnly] = useState(false);
  
  // Scoring weights
  const [semanticWeight, setSemanticWeight] = useState(0.7);
  const [hIndexWeight, setHIndexWeight] = useState(0.3);

  // Search by name
  const searchResearchers = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    try {
      const res = await fetch(`${API_URL}/name?q=${encodeURIComponent(query)}&limit=10`);
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (e) {
      console.error(e);
    }
  };

  // Add seed researcher
  const addSeed = (researcher: Researcher) => {
    if (seedResearchers.length >= 5) return;
    if (seedResearchers.some(s => s.name === researcher.name)) return;
    setSeedResearchers([...seedResearchers, researcher]);
    setSearch('');
    setSearchResults([]);
    setShowSuggestions(false);
  };

  // Remove seed researcher
  const removeSeed = (index: number) => {
    setSeedResearchers(seedResearchers.filter((_, i) => i !== index));
  };

  // Build network from all seeds
  const buildNetwork = useCallback(async () => {
    if (seedResearchers.length === 0) return;
    
    setLoading(true);
    
    try {
      // Search for similar researchers for EACH seed
      const allCandidates: Map<string, { researcher: Researcher; scores: number[]; matchedSeeds: number[] }> = new Map();
      
      for (let seedIdx = 0; seedIdx < seedResearchers.length; seedIdx++) {
        const seed = seedResearchers[seedIdx];
        const searchQuery = `${seed.field} ${seed.subfield || ''}`.trim();
        
        const params = new URLSearchParams({
          q: searchQuery,
          limit: maxResults.toString(),
          min_h_index: minHIndex.toString(),
        });
        if (institutionFilter) params.append('institution', institutionFilter);
        
        const res = await fetch(`${API_URL}/search?${params}`);
        const data = await res.json();
        
        for (const r of data.results || []) {
          const key = r.openalex_id || r.name;
          if (allCandidates.has(key)) {
            const existing = allCandidates.get(key)!;
            existing.scores.push(r.semantic_score || 0);
            existing.matchedSeeds.push(seedIdx);
          } else {
            allCandidates.set(key, {
              researcher: r,
              scores: [r.semantic_score || 0],
              matchedSeeds: [seedIdx],
            });
          }
        }
      }
      
      // Convert to nodes - prioritize those matching MULTIPLE seeds
      const candidateList = Array.from(allCandidates.values());
      
      // Filter to seed institutions only if enabled
      const seedInstitutions = new Set(seedResearchers.map(s => s.institution));
      const filteredCandidates = seedInstitutionsOnly 
        ? candidateList.filter(c => seedInstitutions.has(c.researcher.institution))
        : candidateList;
      
      // Score by: number of seeds matched * average semantic score
      filteredCandidates.sort((a, b) => {
        const aMultiScore = a.matchedSeeds.length * (a.scores.reduce((x, y) => x + y, 0) / a.scores.length);
        const bMultiScore = b.matchedSeeds.length * (b.scores.reduce((x, y) => x + y, 0) / b.scores.length);
        return bMultiScore - aMultiScore;
      });
      
      // Take top candidates
      const topCandidates = filteredCandidates.slice(0, maxResults);
      
      // Create nodes
      const newNodes: Node[] = [];
      
      // Add seeds first
      seedResearchers.forEach((seed, idx) => {
        newNodes.push({
          ...seed,
          id: seed.openalex_id || `seed-${idx}`,
          isSeed: true,
          seedIndex: idx,
          score: 1,
          semantic_score: 1,
        });
      });
      
      // Add candidates (excluding seeds)
      const seedNames = new Set(seedResearchers.map(s => s.name));
      topCandidates.forEach((c, i) => {
        if (seedNames.has(c.researcher.name)) return;
        newNodes.push({
          ...c.researcher,
          id: c.researcher.openalex_id || `candidate-${i}`,
          isSeed: false,
          score: c.matchedSeeds.length * (c.scores.reduce((x, y) => x + y, 0) / c.scores.length),
          semantic_score: c.scores.reduce((x, y) => x + y, 0) / c.scores.length,
          // Store which seeds they match
          matchedSeeds: c.matchedSeeds,
        } as any);
      });
      
      // Create edges
      const newEdges: Edge[] = [];
      
      // Connect each candidate to the seeds they match
      newNodes.forEach(node => {
        if (node.isSeed) return;
        const matchedSeeds = (node as any).matchedSeeds || [];
        matchedSeeds.forEach((seedIdx: number) => {
          const seedNode = newNodes.find(n => n.isSeed && n.seedIndex === seedIdx);
          if (seedNode) {
            newEdges.push({
              source: seedNode.id,
              target: node.id,
              weight: node.semantic_score || 0.5,
              type: 'semantic',
            });
          }
        });
      });
      
      // Connect seeds to each other (to show their relationship)
      for (let i = 0; i < seedResearchers.length; i++) {
        for (let j = i + 1; j < seedResearchers.length; j++) {
          const seed1 = newNodes.find(n => n.isSeed && n.seedIndex === i);
          const seed2 = newNodes.find(n => n.isSeed && n.seedIndex === j);
          if (seed1 && seed2) {
            newEdges.push({
              source: seed1.id,
              target: seed2.id,
              weight: 0.8,
              type: 'semantic',
            });
          }
        }
      }
      
      setNodes(newNodes);
      setEdges(newEdges);
      
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [seedResearchers, maxResults, minHIndex, institutionFilter, seedInstitutionsOnly]);

  // Auto-rebuild when filters change
  useEffect(() => {
    if (seedResearchers.length > 0 && !loading) {
      buildNetwork();
    }
  }, [buildNetwork]);

  // Clear network when no seeds
  useEffect(() => {
    if (seedResearchers.length === 0) {
      setNodes([]);
      setEdges([]);
    }
  }, [seedResearchers.length]);

  // Calculate composite score
  const getCompositeScore = (node: Node): number => {
    if (node.isSeed) return 999; // Seeds always on top
    const maxH = Math.max(...nodes.filter(n => !n.isSeed).map(n => n.h_index)) || 1;
    const matchCount = ((node as any).matchedSeeds?.length || 1);
    const maxMatch = seedResearchers.length;
    
    const semanticNorm = node.semantic_score || 0;
    const hNorm = node.h_index / maxH;
    const matchNorm = matchCount / maxMatch;
    
    // Bonus for matching multiple seeds
    const multiMatchBonus = matchCount > 1 ? 0.2 * (matchCount - 1) : 0;
    
    return semanticNorm * semanticWeight + hNorm * hIndexWeight + multiMatchBonus;
  };

  // Ranked nodes
  const rankedNodes = useMemo(() => {
    return [...nodes]
      .map(n => ({ ...n, compositeScore: getCompositeScore(n) }))
      .sort((a, b) => b.compositeScore - a.compositeScore);
  }, [nodes, semanticWeight, hIndexWeight, seedResearchers.length]);

  // Render network
  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = 600;

    const defs = svg.append('defs');
    const glow = defs.append('filter').attr('id', 'glow');
    glow.append('feGaussianBlur').attr('stdDeviation', '2').attr('result', 'coloredBlur');
    const glowMerge = glow.append('feMerge');
    glowMerge.append('feMergeNode').attr('in', 'coloredBlur');
    glowMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const g = svg.append('g');

    const initialScale = 0.5;
    const initialTransform = d3.zoomIdentity
      .translate(width * 0.25, height * 0.25)
      .scale(initialScale);
    
    g.attr('transform', initialTransform.toString());

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => g.attr('transform', event.transform));
    
    svg.call(zoom);
    svg.call(zoom.transform, initialTransform);

    const nodesCopy = nodes.map(n => ({ ...n }));
    const nodeMap = new Map(nodesCopy.map(n => [n.id, n]));
    
    const edgesCopy = edges.map(e => ({
      ...e,
      source: typeof e.source === 'string' ? e.source : e.source.id,
      target: typeof e.target === 'string' ? e.target : e.target.id,
    })).filter(e => nodeMap.has(e.source as string) && nodeMap.has(e.target as string));

    const simulation = d3.forceSimulation<Node>(nodesCopy)
      .force('link', d3.forceLink<Node, any>(edgesCopy).id((d: any) => d.id).distance(120).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide<Node>().radius(d => getNodeRadius(d) + 8));

    // Draw edges
    const link = g.append('g')
      .selectAll('line')
      .data(edgesCopy)
      .join('line')
      .attr('stroke', d => {
        // Color by which seed it connects to
        const srcNode = nodeMap.get(d.source as string);
        const tgtNode = nodeMap.get(d.target as string);
        if (srcNode?.isSeed) return SEED_COLORS[srcNode.seedIndex || 0];
        if (tgtNode?.isSeed) return SEED_COLORS[tgtNode.seedIndex || 0];
        return '#6366F1';
      })
      .attr('stroke-opacity', 0.4)
      .attr('stroke-width', d => Math.max(1, d.weight * 4))
      .attr('stroke-dasharray', '4,2');

    function getNodeRadius(d: Node): number {
      if (d.isSeed) return 25;
      const matchCount = (d as any).matchedSeeds?.length || 1;
      return Math.max(8, Math.min(20, 8 + matchCount * 4 + Math.sqrt(d.h_index)));
    }

    // Draw nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(nodesCopy)
      .join('circle')
      .attr('r', d => getNodeRadius(d))
      .attr('fill', d => {
        if (d.isSeed) return SEED_COLORS[d.seedIndex || 0];
        // Color by institution or by matched seeds
        const matchCount = (d as any).matchedSeeds?.length || 0;
        if (matchCount > 1) return '#10B981'; // Green for multi-match
        return getInstitutionColor(d.institution);
      })
      .attr('stroke', d => d.isSeed ? '#FFF' : '#FFF')
      .attr('stroke-width', d => d.isSeed ? 4 : 2)
      .attr('cursor', 'pointer')
      .attr('filter', 'url(#glow)')
      .on('mouseover', function(_, d) {
        d3.select(this).attr('stroke', '#FFD700').attr('stroke-width', 4);
        setHoveredNode(d);
      })
      .on('mouseout', function(_, d) {
        d3.select(this)
          .attr('stroke', '#FFF')
          .attr('stroke-width', d.isSeed ? 4 : 2);
        setHoveredNode(null);
      })
      .on('click', (_, d) => {
        if (!d.isSeed) setSelectedNode(d);
      })
      // @ts-ignore
      .call(d3.drag<SVGCircleElement, Node>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // Labels for seeds
    const labels = g.append('g')
      .selectAll('text')
      .data(nodesCopy.filter(n => n.isSeed))
      .join('text')
      .attr('text-anchor', 'middle')
      .attr('dy', d => getNodeRadius(d) + 16)
      .attr('fill', d => SEED_COLORS[d.seedIndex || 0])
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('pointer-events', 'none')
      .attr('paint-order', 'stroke')
      .attr('stroke', '#000')
      .attr('stroke-width', '3px')
      .text(d => d.name.split(' ').slice(-1)[0]);

    simulation.on('tick', () => {
      link
        .attr('x1', d => {
          const src = typeof d.source === 'object' ? d.source : nodeMap.get(d.source as string);
          return src?.x ?? 0;
        })
        .attr('y1', d => {
          const src = typeof d.source === 'object' ? d.source : nodeMap.get(d.source as string);
          return src?.y ?? 0;
        })
        .attr('x2', d => {
          const tgt = typeof d.target === 'object' ? d.target : nodeMap.get(d.target as string);
          return tgt?.x ?? 0;
        })
        .attr('y2', d => {
          const tgt = typeof d.target === 'object' ? d.target : nodeMap.get(d.target as string);
          return tgt?.y ?? 0;
        });
      node
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!);
      labels
        .attr('x', d => d.x!)
        .attr('y', d => d.y!);
    });

  }, [nodes, edges]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <header className="bg-black/50 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center text-xl">
                🔬
              </div>
              <div>
                <h1 className="text-white text-xl font-bold">Research Collaboration Finder</h1>
                <p className="text-gray-400 text-sm">Find researchers who bridge multiple areas</p>
              </div>
            </div>
            <nav className="flex gap-4">
              <a href="/" className="text-gray-400 hover:text-white text-sm">KSU IRIS</a>
              <a href="/consortium" className="text-gray-400 hover:text-white text-sm">Search</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Seed Researchers */}
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700 mb-6">
          <h2 className="text-white font-bold mb-4">1. Add Researchers to Find Connections Between (up to 5)</h2>
          
          {/* Current seeds */}
          {seedResearchers.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {seedResearchers.map((seed, i) => (
                <div 
                  key={i}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg border-2"
                  style={{ borderColor: SEED_COLORS[i], backgroundColor: `${SEED_COLORS[i]}20` }}
                >
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: SEED_COLORS[i] }}
                  />
                  <span className="text-white font-medium">{seed.name}</span>
                  <span className="text-gray-400 text-sm">({seed.institution.split(' ').slice(0, 2).join(' ')})</span>
                  <button 
                    onClick={() => removeSeed(i)}
                    className="text-gray-500 hover:text-white ml-1"
                  >✕</button>
                </div>
              ))}
            </div>
          )}
          
          {/* Search input */}
          {seedResearchers.length < 5 && (
            <div className="relative max-w-xl">
              <input
                type="text"
                value={search}
                onChange={e => {
                  setSearch(e.target.value);
                  searchResearchers(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder={`Add researcher ${seedResearchers.length + 1}...`}
                className="w-full px-4 py-3 rounded-lg bg-gray-900 border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:border-yellow-500"
              />
              
              {showSuggestions && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
                  {searchResults.map((r, i) => (
                    <button
                      key={i}
                      onClick={() => addSeed(r)}
                      disabled={seedResearchers.some(s => s.name === r.name)}
                      className="w-full px-4 py-3 text-left hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex justify-between items-center border-b border-gray-700 last:border-0"
                    >
                      <div>
                        <div className="text-white font-medium">{r.name}</div>
                        <div className="text-gray-400 text-sm">{r.institution}</div>
                        <div className="text-gray-500 text-xs">{r.field}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-purple-400 font-bold">h={r.h_index}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700 mb-6">
          <h2 className="text-white font-bold mb-4">2. Filters & Scoring</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <label className="text-gray-400 text-sm block mb-2">Min h-index: {minHIndex}</label>
              <input
                type="range"
                value={minHIndex}
                onChange={e => setMinHIndex(parseInt(e.target.value))}
                min="0"
                max="50"
                className="w-full"
              />
            </div>
            
            <div>
              <label className="text-gray-400 text-sm block mb-2">Max researchers: {maxResults}</label>
              <input
                type="range"
                value={maxResults}
                onChange={e => setMaxResults(parseInt(e.target.value))}
                min="20"
                max="100"
                step="10"
                className="w-full"
              />
            </div>
            
            <div>
              <label className="text-gray-400 text-sm block mb-2">Institution</label>
              <select
                value={institutionFilter}
                onChange={e => setInstitutionFilter(e.target.value)}
                className="w-full px-3 py-2 rounded bg-gray-900 border border-gray-600 text-white text-sm"
              >
                <option value="">All Institutions</option>
                {Object.keys(INSTITUTION_COLORS).map(inst => (
                  <option key={inst} value={inst}>{inst}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="text-gray-400 text-sm block mb-2">Seed Institutions Only</label>
              <button
                onClick={() => setSeedInstitutionsOnly(!seedInstitutionsOnly)}
                disabled={seedResearchers.length === 0}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  seedInstitutionsOnly 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {seedInstitutionsOnly ? '✓ Same University' : 'Any University'}
              </button>
            </div>
            
            <div>
              <label className="text-gray-400 text-sm block mb-2">Similarity vs h-index: {(semanticWeight * 100).toFixed(0)}% / {(hIndexWeight * 100).toFixed(0)}%</label>
              <input
                type="range"
                value={semanticWeight}
                onChange={e => {
                  const v = parseFloat(e.target.value);
                  setSemanticWeight(v);
                  setHIndexWeight(1 - v);
                }}
                min="0"
                max="1"
                step="0.1"
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Network + Ranked List */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Network */}
          <div className="lg:col-span-2">
            <div className="relative">
              {loading && (
                <div className="absolute inset-0 bg-gray-900/80 flex items-center justify-center z-10 rounded-xl">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-yellow-500 border-t-transparent mx-auto"></div>
                    <p className="text-gray-400 mt-4">Finding connections...</p>
                  </div>
                </div>
              )}
              
              <svg
                ref={svgRef}
                className="w-full bg-gray-900/50 rounded-xl border border-gray-700"
                style={{ height: '600px' }}
                onClick={() => setShowSuggestions(false)}
              />
              
              {nodes.length === 0 && !loading && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <p className="text-gray-500">Add researchers above and click "Find" to build network</p>
                </div>
              )}
              
              {hoveredNode && (
                <div className="absolute top-4 left-4 bg-black/95 border border-gray-600 rounded-xl p-4 max-w-sm shadow-2xl">
                  <div className="flex items-center gap-2">
                    {hoveredNode.isSeed && (
                      <div 
                        className="w-4 h-4 rounded-full" 
                        style={{ backgroundColor: SEED_COLORS[hoveredNode.seedIndex || 0] }}
                      />
                    )}
                    <h3 className="text-white font-bold">{hoveredNode.name}</h3>
                  </div>
                  <p className="text-blue-400 text-sm">{hoveredNode.institution}</p>
                  <div className="mt-2 flex gap-4 text-sm">
                    <span className="text-purple-400">h={hoveredNode.h_index}</span>
                    {!hoveredNode.isSeed && (
                      <span className="text-green-400">
                        Matches {(hoveredNode as any).matchedSeeds?.length || 0} seed{((hoveredNode as any).matchedSeeds?.length || 0) !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-500 text-xs mt-1">{hoveredNode.field}</p>
                </div>
              )}
            </div>
            
            {/* Legend */}
            <div className="mt-4 flex flex-wrap gap-4 text-sm">
              {seedResearchers.map((seed, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: SEED_COLORS[i] }} />
                  <span className="text-gray-400">{seed.name.split(' ').slice(-1)[0]}</span>
                </div>
              ))}
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-green-500" />
                <span className="text-gray-400">Matches multiple seeds</span>
              </div>
            </div>
          </div>
          
          {/* Ranked List */}
          <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-4 max-h-[700px] overflow-y-auto">
            <h3 className="text-white font-bold mb-4 sticky top-0 bg-gray-800 py-2">
              {seedResearchers.length > 1 ? 'Bridge Researchers' : 'Similar Researchers'} ({rankedNodes.filter(n => !n.isSeed).length})
            </h3>
            
            {rankedNodes.filter(n => !n.isSeed).map((node, i) => {
              const matchCount = (node as any).matchedSeeds?.length || 0;
              return (
                <div
                  key={`${node.id}-${i}`}
                  className={`p-3 rounded-lg mb-2 cursor-pointer transition-colors border ${
                    matchCount > 1 
                      ? 'bg-green-500/10 border-green-500/30 hover:bg-green-500/20' 
                      : 'bg-gray-900/50 border-transparent hover:bg-gray-700/50'
                  }`}
                  onClick={() => setSelectedNode(node)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 text-sm">#{i + 1}</span>
                        <span className="text-white font-medium truncate">{node.name}</span>
                        {matchCount > 1 && (
                          <span className="bg-green-500/20 text-green-400 text-xs px-2 py-0.5 rounded-full">
                            {matchCount} matches
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 text-xs truncate">{node.institution}</p>
                    </div>
                    <div className="text-right flex-shrink-0 ml-2">
                      <div className="text-purple-400 font-bold">h={node.h_index}</div>
                    </div>
                  </div>
                  <div className="mt-2 flex gap-1 flex-wrap">
                    {(node as any).matchedSeeds?.map((seedIdx: number) => (
                      <div 
                        key={seedIdx}
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: SEED_COLORS[seedIdx] }}
                        title={seedResearchers[seedIdx]?.name}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
            
            {rankedNodes.filter(n => !n.isSeed).length === 0 && (
              <p className="text-gray-500 text-center py-8">No results yet</p>
            )}
          </div>
        </div>

        {/* Selected researcher detail */}
        {selectedNode && !selectedNode.isSeed && (
          <div className="fixed bottom-4 right-4 bg-gray-900 border border-gray-600 rounded-xl p-6 max-w-md shadow-2xl z-50">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-white font-bold text-lg">{selectedNode.name}</h3>
              <button onClick={() => setSelectedNode(null)} className="text-gray-500 hover:text-white">✕</button>
            </div>
            <p className="text-blue-400">{selectedNode.institution}</p>
            <p className="text-gray-400 text-sm mt-1">{selectedNode.field}</p>
            
            <div className="mt-3">
              <span className="text-gray-400 text-sm">Matches: </span>
              {(selectedNode as any).matchedSeeds?.map((seedIdx: number) => (
                <span 
                  key={seedIdx}
                  className="inline-block px-2 py-1 rounded text-xs mr-1"
                  style={{ backgroundColor: `${SEED_COLORS[seedIdx]}30`, color: SEED_COLORS[seedIdx] }}
                >
                  {seedResearchers[seedIdx]?.name.split(' ').slice(-1)[0]}
                </span>
              ))}
            </div>
            
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div className="bg-purple-500/20 rounded-lg p-2 text-center">
                <div className="text-purple-400 font-bold">{selectedNode.h_index}</div>
                <div className="text-gray-500 text-xs">h-index</div>
              </div>
              <div className="bg-blue-500/20 rounded-lg p-2 text-center">
                <div className="text-blue-400 font-bold">{selectedNode.citations.toLocaleString()}</div>
                <div className="text-gray-500 text-xs">citations</div>
              </div>
            </div>
            
            <div className="mt-4 flex gap-2">
              {selectedNode.orcid && (
                <a href={selectedNode.orcid} target="_blank" className="text-green-400 text-sm hover:underline">ORCID →</a>
              )}
              {selectedNode.openalex_id && (
                <a href={selectedNode.openalex_id} target="_blank" className="text-orange-400 text-sm hover:underline">OpenAlex →</a>
              )}
            </div>
            
            <button
              onClick={() => {
                addSeed(selectedNode);
                setSelectedNode(null);
              }}
              disabled={seedResearchers.length >= 5 || seedResearchers.some(s => s.name === selectedNode.name)}
              className="mt-4 w-full py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 text-white rounded-lg font-medium"
            >
              ➕ Add as Seed Researcher
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
