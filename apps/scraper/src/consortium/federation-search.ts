/**
 * IRIS Federation Search - Cross-Institutional Discovery
 * 
 * Provides semantic search across all consortium members
 */

import * as fs from 'fs';
import * as path from 'path';
import { FederatedSearchQuery, FederatedSearchResult, PersonType } from './types';

interface FederatedProfile {
  id: string;
  tenantSlug: string;
  tenantName: string;
  fullName: string;
  firstName?: string;
  lastName?: string;
  position?: string;
  personType?: PersonType;
  department?: string;
  email?: string;
  photoUrl?: string;
  profileUrl?: string;
  researchInterests: string[];
  keywords: string[];
  openAlexId?: string;
  hIndex?: number;
  citationCount?: number;
  publicationCount?: number;
  matchConfidence: string;
}

interface FederationIndex {
  consortium: string;
  consortiumName: string;
  generatedAt: string;
  totalProfiles: number;
  byTenant: Record<string, number>;
  profiles: FederatedProfile[];
}

export class FederationSearch {
  private index: FederationIndex | null = null;
  private indexPath: string;
  
  constructor(indexPath: string = './data/consortium/federation_index.json') {
    this.indexPath = indexPath;
  }
  
  /**
   * Load the federation index
   */
  async loadIndex(): Promise<void> {
    if (!fs.existsSync(this.indexPath)) {
      throw new Error(`Federation index not found: ${this.indexPath}`);
    }
    
    const content = fs.readFileSync(this.indexPath, 'utf-8');
    this.index = JSON.parse(content);
    
    console.log(`Loaded federation index: ${this.index!.totalProfiles} profiles from ${this.index!.consortiumName}`);
  }
  
  /**
   * Search the federation index
   */
  search(query: FederatedSearchQuery): FederatedSearchResult[] {
    if (!this.index) {
      throw new Error('Index not loaded. Call loadIndex() first.');
    }
    
    let results = this.index.profiles;
    
    // Filter by tenants
    if (query.tenants && query.tenants.length > 0) {
      results = results.filter(p => query.tenants!.includes(p.tenantSlug));
    }
    
    // Filter by person types
    if (query.personTypes && query.personTypes.length > 0) {
      results = results.filter(p => p.personType && query.personTypes!.includes(p.personType));
    }
    
    // Filter by department
    if (query.departments && query.departments.length > 0) {
      const deptLower = query.departments.map(d => d.toLowerCase());
      results = results.filter(p => 
        p.department && deptLower.some(d => p.department!.toLowerCase().includes(d))
      );
    }
    
    // Filter by h-index
    if (query.minHIndex !== undefined) {
      results = results.filter(p => p.hIndex && p.hIndex >= query.minHIndex!);
    }
    
    // Text search
    if (query.query && query.query.trim().length > 0) {
      const searchTerms = query.query.toLowerCase().split(/\s+/);
      
      results = results.map(profile => {
        const score = this.calculateSearchScore(profile, searchTerms);
        return { profile, score };
      })
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(item => item.profile);
    }
    
    // Apply pagination
    const offset = query.offset || 0;
    const limit = query.limit || 20;
    
    results = results.slice(offset, offset + limit);
    
    // Map to search results
    return results.map(profile => this.toSearchResult(profile, query.query || ''));
  }
  
  /**
   * Calculate search score for a profile
   */
  private calculateSearchScore(profile: FederatedProfile, searchTerms: string[]): number {
    let score = 0;
    
    const searchableText = [
      profile.fullName,
      profile.position,
      profile.department,
      profile.tenantName,
      ...profile.researchInterests,
      ...profile.keywords,
    ].filter(Boolean).join(' ').toLowerCase();
    
    for (const term of searchTerms) {
      // Name match (highest weight)
      if (profile.fullName.toLowerCase().includes(term)) {
        score += 10;
      }
      
      // Department match
      if (profile.department?.toLowerCase().includes(term)) {
        score += 5;
      }
      
      // Research interests match
      for (const interest of profile.researchInterests) {
        if (interest.toLowerCase().includes(term)) {
          score += 3;
        }
      }
      
      // Keywords/topics match
      for (const keyword of profile.keywords) {
        if (keyword.toLowerCase().includes(term)) {
          score += 2;
        }
      }
      
      // Position match
      if (profile.position?.toLowerCase().includes(term)) {
        score += 2;
      }
      
      // Institution match
      if (profile.tenantName.toLowerCase().includes(term)) {
        score += 1;
      }
      
      // General text match
      if (searchableText.includes(term)) {
        score += 0.5;
      }
    }
    
    // Boost for having metrics
    if (profile.hIndex && profile.hIndex > 10) {
      score *= 1.1;
    }
    if (profile.matchConfidence === 'HIGH') {
      score *= 1.05;
    }
    
    return score;
  }
  
