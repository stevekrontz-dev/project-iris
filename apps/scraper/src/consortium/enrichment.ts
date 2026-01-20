/**
 * IRIS Consortium Scraper - OpenAlex Enrichment
 * 
 * Enrich scraped faculty data with OpenAlex publication metrics
 */

import { ScrapedPerson, OpenAlexAuthor, OpenAlexWork } from './types';

const OPENALEX_BASE = 'https://api.openalex.org';
const POLITE_EMAIL = 'research@kennesaw.edu';  // For OpenAlex polite pool

interface EnrichmentResult {
  person: ScrapedPerson;
  openAlexId?: string;
  metrics?: {
    worksCount: number;
    citedByCount: number;
    hIndex?: number;
  };
  topics?: string[];
  matchConfidence: 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
  error?: string;
}

export class OpenAlexEnricher {
  private rateLimitDelay = 100;  // ms between requests (polite pool allows 10/sec)
  
  /**
   * Enrich a single person with OpenAlex data
   */
  async enrichPerson(person: ScrapedPerson): Promise<EnrichmentResult> {
    try {
      // First, try to find the author
      const author = await this.findAuthor(person);
      
      if (!author) {
        return {
          person,
          matchConfidence: 'NONE',
        };
      }
      
      // Determine match confidence
      const confidence = this.assessMatchConfidence(person, author);
      
      // Extract topics
      const topics = author.topics
        ?.sort((a, b) => b.score - a.score)
        .slice(0, 10)
        .map(t => t.displayName) || [];
      
      return {
        person,
        openAlexId: author.id,
        metrics: {
          worksCount: author.worksCount,
          citedByCount: author.citedByCount,
          hIndex: author.hIndex,
        },
        topics,
        matchConfidence: confidence,
      };
      
    } catch (error) {
      return {
        person,
        matchConfidence: 'NONE',
        error: String(error),
      };
    }
  }
  
  /**
   * Find an author in OpenAlex
   */
  private async findAuthor(person: ScrapedPerson): Promise<OpenAlexAuthor | null> {
    // Strategy 1: Search by ORCID if available
    if (person.orcidId) {
      const byOrcid = await this.searchByOrcid(person.orcidId);
      if (byOrcid) return byOrcid;
    }
    
    // Strategy 2: Search by name + institution
    const byNameInst = await this.searchByNameAndInstitution(person);
    if (byNameInst) return byNameInst;
    
    // Strategy 3: Search by name only (less reliable)
    const byName = await this.searchByName(person.fullName);
    return byName;
  }
  
  /**
   * Search by ORCID
   */
  private async searchByOrcid(orcid: string): Promise<OpenAlexAuthor | null> {
    const cleanOrcid = orcid.replace('https://orcid.org/', '');
    const url = `${OPENALEX_BASE}/authors/orcid:${cleanOrcid}?mailto=${POLITE_EMAIL}`;
    
    try {
      const response = await fetch(url);
      if (!response.ok) return null;
      
      const data = await response.json();
      return this.mapToOpenAlexAuthor(data);
    } catch {
      return null;
    }
  }
  
