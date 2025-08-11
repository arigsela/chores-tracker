import apiClient from './client';

export interface User {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  is_parent: boolean;
  parent_id: number | null;
}

export interface ChildWithChores extends User {
  chores?: any[]; // Chores are optional and come from eager loading
}

export interface ChildAllowanceSummary {
  id: number;
  username: string;
  completed_chores: number;
  total_earned: number;
  total_adjustments: number;
  paid_out: number;
  balance_due: number;
}

export const usersAPI = {
  // Get current user info
  getMe: async (): Promise<User> => {
    try {
      const response = await apiClient.get('/users/me');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      throw error;
    }
  },

  // Get children for current parent
  getMyChildren: async (): Promise<ChildWithChores[]> => {
    try {
      const response = await apiClient.get('/users/my-children');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch children:', error);
      throw error;
    }
  },

  // Get allowance summary for all children
  getAllowanceSummary: async (): Promise<ChildAllowanceSummary[]> => {
    try {
      const response = await apiClient.get('/users/allowance-summary');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch allowance summary:', error);
      throw error;
    }
  },

  // Create a new child user
  createChildAccount: async (childData: {
    username: string;
    password: string;
  }): Promise<User> => {
    try {
      // Get the parent's ID first
      const parentResponse = await apiClient.get('/users/me');
      const parentId = parentResponse.data.id;
      
      // Create child account using form data
      const formData = new URLSearchParams();
      formData.append('username', childData.username);
      formData.append('password', childData.password);
      formData.append('is_parent', 'false');
      formData.append('parent_id', parentId.toString());
      
      const response = await apiClient.post('/users/register', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to create child account:', error);
      throw error;
    }
  },

  // Reset child's password
  resetChildPassword: async (childId: number, newPassword: string): Promise<User> => {
    try {
      const response = await apiClient.post(`/users/children/${childId}/reset-password`, {
        new_password: newPassword,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to reset password:', error);
      throw error;
    }
  },
};