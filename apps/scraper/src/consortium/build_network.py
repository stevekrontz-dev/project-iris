"""
COLLABORATION NETWORK BUILDER
=============================
Fetches co-authorship data from OpenAlex and builds network graph
"""
import json
import asyncio
import aiohttp
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# Ensure deps
try:
    import networkx as nx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'networkx', '--break-system-packages', '-q'])
    import networkx as nx

INPUT_FILE = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\consortium\southeast_r1r2_20260114_041911.json')
OUTPUT_DIR = Path(r'C:\dev\research\project-iris\apps\scraper\src\consortium\data\consortium\network')

OPENALEX_API = 'https://api.openalex.org'

# Focus on researchers for manageable graph
MIN_H_INDEX = 10  # Lowered to include more researchers
MAX_RESEARCHERS = 5000  # Increased limit


async def fetch_coauthors(session, openalex_id: str) -> list:
    """Fetch top coauthors for a researcher from OpenAlex"""
    author_id = openalex_id.split('/')[-1]
    url = f'{OPENALEX_API}/authors/{author_id}'
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            
            # Get top coauthors from x_concepts or affiliations
            coauthors = []
            
            # Try to get from works endpoint instead
            works_url = f'{OPENALEX_API}/works?filter=author.id:{author_id}&per_page=50&select=authorships'
            async with session.get(works_url, timeout=aiohttp.ClientTimeout(total=15)) as works_resp:
                if works_resp.status == 200:
                    works_data = await works_resp.json()
                    
                    # Extract unique coauthors from works
                    coauthor_ids = set()
                    for work in works_data.get('results', []):
                        for authorship in work.get('authorships', []):
                            author = authorship.get('author', {})
                            aid = author.get('id', '')
                            if aid and aid != openalex_id:
                                coauthor_ids.add(aid)
                    
                    return list(coauthor_ids)[:20]  # Top 20 coauthors
            
            return coauthors
    except Exception as e:
        return []


async def build_network(researchers: list) -> nx.Graph:
    """Build collaboration network from researcher list"""
    G = nx.Graph()
    
    # Add nodes
    researcher_map = {}
    for r in researchers:
        oid = r.get('openalex_id', '')
        if oid:
            G.add_node(oid, 
                      name=r.get('name', ''),
                      institution=r.get('institution', ''),
                      h_index=r.get('h_index', 0),
                      citations=r.get('citations', 0),
                      field=r.get('field', ''))
            researcher_map[oid] = r
    
    print(f'Added {len(G.nodes)} nodes')
    
    # Our institution set
    our_institutions = set(r.get('openalex_id') for r in researchers if r.get('openalex_id'))
    
    # Fetch coauthorships
    print('Fetching coauthorship data...')
    edges = defaultdict(int)
    
    async with aiohttp.ClientSession() as session:
        batch_size = 50
        for i in range(0, len(researchers), batch_size):
            batch = researchers[i:i+batch_size]
            
            tasks = [fetch_coauthors(session, r['openalex_id']) for r in batch if r.get('openalex_id')]
            results = await asyncio.gather(*tasks)
            
            for r, coauthors in zip(batch, results):
                src = r.get('openalex_id', '')
                for coauthor_id in coauthors:
                    if coauthor_id in our_institutions and coauthor_id != src:
                        # Create sorted edge key for undirected graph
                        edge = tuple(sorted([src, coauthor_id]))
                        edges[edge] += 1
            
            batch_num = i // batch_size + 1
            total_batches = (len(researchers) + batch_size - 1) // batch_size
            if batch_num % 10 == 0 or batch_num == total_batches:
                print(f'  Batch {batch_num}/{total_batches}: {len(edges)} edges found')
            
            await asyncio.sleep(0.1)
    
    # Add edges with weights
    for (src, tgt), weight in edges.items():
        if src in G.nodes and tgt in G.nodes:
            G.add_edge(src, tgt, weight=weight)
    
    print(f'Added {len(G.edges)} edges')
    
    return G


def export_network(G: nx.Graph, output_dir: Path):
    """Export network in multiple formats"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # GraphML for Gephi/analysis tools
    graphml_path = output_dir / 'collaboration_network.graphml'
    nx.write_graphml(G, str(graphml_path))
    print(f'Saved GraphML: {graphml_path}')
    
    # JSON for web visualization
    nodes = []
    for node, attrs in G.nodes(data=True):
        nodes.append({
            'id': node,
            'name': attrs.get('name', ''),
            'institution': attrs.get('institution', ''),
            'h_index': attrs.get('h_index', 0),
            'citations': attrs.get('citations', 0),
            'field': attrs.get('field', ''),
            'degree': G.degree(node)
        })
    
    edges = []
    for src, tgt, attrs in G.edges(data=True):
        edges.append({
            'source': src,
            'target': tgt,
            'weight': attrs.get('weight', 1)
        })
    
    json_data = {
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'avg_degree': sum(G.degree(n) for n in G.nodes) / len(G.nodes) if G.nodes else 0,
            'density': nx.density(G),
            'components': nx.number_connected_components(G)
        }
    }
    
    json_path = output_dir / 'collaboration_network.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f'Saved JSON: {json_path}')
    
    # Top collaborators report
    degree_sorted = sorted(G.degree(), key=lambda x: -x[1])[:50]
    
    print('\nTOP 50 COLLABORATORS (by degree):')
    for i, (node, degree) in enumerate(degree_sorted, 1):
        attrs = G.nodes[node]
        print(f'{i:2}. {attrs["name"][:35]:<35} | h={attrs["h_index"]:>3} | deg={degree:>3} | {attrs["institution"][:20]}')
    
    return json_data


async def main():
    print('=' * 70)
    print('COLLABORATION NETWORK BUILDER')
    print('=' * 70)
    print(f'Started: {datetime.now().isoformat()}')
    
    # Load researchers
    print('\nLoading researchers...')
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_researchers = data.get('researchers', [])
    print(f'Total: {len(all_researchers):,} researchers')
    
    # Filter to high-impact
    high_impact = [r for r in all_researchers if r.get('h_index', 0) >= MIN_H_INDEX and r.get('openalex_id')]
    high_impact.sort(key=lambda x: -x.get('h_index', 0))
    high_impact = high_impact[:MAX_RESEARCHERS]
    
    print(f'High-impact (h>={MIN_H_INDEX}): {len(high_impact)} researchers')
    
    # Build network
    G = await build_network(high_impact)
    
    # Export
    print('\nExporting network...')
    stats = export_network(G, OUTPUT_DIR)
    
    print('\n' + '=' * 70)
    print('NETWORK BUILD COMPLETE')
    print('=' * 70)
    print(f'Nodes: {stats["stats"]["total_nodes"]}')
    print(f'Edges: {stats["stats"]["total_edges"]}')
    print(f'Components: {stats["stats"]["components"]}')
    print(f'Density: {stats["stats"]["density"]:.4f}')


if __name__ == '__main__':
    asyncio.run(main())
