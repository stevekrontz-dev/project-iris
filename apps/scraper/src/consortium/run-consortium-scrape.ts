#!/usr/bin/env npx ts-node
/**
 * IRIS Consortium Scraper - Main Runner
 * 
 * Run: npx ts-node apps/scraper/src/consortium/run-consortium-scrape.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import { FacultyDirectoryScraper } from './scraper';
import { enrichConsortiumData } from './enrichment';
import { ATLANTA_CONSORTIUM, ScrapedPerson, TenantConfig } from './types';

interface RunOptions {
  tenants?: string[];           // Filter to specific tenants
  skipScrape?: boolean;         // Use existing scraped data
  skipEnrichment?: boolean;     // Skip OpenAlex enrichment
  verbose?: boolean;
  outputDir?: string;
}

async function run(options: RunOptions = {}) {
  const startTime = Date.now();
  const outputDir = options.outputDir || './data/consortium';
  
  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  console.log('\n' + '█'.repeat(60));
  console.log('  IRIS CONSORTIUM SCRAPER');
  console.log('  Atlanta Neuroscience Consortium');
  console.log('█'.repeat(60) + '\n');
  
  // Determine which tenants to process
  const tenantsToProcess = ATLANTA_CONSORTIUM.members.filter(member => {
    // Skip full tenants (they have their own data)
    if (member.type === 'FULL') {
      console.log(`Skipping ${member.name} (full tenant - has census data)`);
      return false;
    }
    
    // Check if scraping is enabled
    if (!member.scrapeConfig.facultyDirectory?.enabled) {
      console.log(`Skipping ${member.name} (scraping disabled)`);
      return false;
    }
    
    // Filter by specified tenants
    if (options.tenants && options.tenants.length > 0) {
      if (!options.tenants.includes(member.slug)) {
        console.log(`Skipping ${member.name} (not in filter)`);
        return false;
      }
    }
    
    return true;
  });
  
  console.log(`\nProcessing ${tenantsToProcess.length} consortium members:`);
  tenantsToProcess.forEach(t => console.log(`  - ${t.name} (${t.slug})`));
  
  // Collect all scraped data
  const allScrapedData: Map<string, ScrapedPerson[]> = new Map();
  
  // Phase 1: Scrape faculty directories
  if (!options.skipScrape) {
    console.log('\n' + '─'.repeat(60));
    console.log('PHASE 1: Scraping Faculty Directories');
    console.log('─'.repeat(60));
    
    for (const tenant of tenantsToProcess) {
      console.log(`\n>>> Processing: ${tenant.name}`);
      
      try {
        const scraper = new FacultyDirectoryScraper(tenant, { verbose: options.verbose });
        const result = await scraper.scrape();
        const data = scraper.getResults();
        
        allScrapedData.set(tenant.slug, data);
        
        // Save raw scraped data
        const outputPath = path.join(outputDir, `${tenant.slug}_scraped.json`);
        fs.writeFileSync(outputPath, JSON.stringify({
          tenant: tenant.slug,
          institution: tenant.name,
          scrapedAt: new Date().toISOString(),
          count: data.length,
          data: data,
        }, null, 2));
        
        console.log(`Saved ${data.length} records to ${outputPath}`);
        
      } catch (error) {
        console.error(`Error scraping ${tenant.name}:`, error);
      }
    }
  } else {
    // Load existing scraped data
    console.log('\n>>> Loading existing scraped data...');
    
    for (const tenant of tenantsToProcess) {
      const inputPath = path.join(outputDir, `${tenant.slug}_scraped.json`);
      if (fs.existsSync(inputPath)) {
        const content = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
        allScrapedData.set(tenant.slug, content.data);
        console.log(`Loaded ${content.data.length} records for ${tenant.name}`);
      }
    }
  }
  
  // Phase 2: Enrich with OpenAlex
  if (!options.skipEnrichment) {
    console.log('\n' + '─'.repeat(60));
    console.log('PHASE 2: Enriching with OpenAlex');
    console.log('─'.repeat(60));
    
    for (const [tenantSlug, data] of allScrapedData) {
      const tenant = tenantsToProcess.find(t => t.slug === tenantSlug);
      if (!tenant?.enrichment.openAlex) {
        console.log(`Skipping OpenAlex enrichment for ${tenantSlug} (disabled)`);
        continue;
      }
      
      console.log(`\n>>> Enriching ${tenant.name}...`);
      
      try {
        const enriched = await enrichConsortiumData(data, { verbose: options.verbose });
        
        // Save enriched data
        const outputPath = path.join(outputDir, `${tenantSlug}_enriched.json`);
        fs.writeFileSync(outputPath, JSON.stringify({
          tenant: tenantSlug,
          institution: tenant.name,
          enrichedAt: new Date().toISOString(),
          count: enriched.length,
          matchedCount: enriched.filter(e => e.matchConfidence !== 'NONE').length,
          data: enriched,
        }, null, 2));
        
        console.log(`Saved enriched data to ${outputPath}`);
        
      } catch (error) {
        console.error(`Error enriching ${tenant.name}:`, error);
      }
    }
  }
  
  // Phase 3: Build Federation Index
  console.log('\n' + '─'.repeat(60));
  console.log('PHASE 3: Building Federation Index');
  console.log('─'.repeat(60));
  
  const federationIndex: any[] = [];
  
  for (const [tenantSlug, data] of allScrapedData) {
    const tenant = tenantsToProcess.find(t => t.slug === tenantSlug);
    if (!tenant) continue;
    
    // Try to load enriched data
    const enrichedPath = path.join(outputDir, `${tenantSlug}_enriched.json`);
    let enrichedData: Map<string, any> = new Map();
    
    if (fs.existsSync(enrichedPath)) {
      const enrichedContent = JSON.parse(fs.readFileSync(enrichedPath, 'utf-8'));
      for (const item of enrichedContent.data) {
        enrichedData.set(item.person.fullName, item);
      }
    }
    
    // Build federation profiles
    for (const person of data) {
      const enrichment = enrichedData.get(person.fullName);
      
      federationIndex.push({
        id: `${tenantSlug}:${person.fullName.replace(/\s+/g, '-').toLowerCase()}`,
        tenantSlug,
        tenantName: tenant.name,
        
        fullName: person.fullName,
        firstName: person.firstName,
        lastName: person.lastName,
        position: person.position,
        personType: person.personType,
        department: person.department,
        
        email: person.email,
        photoUrl: person.photoUrl,
        profileUrl: person.profileUrl,
        
        researchInterests: person.researchInterests || [],
        keywords: [
          ...(person.researchInterests || []),
          ...(enrichment?.topics || []),
        ],
        
        // Metrics from enrichment
        openAlexId: enrichment?.openAlexId,
        hIndex: enrichment?.metrics?.hIndex,
        citationCount: enrichment?.metrics?.citedByCount,
        publicationCount: enrichment?.metrics?.worksCount,
        matchConfidence: enrichment?.matchConfidence || 'NONE',
      });
    }
  }
  
  // Save federation index
  const federationPath = path.join(outputDir, 'federation_index.json');
  fs.writeFileSync(federationPath, JSON.stringify({
    consortium: ATLANTA_CONSORTIUM.slug,
    consortiumName: ATLANTA_CONSORTIUM.name,
    generatedAt: new Date().toISOString(),
    totalProfiles: federationIndex.length,
    byTenant: Object.fromEntries(
      tenantsToProcess.map(t => [
        t.slug, 
        federationIndex.filter(p => p.tenantSlug === t.slug).length
      ])
    ),
    profiles: federationIndex,
  }, null, 2));
  
  console.log(`\nFederation index saved to ${federationPath}`);
  console.log(`Total profiles: ${federationIndex.length}`);
  
  // Phase 4: Generate Summary Report
  console.log('\n' + '─'.repeat(60));
  console.log('PHASE 4: Summary Report');
  console.log('─'.repeat(60));
  
  const summary = {
    consortium: ATLANTA_CONSORTIUM.name,
    runAt: new Date().toISOString(),
    duration: `${((Date.now() - startTime) / 1000).toFixed(1)}s`,
    
    tenants: tenantsToProcess.map(t => ({
      slug: t.slug,
      name: t.name,
      scraped: allScrapedData.get(t.slug)?.length || 0,
      enriched: federationIndex.filter(p => p.tenantSlug === t.slug && p.matchConfidence !== 'NONE').length,
    })),
    
    totals: {
      profiles: federationIndex.length,
      enrichedWithOpenAlex: federationIndex.filter(p => p.matchConfidence !== 'NONE').length,
      withEmail: federationIndex.filter(p => p.email).length,
      withResearchInterests: federationIndex.filter(p => p.researchInterests?.length > 0).length,
    },
    
    files: {
      scraped: tenantsToProcess.map(t => `${outputDir}/${t.slug}_scraped.json`),
      enriched: tenantsToProcess.map(t => `${outputDir}/${t.slug}_enriched.json`),
      federation: federationPath,
    },
  };
  
  const summaryPath = path.join(outputDir, 'run_summary.json');
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
  
  console.log('\n' + '═'.repeat(60));
  console.log('  CONSORTIUM SCRAPE COMPLETE');
  console.log('═'.repeat(60));
  console.log(`\n  Duration: ${summary.duration}`);
  console.log(`  Total Profiles: ${summary.totals.profiles}`);
  console.log(`  Enriched: ${summary.totals.enrichedWithOpenAlex}`);
  console.log(`\n  Output Directory: ${outputDir}`);
  console.log('\n' + '═'.repeat(60) + '\n');
  
  return summary;
}

// CLI interface
const args = process.argv.slice(2);
const options: RunOptions = {
  verbose: args.includes('--verbose') || args.includes('-v'),
  skipScrape: args.includes('--skip-scrape'),
  skipEnrichment: args.includes('--skip-enrichment'),
};

// Parse tenant filter
const tenantIdx = args.indexOf('--tenants');
if (tenantIdx !== -1 && args[tenantIdx + 1]) {
  options.tenants = args[tenantIdx + 1].split(',');
}

run(options).catch(console.error);
