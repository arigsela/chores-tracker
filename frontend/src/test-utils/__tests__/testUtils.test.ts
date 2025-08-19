/**
 * Test utilities validation tests
 * Ensures our testing foundation is working correctly
 */

import {
  createMockUser,
  createMockChore,
  createMockActivity,
  createMockBalance,
  mockApiClient,
  mockAuthContext,
  resetAllMocks,
  createMockApiResponse,
} from '../index';
import { createMockApiError } from '../factories';

describe('Test Utilities', () => {
  beforeEach(() => {
    resetAllMocks();
  });

  describe('Data Factories', () => {
    it('should create mock user with defaults', () => {
      const user = createMockUser();
      
      expect(user).toEqual({
        id: 1,
        username: 'testuser',
        role: 'parent',
        email: 'test@example.com',
        full_name: 'Test User',
      });
    });

    it('should create mock user with overrides', () => {
      const user = createMockUser({
        id: 999,
        role: 'child',
        username: 'customuser',
      });
      
      expect(user.id).toBe(999);
      expect(user.role).toBe('child');
      expect(user.username).toBe('customuser');
      expect(user.email).toBe('test@example.com'); // Default should remain
    });

    it('should create mock chore with defaults', () => {
      const chore = createMockChore();
      
      expect(chore).toMatchObject({
        id: 1,
        title: 'Test Chore',
        description: 'Test chore description',
        reward: 5.00,
        is_range_reward: false,
        is_recurring: false,
        is_disabled: false,
      });
      expect(chore.created_at).toBeDefined();
    });

    it('should create mock activity with defaults', () => {
      const activity = createMockActivity();
      
      expect(activity).toMatchObject({
        id: 1,
        type: 'chore_completed',
        description: 'Completed: Test Chore',
        amount: 5.00,
        user_id: 2,
        chore_id: 1,
      });
      expect(activity.created_at).toBeDefined();
    });

    it('should create mock balance with defaults', () => {
      const balance = createMockBalance();
      
      expect(balance).toEqual({
        current_balance: 25.50,
        pending_earnings: 10.00,
        total_earned: 100.00,
        total_spent: 75.00,
      });
    });
  });

  describe('Mock Implementations', () => {
    it('should provide API client mock', () => {
      expect(mockApiClient.get).toBeDefined();
      expect(mockApiClient.post).toBeDefined();
      expect(mockApiClient.put).toBeDefined();
      expect(mockApiClient.delete).toBeDefined();
      expect(jest.isMockFunction(mockApiClient.get)).toBe(true);
    });

    it('should provide auth context mock', () => {
      expect(mockAuthContext).toMatchObject({
        isAuthenticated: false,
        isLoading: false,
        user: null,
      });
      expect(jest.isMockFunction(mockAuthContext.login)).toBe(true);
      expect(jest.isMockFunction(mockAuthContext.logout)).toBe(true);
    });

    it('should reset all mocks', () => {
      // Call some mock functions
      mockAuthContext.login('test', 'pass');
      mockApiClient.get?.('/test');
      
      // Verify they were called
      expect(mockAuthContext.login).toHaveBeenCalledWith('test', 'pass');
      expect(mockApiClient.get).toHaveBeenCalledWith('/test');
      
      // Reset and verify they're cleared
      resetAllMocks();
      expect(mockAuthContext.login).not.toHaveBeenCalled();
      expect(mockApiClient.get).not.toHaveBeenCalled();
    });
  });

  describe('API Response Helpers', () => {
    it('should create mock API response', () => {
      const data = { id: 1, name: 'test' };
      const response = createMockApiResponse(data, 201);
      
      expect(response).toEqual({
        data,
        status: 201,
        statusText: 'OK',
        headers: {},
        config: {},
      });
    });

    it('should create mock API error', () => {
      const error = createMockApiError('Test error', 404);
      
      expect(error).toEqual({
        response: {
          data: {
            detail: 'Test error',
          },
          status: 404,
          statusText: 'Internal Server Error',
        },
        message: 'Test error',
        isAxiosError: true,
      });
    });
  });

  describe('AsyncStorage Mock', () => {
    it('should be mocked globally', () => {
      // AsyncStorage should be mocked by our setup
      const AsyncStorage = require('@react-native-async-storage/async-storage');
      
      expect(jest.isMockFunction(AsyncStorage.getItem)).toBe(true);
      expect(jest.isMockFunction(AsyncStorage.setItem)).toBe(true);
      expect(jest.isMockFunction(AsyncStorage.removeItem)).toBe(true);
    });
  });
});