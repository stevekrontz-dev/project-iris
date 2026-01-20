/**
 * IRIS Consortium Scraper - Base Scraper Class
 * 
 * Generic faculty directory scraper that can be configured for different institutions
 */

import * as cheerio from 'cheerio';
import { 
  TenantConfig, 
  ScrapedPerson, 
  FacultySelectors,
  ImportResult,
  ImportError,
  PersonType 
} from './types';

export interface ScraperOptions {
  verbose?: boolean;
  dryRun?: boolean;
  maxPages?: number;
}

export class FacultyDirectoryScraper {
  private config: TenantConfig;
  private options: ScraperOptions;
  private errors: ImportError[] = [];
  private results: ScrapedPerson[] = [];
  
  constructor(config: TenantConfig, options: ScraperOptions = {}) {
    this.config = config;
    this.options = options;
  }
  
  /**
   * Main entry point - scrape all configured faculty directories
   */
  async scrape(): Promise<ImportResult> {
    const startedAt = new Date();
    
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Starting scrape for: ${this.config.name}`);
    console.log(`Tenant slug: ${this.config.slug}`);
    console.log(`${'='.repeat(60)}\n`);
    
    const facultyConfig = this.config.scrapeConfig.facultyDirectory;
    
    if (!facultyConfig?.enabled) {
      console.log('Faculty directory scraping disabled for this tenant');
      return this.buildResult(startedAt);
    }
    
    // Scrape each configured URL
    const urls = facultyConfig.listUrls || [facultyConfig.baseUrl];
    
    for (const url of urls) {
      console.log(`\nScraping: ${url}`);
      await this.scrapeUrl(url, facultyConfig.selectors);
      
      // Rate limiting
      await this.delay(this.config.scrapeConfig.rateLimit.delayBetweenPages);
    }
    
    return this.buildResult(startedAt);
  }
  
  /**
   * Scrape a single URL
   */
  private async scrapeUrl(url: string, selectors: FacultySelectors): Promise<void> {
    try {
      const html = await this.fetchPage(url);
      const $ = cheerio.load(html);
      
      // Find all person containers
      const containers = $(selectors.personContainer);
      console.log(`Found ${containers.length} person containers`);
      
      containers.each((index, element) => {
        try {
          const person = this.extractPerson($, $(element), selectors, url);
          if (person && person.fullName) {
            this.results.push(person);
            
            if (this.options.verbose) {
              console.log(`  [${index + 1}] ${person.fullName} - ${person.position || 'No position'}`);
            }
          }
        } catch (error) {
          this.errors.push({
            url,
            error: `Failed to extract person at index ${index}: ${error}`,
            timestamp: new Date(),
          });
        }
      });
      
      console.log(`Extracted ${this.results.length} people so far`);
      
    } catch (error) {
      this.errors.push({
        url,
        error: `Failed to fetch page: ${error}`,
        timestamp: new Date(),
      });
      console.error(`Error scraping ${url}:`, error);
    }
  }
  
  /**
   * Extract person data from a container element
   */
  private extractPerson(
    $: cheerio.CheerioAPI, 
    container: cheerio.Cheerio<cheerio.Element>,
    selectors: FacultySelectors,
    sourceUrl: string
  ): ScrapedPerson | null {
    const getText = (selector?: string): string | undefined => {
      if (!selector) return undefined;
      const text = container.find(selector).first().text().trim();
      return text || undefined;
    };
    
    const getAttr = (selector: string, attr: string): string | undefined => {
      const val = container.find(selector).first().attr(attr);
      return val || undefined;
    };
    
    const getHref = (selector: string): string | undefined => {
      return getAttr(selector, 'href');
    };
    
    // Extract name
    const rawName = getText(selectors.name);
    if (!rawName) return null;
    
    const { firstName, lastName, fullName } = this.parseName(rawName);
    
    // Extract email
    let email = getHref('a[href^="mailto:"]');
    if (email) {
      email = email.replace('mailto:', '').split('?')[0].trim();
    }
    
    // Extract research interests
    let researchInterests: string[] | undefined;
    if (selectors.researchInterests) {
      const interestsText = getText(selectors.researchInterests);
      if (interestsText) {
        researchInterests = this.parseInterests(interestsText);
      }
    }
    
    // Extract photo URL
    let photoUrl = getAttr('img', 'src');
    if (photoUrl && !photoUrl.startsWith('http')) {
      // Make absolute
      const base = new URL(sourceUrl);
      photoUrl = new URL(photoUrl, base.origin).toString();
    }
    
    // Extract profile URL
    let profileUrl = getHref(selectors.profileUrl || 'a');
    if (profileUrl && !profileUrl.startsWith('http')) {
      const base = new URL(sourceUrl);
      profileUrl = new URL(profileUrl, base.origin).toString();
    }
    
    return {
      tenantSlug: this.config.slug,
      sourceUrl,
      scrapedAt: new Date(),
      
      fullName,
      firstName,
      lastName,
      
      position: getText(selectors.position),
      department: getText(selectors.department),
      personType: this.inferPersonType(getText(selectors.position)),
      
      email,
      phone: getText(selectors.phone),
      officeLocation: getText(selectors.office),
      
      bio: getText(selectors.bio),
      researchInterests,
      
      photoUrl,
      profileUrl,
    };
  }
  
  /**
   * Parse a full name into components
   */
  private parseName(rawName: string): { firstName?: string; lastName?: string; fullName: string } {
    // Clean up the name
    let name = rawName
      .replace(/\s+/g, ' ')
      .replace(/,\s*(Ph\.?D\.?|M\.?D\.?|Dr\.?|Prof\.?)/gi, '')
      .trim();
    
    // Remove titles
    const titles = ['Dr.', 'Dr', 'Prof.', 'Prof', 'Professor', 'Mr.', 'Ms.', 'Mrs.'];
    for (const title of titles) {
      if (name.startsWith(title + ' ')) {
        name = name.substring(title.length + 1);
      }
    }
    
    // Remove suffixes
    const suffixes = ['Ph.D.', 'PhD', 'M.D.', 'MD', 'Jr.', 'Jr', 'Sr.', 'Sr', 'III', 'II'];
    for (const suffix of suffixes) {
      if (name.endsWith(' ' + suffix) || name.endsWith(', ' + suffix)) {
        name = name.replace(new RegExp('[,\\s]+' + suffix.replace('.', '\\.') + '$'), '');
      }
    }
    
    name = name.trim();
    
    // Split into parts
    const parts = name.split(' ').filter(p => p.length > 0);
    
    if (parts.length === 0) {
      return { fullName: rawName };
    }
    
    if (parts.length === 1) {
      return { lastName: parts[0], fullName: name };
    }
    
    // Last part is last name, first part(s) are first name
    const lastName = parts[parts.length - 1];
    const firstName = parts.slice(0, -1).join(' ');
    
    return { firstName, lastName, fullName: name };
  }
  
  /**
   * Parse research interests from text
   */
  private parseInterests(text: string): string[] {
    // Common separators
    const separators = [';', ',', '•', '|', '\n'];
    
    for (const sep of separators) {
      if (text.includes(sep)) {
        return text
          .split(sep)
          .map(s => s.trim())
          .filter(s => s.length > 0 && s.length < 100);
      }
    }
    
    // No separator found, return as single interest if reasonable length
    if (text.length < 200) {
      return [text];
    }
    
    return [];
  }
  
  /**
   * Infer person type from position title
   */
  private inferPersonType(position?: string): PersonType {
    if (!position) return 'FACULTY';
    
    const pos = position.toLowerCase();
    
    if (pos.includes('emeritus') || pos.includes('emerita')) return 'EMERITUS';
    if (pos.includes('postdoc') || pos.includes('post-doc')) return 'POSTDOC';
    if (pos.includes('graduate') || pos.includes('phd student') || pos.includes('doctoral')) return 'GRADUATE_STUDENT';
    if (pos.includes('research scientist') || pos.includes('researcher')) return 'RESEARCHER';
    if (pos.includes('staff') || pos.includes('coordinator') || pos.includes('administrator')) return 'STAFF';
    if (pos.includes('affiliate') || pos.includes('adjunct')) return 'AFFILIATE';
    if (pos.includes('dean') || pos.includes('director') || pos.includes('chair')) return 'ADMINISTRATOR';
    if (pos.includes('professor') || pos.includes('lecturer') || pos.includes('instructor')) return 'FACULTY';
    
    return 'FACULTY';
  }
  
  /**
   * Fetch a page with proper headers and error handling
   */
  private async fetchPage(url: string): Promise<string> {
    const response = await fetch(url, {
      headers: {
        'User-Agent': this.config.scrapeConfig.userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.text();
  }
  
  /**
   * Delay helper for rate limiting
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  /**
   * Build the final import result
   */
  private buildResult(startedAt: Date): ImportResult {
    const result: ImportResult = {
      tenantSlug: this.config.slug,
      importType: 'FACULTY_DIRECTORY',
      startedAt,
      completedAt: new Date(),
      stats: {
        found: this.results.length,
        created: 0,  // Will be set by persistence layer
        updated: 0,
        skipped: 0,
        failed: this.errors.length,
      },
      errors: this.errors,
    };
    
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Scrape complete for: ${this.config.name}`);
    console.log(`Found: ${result.stats.found} people`);
    console.log(`Errors: ${result.stats.failed}`);
    console.log(`${'='.repeat(60)}\n`);
    
    return result;
  }
  
  /**
   * Get scraped results
   */
  getResults(): ScrapedPerson[] {
    return this.results;
  }
  
  /**
   * Get errors
   */
  getErrors(): ImportError[] {
    return this.errors;
  }
}

/**
 * Utility function to scrape all consortium members
 */
export async function scrapeConsortium(
  members: TenantConfig[],
  options: ScraperOptions = {}
): Promise<Map<string, ImportResult>> {
  const results = new Map<string, ImportResult>();
  
  for (const member of members) {
    if (member.type === 'CONSORTIUM' && member.scrapeConfig.facultyDirectory?.enabled) {
      console.log(`\n${'#'.repeat(60)}`);
      console.log(`Processing consortium member: ${member.name}`);
      console.log(`${'#'.repeat(60)}`);
      
      const scraper = new FacultyDirectoryScraper(member, options);
      const result = await scraper.scrape();
      results.set(member.slug, result);
      
      // Save results to file
      const outputPath = `./data/consortium/${member.slug}_faculty.json`;
      const scrapedData = scraper.getResults();
      
      // We'll handle file I/O in the runner script
      (result as any).scrapedData = scrapedData;
    }
  }
  
  return results;
}