  /**
   * Convert profile to search result
   */
  private toSearchResult(profile: FederatedProfile, query: string): FederatedSearchResult {
    const highlights: { field: string; matches: string[] }[] = [];
    const queryTerms = query.toLowerCase().split(/\s+/).filter(t => t.length > 0);
    
    // Find highlights
    if (queryTerms.length > 0) {
      for (const interest of profile.researchInterests) {
        const matches = queryTerms.filter(t => interest.toLowerCase().includes(t));
        if (matches.length > 0) {
          highlights.push({ field: 'researchInterests', matches: [interest] });
        }
      }
    }
    
    return {
      person: {
        id: profile.id,
        fullName: profile.fullName,
        position: profile.position,
        department: profile.department,
        institution: profile.tenantName,
        institutionSlug: profile.tenantSlug,
      },
      score: 0,  // Score is used for sorting, not returned
      highlights: highlights.length > 0 ? highlights : undefined,
      metrics: profile.hIndex || profile.citationCount || profile.publicationCount ? {
        hIndex: profile.hIndex,
        citationCount: profile.citationCount,
        publicationCount: profile.publicationCount,
      } : undefined,
      links: profile.openAlexId ? {
        orcid: undefined,  // Would need to extract from OpenAlex
        googleScholar: undefined,
        website: profile.profileUrl,
      } : undefined,
    };
  }
  
  /**
   * Get statistics about the index
   */
  getStats(): object {
    if (!this.index) {
      throw new Error('Index not loaded');
    }
    
    const profiles = this.index.profiles;
    
    return {
      consortium: this.index.consortiumName,
      generatedAt: this.index.generatedAt,
      totalProfiles: this.index.totalProfiles,
      
      byInstitution: this.index.byTenant,
      
      coverage: {
        withEmail: profiles.filter(p => p.email).length,
        withResearchInterests: profiles.filter(p => p.researchInterests.length > 0).length,
        withOpenAlex: profiles.filter(p => p.openAlexId).length,
        withHIndex: profiles.filter(p => p.hIndex).length,
      },
      
      byPersonType: this.groupBy(profiles, 'personType'),
      
      topDepartments: this.getTopValues(profiles, 'department', 10),
    };
  }
  
  /**
   * Group profiles by a field
   */
  private groupBy(profiles: FederatedProfile[], field: keyof FederatedProfile): Record<string, number> {
    const groups: Record<string, number> = {};
    
    for (const profile of profiles) {
      const value = String(profile[field] || 'Unknown');
      groups[value] = (groups[value] || 0) + 1;
    }
    
    return groups;
  }
  
  /**
   * Get top N values for a field
   */
  private getTopValues(
    profiles: FederatedProfile[], 
    field: keyof FederatedProfile, 
    n: number
  ): Array<{ value: string; count: number }> {
    const counts = this.groupBy(profiles, field);
    
    return Object.entries(counts)
      .filter(([value]) => value !== 'Unknown' && value !== 'undefined')
      .sort((a, b) => b[1] - a[1])
      .slice(0, n)
      .map(([value, count]) => ({ value, count }));
  }
  
  /**
   * Find potential collaborators based on research interests
   */
  findCollaborators(
    researchInterests: string[],
    excludeTenant?: string,
    limit: number = 10
  ): FederatedSearchResult[] {
    return this.search({
      query: researchInterests.join(' '),
      tenants: excludeTenant ? 
        Object.keys(this.index?.byTenant || {}).filter(t => t !== excludeTenant) : 
        undefined,
      limit,
    });
  }
  
  /**
   * Find researchers by topic/keyword
   */
  findByTopic(topic: string, limit: number = 20): FederatedSearchResult[] {
    return this.search({
      query: topic,
      limit,
    });
  }
  
  /**
   * Get all researchers from a specific institution
   */
  getByInstitution(tenantSlug: string): FederatedProfile[] {
    if (!this.index) {
      throw new Error('Index not loaded');
    }
    
    return this.index.profiles.filter(p => p.tenantSlug === tenantSlug);
  }
}

// CLI demo
async function demo() {
  const search = new FederationSearch();
  
  try {
    await search.loadIndex();
    
    console.log('\n' + '═'.repeat(60));
    console.log('  FEDERATION SEARCH DEMO');
    console.log('═'.repeat(60));
    
    // Show stats
    console.log('\n📊 Index Statistics:');
    console.log(JSON.stringify(search.getStats(), null, 2));
    
    // Example searches
    const exampleSearches = [
      'brain computer interface',
      'neural engineering',
      'ALS communication',
      'EEG signal processing',
      'machine learning neuroscience',
    ];
    
    for (const query of exampleSearches) {
      console.log(`\n🔍 Search: "${query}"`);
      const results = search.search({ query, limit: 5 });
      
      if (results.length === 0) {
        console.log('   No results found');
      } else {
        for (const result of results) {
          console.log(`   • ${result.person.fullName} - ${result.person.position || 'No position'}`);
          console.log(`     📍 ${result.person.institution} | ${result.person.department || 'No dept'}`);
          if (result.metrics?.hIndex) {
            console.log(`     📈 h-index: ${result.metrics.hIndex}`);
          }
        }
      }
    }
    
  } catch (error) {
    console.error('Demo failed:', error);
  }
}

// Run demo if called directly
if (require.main === module) {
  demo();
}

export { FederationSearch };
