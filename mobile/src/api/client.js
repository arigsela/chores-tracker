import axios from 'axios';
import Config from 'react-native-config';
import { storageService } from '../services/storageService';

// Use your Mac's IP address for physical device testing
const API_URL = Config.API_URL || 'http://192.168.0.250:8000/api/v1';
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
    console.error('Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
