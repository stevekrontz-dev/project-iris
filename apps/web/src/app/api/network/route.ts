import { NextResponse } from 'next/server';
import * as fs from 'fs';

const DATA_PATHS = [
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_library.json',
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_enriched.json',
  'C:/Users/Steve/Projects/project-iris/apps/scraper/output/faculty_fixed.json',
];

interface Publication {
  title: string;
  authors?: string[];
  year?: number;
  journal?: string;
  citations?: number;
  doi?: string;
  article_url?: string;
}

interface Researcher {
  net_id: string;
  name: string;
  department?: string;
  college?: string;
  h_index?: number;
  citation_count?: number;
  scholar?: {
    interests?: string[];
    publications?: Publication[];
  };
}

interface GraphNode {
  id: string;
  name: string;
  department: string;
  college: string;
  h_index: number;
  citations: number;
  publication_count: number;
  interests: string[];
  // AI-computed metrics
  innovation_potential: number; // 0-1 score for spinout potential
  collaboration_score: number; // How connected they are
  interdisciplinary_score: number; // Cross-department connections
}

interface GraphEdge {
  source: string;
  target: string;
  weight: number; // Number of shared publications
  shared_publications: {
    title: string;
    year?: number;
    doi?: string;
    url?: string;
  }[];
  connection_type: 'co_author' | 'topic_overlap' | 'citation';
  // AI insight
  synergy_score: number; // How promising this connection is
}

function loadResearcherData(): Researcher[] {
  for (const dataPath of DATA_PATHS) {
    try {
      if (fs.existsSync(dataPath)) {
        const rawData = fs.readFileSync(dataPath, 'utf-8');
        return JSON.parse(rawData);
      }
    } catch (e) {
      console.error(`Error loading ${dataPath}:`, e);
    }
  }
  return [];
}

