/**
 * Iris Geometry Utilities
 * Calculates positions for nodes to form an organic eye iris pattern
 */

import { GraphNode } from './types';

export interface IrisConfig {
  centerX: number;
  centerY: number;
  pupilRadius: number;    // Empty center (~50px)
  innerRadius: number;    // First ring of nodes (~100px)
  outerRadius: number;    // Outer edge (~300px or viewport-based)
  ringCount: number;      // Number of concentric rings (6)
}



export interface IrisPosition {
  x: number;
  y: number;
  ring: number;
  angle: number;
}

// Seeded random for consistent positioning across renders
function seededRandom(seed: number): () => number {
  return function () {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
}

// Simple 1D noise function for organic variation
function noise1D(x: number, seed: number): number {
  const random = seededRandom(Math.floor(x * 1000) + seed);
  return random() * 2 - 1; // -1 to 1
}

/**
 * Calculate the "value score" of a node for ring placement
 * Higher value = closer to center
 */
function calculateNodeValue(node: GraphNode): number {
  const hIndexScore = Math.min((node.h_index || 0) / 50, 1);
  const innovationScore = node.innovation_potential || 0;
  const collaborationScore = node.collaboration_score || 0;
  const interdisciplinaryScore = node.interdisciplinary_score || 0;

  // Weighted combination
  return (
    hIndexScore * 0.3 +
    innovationScore * 0.35 +
    collaborationScore * 0.2 +
    interdisciplinaryScore * 0.15
  );
}

/**
 * Calculate iris positions for all nodes with organic scatter
 */
export function calculateIrisPositions(
  nodes: GraphNode[],
  config: IrisConfig
): Map<string, IrisPosition> {
  const positions = new Map<string, IrisPosition>();

  // Sort nodes by value score (highest first - they go toward center)
  const sortedNodes = [...nodes].sort((a, b) =>
    calculateNodeValue(b) - calculateNodeValue(a)
  );

  const ringSpacing = (config.outerRadius - config.innerRadius) / config.ringCount;
  const nodesPerRing: number[] = [];

  // Calculate how many nodes per ring (more in outer rings)
  // Inner rings are denser per unit area, but smaller circumference
  let totalSlots = 0;
  for (let ring = 0; ring < config.ringCount; ring++) {
    const ringRadius = config.innerRadius + ring * ringSpacing;
    const circumference = 2 * Math.PI * ringRadius;
    // Nodes spaced ~20-25px apart on average
    const slots = Math.floor(circumference / 22);
    nodesPerRing.push(slots);
    totalSlots += slots;
  }

  // Distribute nodes across rings based on value
  // High-value nodes get inner rings
  let nodeIndex = 0;
  const nodesByRing: GraphNode[][] = Array(config.ringCount).fill(null).map(() => []);

  // Scale slots if we have more or fewer nodes than total slots
  const scaleFactor = nodes.length / totalSlots;

  for (let ring = 0; ring < config.ringCount; ring++) {
    const scaledSlots = Math.ceil(nodesPerRing[ring] * scaleFactor);
    for (let i = 0; i < scaledSlots && nodeIndex < sortedNodes.length; i++) {
      nodesByRing[ring].push(sortedNodes[nodeIndex]);
      nodeIndex++;
    }
  }

  // Now position nodes within each ring with organic scatter
  for (let ring = 0; ring < config.ringCount; ring++) {
    const ringNodes = nodesByRing[ring];
    const baseRadius = config.innerRadius + ring * ringSpacing + ringSpacing / 2;

    ringNodes.forEach((node, i) => {
      // Base angle evenly distributed
      const baseAngle = (i / ringNodes.length) * 2 * Math.PI;

      // Create seed from node id for consistent randomness
      const nodeSeed = node.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const random = seededRandom(nodeSeed);

      // Organic angle jitter (up to 15% of slot spacing)
      const slotAngle = (2 * Math.PI) / ringNodes.length;
      const angleJitter = (random() - 0.5) * slotAngle * 0.4;

      // Organic radius jitter (within ring bounds)
      const radiusJitter = (random() - 0.5) * ringSpacing * 0.6;

      // Add noise-based variation for more organic feel
      const noiseAngle = noise1D(baseAngle * 3, nodeSeed) * 0.08;
      const noiseRadius = noise1D(ring + nodeSeed / 1000, nodeSeed + 1) * ringSpacing * 0.2;

      const finalAngle = baseAngle + angleJitter + noiseAngle;
      const finalRadius = Math.max(
        config.pupilRadius + 10, // Don't go into pupil
        Math.min(
          config.outerRadius - 10, // Don't go past outer edge
          baseRadius + radiusJitter + noiseRadius
        )
      );

      positions.set(node.id, {
        x: config.centerX + finalRadius * Math.cos(finalAngle),
        y: config.centerY + finalRadius * Math.sin(finalAngle),
        ring,
        angle: finalAngle
      });
    });
  }

  return positions;
}

/**
 * Create default iris config based on viewport dimensions
 */
export function createIrisConfig(
  width: number,
  height: number,
  nodeCount: number
): IrisConfig {
  const centerX = width / 2;
  const centerY = height / 2;
  const maxDimension = Math.min(width, height);

  // Scale iris size based on node count and viewport
  const baseRadius = maxDimension * 0.4; // 80% of viewport min dimension

  // Adjust for node density
  const densityFactor = Math.min(1.2, Math.max(0.8, nodeCount / 800));

  return {
    centerX,
    centerY,
    pupilRadius: baseRadius * 0.12, // 12% - empty pupil
    innerRadius: baseRadius * 0.18, // 18% - first ring starts
    outerRadius: baseRadius * densityFactor, // Full iris radius
    ringCount: 6
  };
}

/**
 * Generate striation line data for iris visual effect
 */
export function generateIrisStriations(
  config: IrisConfig,
  count: number = 48
): Array<{ x1: number; y1: number; x2: number; y2: number }> {
  const striations: Array<{ x1: number; y1: number; x2: number; y2: number }> = [];

  for (let i = 0; i < count; i++) {
    const angle = (i / count) * 2 * Math.PI;
    // Add slight angle variation for organic look
    const angleVar = (Math.random() - 0.5) * 0.05;
    const finalAngle = angle + angleVar;

    striations.push({
      x1: config.centerX + config.pupilRadius * Math.cos(finalAngle),
      y1: config.centerY + config.pupilRadius * Math.sin(finalAngle),
      x2: config.centerX + config.outerRadius * Math.cos(finalAngle),
      y2: config.centerY + config.outerRadius * Math.sin(finalAngle)
    });
  }

  return striations;
}
