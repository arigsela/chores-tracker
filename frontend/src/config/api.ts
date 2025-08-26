/**
 * API Configuration utility for environment-based API URL selection
 * Supports runtime configuration via window.APP_CONFIG (set by nginx container startup)
 * and build-time React environment variables (for development/static builds)
 */

// Global window interface extension for TypeScript
declare global {
  interface Window {
    APP_CONFIG?: {
      API_URL?: string;
      NODE_ENV?: string;
    };
  }
}

export const getAPIUrl = (): string => {
  // Priority 1: Runtime configuration (set by nginx container startup)
  if (typeof window !== 'undefined' && window.APP_CONFIG?.API_URL) {
    console.log('🚀 Using runtime APP_CONFIG.API_URL:', window.APP_CONFIG.API_URL);
    return window.APP_CONFIG.API_URL;
  }

  // Priority 2: Build-time React environment variable (prefixed with REACT_APP_)
  if (process.env.REACT_APP_API_URL) {
    console.log('⚛️  Using build-time REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    return process.env.REACT_APP_API_URL;
  }

  // Priority 3: Default for local development
  const defaultUrl = 'http://localhost:8000/api/v1';
  console.log('🏠 No runtime or build-time API_URL found, using default:', defaultUrl);
  return defaultUrl;
};

// Note: API_URL is now dynamic - call getAPIUrl() when needed rather than caching at module load time
// This ensures runtime configuration (window.APP_CONFIG) is available when the URL is requested

// Export the function for dynamic resolution
export { getAPIUrl };