  /**
   * Search by name and institution
   */
  private async searchByNameAndInstitution(person: ScrapedPerson): Promise<OpenAlexAuthor | null> {
    // Build search query
    const nameQuery = encodeURIComponent(person.fullName);
    
    // Map tenant to institution search
    const institutionFilters: Record<string, string> = {
      'ksu': 'I173911158',      // Kennesaw State University
      'emory': 'I136199984',    // Emory University
      'gatech': 'I64801317',    // Georgia Institute of Technology
      'gsu': 'I25215891',       // Georgia State University
    };
    
    const instFilter = institutionFilters[person.tenantSlug];
    let url = `${OPENALEX_BASE}/authors?search=${nameQuery}&mailto=${POLITE_EMAIL}`;
    
    if (instFilter) {
      url += `&filter=last_known_institutions.id:${instFilter}`;
    }
    
    await this.delay(this.rateLimitDelay);
    
    try {
      const response = await fetch(url);
      if (!response.ok) return null;
      
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        // Return best match
        return this.mapToOpenAlexAuthor(data.results[0]);
      }
      
      return null;
    } catch {
      return null;
    }
  }
  
  /**
   * Search by name only
   */
  private async searchByName(name: string): Promise<OpenAlexAuthor | null> {
    const nameQuery = encodeURIComponent(name);
    const url = `${OPENALEX_BASE}/authors?search=${nameQuery}&mailto=${POLITE_EMAIL}&per_page=1`;
    
    await this.delay(this.rateLimitDelay);
    
    try {
      const response = await fetch(url);
      if (!response.ok) return null;
      
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        return this.mapToOpenAlexAuthor(data.results[0]);
      }
      
      return null;
    } catch {
      return null;
    }
  }
  
  /**
   * Get recent works for an author
   */
  async getAuthorWorks(openAlexId: string, limit: number = 10): Promise<OpenAlexWork[]> {
    const shortId = openAlexId.replace('https://openalex.org/', '');
    const url = `${OPENALEX_BASE}/works?filter=author.id:${shortId}&sort=publication_date:desc&per_page=${limit}&mailto=${POLITE_EMAIL}`;
    
    await this.delay(this.rateLimitDelay);
    
    try {
      const response = await fetch(url);
      if (!response.ok) return [];
      
      const data = await response.json();
      
      return (data.results || []).map((work: any) => ({
        id: work.id,
        doi: work.doi,
        title: work.title,
        abstract: work.abstract_inverted_index ? this.reconstructAbstract(work.abstract_inverted_index) : undefined,
        publicationDate: work.publication_date,
        publicationYear: work.publication_year,
        type: work.type,
        citedByCount: work.cited_by_count || 0,
        venue: work.primary_location?.source ? {
          displayName: work.primary_location.source.display_name,
          publisher: work.primary_location.source.host_organization_name,
        } : undefined,
        authorships: (work.authorships || []).map((a: any) => ({
          authorPosition: a.author_position,
          author: {
            id: a.author.id,
            displayName: a.author.display_name,
          },
          isCorresponding: a.is_corresponding || false,
        })),
      }));
      
    } catch {
      return [];
    }
  }
  
  /**
   * Map OpenAlex API response to our type
   */
  private mapToOpenAlexAuthor(data: any): OpenAlexAuthor {
    return {
      id: data.id,
      displayName: data.display_name,
      orcid: data.orcid,
      worksCount: data.works_count || 0,
      citedByCount: data.cited_by_count || 0,
      hIndex: data.summary_stats?.h_index,
      lastKnownInstitution: data.last_known_institutions?.[0] ? {
        id: data.last_known_institutions[0].id,
        displayName: data.last_known_institutions[0].display_name,
        ror: data.last_known_institutions[0].ror,
      } : undefined,
      topics: (data.topics || []).map((t: any) => ({
        id: t.id,
        displayName: t.display_name,
        score: t.score || 0,
      })),
    };
  }
  
  /**
   * Reconstruct abstract from inverted index
   */
  private reconstructAbstract(invertedIndex: Record<string, number[]>): string {
    const words: [string, number][] = [];
    
    for (const [word, positions] of Object.entries(invertedIndex)) {
      for (const pos of positions) {
        words.push([word, pos]);
      }
    }
    
    words.sort((a, b) => a[1] - b[1]);
    return words.map(w => w[0]).join(' ');
  }
  
  /**
   * Assess confidence in the match
   */
  private assessMatchConfidence(
    person: ScrapedPerson, 
    author: OpenAlexAuthor
  ): 'HIGH' | 'MEDIUM' | 'LOW' {
    let score = 0;
    
    // Name similarity
    const personNameLower = person.fullName.toLowerCase();
    const authorNameLower = author.displayName.toLowerCase();
    
    if (personNameLower === authorNameLower) {
      score += 3;
    } else if (this.namesSimilar(personNameLower, authorNameLower)) {
      score += 2;
    } else {
      score += 1;
    }
    
    // Institution match
    if (author.lastKnownInstitution) {
      const instName = author.lastKnownInstitution.displayName.toLowerCase();
      const tenantInstitutions: Record<string, string[]> = {
        'ksu': ['kennesaw', 'ksu'],
        'emory': ['emory'],
        'gatech': ['georgia tech', 'georgia institute'],
        'gsu': ['georgia state'],
      };
      
      const matches = tenantInstitutions[person.tenantSlug] || [];
      if (matches.some(m => instName.includes(m))) {
        score += 3;
      }
    }
    
    // Has publications
    if (author.worksCount > 10) score += 1;
    if (author.worksCount > 50) score += 1;
    
    if (score >= 6) return 'HIGH';
    if (score >= 4) return 'MEDIUM';
    return 'LOW';
  }
  
  /**
   * Check if names are similar (handles middle initials, etc.)
   */
  private namesSimilar(name1: string, name2: string): boolean {
    // Remove common variations
    const normalize = (n: string) => n
      .replace(/[^a-z\s]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
    
    const n1 = normalize(name1);
    const n2 = normalize(name2);
    
    // Exact match
    if (n1 === n2) return true;
    
    // Check if one contains the other
    const parts1 = n1.split(' ');
    const parts2 = n2.split(' ');
    
    // At least first and last name match
    if (parts1.length >= 2 && parts2.length >= 2) {
      const firstMatch = parts1[0] === parts2[0];
      const lastMatch = parts1[parts1.length - 1] === parts2[parts2.length - 1];
      if (firstMatch && lastMatch) return true;
    }
    
    return false;
  }
  
  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Batch enrich multiple people
 */
export async function enrichConsortiumData(
  people: ScrapedPerson[],
  options: { verbose?: boolean; batchSize?: number } = {}
): Promise<EnrichmentResult[]> {
  const enricher = new OpenAlexEnricher();
  const results: EnrichmentResult[] = [];
  const batchSize = options.batchSize || 10;
  
  console.log(`\nEnriching ${people.length} people with OpenAlex data...`);
  
  for (let i = 0; i < people.length; i += batchSize) {
    const batch = people.slice(i, i + batchSize);
    
    const batchResults = await Promise.all(
      batch.map(person => enricher.enrichPerson(person))
    );
    
    results.push(...batchResults);
    
    const enriched = batchResults.filter(r => r.matchConfidence !== 'NONE').length;
    console.log(`  Batch ${Math.floor(i / batchSize) + 1}: ${enriched}/${batch.length} matched`);
    
    // Small delay between batches
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  const totalEnriched = results.filter(r => r.matchConfidence !== 'NONE').length;
  console.log(`\nEnrichment complete: ${totalEnriched}/${people.length} matched (${(totalEnriched / people.length * 100).toFixed(1)}%)`);
  
  return results;
}
