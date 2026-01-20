'use client';

import { useEffect, useRef, useState } from 'react';

interface Person {
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
  all_leaders: Person[];
  colleges?: Record<string, Person[]>;
}

const LEVEL_COLORS: Record<number, string> = {
  1: '#DC2626', 2: '#EA580C', 3: '#D97706', 4: '#CA8A04',
  5: '#65A30D', 6: '#16A34A', 7: '#059669', 8: '#0D9488',
  9: '#0891B2', 10: '#0284C7', 11: '#2563EB', 12: '#4F46E5',
  13: '#7C3AED', 14: '#9333EA', 15: '#A855F7', 16: '#C026D3',
  17: '#DB2777', 18: '#E11D48', 19: '#F43F5E', 20: '#64748B', 25: '#94A3B8',
};

export default function OrgTreePage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [data, setData] = useState<OrgData | null>(null);
  const [selectedCollege, setSelectedCollege] = useState<string>('all');
  const [maxLevel, setMaxLevel] = useState<number>(12);
  const [hoveredPerson, setHoveredPerson] = useState<Person | null>(null);

  useEffect(() => {
    fetch('/api/org-chart')
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const loadD3 = async () => {
      if (!svgRef.current) return;
      
      const d3 = await import('d3');
      
      const svg = d3.select(svgRef.current);
      svg.selectAll('*').remove();

      const width = svgRef.current.clientWidth;
      const height = svgRef.current.clientHeight;

      let people = data.all_leaders.filter(p => p.level <= maxLevel);
      if (selectedCollege !== 'all') {
        people = people.filter(p => p.college === selectedCollege);
      }
      if (people.length > 500) people = people.slice(0, 500);

      const nodes: any[] = [];
      const links: any[] = [];
      
      const colleges = new Set(people.map(p => p.college || 'Unknown'));
      const collegeNodes: Record<string, any> = {};
      
      colleges.forEach(college => {
        const node = { id: `college-${college}`, name: college, type: 'college', level: 0, radius: 20 };
        collegeNodes[college] = node;
        nodes.push(node);
      });

      people.forEach((person, i) => {
        const node = { id: `person-${i}`, ...person, type: 'person', radius: Math.max(4, 12 - person.level) };
        nodes.push(node);
        const college = person.college || 'Unknown';
        if (collegeNodes[college]) {
          links.push({ source: collegeNodes[college].id, target: node.id, strength: 0.1 });
        }
      });

      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id((d: any) => d.id).distance(50).strength(0.2))
        .force('charge', d3.forceManyBody().strength(-100))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius((d: any) => d.radius + 5));

      const g = svg.append('g');
      
      svg.call(d3.zoom().scaleExtent([0.1, 4]).on('zoom', (event) => {
        g.attr('transform', event.transform);
      }) as any);

      const link = g.append('g').selectAll('line').data(links).join('line')
        .attr('stroke', '#374151').attr('stroke-opacity', 0.3).attr('stroke-width', 1);

      const node = g.append('g').selectAll('circle').data(nodes).join('circle')
        .attr('r', (d: any) => d.radius)
        .attr('fill', (d: any) => d.type === 'college' ? '#FDBB30' : (LEVEL_COLORS[d.level] || '#64748B'))
        .attr('stroke', '#fff').attr('stroke-width', 1).style('cursor', 'pointer')
        .call(d3.drag()
          .on('start', (event, d: any) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on('drag', (event, d: any) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d: any) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }) as any)
        .on('mouseover', (event, d: any) => { if (d.type === 'person') setHoveredPerson(d); })
        .on('mouseout', () => setHoveredPerson(null));

      const labels = g.append('g').selectAll('text')
        .data(nodes.filter((n: any) => n.type === 'college')).join('text')
        .text((d: any) => d.name.substring(0, 25))
        .attr('font-size', '10px').attr('fill', '#FDBB30').attr('text-anchor', 'middle').attr('dy', -25);

      simulation.on('tick', () => {
        link.attr('x1', (d: any) => d.source.x).attr('y1', (d: any) => d.source.y)
            .attr('x2', (d: any) => d.target.x).attr('y2', (d: any) => d.target.y);
        node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);
        labels.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y);
      });
    };
    loadD3();
  }, [data, selectedCollege, maxLevel]);

  const colleges = data?.colleges ? Object.keys(data.colleges).sort() : [];

  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col">
      <header className="bg-[#0B1315] border-b border-gray-700 px-6 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-[#FDBB30]">KSU Political Map</h1>
            <p className="text-xs text-gray-400">{data ? `${data.total_leaders} people` : 'Loading...'}</p>
          </div>
          <div className="flex gap-4 items-center">
            <select value={selectedCollege} onChange={(e) => setSelectedCollege(e.target.value)}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm">
              <option value="all">All Colleges</option>
              {colleges.map(c => <option key={c} value={c}>{c.substring(0, 40)}</option>)}
            </select>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Depth:</span>
              <input type="range" min="5" max="25" value={maxLevel} onChange={(e) => setMaxLevel(parseInt(e.target.value))} className="w-24"/>
              <span className="text-xs w-6">{maxLevel}</span>
            </div>
            <a href="/org-chart" className="text-gray-400 hover:text-white text-sm">List</a>
            <a href="/search" className="text-gray-400 hover:text-white text-sm">Search</a>
          </div>
        </div>
      </header>

      <div className="bg-gray-800 px-6 py-2 flex gap-3 flex-wrap text-xs border-b border-gray-700">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-600"></span>President</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-orange-600"></span>VP</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-lime-600"></span>Dean</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-teal-600"></span>Chair</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-cyan-600"></span>Director</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-violet-600"></span>Faculty</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-slate-500"></span>Staff</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#FDBB30]"></span>College</span>
      </div>

      <div className="flex-1 relative">
        <svg ref={svgRef} className="w-full h-full" />
        
        {hoveredPerson && (
          <div className="absolute top-4 left-4 bg-gray-800 border border-gray-600 rounded-lg p-4 shadow-xl max-w-sm z-10">
            <div className="font-bold text-lg">{hoveredPerson.name}</div>
            <div className="text-sm text-gray-300">{hoveredPerson.title}</div>
            <div className="text-xs text-gray-400 mt-1">{hoveredPerson.college}</div>
            {hoveredPerson.unit && <div className="text-xs text-gray-500">{hoveredPerson.unit}</div>}
            <div className="mt-2 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{background: LEVEL_COLORS[hoveredPerson.level]}}/>
              <span className="text-xs">Level {hoveredPerson.level} - {hoveredPerson.category}</span>
            </div>
          </div>
        )}

        <div className="absolute bottom-4 right-4 text-xs text-gray-500">
          Scroll to zoom | Drag to pan | Drag nodes to rearrange
        </div>
      </div>
    </div>
  );
}
