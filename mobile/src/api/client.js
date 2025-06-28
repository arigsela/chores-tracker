import axios from 'axios';
import Config from 'react-native-config';
import { storageService } from '../services/storageService';

// Detect if running on simulator or device
import { Platform } from 'react-native';

const getAPIUrl = () => {
  if (Config.API_URL) {
    return Config.API_URL;
  }
  
  // For iOS simulator, we can use localhost
  // For physical device, use Mac's IP address
  if (Platform.OS === 'ios' && __DEV__) {
    // Check if running in simulator by checking for localhost connectivity
    // In production, this would be replaced with actual API URL
    return 'http://localhost:8000/api/v1';
  }
  
  // Default to Mac's IP for physical device testing
  return 'http://192.168.0.250:8000/api/v1';
};

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
    console.error('Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
