import apiClient from './client';

export interface Chore {
  id: number;
  title: string;
  description: string | null;
  reward: number | null;
  is_range_reward: boolean;
  min_reward: number | null;
  max_reward: number | null;
  cooldown_days: number | null;
  assigned_to_id?: number | null;
  assignee_id?: number | null; // Backend uses this field name  
  assigned_to_username?: string;
  completed_at?: string | null;
  completion_date?: string | null; // Backend uses this field name
  approved_at?: string | null;
  approval_reward?: number | null;
  created_at: string;
  created_by_id?: number;
  creator_id?: number; // Backend uses this field name
  is_active?: boolean;
  is_completed?: boolean; // Backend uses this field
  is_approved?: boolean; // Backend uses this field
  is_disabled?: boolean; // Backend uses this field
  is_recurring: boolean;
  next_available_at?: string | null;
}

export type ChoreStatus = 'available' | 'active' | 'completed' | 'pending_approval' | 'approved';

export const choreAPI = {
  // Get all chores for the current user
  getMyChores: async (status?: ChoreStatus): Promise<Chore[]> => {
    try {
      const params: any = {};
      if (status) {
        params.status = status;
      }
      const response = await apiClient.get('/chores', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch chores:', error);
      throw error;
    }
  },

  // Get available chores for child to claim
  getAvailableChores: async (): Promise<Chore[]> => {
    try {
      const response = await apiClient.get('/chores/available');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch available chores:', error);
      throw error;
    }
  },

  // Complete a chore
  completeChore: async (choreId: number): Promise<Chore> => {
    try {
      const response = await apiClient.post(`/chores/${choreId}/complete`);
      return response.data;
    } catch (error) {
      console.error('Failed to complete chore:', error);
      throw error;
    }
  },

  // Get chores pending approval (parent only)
  getPendingApprovalChores: async (): Promise<Chore[]> => {
    try {
      const response = await apiClient.get('/chores/pending-approval');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch pending approval chores:', error);
      throw error;
    }
  },

  // Approve a chore (parent only)
  approveChore: async (choreId: number, rewardValue?: number): Promise<Chore> => {
    try {
      const data: any = {};
      if (rewardValue !== undefined) {
        data.reward_value = rewardValue;
      }
      const response = await apiClient.post(`/chores/${choreId}/approve`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to approve chore:', error);
      throw error;
    }
  },

  // Get chores for a specific child (parent only)
  getChildChores: async (childId: number): Promise<Chore[]> => {
    try {
      const response = await apiClient.get(`/chores/child/${childId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch child chores:', error);
      throw error;
    }
  },

  // Get completed chores for a specific child (parent only)
  getChildCompletedChores: async (childId: number): Promise<Chore[]> => {
    try {
      const response = await apiClient.get(`/chores/child/${childId}/completed`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch child completed chores:', error);
      throw error;
    }
  },

  // Create a new chore (parent only)
  createChore: async (choreData: {
    title: string;
    description?: string;
    reward?: number;
    is_range_reward: boolean;
    min_reward?: number;
    max_reward?: number;
    assignee_id: number;  // Required by backend
    is_recurring: boolean;
    cooldown_days?: number;
  }): Promise<Chore> => {
    try {
      const response = await apiClient.post('/chores/', choreData);
      return response.data;
    } catch (error) {
      console.error('Failed to create chore:', error);
      throw error;
    }
  },

  // Update an existing chore (parent only)
  updateChore: async (choreId: number, choreData: {
    title?: string;
    description?: string;
    reward?: number;
    is_range_reward?: boolean;
    min_reward?: number;
    max_reward?: number;
    assigned_to_id?: number;
    is_recurring?: boolean;
    cooldown_days?: number;
  }): Promise<Chore> => {
    try {
      const response = await apiClient.put(`/chores/${choreId}`, choreData);
      return response.data;
    } catch (error) {
      console.error('Failed to update chore:', error);
      throw error;
    }
  },

  // Disable a chore (parent only)
  disableChore: async (choreId: number): Promise<Chore> => {
    try {
      const response = await apiClient.post(`/chores/${choreId}/disable`);
      return response.data;
    } catch (error) {
      console.error('Failed to disable chore:', error);
      throw error;
    }
  },

  // Enable a chore (parent only)
  enableChore: async (choreId: number): Promise<Chore> => {
    try {
      const response = await apiClient.post(`/chores/${choreId}/enable`);
      return response.data;
    } catch (error) {
      console.error('Failed to enable chore:', error);
      throw error;
    }
  },

  // Delete a chore (parent only)
  deleteChore: async (choreId: number): Promise<void> => {
    try {
      await apiClient.delete(`/chores/${choreId}`);
    } catch (error) {
      console.error('Failed to delete chore:', error);
      throw error;
    }
  },

};