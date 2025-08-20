/**
 * Users API Module Tests (Simplified Working Version)
 * Tests core user-related API operations
 */

import axios from 'axios';
import { usersAPI } from '../users';
import { 
  resetAllMocks, 
  createMockApiUser, 
  createMockApiParent, 
  createMockApiChild,
  createMockChildWithChores,
  createMockChildWithChoresList,
  createMockChildAllowanceSummary,
  createMockAllowanceSummaryList,
  createMockApiResponse, 
  createMockApiError 
} from '../../test-utils';

// Get the mocked axios and client instance
const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockApiClient = (mockedAxios.create as jest.Mock).mock.results[0]?.value;

describe('Users API Module (Core Tests)', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
    // Ensure mock client is reset properly
    if (mockApiClient) {
      mockApiClient.get.mockReset();
      mockApiClient.post.mockReset();
      mockApiClient.put.mockReset();
      mockApiClient.delete.mockReset();
    }
  });

  describe('getMe', () => {
    it('should fetch current user data successfully', async () => {
      const mockUser = createMockApiParent({
        id: 1,
        username: 'currentuser',
        email: 'current@test.com',
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockUser));

      const result = await usersAPI.getMe();

      expect(mockApiClient.get).toHaveBeenCalledWith('/users/me');
      expect(result).toEqual(mockUser);
      expect(result.is_parent).toBe(true);
    });

    it('should handle child user data successfully', async () => {
      const mockChildUser = createMockApiChild({
        id: 2,
        username: 'childuser',
        email: null,
        parent_id: 1,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChildUser));

      const result = await usersAPI.getMe();

      expect(result).toEqual(mockChildUser);
      expect(result.is_parent).toBe(false);
      expect(result.parent_id).toBe(1);
    });

    it('should handle inactive user correctly', async () => {
      const mockUser = createMockApiUser({
        is_active: false,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockUser));

      const result = await usersAPI.getMe();

      expect(result.is_active).toBe(false);
    });
  });

  describe('getMyChildren', () => {
    it('should fetch all children for current parent', async () => {
      const mockChildren = createMockChildWithChoresList(3);

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChildren));

      const result = await usersAPI.getMyChildren();

      expect(mockApiClient.get).toHaveBeenCalledWith('/users/my-children');
      expect(result).toEqual(mockChildren);
      expect(result).toHaveLength(3);
      expect(result[0].is_parent).toBe(false);
      expect(result[0].chores).toBeDefined();
    });

    it('should handle empty children list', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      const result = await usersAPI.getMyChildren();

      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });

    it('should handle children without chores', async () => {
      const mockChildren = [
        createMockChildWithChores({
          id: 2,
          username: 'child1',
          chores: [],
        }),
        createMockChildWithChores({
          id: 3,
          username: 'child2',
          chores: undefined,
        }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChildren));

      const result = await usersAPI.getMyChildren();

      expect(result[0].chores).toEqual([]);
      expect(result[1].chores).toBeUndefined();
    });

    it('should handle large number of children', async () => {
      const mockChildren = createMockChildWithChoresList(10);

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChildren));

      const result = await usersAPI.getMyChildren();

      expect(result).toHaveLength(10);
      expect(result.every(child => !child.is_parent)).toBe(true);
    });
  });

  describe('getAllowanceSummary', () => {
    it('should fetch allowance summary for all children', async () => {
      const mockSummary = createMockAllowanceSummaryList(2);

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockSummary));

      const result = await usersAPI.getAllowanceSummary();

      expect(mockApiClient.get).toHaveBeenCalledWith('/users/allowance-summary');
      expect(result).toEqual(mockSummary);
      expect(result).toHaveLength(2);
      expect(result[0]).toHaveProperty('completed_chores');
      expect(result[0]).toHaveProperty('total_earned');
      expect(result[0]).toHaveProperty('balance_due');
    });

    it('should handle zero balances correctly', async () => {
      const mockSummary = [
        createMockChildAllowanceSummary({
          id: 2,
          username: 'newchild',
          completed_chores: 0,
          total_earned: 0.00,
          total_adjustments: 0.00,
          paid_out: 0.00,
          balance_due: 0.00,
        }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockSummary));

      const result = await usersAPI.getAllowanceSummary();

      expect(result[0].completed_chores).toBe(0);
      expect(result[0].total_earned).toBe(0.00);
      expect(result[0].balance_due).toBe(0.00);
    });

    it('should handle negative adjustments', async () => {
      const mockSummary = [
        createMockChildAllowanceSummary({
          total_earned: 20.00,
          total_adjustments: -5.00,
          balance_due: 15.00,
        }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockSummary));

      const result = await usersAPI.getAllowanceSummary();

      expect(result[0].total_adjustments).toBe(-5.00);
      expect(result[0].balance_due).toBe(15.00);
    });

    it('should handle empty allowance summary', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      const result = await usersAPI.getAllowanceSummary();

      expect(result).toEqual([]);
    });

    it('should handle decimal precision in financial data', async () => {
      const mockSummary = [
        createMockChildAllowanceSummary({
          total_earned: 12.34,
          total_adjustments: 1.23,
          balance_due: 13.57,
        }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockSummary));

      const result = await usersAPI.getAllowanceSummary();

      expect(result[0].total_earned).toBe(12.34);
      expect(result[0].total_adjustments).toBe(1.23);
      expect(result[0].balance_due).toBe(13.57);
    });
  });

  describe('createChildAccount', () => {
    it('should create a new child account successfully', async () => {
      const childData = {
        username: 'newchild',
        password: 'securepass123',
      };

      const createdChild = createMockApiChild({
        id: 3,
        username: 'newchild',
        is_parent: false,
        parent_id: 1,
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(createdChild));

      const result = await usersAPI.createChildAccount(childData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/users/', {
        username: 'newchild',
        password: 'securepass123',
        is_parent: false,
      });
      expect(result).toEqual(createdChild);
      expect(result.is_parent).toBe(false);
      expect(result.parent_id).toBe(1);
    });

    it('should handle special characters in username', async () => {
      const childData = {
        username: 'child_with-special.chars',
        password: 'securepass123',
      };

      const createdChild = createMockApiChild({
        username: 'child_with-special.chars',
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(createdChild));

      const result = await usersAPI.createChildAccount(childData);

      expect(result.username).toBe('child_with-special.chars');
    });
  });

  describe('resetChildPassword', () => {
    it('should reset child password successfully', async () => {
      const childId = 2;
      const newPassword = 'newSecurePass456';

      const updatedChild = createMockApiChild({
        id: childId,
        username: 'testchild',
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(updatedChild));

      const result = await usersAPI.resetChildPassword(childId, newPassword);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/users/children/2/reset-password',
        JSON.stringify(newPassword),
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      expect(result).toEqual(updatedChild);
    });

    it('should handle password string serialization correctly', async () => {
      const childId = 2;
      const newPassword = 'password with spaces!@#';

      const updatedChild = createMockApiChild({ id: childId });
      mockApiClient.post.mockResolvedValue(createMockApiResponse(updatedChild));

      await usersAPI.resetChildPassword(childId, newPassword);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/users/children/2/reset-password',
        JSON.stringify('password with spaces!@#'),
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });

    it('should handle numeric child IDs correctly', async () => {
      const childId = 123;
      const newPassword = 'testPassword';
      const updatedChild = createMockApiChild({ id: childId });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(updatedChild));

      await usersAPI.resetChildPassword(childId, newPassword);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/users/children/123/reset-password',
        expect.any(String),
        expect.any(Object)
      );
    });
  });

  describe('Data Type Validation', () => {
    it('should handle various user ID formats', async () => {
      const mockUser = createMockApiUser({ id: 999 });
      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockUser));

      const result = await usersAPI.getMe();
      expect(result.id).toBe(999);
      expect(typeof result.id).toBe('number');
    });

    it('should handle nullable email fields correctly', async () => {
      const mockChild = createMockApiChild({ email: null });
      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChild));

      const result = await usersAPI.getMe();
      expect(result.email).toBeNull();
    });

    it('should handle boolean flags consistently', async () => {
      const mockUser = createMockApiUser({
        is_active: false,
        is_parent: true,
      });
      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockUser));

      const result = await usersAPI.getMe();
      expect(typeof result.is_active).toBe('boolean');
      expect(typeof result.is_parent).toBe('boolean');
      expect(result.is_active).toBe(false);
      expect(result.is_parent).toBe(true);
    });

    it('should handle parent_id relationships correctly', async () => {
      const parentUser = createMockApiParent({ parent_id: null });
      const childUser = createMockApiChild({ parent_id: 1 });

      mockApiClient.get.mockResolvedValueOnce(createMockApiResponse(parentUser));
      const parentResult = await usersAPI.getMe();
      expect(parentResult.parent_id).toBeNull();

      mockApiClient.get.mockResolvedValueOnce(createMockApiResponse(childUser));
      const childResult = await usersAPI.getMe();
      expect(childResult.parent_id).toBe(1);
      expect(typeof childResult.parent_id).toBe('number');
    });
  });

  describe('Error Handling', () => {
    it('should handle network connectivity issues', async () => {
      const networkError = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(networkError);

      await expect(usersAPI.getMe()).rejects.toThrow('Network Error');
    });

    it('should handle malformed JSON responses', async () => {
      const malformedResponse = { data: null };
      mockApiClient.get.mockResolvedValue(malformedResponse);

      const result = await usersAPI.getMe();
      expect(result).toBeNull();
    });
  });
});