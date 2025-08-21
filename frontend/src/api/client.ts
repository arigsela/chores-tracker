import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../config/api';

// Constants
const TOKEN_KEY = '@chores_tracker:token';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      const token = await AsyncStorage.getItem(TOKEN_KEY);
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error retrieving token:', error);
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear it
      await AsyncStorage.removeItem(TOKEN_KEY);
      // TODO: Redirect to login screen
    }
    return Promise.reject(error);
  }
);

// Auth API functions
export const authAPI = {
  login: async (username: string, password: string) => {
    // Backend expects form-encoded data for login
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    console.log('API Client: Logging in to', `${API_URL}/users/login`);
    console.log('API Client: Form data:', formData.toString());

    try {
      const response = await axios.post(`${API_URL}/users/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      console.log('API Client: Login response status:', response.status);
      console.log('API Client: Login response data:', response.data);

      // Store token if login successful
      if (response.data.access_token) {
        console.log('API Client: Storing token');
        await AsyncStorage.setItem(TOKEN_KEY, response.data.access_token);
        
        // Now fetch user data with the token
        console.log('API Client: Fetching user data');
        const userResponse = await apiClient.get('/users/me');
        console.log('API Client: User data:', userResponse.data);
        
        // Return combined data
        return {
          access_token: response.data.access_token,
          token_type: response.data.token_type,
          user: userResponse.data
        };
      }

      return response.data;
    } catch (error: any) {
      console.error('API Client: Login failed:', error.message);
      if (error.response) {
        console.error('API Client: Error response:', error.response.data);
      }
      throw error;
    }
  },

  getCurrentUser: async () => {
    try {
      const response = await apiClient.get('/users/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get current user:', error);
      throw error;
    }
  },

  logout: async () => {
    await AsyncStorage.removeItem(TOKEN_KEY);
  },

  getToken: async () => {
    return await AsyncStorage.getItem(TOKEN_KEY);
  },

  isAuthenticated: async () => {
    const token = await AsyncStorage.getItem(TOKEN_KEY);
    return !!token;
  },
};

export { apiClient };
export default apiClient;