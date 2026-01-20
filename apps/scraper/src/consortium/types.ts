/**
 * IRIS Consortium Scraper - Types and Interfaces
 * 
 * Defines the data structures for multi-tenant consortium scraping
 */

// ============================================
// TENANT CONFIGURATION
// ============================================

export interface TenantConfig {
  slug: string;
  name: string;
  shortName: string;
  domain: string;
  type: 'FULL' | 'CONSORTIUM';
  
  // Scraping configuration
  scrapeConfig: ScrapeConfig;
  
  // Enrichment settings
  enrichment: {
    openAlex: boolean;
    orcid: boolean;
    googleScholar: boolean;
  };
}

export interface ScrapeConfig {
  // Faculty directory
  facultyDirectory?: {
    enabled: boolean;
    baseUrl: string;
    listUrls?: string[];      // Multiple department pages
    selectors: FacultySelectors;
    pagination?: PaginationConfig;
  };
  
  // Department pages
  departments?: {
    enabled: boolean;
    indexUrl: string;
    selectors: DepartmentSelectors;
  };
  
  // Rate limiting
  rateLimit: {
    requestsPerSecond: number;
    delayBetweenPages: number;  // ms
  };
  
  // User agent
  userAgent: string;
}

export interface FacultySelectors {
  // Container for each faculty member
  personContainer: string;
  
  // Individual fields (CSS selectors or XPath)
  name: string;
  position?: string;
  department?: string;
  email?: string;
  phone?: string;
  office?: string;
  bio?: string;
  photoUrl?: string;
  profileUrl?: string;
  researchInterests?: string;
}

export interface DepartmentSelectors {
  departmentContainer: string;
  name: string;
  url?: string;
  college?: string;
}

export interface PaginationConfig {
  type: 'page-number' | 'next-button' | 'infinite-scroll' | 'none';
  nextSelector?: string;
  pageParamName?: string;
  maxPages?: number;
}

// ============================================
// SCRAPED DATA STRUCTURES
// ============================================

export interface ScrapedPerson {
  // Source tracking
  tenantSlug: string;
  sourceUrl: string;
  scrapedAt: Date;
  
  // Identity
  fullName: string;
  firstName?: string;
  lastName?: string;
  
  // Position
  title?: string;           // Dr., Prof., etc.
  position?: string;        // "Associate Professor"
  personType?: PersonType;
  
  // Organization
  department?: string;
  college?: string;
  
  // Contact
  email?: string;
  phone?: string;
  officeLocation?: string;
  
  // Research
  bio?: string;
  researchInterests?: string[];
  keywords?: string[];
  
  // Links
  photoUrl?: string;
  profileUrl?: string;
  websiteUrl?: string;
  orcidId?: string;
  googleScholarId?: string;
  linkedinUrl?: string;
  
  // Raw HTML for debugging
  rawHtml?: string;
}

export type PersonType = 
  | 'FACULTY'
  | 'STAFF'
  | 'RESEARCHER'
  | 'POSTDOC'
  | 'GRADUATE_STUDENT'
  | 'ADMINISTRATOR'
  | 'EMERITUS'
  | 'AFFILIATE'
  | 'OTHER';

export interface ScrapedDepartment {
  tenantSlug: string;
  name: string;
  code?: string;
  collegeName?: string;
  url?: string;
  facultyCount?: number;
}

// ============================================
// ENRICHMENT DATA
// ============================================

export interface OpenAlexAuthor {
  id: string;
  displayName: string;
  orcid?: string;
  worksCount: number;
  citedByCount: number;
  hIndex?: number;
  lastKnownInstitution?: {
    id: string;
    displayName: string;
    ror?: string;
  };
  topics?: Array<{
    id: string;
    displayName: string;
    score: number;
  }>;
}

export interface OpenAlexWork {
  id: string;
  doi?: string;
  title: string;
  abstract?: string;
  publicationDate?: string;
  publicationYear?: number;
  type?: string;
  citedByCount: number;
  venue?: {
    displayName?: string;
    publisher?: string;
  };
  authorships: Array<{
    authorPosition: string;
    author: {
      id: string;
      displayName: string;
    };
    isCorresponding: boolean;
  }>;
}

// ============================================
// IMPORT/EXPORT STRUCTURES
// ============================================

export interface ImportResult {
  tenantSlug: string;
  importType: string;
  startedAt: Date;
  completedAt?: Date;
  
  stats: {
    found: number;
    created: number;
    updated: number;
    skipped: number;
    failed: number;
  };
  
  errors: ImportError[];
}

export interface ImportError {
  url?: string;
  personName?: string;
  error: string;
  stack?: string;
  timestamp: Date;
}

// ============================================
// FEDERATION STRUCTURES
// ============================================

export interface FederatedSearchQuery {
  query: string;
  tenants?: string[];         // Filter to specific tenants
  personTypes?: PersonType[];
  departments?: string[];
  minHIndex?: number;
  seekingCollaborators?: boolean;
  limit?: number;
  offset?: number;
}

export interface FederatedSearchResult {
  person: {
    id: string;
    fullName: string;
    position?: string;
    department?: string;
    institution: string;
    institutionSlug: string;
  };
  
