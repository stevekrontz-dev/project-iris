    },
    userAgent: 'IRIS Research Platform',
  },
  enrichment: {
    openAlex: true,
    orcid: true,
    googleScholar: false,
  },
};

// ============================================
// COMBINED ATLANTA CONSORTIUM CONFIG
// ============================================

export const ATLANTA_CONSORTIUM_CONFIGS = [
  KSU_CONFIG,
  EMORY_CONFIG,
  GATECH_BME_CONFIG,
  GSU_CONFIG,
];

// OpenAlex Institution IDs for filtering
export const OPENALEX_INSTITUTIONS = {
  ksu: 'I173911158',      // Kennesaw State University
  emory: 'I136199984',    // Emory University  
  gatech: 'I64801317',    // Georgia Institute of Technology
  gsu: 'I25215891',       // Georgia State University
};

// ROR IDs for institutions
export const ROR_INSTITUTIONS = {
  ksu: 'https://ror.org/02j1wme58',
  emory: 'https://ror.org/03czfpz43',
  gatech: 'https://ror.org/01zkghx44',
  gsu: 'https://ror.org/028qhbr48',
};
