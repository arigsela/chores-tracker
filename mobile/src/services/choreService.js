import apiClient from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';

// Helper function to map backend chore to frontend format
const mapChoreFromBackend = (chore) => {
  return {
    ...chore,
    // Map backend fields to frontend expected fields
    reward_amount: chore.is_range_reward ? (chore.min_reward || 0) : (chore.reward || 0),
    max_reward_amount: chore.max_reward || null,
    reward_type: chore.is_range_reward ? 'range' : 'fixed',
    recurrence: chore.is_recurring ? 'recurring' : 'once',
    // Map status based on backend boolean flags
    status: chore.is_disabled ? 'disabled' :
            chore.is_approved ? 'approved' : 
            chore.is_completed ? 'pending' : 
            'created',
    // For approved chores, use the actual approved amount or fallback to reward
    approved_reward_amount: chore.approved_reward_amount || chore.reward || 0,
  };
};

export const choreService = {
  // Parent endpoints
  async getAllChores() {
    try {
      const response = await apiClient.get(API_ENDPOINTS.CHORES.LIST);
      return {
        success: true,
        data: response.data.map(mapChoreFromBackend),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch chores',
      };
    }
  },

  async createChore(choreData) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.CHORES.CREATE, choreData);
      return {
        success: true,
        data: mapChoreFromBackend(response.data),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create chore',
      };
    }
  },

  async updateChore(choreId, choreData) {
    try {
      const response = await apiClient.put(API_ENDPOINTS.CHORES.UPDATE(choreId), choreData);
      return {
        success: true,
        data: mapChoreFromBackend(response.data),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update chore',
      };
    }
  },

  async deleteChore(choreId) {
    try {
      const response = await apiClient.delete(API_ENDPOINTS.CHORES.DELETE(choreId));
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to delete chore',
      };
    }
  },

  async disableChore(choreId) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.CHORES.DISABLE(choreId), {});
      return {
        success: true,
        data: mapChoreFromBackend(response.data),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to disable chore',
      };
    }
  },

  async getPendingApprovals() {
    try {
      const response = await apiClient.get('/chores/pending-approval');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch pending approvals',
      };
    }
  },

  async approveChore(choreId, rewardAmount) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.CHORES.APPROVE(choreId), {
        is_approved: true,
        reward_value: rewardAmount,
      });
      return {
        success: true,
        data: mapChoreFromBackend(response.data),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to approve chore',
      };
    }
  },

  // Child endpoints
  async getChildChores(childId) {
    try {
      // Use the main chores endpoint - it automatically filters for children
      const response = await apiClient.get(API_ENDPOINTS.CHORES.LIST);
      return {
        success: true,
        data: response.data.map(mapChoreFromBackend),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch child chores',
      };
    }
  },

  async completeChore(choreId) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.CHORES.COMPLETE(choreId), {
        is_completed: true,
      });
      return {
        success: true,
        data: mapChoreFromBackend(response.data),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to complete chore',
      };
    }
  },

  async getChildCompletedChores(childId) {
    try {
      const response = await apiClient.get(`/chores/child/${childId}/completed`);
      return {
        success: true,
        data: response.data.map(mapChoreFromBackend),
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch completed chores',
      };
    }
  },

  // Get completed chores for all children (parent view)
  async getAllChildrenCompletedChores() {
    try {
      const response = await apiClient.get('/chores/');
      const allChores = response.data.map(mapChoreFromBackend);
      // Filter for completed chores
      const completedChores = allChores.filter(chore => chore.is_completed);
      return {
        success: true,
        data: completedChores,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch completed chores',
      };
    }
  },

  // Utility functions
  formatReward(rewardType, rewardAmount, maxReward = null) {
    if (rewardType === 'fixed') {
      return `$${rewardAmount.toFixed(2)}`;
    } else if (rewardType === 'range' && maxReward) {
      return `$${rewardAmount.toFixed(2)} - $${maxReward.toFixed(2)}`;
    }
    return 'No reward';
  },

  getStatusColor(status) {
    const colors = {
      created: '#2196F3',    // Blue
      pending: '#FF9800',    // Orange
      approved: '#4CAF50',   // Green
      disabled: '#9E9E9E',   // Gray
    };
    return colors[status] || '#000000';
  },

  getStatusLabel(status) {
    const labels = {
      created: 'To Do',
      pending: 'Pending Approval',
      approved: 'Completed',
      disabled: 'Disabled',
    };
    return labels[status] || status;
  },
};