  score: number;              // Similarity score
  highlights?: {
    field: string;
    matches: string[];
  }[];
  
  metrics?: {
    hIndex?: number;
    citationCount?: number;
    publicationCount?: number;
  };
  
  links?: {
    orcid?: string;
    googleScholar?: string;
    website?: string;
  };
}

// ============================================
// CONSORTIUM CONFIGURATION
// ============================================

export interface ConsortiumConfig {
  slug: string;
  name: string;
  description?: string;
  
  members: TenantConfig[];
  
  // Shared settings
  federation: {
    enabled: boolean;
    autoSync: boolean;
    syncIntervalHours: number;
  };
}

// ============================================
// ATLANTA NEUROSCIENCE CONSORTIUM CONFIG
// ============================================

export const ATLANTA_CONSORTIUM: ConsortiumConfig = {
  slug: 'atlanta-neuroscience',
  name: 'Atlanta Neuroscience Consortium',
  description: 'Cross-institutional collaboration network for neuroscience research in Atlanta',
  
  members: [
    // KSU - Full tenant (we have census data)
    {
      slug: 'ksu',
      name: 'Kennesaw State University',
      shortName: 'KSU',
      domain: 'kennesaw.edu',
      type: 'FULL',
      scrapeConfig: {
        facultyDirectory: {
          enabled: false,  // We have census data
          baseUrl: '',
          selectors: {} as FacultySelectors,
        },
        rateLimit: { requestsPerSecond: 2, delayBetweenPages: 500 },
        userAgent: 'IRIS Research Platform (research purposes)',
      },
      enrichment: { openAlex: true, orcid: true, googleScholar: false },
    },
    
    // Emory - Consortium (scrape public faculty)
    {
      slug: 'emory',
      name: 'Emory University',
      shortName: 'Emory',
      domain: 'emory.edu',
      type: 'CONSORTIUM',
      scrapeConfig: {
        facultyDirectory: {
          enabled: true,
          baseUrl: 'https://med.emory.edu/departments/neurology/faculty/index.html',
          listUrls: [
            'https://med.emory.edu/departments/neurology/faculty/index.html',
            'https://biomed.emory.edu/PROGRAM_SITES/NS/about-us/faculty-search.html',
          ],
          selectors: {
            personContainer: '.faculty-member, .card, .profile',
            name: 'h3, .name, .faculty-name',
            position: '.title, .position, .rank',
            department: '.department',
            email: 'a[href^="mailto:"]',
            profileUrl: 'a[href*="faculty"], a[href*="profile"]',
            photoUrl: 'img',
          },
        },
        rateLimit: { requestsPerSecond: 1, delayBetweenPages: 2000 },
        userAgent: 'IRIS Research Platform (academic research collaboration)',
      },
      enrichment: { openAlex: true, orcid: true, googleScholar: false },
    },
    
    // Georgia Tech - Consortium
    {
      slug: 'gatech',
      name: 'Georgia Institute of Technology',
      shortName: 'Georgia Tech',
      domain: 'gatech.edu',
      type: 'CONSORTIUM',
      scrapeConfig: {
        facultyDirectory: {
          enabled: true,
          baseUrl: 'https://bme.gatech.edu/bme/faculty',
          listUrls: [
            'https://bme.gatech.edu/bme/faculty',
            'https://neuro.gatech.edu/faculty',
            'https://neuro.gatech.edu/faculty-area',
          ],
          selectors: {
            personContainer: '.views-row, .faculty-card, .person',
            name: 'h2, h3, .name',
            position: '.field-title, .position',
            department: '.field-department',
            email: 'a[href^="mailto:"]',
            profileUrl: 'a[href*="bio"], a[href*="faculty"]',
            photoUrl: 'img',
            researchInterests: '.research-interests, .field-research',
          },
        },
        rateLimit: { requestsPerSecond: 1, delayBetweenPages: 2000 },
        userAgent: 'IRIS Research Platform (academic research collaboration)',
      },
      enrichment: { openAlex: true, orcid: true, googleScholar: false },
    },
    
    // Georgia State - Consortium
    {
      slug: 'gsu',
      name: 'Georgia State University',
      shortName: 'GSU',
      domain: 'gsu.edu',
      type: 'CONSORTIUM',
      scrapeConfig: {
        facultyDirectory: {
          enabled: true,
          baseUrl: 'https://neuroscience.gsu.edu/directory/',
          listUrls: [
            'https://neuroscience.gsu.edu/directory/',
          ],
          selectors: {
            personContainer: '.faculty-profile, .profile-card, .person',
            name: 'h2, h3, .name',
            position: '.title, .position',
            department: '.department',
            email: 'a[href^="mailto:"]',
            profileUrl: 'a[href*="profile"], a[href*="directory"]',
            photoUrl: 'img',
            bio: '.bio, .research-description',
          },
        },
        rateLimit: { requestsPerSecond: 1, delayBetweenPages: 2000 },
        userAgent: 'IRIS Research Platform (academic research collaboration)',
      },
      enrichment: { openAlex: true, orcid: true, googleScholar: false },
    },
  ],
  
  federation: {
    enabled: true,
    autoSync: true,
    syncIntervalHours: 24,
  },
};
