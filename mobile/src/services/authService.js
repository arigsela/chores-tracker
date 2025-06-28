import apiClient from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';
import { storageService } from './storageService';
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';

const rnBiometrics = new ReactNativeBiometrics();

export const authService = {
  async login(username, password) {
    try {
      // Form data for OAuth2 password flow
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      formData.append('grant_type', 'password');

      const response = await apiClient.post(API_ENDPOINTS.AUTH.LOGIN, formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;

      // Store token
      await storageService.setAuthToken(access_token);

      // Get user profile
      const userResponse = await apiClient.get(API_ENDPOINTS.USERS.ME);
      await storageService.setUserData(userResponse.data);

      return {
        success: true,
        user: userResponse.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  },

  async logout() {
    try {
      // Clear local storage
      await storageService.clearAll();
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error.message };
    }
  },

  async checkBiometricAvailability() {
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      
      if (available && biometryType === BiometryTypes.FaceID) {
        return { available: true, type: 'FaceID' };
      } else if (available && biometryType === BiometryTypes.TouchID) {
        return { available: true, type: 'TouchID' };
      } else if (available && biometryType === BiometryTypes.Biometrics) {
        return { available: true, type: 'Biometrics' };
      } else {
        return { available: false, type: null };
      }
    } catch (error) {
      console.error('Biometric check error:', error);
      return { available: false, type: null };
    }
  },

  async authenticateWithBiometric() {
    try {
      const { success } = await rnBiometrics.simplePrompt({
        promptMessage: 'Authenticate to access Chores Tracker',
        cancelButtonText: 'Cancel',
      });
      return success;
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return false;
    }
  },

  async setupBiometric() {
    const biometricEnabled = await storageService.getBiometricEnabled();
    if (!biometricEnabled) {
      const { available } = await this.checkBiometricAvailability();
      if (available) {
        await storageService.setBiometricEnabled(true);
        return true;
      }
    }
    return biometricEnabled;
  },

  async getCurrentUser() {
    return await storageService.getUserData();
  },

  async isAuthenticated() {
    const token = await storageService.getAuthToken();
    const user = await storageService.getUserData();
    return !!(token && user);
  },
};
