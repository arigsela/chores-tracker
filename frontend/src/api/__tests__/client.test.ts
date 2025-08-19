/**
 * API Client Core Tests
 * Tests the foundational API client functionality including token management,
 * error handling, and auth API functions
 */

import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { resetAllMocks } from '../../test-utils';
import { authAPI } from '../client';

// Get the mocked axios (already mocked in setup.ts)
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Get the mock API client instance
const mockApiClient = (mockedAxios.create as jest.Mock).mock.results[0]?.value;

describe('API Client Core', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
  });

  describe('Client Configuration', () => {
    it('should use correct configuration constants', () => {
      // Since the client is imported after mocking, we can test the constants are used
      // by verifying the behavior of API calls
      expect(authAPI).toBeDefined();
      expect(typeof authAPI.login).toBe('function');
      expect(typeof authAPI.logout).toBe('function');
      expect(typeof authAPI.getToken).toBe('function');
      expect(typeof authAPI.isAuthenticated).toBe('function');
      expect(typeof authAPI.getCurrentUser).toBe('function');
    });
  });

  describe('Auth API Functions', () => {
    describe('login', () => {
      it('should send login request with form data and store token', async () => {
        const mockLoginResponse = {
          data: {
            access_token: 'new-token-123',
            token_type: 'bearer',
          },
        };

        const mockUserResponse = {
          data: {
            id: 1,
            username: 'testuser',
            email: 'test@example.com',
            is_parent: true,
          },
        };

        // Mock the direct axios.post call for login
        mockedAxios.post.mockResolvedValue(mockLoginResponse);
        // Mock the instance.get call for user data
        mockApiClient.get.mockResolvedValue(mockUserResponse);

        const result = await authAPI.login('testuser', 'password123');

        // Verify login request was made correctly
        expect(mockedAxios.post).toHaveBeenCalledWith(
          'http://localhost:8000/api/v1/users/login',
          expect.any(URLSearchParams),
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          }
        );

        // Verify form data content
        const formData = mockedAxios.post.mock.calls[0][1] as URLSearchParams;
        expect(formData.get('username')).toBe('testuser');
        expect(formData.get('password')).toBe('password123');

        // Verify token was stored
        expect(AsyncStorage.setItem).toHaveBeenCalledWith(
          '@chores_tracker:token',
          'new-token-123'
        );

        // Verify user data was fetched
        expect(mockApiClient.get).toHaveBeenCalledWith('/users/me');

        // Verify combined response
        expect(result).toEqual({
          access_token: 'new-token-123',
          token_type: 'bearer',
          user: mockUserResponse.data,
        });
      });

      it('should handle login failure correctly', async () => {
        const error = new Error('Request failed with status code 401');
        error.response = {
          status: 401,
          data: { detail: 'Invalid credentials' },
        };

        mockedAxios.post.mockRejectedValue(error);

        await expect(authAPI.login('baduser', 'badpass')).rejects.toThrow();
        
        // Should not store token on failure
        expect(AsyncStorage.setItem).not.toHaveBeenCalled();
      });

      it('should handle user data fetch failure after successful login', async () => {
        const mockLoginResponse = {
          data: {
            access_token: 'new-token-123',
            token_type: 'bearer',
          },
        };

        mockedAxios.post.mockResolvedValue(mockLoginResponse);
        mockApiClient.get.mockRejectedValue(new Error('User fetch failed'));

        await expect(authAPI.login('testuser', 'password123')).rejects.toThrow('User fetch failed');
      });

      it('should handle response without access_token', async () => {
        const mockResponse = {
          data: {
            // Missing access_token
            token_type: 'bearer',
          },
        };

        mockedAxios.post.mockResolvedValue(mockResponse);

        const result = await authAPI.login('testuser', 'password123');

        expect(result).toEqual(mockResponse.data);
        expect(AsyncStorage.setItem).not.toHaveBeenCalled();
        expect(mockApiClient.get).not.toHaveBeenCalled();
      });
    });

    describe('getCurrentUser', () => {
      it('should fetch current user data successfully', async () => {
        const mockUserData = {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          is_parent: true,
        };

        mockApiClient.get.mockResolvedValue({ data: mockUserData });

        const result = await authAPI.getCurrentUser();

        expect(mockApiClient.get).toHaveBeenCalledWith('/users/me');
        expect(result).toEqual(mockUserData);
      });

      it('should handle getCurrentUser failure', async () => {
        const error = new Error('Unauthorized');
        mockApiClient.get.mockRejectedValue(error);

        await expect(authAPI.getCurrentUser()).rejects.toThrow('Unauthorized');
      });
    });

    describe('logout', () => {
      it('should remove token from storage', async () => {
        await authAPI.logout();

        expect(AsyncStorage.removeItem).toHaveBeenCalledWith('@chores_tracker:token');
      });
    });

    describe('getToken', () => {
      it('should retrieve token from storage', async () => {
        (AsyncStorage.getItem as jest.Mock).mockResolvedValue('stored-token');

        const result = await authAPI.getToken();

        expect(AsyncStorage.getItem).toHaveBeenCalledWith('@chores_tracker:token');
        expect(result).toBe('stored-token');
      });

      it('should return null when no token exists', async () => {
        (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

        const result = await authAPI.getToken();

        expect(result).toBeNull();
      });
    });

    describe('isAuthenticated', () => {
      it('should return true when token exists', async () => {
        (AsyncStorage.getItem as jest.Mock).mockResolvedValue('some-token');

        const result = await authAPI.isAuthenticated();

        expect(result).toBe(true);
      });

      it('should return false when token does not exist', async () => {
        (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

        const result = await authAPI.isAuthenticated();

        expect(result).toBe(false);
      });

      it('should return false when token is empty string', async () => {
        (AsyncStorage.getItem as jest.Mock).mockResolvedValue('');

        const result = await authAPI.isAuthenticated();

        expect(result).toBe(false);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      const networkError = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(networkError);

      await expect(authAPI.getCurrentUser()).rejects.toThrow('Network Error');
    });

    it('should handle timeout errors', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 10000ms exceeded',
      };
      mockApiClient.get.mockRejectedValue(timeoutError);

      await expect(authAPI.getCurrentUser()).rejects.toMatchObject(timeoutError);
    });
  });

  describe('Configuration Constants', () => {
    it('should use correct token storage key', () => {
      // Verify the token key is used consistently in AsyncStorage operations
      authAPI.getToken();
      expect(AsyncStorage.getItem).toHaveBeenCalledWith('@chores_tracker:token');
    });

    it('should use correct API base URL in login calls', async () => {
      // Test that the correct URL is used by checking the actual API call
      const mockResponse = { data: { access_token: 'token' } };
      mockedAxios.post.mockResolvedValue(mockResponse);
      mockApiClient.get.mockResolvedValue({ data: { id: 1 } });

      await authAPI.login('test', 'pass');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/users/login',
        expect.any(URLSearchParams),
        expect.any(Object)
      );
    });

    it('should use correct content type for login', async () => {
      const mockResponse = { data: { access_token: 'token' } };
      mockedAxios.post.mockResolvedValue(mockResponse);
      mockApiClient.get.mockResolvedValue({ data: { id: 1 } });

      await authAPI.login('test', 'pass');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(URLSearchParams),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
    });
  });

  describe('Form Data Handling', () => {
    it('should properly encode login form data', async () => {
      const mockResponse = { data: { access_token: 'token' } };
      mockedAxios.post.mockResolvedValue(mockResponse);
      mockApiClient.get.mockResolvedValue({ data: { id: 1 } });

      await authAPI.login('test@user.com', 'password with spaces!@#');

      const formData = mockedAxios.post.mock.calls[0][1] as URLSearchParams;
      expect(formData.get('username')).toBe('test@user.com');
      expect(formData.get('password')).toBe('password with spaces!@#');
      expect(formData.toString()).toContain('username=test%40user.com');
      expect(formData.toString()).toContain('password=password+with+spaces%21%40%23');
    });
  });
});