function normalizeAuthorName(name: string): string {
  // Normalize author names for matching
  return name
    .toLowerCase()
    .replace(/[^a-z\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .filter(p => p.length > 1)
    .slice(0, 2) // First two name parts
    .join(' ');
}

function calculateInnovationPotential(researcher: Researcher): number {
  // AI heuristic: High h-index + diverse interests + recent publications = spinout potential
  const hIndexScore = Math.min((researcher.h_index || 0) / 40, 1);
  const interestDiversity = Math.min((researcher.scholar?.interests?.length || 0) / 5, 1);
  const pubCount = researcher.scholar?.publications?.length || 0;
  const recentPubs = researcher.scholar?.publications?.filter(p => (p.year || 0) >= 2020).length || 0;
  const recencyScore = pubCount > 0 ? recentPubs / pubCount : 0;

  return (hIndexScore * 0.4 + interestDiversity * 0.3 + recencyScore * 0.3);
}

function calculateSynergyScore(
  r1: Researcher,
  r2: Researcher,
  sharedPubs: number
): number {
  // AI heuristic: Different departments + shared publications + complementary interests = high synergy
  const crossDepartment = r1.department !== r2.department ? 0.3 : 0;
  const sharedPubScore = Math.min(sharedPubs / 5, 0.4);

  // Check for complementary interests
  const interests1 = new Set(r1.scholar?.interests?.map(i => i.toLowerCase()) || []);
  const interests2 = new Set(r2.scholar?.interests?.map(i => i.toLowerCase()) || []);
  const sharedInterests = [...interests1].filter(i => interests2.has(i)).length;
  const totalInterests = new Set([...interests1, ...interests2]).size;
  const interestOverlap = totalInterests > 0 ? sharedInterests / totalInterests : 0;

  return crossDepartment + sharedPubScore + (interestOverlap * 0.3);
}

export async function GET() {
  const researchers = loadResearcherData();

  // Include all researchers (not just enriched ones)
  const enrichedResearchers = researchers;

  // Build author name to researcher ID mapping
  const authorToResearcher = new Map<string, string>();
  enrichedResearchers.forEach(r => {
    const normalizedName = normalizeAuthorName(r.name);
    authorToResearcher.set(normalizedName, r.net_id);

    // Also add first/last variations
    const parts = r.name.split(' ');
    if (parts.length >= 2) {
      authorToResearcher.set(normalizeAuthorName(`${parts[0]} ${parts[parts.length - 1]}`), r.net_id);
    }
  });

  // Build nodes
  const nodes: GraphNode[] = enrichedResearchers.map(r => ({
    id: r.net_id,
    name: r.name,
    department: r.department?.split('\n')[0]?.trim() || 'Unknown',
    college: r.college?.split('\n')[0]?.trim() || 'Unknown',
    h_index: r.h_index || 0,
    citations: r.citation_count || r.scholar?.publications?.reduce((sum, p) => sum + (p.citations || 0), 0) || 0,
    publication_count: r.scholar?.publications?.length || 0,
    interests: r.scholar?.interests || [],
    innovation_potential: calculateInnovationPotential(r),
    collaboration_score: 0, // Will be calculated after edges
    interdisciplinary_score: 0,
  }));

  // Build edges from co-authorship
  const edgeMap = new Map<string, GraphEdge>();

  enrichedResearchers.forEach(r => {
    const publications = r.scholar?.publications || [];

    publications.forEach(pub => {
      if (!pub.authors || pub.authors.length < 2) return;

      // Find KSU co-authors
      pub.authors.forEach(authorName => {
        const normalizedAuthor = normalizeAuthorName(authorName);
        const coAuthorId = authorToResearcher.get(normalizedAuthor);

        if (coAuthorId && coAuthorId !== r.net_id) {
          const edgeKey = [r.net_id, coAuthorId].sort().join('|');

          if (!edgeMap.has(edgeKey)) {
            const coAuthor = enrichedResearchers.find(x => x.net_id === coAuthorId);
            edgeMap.set(edgeKey, {
              source: r.net_id,
              target: coAuthorId,
              weight: 0,
              shared_publications: [],
              connection_type: 'co_author',
              synergy_score: coAuthor ? calculateSynergyScore(r, coAuthor, 1) : 0.5,
            });
          }

          const edge = edgeMap.get(edgeKey)!;

          // Check if this publication is already added
          const pubExists = edge.shared_publications.some(p => p.title === pub.title);
          if (!pubExists) {
            edge.weight++;
            edge.shared_publications.push({
              title: pub.title,
              year: pub.year,
              doi: pub.doi,
              url: pub.article_url,
            });

            // Update synergy score
            const coAuthor = enrichedResearchers.find(x => x.net_id === coAuthorId);
            if (coAuthor) {
              edge.synergy_score = calculateSynergyScore(r, coAuthor, edge.weight);
            }
          }
        }
      });
    });
  });

  const edges = Array.from(edgeMap.values());

  // Calculate collaboration scores
  const collaborationCounts = new Map<string, number>();
  edges.forEach(e => {
    collaborationCounts.set(e.source, (collaborationCounts.get(e.source) || 0) + e.weight);
    collaborationCounts.set(e.target, (collaborationCounts.get(e.target) || 0) + e.weight);
  });

  const maxCollabs = Math.max(...collaborationCounts.values(), 1);
  nodes.forEach(n => {
    n.collaboration_score = (collaborationCounts.get(n.id) || 0) / maxCollabs;
  });

  // Calculate interdisciplinary scores
  const deptConnections = new Map<string, Set<string>>();
  edges.forEach(e => {
    const sourceNode = nodes.find(n => n.id === e.source);
    const targetNode = nodes.find(n => n.id === e.target);
    if (sourceNode && targetNode && sourceNode.department !== targetNode.department) {
      if (!deptConnections.has(e.source)) deptConnections.set(e.source, new Set());
      if (!deptConnections.has(e.target)) deptConnections.set(e.target, new Set());
      deptConnections.get(e.source)!.add(targetNode.department);
      deptConnections.get(e.target)!.add(sourceNode.department);
    }
  });

  const maxDepts = Math.max(...[...deptConnections.values()].map(s => s.size), 1);
  nodes.forEach(n => {
    n.interdisciplinary_score = (deptConnections.get(n.id)?.size || 0) / maxDepts;
  });

  // Get unique departments for legend
  const departments = [...new Set(nodes.map(n => n.department))].sort();

  return NextResponse.json({
    nodes,
    edges,
    departments,
    stats: {
      total_researchers: nodes.length,
      total_connections: edges.length,
      avg_connections: edges.length > 0 ? (edges.reduce((s, e) => s + e.weight, 0) / edges.length).toFixed(1) : 0,
      high_potential_researchers: nodes.filter(n => n.innovation_potential > 0.7).length,
    }
  });
}
