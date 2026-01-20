'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import {
  calculateIrisPositions,
  createIrisConfig,
  type IrisPosition
} from '@/lib/irisGeometry';
import {
  findMostInterestingCluster,
  calculateOptimalZoom
} from '@/lib/clusterAnalysis';
import type { GraphNode, GraphEdge, ClusterInfo } from '@/lib/types';



type AnimationPhase = 'forming' | 'pausing' | 'zooming' | 'complete';

interface IrisLoadingAnimationProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onComplete: (cluster: ClusterInfo | null, positions: Map<string, { x: number; y: number }>) => void;
  getDepartmentColor: (dept: string) => string;
}

// Cinematic timing - slow and smooth like 3D render
const TIMING = {
  FORMATION: 5000,
  PAUSE: 2500,
  ZOOM: 3500,
  PUPIL_DILATE: 1500,
  STAGGER_DELAY: 2,
};

// Photorealistic iris color palette (based on reference images)
const IRIS_PALETTE = {
  // Base colors
  pupil: '#000000',
  limbalRing: '#1a1a1a',

  // Fiber colors - blue/green/gold tones from reference
  fiberDark: '#1e3a4c',
  fiberMid: '#2d5a6b',
  fiberLight: '#4a8fa8',
  fiberGold: '#8b7355',
  fiberAmber: '#a67c52',
  fiberTeal: '#3d7a7a',

  // Accent colors
  cryptDark: '#0a1520',
  highlight: '#7ec8e3',
  collarette: '#5a4a3a',
};

