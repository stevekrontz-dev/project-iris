// KSU Research Platform - Shared Types & Constants

// ============================================
// BRANDING
// ============================================

export const PLATFORM_NAME = 'KSU Research';
export const PLATFORM_TAGLINE = 'Research Development Acceleration Platform';

// AI System Branding
export const AI_NAME = 'IRIS';
export const AI_FULL_NAME = 'Intelligent Research Information System';
export const AI_TAGLINE = 'Seeing connections others miss';

// ============================================
// COLORS (KSU Brand)
// ============================================

export const COLORS = {
  ksuGold: '#FFC423',
  ksuBlack: '#000000',
  ksuDark: '#1a1a1a',
  accentBlue: '#2563eb',
  accentGreen: '#059669',
  accentPurple: '#7c3aed',
} as const;

// ============================================
// EXTERNAL URLS
// ============================================

export const EXTERNAL_URLS = {
  ksuFacultyWeb: 'https://facultyweb.kennesaw.edu',
  ksuDirectory: 'https://directory.kennesaw.edu',
  ksuResearch: 'https://www.kennesaw.edu/research',
  googleScholar: 'https://scholar.google.com',
  orcid: 'https://orcid.org',
  nihReporter: 'https://reporter.nih.gov',
} as const;

// ============================================
// API ENDPOINTS (External Services)
// ============================================

export const API_ENDPOINTS = {
  orcidApi: 'https://pub.orcid.org/v3.0',
  nihReporterApi: 'https://api.reporter.nih.gov/v2',
  crossrefApi: 'https://api.crossref.org',
  openAlexApi: 'https://api.openalex.org',
} as const;

// ============================================
// MATCH TYPES & SCORES
// ============================================

export const MATCH_THRESHOLDS = {
  high: 0.8,      // Strong match
  medium: 0.6,    // Moderate match
  low: 0.4,       // Weak match (minimum to show)
} as const;

export const MATCH_TYPE_LABELS = {
  COLLABORATOR: 'Potential Collaborator',
  METHODOLOGY: 'Shared Methodology',
  EQUIPMENT: 'Equipment Sharing',
  GRANT: 'Grant Partner',
  CROSS_DISCIPLINARY: 'Cross-Disciplinary Opportunity',
} as const;

// ============================================
// VALIDATION
// ============================================

export const ALLOWED_EMAIL_DOMAINS = [
  'kennesaw.edu',
  'students.kennesaw.edu',
] as const;

export const isAllowedEmailDomain = (email: string): boolean => {
  const domain = email.split('@')[1]?.toLowerCase();
  return ALLOWED_EMAIL_DOMAINS.some(allowed => domain === allowed || domain?.endsWith(`.${allowed}`));
};

// ============================================
// TYPE EXPORTS
// ============================================

export type MatchTypeKey = keyof typeof MATCH_TYPE_LABELS;
export type MatchThreshold = keyof typeof MATCH_THRESHOLDS;
