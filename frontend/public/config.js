// Runtime configuration for frontend application
// This file is served as a static asset and provides runtime environment variables
window.APP_CONFIG = {
  API_URL: 'http://chores-tracker-service:8000/api/v1',  // Production API URL for Kubernetes
  NODE_ENV: 'production'
};