// Generate a random fiber color from the palette
function getRandomFiberColor(): string {
  const colors = [
    IRIS_PALETTE.fiberDark,
    IRIS_PALETTE.fiberMid,
    IRIS_PALETTE.fiberLight,
    IRIS_PALETTE.fiberGold,
    IRIS_PALETTE.fiberAmber,
    IRIS_PALETTE.fiberTeal,
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

// Blend node color with iris tones
function blendWithIris(hexColor: string): string {
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);

  // Blend with teal/blue iris tone
  const irisR = 45, irisG = 100, irisB = 120;
  const blend = 0.6;

  const newR = Math.round(r * (1 - blend) + irisR * blend);
  const newG = Math.round(g * (1 - blend) + irisG * blend);
  const newB = Math.round(b * (1 - blend) + irisB * blend);

  return `rgb(${newR}, ${newG}, ${newB})`;
}

export default function IrisLoadingAnimation({
  nodes,
  edges,
  onComplete,
  getDepartmentColor
}: IrisLoadingAnimationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState<AnimationPhase>('forming');
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [progress, setProgress] = useState(0);
  const animationRef = useRef<{ cancelled: boolean }>({ cancelled: false });
  const irisPositionsRef = useRef<Map<string, IrisPosition>>(new Map());
  const clusterRef = useRef<ClusterInfo | null>(null);

  const prefersReducedMotion = typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  const skipAnimation = useCallback(() => {
    animationRef.current.cancelled = true;
    const finalPositions = new Map<string, { x: number; y: number }>();
    irisPositionsRef.current.forEach((pos, id) => {
      finalPositions.set(id, { x: pos.x, y: pos.y });
    });
    onComplete(clusterRef.current, finalPositions);
  }, [onComplete]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter' || e.key === 'Escape') {
        e.preventDefault();
        skipAnimation();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [skipAnimation]);

  useEffect(() => {
    if (!containerRef.current) return;
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (prefersReducedMotion && dimensions.width > 0) {
      skipAnimation();
    }
  }, [prefersReducedMotion, dimensions, skipAnimation]);

  // Main animation
  useEffect(() => {
    if (!svgRef.current || !dimensions.width || !dimensions.height || nodes.length === 0) return;
    if (animationRef.current.cancelled) return;

    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);

    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const defs = svg.append('defs');

    // Complex radial gradient for iris base with more depth
    const irisGradient = defs.append('radialGradient')
      .attr('id', 'iris-gradient')
      .attr('cx', '50%')
      .attr('cy', '50%')
      .attr('r', '50%');

    irisGradient.append('stop').attr('offset', '0%').attr('stop-color', '#000');
    irisGradient.append('stop').attr('offset', '10%').attr('stop-color', '#050a0d');
    irisGradient.append('stop').attr('offset', '18%').attr('stop-color', '#1a3040');
    irisGradient.append('stop').attr('offset', '30%').attr('stop-color', '#2a4858');
    irisGradient.append('stop').attr('offset', '45%').attr('stop-color', '#3a6878');
    irisGradient.append('stop').attr('offset', '60%').attr('stop-color', '#4a8898');
    irisGradient.append('stop').attr('offset', '75%').attr('stop-color', '#3a6878');
    irisGradient.append('stop').attr('offset', '88%').attr('stop-color', '#1a3040');
    irisGradient.append('stop').attr('offset', '100%').attr('stop-color', '#0a0a0a');

    // Gold/amber collarette ring gradient
    const goldGradient = defs.append('radialGradient')
      .attr('id', 'gold-ring')
      .attr('cx', '50%')
      .attr('cy', '50%')
      .attr('r', '50%');

    goldGradient.append('stop').attr('offset', '0%').attr('stop-color', '#b89060').attr('stop-opacity', '0.15');
    goldGradient.append('stop').attr('offset', '25%').attr('stop-color', '#a67c52').attr('stop-opacity', '0.25');
    goldGradient.append('stop').attr('offset', '45%').attr('stop-color', 'transparent');
    goldGradient.append('stop').attr('offset', '100%').attr('stop-color', 'transparent');

    // Catch light gradient (simulates light reflection)
    const catchLightGradient = defs.append('radialGradient')
      .attr('id', 'catch-light')
      .attr('cx', '30%')
      .attr('cy', '30%')
      .attr('r', '50%');

    catchLightGradient.append('stop').attr('offset', '0%').attr('stop-color', '#fff').attr('stop-opacity', '0.9');
    catchLightGradient.append('stop').attr('offset', '30%').attr('stop-color', '#fff').attr('stop-opacity', '0.4');
    catchLightGradient.append('stop').attr('offset', '100%').attr('stop-color', '#fff').attr('stop-opacity', '0');

    // Depth shadow for 3D effect
    const depthShadow = defs.append('radialGradient')
      .attr('id', 'depth-shadow')
      .attr('cx', '50%')
      .attr('cy', '50%')
      .attr('r', '50%');

    depthShadow.append('stop').attr('offset', '85%').attr('stop-color', 'transparent');
    depthShadow.append('stop').attr('offset', '95%').attr('stop-color', '#000').attr('stop-opacity', '0.3');
    depthShadow.append('stop').attr('offset', '100%').attr('stop-color', '#000').attr('stop-opacity', '0.6');

    // Subtle blur filter for soft edges
    const blurFilter = defs.append('filter')
      .attr('id', 'soft-blur')
      .attr('x', '-20%')
      .attr('y', '-20%')
      .attr('width', '140%')
      .attr('height', '140%');
    blurFilter.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', '2');

    const irisConfig = createIrisConfig(width, height, nodes.length);
    const irisPositions = calculateIrisPositions(nodes as GraphNode[], irisConfig);
    irisPositionsRef.current = irisPositions;

    const nodesWithPositions = nodes.map(node => {
      const pos = irisPositions.get(node.id);
      return { ...node, x: pos?.x || irisConfig.centerX, y: pos?.y || irisConfig.centerY };
    });

    const cluster = findMostInterestingCluster(nodesWithPositions, edges);
    clusterRef.current = cluster;

    const g = svg.append('g').attr('class', 'iris-container');
    const cx = irisConfig.centerX;
    const cy = irisConfig.centerY;
    const outerR = irisConfig.outerRadius;
    const pupilR = irisConfig.pupilRadius;

    // === PHOTOREALISTIC 3D IRIS STRUCTURE ===

    // 0. Outer shadow ring for depth (sclera shadow)
    g.append('circle')
      .attr('cx', cx).attr('cy', cy)
      .attr('r', outerR + 20)
      .attr('fill', 'url(#depth-shadow)')
      .attr('opacity', 0)
      .transition().duration(2500).ease(d3.easeCubicOut)
      .attr('opacity', 1);

    // 1. Dark outer limbal ring (thick, defined edge)
    g.append('circle')
      .attr('cx', cx).attr('cy', cy)
      .attr('r', outerR + 8)
      .attr('fill', 'none')
      .attr('stroke', '#0a0f12')
      .attr('stroke-width', 18)
      .attr('opacity', 0)
      .transition().duration(2500).ease(d3.easeCubicOut)
      .attr('opacity', 1);

    // 2. Main iris base with gradient (the colored disc)
    g.append('circle')
      .attr('cx', cx).attr('cy', cy)
      .attr('r', outerR)
      .attr('fill', 'url(#iris-gradient)')
      .attr('opacity', 0)
      .transition().duration(2500).ease(d3.easeCubicOut)
      .attr('opacity', 1);

    // 3. Gold/amber collarette ring (around pupil area)
    g.append('circle')
      .attr('cx', cx).attr('cy', cy)
      .attr('r', pupilR + 35)
      .attr('fill', 'url(#gold-ring)')
      .attr('opacity', 0)
      .transition().delay(800).duration(2000).ease(d3.easeCubicOut)
      .attr('opacity', 0.8);

    // 4. DETAILED RADIAL FIBERS (organic, flowing like real iris)
    const fiberGroup = g.append('g').attr('class', 'fibers');

    // Helper: create curved fiber path for organic look
    const createFiberPath = (startR: number, endR: number, angle: number, curve: number) => {
      const startX = cx + startR * Math.cos(angle);
      const startY = cy + startR * Math.sin(angle);
      const endX = cx + endR * Math.cos(angle + curve);
      const endY = cy + endR * Math.sin(angle + curve);
      const midR = (startR + endR) / 2;
      const controlAngle = angle + curve * 0.5 + (Math.random() - 0.5) * 0.03;
      const controlX = cx + midR * Math.cos(controlAngle);
      const controlY = cy + midR * Math.sin(controlAngle);
      return `M${startX},${startY} Q${controlX},${controlY} ${endX},${endY}`;
    };

    // Layer 1: Primary fibers - thick structural strands
    for (let i = 0; i < 180; i++) {
      const angle = (i / 180) * Math.PI * 2 + (Math.random() - 0.5) * 0.025;
      const innerR = pupilR + 8 + Math.random() * 6;
      const outerEnd = outerR * (0.78 + Math.random() * 0.2);
      const curve = (Math.random() - 0.5) * 0.04;
      const width = 2 + Math.random() * 2.5;

      fiberGroup.append('path')
        .attr('d', createFiberPath(innerR, outerEnd, angle, curve))
        .attr('fill', 'none')
        .attr('stroke', getRandomFiberColor())
        .attr('stroke-width', width)
        .attr('stroke-opacity', 0)
        .attr('stroke-linecap', 'round')
        .transition()
        .delay(i * 5)
        .duration(TIMING.FORMATION * 0.6)
        .ease(d3.easeCubicOut)
        .attr('stroke-opacity', 0.65 + Math.random() * 0.25);
    }

    // Layer 2: Secondary fibers - medium thickness
    for (let i = 0; i < 140; i++) {
      const angle = (i / 140) * Math.PI * 2 + (Math.random() - 0.5) * 0.05;
      const innerR = pupilR + 15 + Math.random() * 10;
      const outerEnd = outerR * (0.55 + Math.random() * 0.35);
      const curve = (Math.random() - 0.5) * 0.05;

      fiberGroup.append('path')
        .attr('d', createFiberPath(innerR, outerEnd, angle, curve))
        .attr('fill', 'none')
        .attr('stroke', getRandomFiberColor())
        .attr('stroke-width', 1.2 + Math.random() * 1.5)
        .attr('stroke-opacity', 0)
        .attr('stroke-linecap', 'round')
        .transition()
        .delay(150 + i * 4)
        .duration(TIMING.FORMATION * 0.5)
        .ease(d3.easeCubicOut)
        .attr('stroke-opacity', 0.5 + Math.random() * 0.35);
    }

    // Layer 3: Inner fibers near pupil (bright collarette area)
    for (let i = 0; i < 100; i++) {
      const angle = (i / 100) * Math.PI * 2 + (Math.random() - 0.5) * 0.06;
      const innerR = pupilR + 5;
      const outerEnd = pupilR + 30 + Math.random() * 45;
      const curve = (Math.random() - 0.5) * 0.03;

      fiberGroup.append('path')
        .attr('d', createFiberPath(innerR, outerEnd, angle, curve))
        .attr('fill', 'none')
        .attr('stroke', IRIS_PALETTE.fiberLight)
        .attr('stroke-width', 1 + Math.random() * 1.2)
        .attr('stroke-opacity', 0)
        .attr('stroke-linecap', 'round')
        .transition()
        .delay(300 + i * 3)
        .duration(TIMING.FORMATION * 0.45)
        .ease(d3.easeCubicOut)
        .attr('stroke-opacity', 0.45 + Math.random() * 0.35);
    }

    // Layer 4: Highlight streaks (catching light)
    for (let i = 0; i < 50; i++) {
      const angle = (i / 50) * Math.PI * 2 + (Math.random() - 0.5) * 0.1;
      const innerR = pupilR + 18 + Math.random() * 15;
      const outerEnd = outerR * (0.68 + Math.random() * 0.28);
      const curve = (Math.random() - 0.5) * 0.04;

      fiberGroup.append('path')
        .attr('d', createFiberPath(innerR, outerEnd, angle, curve))
        .attr('fill', 'none')
        .attr('stroke', IRIS_PALETTE.highlight)
        .attr('stroke-width', 1 + Math.random() * 1.5)
        .attr('stroke-opacity', 0)
        .attr('stroke-linecap', 'round')
        .transition()
        .delay(600 + i * 8)
        .duration(TIMING.FORMATION * 0.5)
        .ease(d3.easeCubicOut)
        .attr('stroke-opacity', 0.35 + Math.random() * 0.3);
    }

    // Layer 5: Fine detail fibers (very subtle)
    for (let i = 0; i < 80; i++) {
      const angle = (i / 80) * Math.PI * 2 + (Math.random() - 0.5) * 0.08;
      const innerR = pupilR + 10 + Math.random() * 30;
      const outerEnd = innerR + 40 + Math.random() * 60;
      const curve = (Math.random() - 0.5) * 0.06;

      fiberGroup.append('path')
        .attr('d', createFiberPath(innerR, Math.min(outerEnd, outerR * 0.95), angle, curve))
        .attr('fill', 'none')
        .attr('stroke', '#6ab0c8')
        .attr('stroke-width', 0.6 + Math.random() * 0.8)
        .attr('stroke-opacity', 0)
        .attr('stroke-linecap', 'round')
        .transition()
        .delay(800 + i * 6)
        .duration(TIMING.FORMATION * 0.4)
        .ease(d3.easeCubicOut)
        .attr('stroke-opacity', 0.3 + Math.random() * 0.25);
    }

    // 5. Crypts (dark spots/holes in iris texture)
    const cryptGroup = g.append('g').attr('class', 'crypts');
    for (let i = 0; i < 35; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = pupilR + 30 + Math.random() * (outerR - pupilR - 50);
      const size = 2 + Math.random() * 4;

      cryptGroup.append('ellipse')
        .attr('cx', cx + dist * Math.cos(angle))
        .attr('cy', cy + dist * Math.sin(angle))
        .attr('rx', size)
        .attr('ry', size * (0.6 + Math.random() * 0.4))
        .attr('fill', IRIS_PALETTE.cryptDark)
        .attr('opacity', 0)
        .attr('transform', `rotate(${Math.random() * 360}, ${cx + dist * Math.cos(angle)}, ${cy + dist * Math.sin(angle)})`)
        .transition()
        .delay(1500 + i * 30)
        .duration(1500)
        .ease(d3.easeQuadOut)
        .attr('opacity', 0.4 + Math.random() * 0.3);
    }

    // 6. Collarette ring (textured ring around pupil)
    const collaretteGroup = g.append('g').attr('class', 'collarette');
    for (let i = 0; i < 72; i++) {
      const angle = (i / 72) * Math.PI * 2;
      const variation = Math.random() * 4;
      collaretteGroup.append('circle')
        .attr('cx', cx + (pupilR + 20 + variation) * Math.cos(angle))
        .attr('cy', cy + (pupilR + 20 + variation) * Math.sin(angle))
        .attr('r', 1.5 + Math.random() * 1.5)
        .attr('fill', IRIS_PALETTE.collarette)
        .attr('opacity', 0)
        .transition()
        .delay(600 + i * 8)
        .duration(1500)
        .ease(d3.easeCubicOut)
        .attr('opacity', 0.35 + Math.random() * 0.25);
    }

    // 7. Pupil (solid black) - starts larger, contracts for "focusing" effect
    const pupilElement = g.append('circle')
      .attr('cx', cx).attr('cy', cy)
      .attr('r', pupilR * 1.3) // Start 30% larger
      .attr('fill', IRIS_PALETTE.pupil)
      .attr('opacity', 0);

    pupilElement
      .transition().duration(1800).ease(d3.easeCubicOut)
      .attr('opacity', 1)
      .attr('r', pupilR); // Contract to normal size

    // 8. Pupil edge softness (gradient ring for realism)
    g.append('circle')
      .attr('cx', cx).attr('cy', cy)
      .attr('r', pupilR + 3)
      .attr('fill', 'none')
      .attr('stroke', '#000')
      .attr('stroke-width', 6)
      .attr('filter', 'url(#soft-blur)')
      .attr('opacity', 0)
      .transition().delay(500).duration(1500)
      .attr('opacity', 0.5);

    // 9. Primary catch light (main light reflection)
    const catchLightGroup = g.append('g').attr('class', 'catch-lights');

    catchLightGroup.append('ellipse')
      .attr('cx', cx - pupilR * 0.5)
      .attr('cy', cy - pupilR * 0.5)
      .attr('rx', pupilR * 0.35)
      .attr('ry', pupilR * 0.25)
      .attr('fill', 'url(#catch-light)')
      .attr('transform', `rotate(-30, ${cx - pupilR * 0.5}, ${cy - pupilR * 0.5})`)
      .attr('opacity', 0)
      .transition().delay(2200).duration(1200).ease(d3.easeCubicOut)
      .attr('opacity', 0.7);

    // 10. Secondary catch light (smaller, opposite side)
    catchLightGroup.append('ellipse')
      .attr('cx', cx + pupilR * 0.35)
      .attr('cy', cy + pupilR * 0.4)
      .attr('rx', pupilR * 0.12)
      .attr('ry', pupilR * 0.08)
      .attr('fill', '#fff')
      .attr('opacity', 0)
      .transition().delay(2400).duration(1000).ease(d3.easeCubicOut)
      .attr('opacity', 0.25);

    // 11. Subtle specular highlight on iris (wet eye effect)
    g.append('ellipse')
      .attr('cx', cx - outerR * 0.2)
      .attr('cy', cy - outerR * 0.25)
      .attr('rx', outerR * 0.15)
      .attr('ry', outerR * 0.08)
      .attr('fill', '#fff')
      .attr('filter', 'url(#soft-blur)')
      .attr('opacity', 0)
      .transition().delay(2600).duration(1500)
      .attr('opacity', 0.08);

    // 12. Research nodes as subtle points in iris texture
    const nodeGroup = g.append('g').attr('class', 'nodes');

    const nodeElements = nodeGroup.selectAll('g.node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', `translate(${cx}, ${cy})`)
      .attr('opacity', 0);

    // Nodes as subtle luminous points within the iris
    nodeElements.append('circle')
      .attr('r', d => 2.5 + Math.sqrt(d.h_index || 1) * 0.6)
      .attr('fill', d => blendWithIris(getDepartmentColor(d.department)))
      .attr('filter', 'url(#soft-blur)');

    // Bright core point
    nodeElements.append('circle')
      .attr('r', d => 1.5 + Math.sqrt(d.h_index || 1) * 0.35)
      .attr('fill', d => getDepartmentColor(d.department));

    // Extra glow for high-potential nodes
    nodeElements.filter(d => d.innovation_potential > 0.7)
      .append('circle')
      .attr('r', d => 1 + Math.sqrt(d.h_index || 1) * 0.25)
      .attr('fill', IRIS_PALETTE.highlight)
      .attr('opacity', 0.6);

    // === PHASE 1: Formation ===
    setPhase('forming');

    nodeElements.each(function (d, i) {
      const pos = irisPositions.get(d.id);
      if (!pos || animationRef.current.cancelled) return;

      d3.select(this)
        .transition()
        .delay(2000 + i * TIMING.STAGGER_DELAY)
        .duration(TIMING.FORMATION)
        .ease(d3.easeQuadOut)
        .attr('transform', `translate(${pos.x}, ${pos.y})`)
        .attr('opacity', 0.7);
    });

    const formationInterval = setInterval(() => {
      if (animationRef.current.cancelled) { clearInterval(formationInterval); return; }
      setProgress(prev => Math.min(prev + 0.8, 40));
    }, TIMING.FORMATION / 50);

    // === PHASE 2: Pause ===
    const pauseTimeout = setTimeout(() => {
      if (animationRef.current.cancelled) return;
      clearInterval(formationInterval);
      setProgress(50);
      setPhase('pausing');
    }, 2000 + TIMING.FORMATION + nodes.length * TIMING.STAGGER_DELAY);

    // === PHASE 3: Zoom ===
    const zoomTimeout = setTimeout(() => {
      if (animationRef.current.cancelled) return;
      setPhase('zooming');
      setProgress(60);

      if (cluster) {
        cluster.clusterNodes.forEach(node => {
          const pos = irisPositions.get(node.id);
          if (pos) { node.x = pos.x; node.y = pos.y; }
        });

        const zoomTransform = calculateOptimalZoom(cluster.clusterNodes, width, height, 150);

        const zoom = d3.zoom<SVGSVGElement, unknown>()
          .scaleExtent([0.1, 4])
          .on('zoom', (event) => { g.attr('transform', event.transform); });

        svg.call(zoom);

        // Pupil dilates slightly as we zoom in (like focusing)
        pupilElement
          .transition()
          .duration(TIMING.PUPIL_DILATE)
          .ease(d3.easeCubicInOut)
          .attr('r', pupilR * 0.85);

        // Slow, smooth zoom with slight delay for pupil to start dilating
        svg.transition()
          .delay(300)
          .duration(TIMING.ZOOM)
          .ease(d3.easeCubicInOut)
          .call(zoom.transform, d3.zoomIdentity
            .translate(zoomTransform.translateX, zoomTransform.translateY)
            .scale(zoomTransform.scale));

        // Fade out iris structure smoothly
        const fadeDelay = 200;
        fiberGroup.transition().delay(fadeDelay).duration(TIMING.ZOOM * 0.8).attr('opacity', 0);
        cryptGroup.transition().delay(fadeDelay).duration(TIMING.ZOOM * 0.8).attr('opacity', 0);
        collaretteGroup.transition().delay(fadeDelay).duration(TIMING.ZOOM * 0.8).attr('opacity', 0);
        catchLightGroup.transition().delay(fadeDelay).duration(TIMING.ZOOM * 0.6).attr('opacity', 0);
        g.selectAll('circle:not(.node circle):not(.collarette circle)').transition().delay(fadeDelay).duration(TIMING.ZOOM * 0.8).attr('opacity', 0);
        g.selectAll('ellipse:not(.node ellipse)').transition().delay(fadeDelay).duration(TIMING.ZOOM * 0.7).attr('opacity', 0);
      }

      const zoomInterval = setInterval(() => {
        if (animationRef.current.cancelled) { clearInterval(zoomInterval); return; }
        setProgress(prev => Math.min(prev + 2, 95));
      }, TIMING.ZOOM / 20);

      setTimeout(() => clearInterval(zoomInterval), TIMING.ZOOM);
    }, 2000 + TIMING.FORMATION + nodes.length * TIMING.STAGGER_DELAY + TIMING.PAUSE);

    // === PHASE 4: Complete ===
    const completeTimeout = setTimeout(() => {
      if (animationRef.current.cancelled) return;
      setPhase('complete');
      setProgress(100);

      const finalPositions = new Map<string, { x: number; y: number }>();
      irisPositions.forEach((pos, id) => { finalPositions.set(id, { x: pos.x, y: pos.y }); });

      setTimeout(() => {
        if (!animationRef.current.cancelled) { onComplete(cluster, finalPositions); }
      }, 500);
    }, 2000 + TIMING.FORMATION + nodes.length * TIMING.STAGGER_DELAY + TIMING.PAUSE + TIMING.ZOOM);

    return () => {
      animationRef.current.cancelled = true;
      clearInterval(formationInterval);
      clearTimeout(pauseTimeout);
      clearTimeout(zoomTimeout);
      clearTimeout(completeTimeout);
    };
  }, [dimensions, nodes, edges, getDepartmentColor, onComplete]);

  const phaseLabels: Record<AnimationPhase, string> = {
    forming: 'PERCEIVING',
    pausing: 'RECOGNIZING',
    zooming: 'FOCUSING',
    complete: 'EXPLORING'
  };

  return (
    <div ref={containerRef} className="absolute inset-0 z-40 bg-[#030506]">
      <svg ref={svgRef} className="w-full h-full" />

      {/* Subtle vignette overlay for cinematic depth */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.4) 100%)'
        }}
      />

      <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-end pb-16">
        <div className="text-center mb-4">
          <h2 className="text-sm font-extralight tracking-[0.4em] text-white/25 uppercase">
            {phaseLabels[phase]}
          </h2>
        </div>

        <div className="w-24 h-[1px] bg-white/5 mb-6 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-transparent via-white/40 to-transparent transition-all duration-1000 ease-out"
            style={{ width: `${progress}%`, marginLeft: `${(100 - progress) / 2}%` }}
          />
        </div>

        <button
          onClick={skipAnimation}
          className="pointer-events-auto text-white/15 hover:text-white/30 text-[10px] tracking-widest uppercase transition-colors duration-500"
        >
          skip intro
        </button>
      </div>

      {phase === 'zooming' && clusterRef.current && (
        <div className="absolute top-8 left-8 bg-black/40 backdrop-blur-sm rounded-sm px-5 py-3 border border-white/5">
          <p className="text-[9px] text-white/20 uppercase tracking-[0.2em] mb-1.5">Focusing on</p>
          <h3 className="text-sm font-light text-white/70 tracking-wide">{clusterRef.current.centerNode.name}</h3>
          <p className="text-[10px] text-white/30 mt-1">{clusterRef.current.centerNode.department}</p>
        </div>
      )}
    </div>
  );
}
