// API Configuration
// Uses environment variables in production, localhost in development

const getApiUrl = () => {
  // Check for production environment variable first
  if (typeof window !== 'undefined') {
    // Client-side: use the public env var
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  // Server-side
  return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const getEmailApiUrl = () => {
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_EMAIL_API_URL || 'http://localhost:8001';
  }
  return process.env.EMAIL_API_URL || process.env.NEXT_PUBLIC_EMAIL_API_URL || 'http://localhost:8001';
};

export const API_URL = getApiUrl();
export const EMAIL_API_URL = getEmailApiUrl();

export const api = {
  search: (params: URLSearchParams) => `${API_URL}/search?${params}`,
  stats: () => `${API_URL}/stats`,
  name: (query: string, limit = 10) => `${API_URL}/name?q=${encodeURIComponent(query)}&limit=${limit}`,
};

export const emailApi = {
  preview: () => `${EMAIL_API_URL}/preview-briefing`,
  send: () => `${EMAIL_API_URL}/send-briefing`,
  health: () => `${EMAIL_API_URL}/health`,
};
