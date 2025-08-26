/**
 * Chores API Module Tests
 * Tests all chore-related API operations including CRUD, status management,
 * approval workflows, and chore lifecycle operations
 */

import axios from 'axios';
import { choreAPI, ChoreStatus } from '../chores';
import { resetAllMocks } from '../../test-utils';
import { createMockChore, createMockApiResponse, createMockApiError } from '../../test-utils/factories';

// Mock the API client module directly
jest.mock('../client', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
  },
}));

// Import the mocked client
import apiClient from '../client';
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Chores API Module', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
  });

  describe('getMyChores', () => {
    it('should fetch all chores for current user without status filter', async () => {
      const mockChores = [
        createMockChore({ id: 1, title: 'Chore 1' }),
        createMockChore({ id: 2, title: 'Chore 2' }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChores));

      const result = await choreAPI.getMyChores();

      expect(mockApiClient.get).toHaveBeenCalledWith('/chores', { params: {} });
      expect(result).toEqual(mockChores);
    });

    it('should fetch chores with status filter', async () => {
      const mockChores = [createMockChore({ id: 1, is_completed: true })];
      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChores));

      const status: ChoreStatus = 'completed';
      const result = await choreAPI.getMyChores(status);

      expect(mockApiClient.get).toHaveBeenCalledWith('/chores', { 
        params: { status: 'completed' } 
      });
      expect(result).toEqual(mockChores);
    });

    it('should handle empty chores list', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      const result = await choreAPI.getMyChores();

      expect(result).toEqual([]);
    });

    it('should handle API errors gracefully', async () => {
      const error = createMockApiError('Failed to fetch chores', 500);
      mockApiClient.get.mockRejectedValue(error);

      await expect(choreAPI.getMyChores()).rejects.toThrow();
    });
  });

  describe('getAvailableChores', () => {
    it('should fetch available chores for claiming', async () => {
      const mockChores = [
        createMockChore({ id: 1, assigned_to_id: null }),
        createMockChore({ id: 2, assigned_to_id: null }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockChores));

      const result = await choreAPI.getAvailableChores();

      expect(mockApiClient.get).toHaveBeenCalledWith('/chores/available');
      expect(result).toEqual(mockChores);
    });

    it('should handle no available chores', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      const result = await choreAPI.getAvailableChores();

      expect(result).toEqual([]);
    });

    it('should handle API errors', async () => {
      const error = createMockApiError('Access denied', 403);
      mockApiClient.get.mockRejectedValue(error);

      await expect(choreAPI.getAvailableChores()).rejects.toThrow();
    });
  });

  describe('completeChore', () => {
    it('should mark chore as completed', async () => {
      const completedChore = createMockChore({ 
        id: 1, 
        is_completed: true, 
        completed_at: '2024-01-01T12:00:00Z' 
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(completedChore));

      const result = await choreAPI.completeChore(1);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/complete');
      expect(result).toEqual(completedChore);
      expect(result.is_completed).toBe(true);
      expect(result.completed_at).toBeDefined();
    });

    it('should handle chore not found', async () => {
      const error = createMockApiError('Chore not found', 404);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.completeChore(999)).rejects.toThrow();
    });

    it('should handle unauthorized completion', async () => {
      const error = createMockApiError('Unauthorized', 403);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.completeChore(1)).rejects.toThrow();
    });
  });

  describe('getPendingApprovalChores', () => {
    it('should fetch chores pending approval', async () => {
      const pendingChores = [
        createMockChore({ 
          id: 1, 
          is_completed: true, 
          is_approved: false,
          completed_at: '2024-01-01T12:00:00Z'
        }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(pendingChores));

      const result = await choreAPI.getPendingApprovalChores();

      expect(mockApiClient.get).toHaveBeenCalledWith('/chores/pending-approval');
      expect(result).toEqual(pendingChores);
    });

    it('should handle no pending chores', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      const result = await choreAPI.getPendingApprovalChores();

      expect(result).toEqual([]);
    });

    it('should handle parent-only access restriction', async () => {
      const error = createMockApiError('Parent access required', 403);
      mockApiClient.get.mockRejectedValue(error);

      await expect(choreAPI.getPendingApprovalChores()).rejects.toThrow();
    });
  });

  describe('approveChore', () => {
    it('should approve chore without reward value', async () => {
      const approvedChore = createMockChore({ 
        id: 1, 
        is_completed: true, 
        is_approved: true,
        approved_at: '2024-01-01T13:00:00Z',
        approval_reward: 5.00
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(approvedChore));

      const result = await choreAPI.approveChore(1);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/approve', {});
      expect(result).toEqual(approvedChore);
      expect(result.is_approved).toBe(true);
      expect(result.approved_at).toBeDefined();
    });

    it('should approve chore with custom reward value', async () => {
      const approvedChore = createMockChore({ 
        id: 1, 
        is_completed: true, 
        is_approved: true,
        approved_at: '2024-01-01T13:00:00Z',
        approval_reward: 7.50
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(approvedChore));

      const result = await choreAPI.approveChore(1, 7.50);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/approve', {
        reward_value: 7.50
      });
      expect(result).toEqual(approvedChore);
      expect(result.approval_reward).toBe(7.50);
    });

    it('should approve range reward chore with value', async () => {
      const rangeChore = createMockChore({
        id: 1,
        is_range_reward: true,
        min_reward: 3.00,
        max_reward: 10.00,
        is_completed: true,
        is_approved: true,
        approval_reward: 8.00
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(rangeChore));

      const result = await choreAPI.approveChore(1, 8.00);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/approve', {
        reward_value: 8.00
      });
      expect(result.approval_reward).toBe(8.00);
    });

    it('should handle chore already approved', async () => {
      const error = createMockApiError('Chore already approved', 400);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.approveChore(1)).rejects.toThrow();
    });
  });

  describe('rejectChore', () => {
    it('should reject chore with reason', async () => {
      const rejectedChore = createMockChore({ 
        id: 1, 
        is_completed: false,
        completed_at: null,
        rejection_reason: 'Not done properly'
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(rejectedChore));

      const result = await choreAPI.rejectChore(1, 'Not done properly');

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/reject', {
        rejection_reason: 'Not done properly'
      });
      expect(result).toEqual(rejectedChore);
      expect(result.rejection_reason).toBe('Not done properly');
      expect(result.is_completed).toBe(false);
    });

    it('should handle rejection with empty reason', async () => {
      const rejectedChore = createMockChore({ 
        id: 1, 
        rejection_reason: ''
      });

      mockApiClient.post.mockResolvedValue(createMockApiResponse(rejectedChore));

      const result = await choreAPI.rejectChore(1, '');

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/reject', {
        rejection_reason: ''
      });
      expect(result.rejection_reason).toBe('');
    });

    it('should handle chore not found for rejection', async () => {
      const error = createMockApiError('Chore not found', 404);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.rejectChore(999, 'reason')).rejects.toThrow();
    });
  });

  describe('getChildChores', () => {
    it('should fetch chores for specific child', async () => {
      const childChores = [
        createMockChore({ id: 1, assigned_to_id: 2 }),
        createMockChore({ id: 2, assigned_to_id: 2 }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(childChores));

      const result = await choreAPI.getChildChores(2);

      expect(mockApiClient.get).toHaveBeenCalledWith('/chores/child/2');
      expect(result).toEqual(childChores);
    });

    it('should handle child with no chores', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      const result = await choreAPI.getChildChores(2);

      expect(result).toEqual([]);
    });

    it('should handle invalid child ID', async () => {
      const error = createMockApiError('Child not found', 404);
      mockApiClient.get.mockRejectedValue(error);

      await expect(choreAPI.getChildChores(999)).rejects.toThrow();
    });
  });

  describe('getChildCompletedChores', () => {
    it('should fetch completed chores for specific child', async () => {
      const completedChores = [
        createMockChore({ 
          id: 1, 
          assigned_to_id: 2, 
          is_completed: true,
          completed_at: '2024-01-01T12:00:00Z'
        }),
      ];

      mockApiClient.get.mockResolvedValue(createMockApiResponse(completedChores));

      const result = await choreAPI.getChildCompletedChores(2);

      expect(mockApiClient.get).toHaveBeenCalledWith('/chores/child/2/completed');
      expect(result).toEqual(completedChores);
      expect(result[0].is_completed).toBe(true);
    });

    it('should handle child with no completed chores', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      const result = await choreAPI.getChildCompletedChores(2);

      expect(result).toEqual([]);
    });
  });

  describe('createChore', () => {
    it('should create a basic fixed reward chore', async () => {
      const choreData = {
        title: 'New Chore',
        description: 'Test description',
        reward: 5.00,
        is_range_reward: false,
        assignee_id: 2,
        is_recurring: false,
      };

      const createdChore = createMockChore(choreData);
      mockApiClient.post.mockResolvedValue(createMockApiResponse(createdChore));

      const result = await choreAPI.createChore(choreData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores', choreData);
      expect(result).toEqual(createdChore);
    });

    it('should create a range reward chore', async () => {
      const choreData = {
        title: 'Range Chore',
        description: 'Range reward test',
        is_range_reward: true,
        min_reward: 3.00,
        max_reward: 10.00,
        assignee_id: 2,
        is_recurring: false,
      };

      const createdChore = createMockChore(choreData);
      mockApiClient.post.mockResolvedValue(createMockApiResponse(createdChore));

      const result = await choreAPI.createChore(choreData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores', choreData);
      expect(result.is_range_reward).toBe(true);
      expect(result.min_reward).toBe(3.00);
      expect(result.max_reward).toBe(10.00);
    });

    it('should create a recurring chore', async () => {
      const choreData = {
        title: 'Weekly Chore',
        description: 'Recurring test',
        reward: 5.00,
        is_range_reward: false,
        assignee_id: 2,
        is_recurring: true,
        cooldown_days: 7,
      };

      const createdChore = createMockChore(choreData);
      mockApiClient.post.mockResolvedValue(createMockApiResponse(createdChore));

      const result = await choreAPI.createChore(choreData);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores', choreData);
      expect(result.is_recurring).toBe(true);
      expect(result.cooldown_days).toBe(7);
    });

    it('should handle validation errors', async () => {
      const choreData = {
        title: '', // Invalid empty title
        is_range_reward: false,
        assignee_id: 2,
        is_recurring: false,
      };

      const error = createMockApiError('Title is required', 400);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.createChore(choreData)).rejects.toThrow();
    });

    it('should handle missing assignee', async () => {
      const choreData = {
        title: 'Test Chore',
        is_range_reward: false,
        assignee_id: 999, // Non-existent user
        is_recurring: false,
      };

      const error = createMockApiError('Assignee not found', 404);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.createChore(choreData)).rejects.toThrow();
    });
  });

  describe('updateChore', () => {
    it('should update chore title and description', async () => {
      const updateData = {
        title: 'Updated Title',
        description: 'Updated description',
      };

      const updatedChore = createMockChore({ id: 1, ...updateData });
      mockApiClient.put.mockResolvedValue(createMockApiResponse(updatedChore));

      const result = await choreAPI.updateChore(1, updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith('/chores/1', updateData);
      expect(result.title).toBe('Updated Title');
      expect(result.description).toBe('Updated description');
    });

    it('should update chore reward amount', async () => {
      const updateData = {
        reward: 7.50,
      };

      const updatedChore = createMockChore({ id: 1, reward: 7.50 });
      mockApiClient.put.mockResolvedValue(createMockApiResponse(updatedChore));

      const result = await choreAPI.updateChore(1, updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith('/chores/1', updateData);
      expect(result.reward).toBe(7.50);
    });

    it('should update chore assignment', async () => {
      const updateData = {
        assignee_id: 3,
      };

      const updatedChore = createMockChore({ id: 1, assignee_id: 3 });
      mockApiClient.put.mockResolvedValue(createMockApiResponse(updatedChore));

      const result = await choreAPI.updateChore(1, updateData);

      expect(mockApiClient.put).toHaveBeenCalledWith('/chores/1', updateData);
      expect(result.assignee_id).toBe(3);
    });

    it('should convert fixed to range reward', async () => {
      const updateData = {
        is_range_reward: true,
        min_reward: 2.00,
        max_reward: 8.00,
        reward: undefined, // Clear fixed reward
      };

      const updatedChore = createMockChore({ 
        id: 1, 
        is_range_reward: true,
        min_reward: 2.00,
        max_reward: 8.00,
        reward: null
      });
      mockApiClient.put.mockResolvedValue(createMockApiResponse(updatedChore));

      const result = await choreAPI.updateChore(1, updateData);

      expect(result.is_range_reward).toBe(true);
      expect(result.min_reward).toBe(2.00);
      expect(result.max_reward).toBe(8.00);
    });

    it('should handle chore not found', async () => {
      const error = createMockApiError('Chore not found', 404);
      mockApiClient.put.mockRejectedValue(error);

      await expect(choreAPI.updateChore(999, { title: 'test' })).rejects.toThrow();
    });
  });

  describe('disableChore', () => {
    it('should disable an active chore', async () => {
      const disabledChore = createMockChore({ id: 1, is_disabled: true });
      mockApiClient.post.mockResolvedValue(createMockApiResponse(disabledChore));

      const result = await choreAPI.disableChore(1);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/disable');
      expect(result.is_disabled).toBe(true);
    });

    it('should handle chore not found', async () => {
      const error = createMockApiError('Chore not found', 404);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.disableChore(999)).rejects.toThrow();
    });
  });

  describe('enableChore', () => {
    it('should enable a disabled chore', async () => {
      const enabledChore = createMockChore({ id: 1, is_disabled: false });
      mockApiClient.post.mockResolvedValue(createMockApiResponse(enabledChore));

      const result = await choreAPI.enableChore(1);

      expect(mockApiClient.post).toHaveBeenCalledWith('/chores/1/enable');
      expect(result.is_disabled).toBe(false);
    });

    it('should handle already enabled chore', async () => {
      const error = createMockApiError('Chore is already enabled', 400);
      mockApiClient.post.mockRejectedValue(error);

      await expect(choreAPI.enableChore(1)).rejects.toThrow();
    });
  });

  describe('deleteChore', () => {
    it('should delete a chore', async () => {
      mockApiClient.delete.mockResolvedValue(createMockApiResponse({}));

      await choreAPI.deleteChore(1);

      expect(mockApiClient.delete).toHaveBeenCalledWith('/chores/1');
    });

    it('should handle chore not found', async () => {
      const error = createMockApiError('Chore not found', 404);
      mockApiClient.delete.mockRejectedValue(error);

      await expect(choreAPI.deleteChore(999)).rejects.toThrow();
    });

    it('should handle deletion of chore with completions', async () => {
      const error = createMockApiError('Cannot delete chore with completions', 400);
      mockApiClient.delete.mockRejectedValue(error);

      await expect(choreAPI.deleteChore(1)).rejects.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should handle network timeouts', async () => {
      const timeoutError = new Error('timeout of 10000ms exceeded');
      timeoutError.code = 'ECONNABORTED';
      mockApiClient.get.mockRejectedValue(timeoutError);

      await expect(choreAPI.getMyChores()).rejects.toThrow('timeout of 10000ms exceeded');
    });

    it('should handle server errors', async () => {
      const serverError = createMockApiError('Internal server error', 500);
      mockApiClient.get.mockRejectedValue(serverError);

      await expect(choreAPI.getMyChores()).rejects.toThrow();
    });

    it('should handle malformed responses', async () => {
      mockApiClient.get.mockResolvedValue({ data: null });

      const result = await choreAPI.getMyChores();
      expect(result).toBeNull();
    });
  });

  describe('Parameter Validation', () => {
    it('should handle various ChoreStatus values', async () => {
      const statuses: ChoreStatus[] = ['available', 'active', 'completed', 'pending_approval', 'approved'];
      
      for (const status of statuses) {
        mockApiClient.get.mockResolvedValue(createMockApiResponse([]));
        
        await choreAPI.getMyChores(status);
        
        expect(mockApiClient.get).toHaveBeenCalledWith('/chores', { 
          params: { status } 
        });
      }
    });

    it('should handle numeric IDs correctly', async () => {
      mockApiClient.get.mockResolvedValue(createMockApiResponse([]));

      await choreAPI.getChildChores(123);
      expect(mockApiClient.get).toHaveBeenCalledWith('/chores/child/123');

      await choreAPI.getChildCompletedChores(456);
      expect(mockApiClient.get).toHaveBeenCalledWith('/chores/child/456/completed');
    });

    it('should handle decimal reward values', async () => {
      const choreData = {
        title: 'Test',
        reward: 12.34,
        is_range_reward: false,
        assignee_id: 1,
        is_recurring: false,
      };

      mockApiClient.post.mockResolvedValue(createMockApiResponse(createMockChore()));
      
      await choreAPI.createChore(choreData);
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/chores', 
        expect.objectContaining({ reward: 12.34 })
      );
    });
  });
});