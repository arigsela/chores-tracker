/**
 * API Configuration utility for environment-based API URL selection
 * Supports both runtime environment variables (for containerized deployments)
 * and build-time React environment variables (for static builds)
 */

export const getAPIUrl = (): string => {
  // Priority 1: Runtime environment variable (set by Kubernetes deployment)
  if (process.env.API_URL) {
    console.log('🚀 Using runtime API_URL:', process.env.API_URL);
    return process.env.API_URL;
  }

  // Priority 2: Build-time React environment variable (prefixed with REACT_APP_)
  if (process.env.REACT_APP_API_URL) {
    console.log('⚛️  Using build-time REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    return process.env.REACT_APP_API_URL;
  }

  // Priority 3: Default for local development
  const defaultUrl = 'http://localhost:8000/api/v1';
  console.log('🏠 No environment API_URL found, using default:', defaultUrl);
  return defaultUrl;
};

export const API_URL = getAPIUrl();

// Log the final API URL for debugging
console.log('🌐 Final API URL configured:', API_URL);