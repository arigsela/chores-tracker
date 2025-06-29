import axios from 'axios';
import { storageService } from '../services/storageService';
import { getAPIUrl } from '../config/api';

const API_URL = getAPIUrl();
console.log('API URL configured as:', API_URL);

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const token = await storageService.getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      await storageService.clearAll();
      // Navigate to login (will be handled by auth context)
    }
    
    // Better error logging
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout');
    } else if (error.message === 'Network Error') {
      console.error('Network Error - Cannot reach server at:', error.config?.baseURL);
      console.error('Full URL attempted:', error.config?.url);
      console.error('Make sure backend is running and accessible from device');
    }
    
    console.error('Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
