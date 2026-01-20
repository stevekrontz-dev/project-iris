import * as d3 from 'd3';

export interface GraphNode extends d3.SimulationNodeDatum {
    id: string;
    name: string;
    department: string;

    // Optional basics
    title?: string;
    college?: string;

    // Metrics
    h_index: number;
    citations: number;
    publication_count: number;
    citation_count?: number; // Alias or alternative

    // Analysis
    interests: string[];
    innovation_potential: number;
    collaboration_score: number;
    interdisciplinary_score: number;

    // D3 & Geometry
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;

    // Misc
    publications?: { title: string; year?: number }[];
    [key: string]: unknown;
}

export interface SharedPublication {
    title: string;
    year?: number;
    doi?: string;
    url?: string;
}

export interface GraphEdge {
    source: string | GraphNode;
    target: string | GraphNode;
    weight: number;
    shared_publications: SharedPublication[];
    connection_type: string;
    synergy_score: number;
    [key: string]: unknown;
}

export interface ClusterInfo {
    centerId: string;
    centerNode: GraphNode;
    clusterNodes: GraphNode[];
    centroid: { x: number; y: number };
    score: number;
    stats: {
        connectionCount: number;
        avgInnovation: number;
        departmentCount: number;
        avgSynergy: number;
    };
}
