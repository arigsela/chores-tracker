// Test script to verify API connection
import apiClient from '../api/client';

export const testAPIConnection = async () => {
  try {
    console.log('Testing API connection...');
    const response = await apiClient.get('/health');
    console.log('API Health Check:', response.data);
    return true;
  } catch (error) {
    console.error('API Connection Error:', error.message);
    if (error.code === 'ECONNREFUSED') {
      console.error('Make sure your backend is running on http://localhost:8000');
    }
    return false;
  }
};
