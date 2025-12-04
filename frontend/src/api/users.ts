import apiClient from './client';

export interface User {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  is_parent: boolean;
  parent_id: number | null;
}

export interface ChoreAssignmentSummary {
  id: number;
  chore_id: number;
  chore_title: string;
  reward: number;
  is_completed: boolean;
  is_approved: boolean;
}

export interface ChildWithChores extends User {
  chores?: ChoreAssignmentSummary[]; // Chore assignments for this child
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

  // Get all children in the current user's family
  getFamilyChildren: async (): Promise<ChildWithChores[]> => {
    try {
      const response = await apiClient.get('/users/my-family-children');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch family children:', error);
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
      // Create child account using the authenticated endpoint
      // The parent_id will be set automatically from the current user
      const response = await apiClient.post('/users/', {
        username: childData.username,
        password: childData.password,
        is_parent: false,
        // parent_id is automatically set from the authenticated parent
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
      // The API expects just the password string as the body, not an object
      const response = await apiClient.post(
        `/users/children/${childId}/reset-password`, 
        JSON.stringify(newPassword),
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to reset password:', error);
      throw error;
    }
  },
};