/**
 * Cluster Analysis for IRIS
 * Identifies the most interesting research cluster for zoom targeting
 */

import { GraphNode, GraphEdge, ClusterInfo } from './types';



/**
 * Build adjacency map from edges
 */
function buildAdjacencyMap(
  nodes: GraphNode[],
  edges: GraphEdge[]
): Map<string, Set<string>> {
  const adjacency = new Map<string, Set<string>>();

  // Initialize all nodes
  nodes.forEach(node => adjacency.set(node.id, new Set()));

  // Add edges
  edges.forEach(edge => {
    const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
    const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;

    adjacency.get(sourceId)?.add(targetId);
    adjacency.get(targetId)?.add(sourceId);
  });

  return adjacency;
}

/**
 * Calculate cluster density (how interconnected nodes are within cluster)
 */
function calculateClusterDensity(
  clusterNodeIds: Set<string>,
  edges: GraphEdge[]
): number {
  const internalEdges = edges.filter(edge => {
    const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
    const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
    return clusterNodeIds.has(sourceId) && clusterNodeIds.has(targetId);
  });

  const nodeCount = clusterNodeIds.size;
  const maxPossibleEdges = (nodeCount * (nodeCount - 1)) / 2;

  return maxPossibleEdges > 0 ? internalEdges.length / maxPossibleEdges : 0;
}

/**
 * Calculate average synergy score for edges connected to a node
 */
function calculateAvgSynergy(
  nodeId: string,
  edges: GraphEdge[]
): number {
  const connectedEdges = edges.filter(edge => {
    const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
    const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;
    return sourceId === nodeId || targetId === nodeId;
  });

  if (connectedEdges.length === 0) return 0;

  const totalSynergy = connectedEdges.reduce((sum, edge) => sum + (edge.synergy_score || 0), 0);
  return totalSynergy / connectedEdges.length;
}

/**
 * Score a potential cluster center node
 */
function scoreClusterCenter(
  node: GraphNode,
  neighbors: GraphNode[],
  adjacency: Map<string, Set<string>>,
  edges: GraphEdge[]
): number {
  const neighborIds = new Set(neighbors.map(n => n.id));
  neighborIds.add(node.id);

  // Component 1: Connection count (0.25 weight)
  // More connections = more central
  const connectionCount = adjacency.get(node.id)?.size || 0;
  const connectionScore = Math.min(connectionCount / 15, 1) * 0.25;

  // Component 2: Innovation potential (0.30 weight)
  // High innovation nodes are more interesting
  const innovationScore = (node.innovation_potential || 0) * 0.30;

  // Component 3: Interdisciplinary score (0.25 weight)
  // Cross-disciplinary clusters are valuable
  const interdisciplinaryScore = (node.interdisciplinary_score || 0) * 0.25;

  // Component 4: Cluster density (0.20 weight)
  // Denser clusters are more cohesive
  const density = calculateClusterDensity(neighborIds, edges);
  const densityScore = density * 0.20;

  // Bonus: Cross-department diversity (+0.10 max)
  const uniqueDepartments = new Set(neighbors.map(n => n.department));
  const diversityBonus = Math.min(uniqueDepartments.size / 5, 1) * 0.10;

  return connectionScore + innovationScore + interdisciplinaryScore + densityScore + diversityBonus;
}

/**
 * Calculate centroid of a group of positioned nodes
 */
function calculateCentroid(nodes: GraphNode[]): { x: number; y: number } {
  const positionedNodes = nodes.filter(n => n.x !== undefined && n.y !== undefined);

  if (positionedNodes.length === 0) {
    return { x: 0, y: 0 };
  }

  const sumX = positionedNodes.reduce((sum, n) => sum + (n.x || 0), 0);
  const sumY = positionedNodes.reduce((sum, n) => sum + (n.y || 0), 0);

  return {
    x: sumX / positionedNodes.length,
    y: sumY / positionedNodes.length
  };
}

/**
 * Find the most interesting research cluster in the network
 */
export function findMostInterestingCluster(
  nodes: GraphNode[],
  edges: GraphEdge[],
  maxClusterSize: number = 30
): ClusterInfo | null {
  if (nodes.length === 0) return null;

  const adjacency = buildAdjacencyMap(nodes, edges);
  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  let bestCluster: ClusterInfo | null = null;
  let bestScore = -1;

  // Score each node as a potential cluster center
  for (const node of nodes) {
    const neighborIds = adjacency.get(node.id) || new Set();
    const neighbors = [...neighborIds]
      .map(id => nodeMap.get(id))
      .filter((n): n is GraphNode => n !== undefined);

    // Skip nodes with very few connections
    if (neighbors.length < 3) continue;

    // Limit cluster size for exploration view
    const clusterNeighbors = neighbors
      .sort((a, b) => (b.innovation_potential || 0) - (a.innovation_potential || 0))
      .slice(0, maxClusterSize - 1);

    const score = scoreClusterCenter(node, clusterNeighbors, adjacency, edges);

    if (score > bestScore) {
      bestScore = score;

      const clusterNodes = [node, ...clusterNeighbors];
      const uniqueDepts = new Set(clusterNodes.map(n => n.department));

      bestCluster = {
        centerId: node.id,
        centerNode: node,
        clusterNodes,
        centroid: calculateCentroid(clusterNodes),
        score,
        stats: {
          connectionCount: neighborIds.size,
          avgInnovation: clusterNodes.reduce((sum, n) => sum + (n.innovation_potential || 0), 0) / clusterNodes.length,
          departmentCount: uniqueDepts.size,
          avgSynergy: calculateAvgSynergy(node.id, edges)
        }
      };
    }
  }

  return bestCluster;
}

/**
 * Calculate optimal zoom transform to fit cluster in viewport
 */
export function calculateOptimalZoom(
  clusterNodes: GraphNode[],
  viewportWidth: number,
  viewportHeight: number,
  padding: number = 120
): { scale: number; translateX: number; translateY: number } {
  const positionedNodes = clusterNodes.filter(n => n.x !== undefined && n.y !== undefined);

  if (positionedNodes.length === 0) {
    return { scale: 1, translateX: 0, translateY: 0 };
  }

  // Calculate bounding box
  const xs = positionedNodes.map(n => n.x!);
  const ys = positionedNodes.map(n => n.y!);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const clusterWidth = maxX - minX + padding * 2;
  const clusterHeight = maxY - minY + padding * 2;

  // Calculate scale to fit cluster
  const scaleX = viewportWidth / clusterWidth;
  const scaleY = viewportHeight / clusterHeight;
  const scale = Math.min(scaleX, scaleY, 2.5); // Cap at 2.5x for readability

  // Calculate center
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;

  // Translation to center the cluster
  const translateX = viewportWidth / 2 - centerX * scale;
  const translateY = viewportHeight / 2 - centerY * scale;

  return { scale, translateX, translateY };
}

/**
 * Get bounding box of cluster nodes
 */
export function getClusterBounds(clusterNodes: GraphNode[]): {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  width: number;
  height: number;
} {
  const positionedNodes = clusterNodes.filter(n => n.x !== undefined && n.y !== undefined);

  if (positionedNodes.length === 0) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0, width: 0, height: 0 };
  }

  const xs = positionedNodes.map(n => n.x!);
  const ys = positionedNodes.map(n => n.y!);

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  return {
    minX,
    maxX,
    minY,
    maxY,
    width: maxX - minX,
    height: maxY - minY
  };
}
