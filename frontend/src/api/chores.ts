import apiClient from './client';

/**
 * Assignment mode types for multi-assignment chore system
 */
export type AssignmentMode = 'single' | 'multi_independent' | 'unassigned';

/**
 * Assignment interface - represents the relationship between a chore and an assignee
 */
export interface Assignment {
  id: number;
  chore_id: number;
  assignee_id: number;
  assignee_name?: string;
  is_completed: boolean;
  is_approved: boolean;
  completion_date: string | null;
  approval_date: string | null;
  approval_reward: number | null;
  rejection_reason: string | null;
}

/**
 * Chore interface - updated for multi-assignment support
 */
export interface Chore {
  id: number;
  title: string;
  description: string | null;
  reward: number | null;
  is_range_reward: boolean;
  min_reward: number | null;
  max_reward: number | null;
  cooldown_days: number | null;

  // Multi-assignment fields (NEW)
  assignment_mode: AssignmentMode;
  assignee_ids?: number[];
  assignments?: Assignment[];

  // Legacy single-assignment fields (DEPRECATED - for backward compatibility)
  /** @deprecated Use assignments array instead */
  assigned_to_id?: number | null;
  /** @deprecated Use assignee_ids array instead */
  assignee_id?: number | null;
  /** @deprecated Check assignment.assignee_name instead */
  assigned_to_username?: string;
  /** @deprecated Check assignment.completion_date instead */
  completed_at?: string | null;
  /** @deprecated Check assignment.completion_date instead */
  completion_date?: string | null;
  /** @deprecated Check assignment.approval_date instead */
  approved_at?: string | null;
  /** @deprecated Check assignment.approval_reward instead */
  approval_reward?: number | null;
  /** @deprecated Check assignment.rejection_reason instead */
  rejection_reason?: string | null;
  /** @deprecated Check assignment.is_completed instead */
  is_completed?: boolean;
  /** @deprecated Check assignment.is_approved instead */
  is_approved?: boolean;

  // Standard fields
  created_at: string;
  created_by_id?: number;
  creator_id?: number; // Backend uses this field name
  is_active?: boolean;
  is_disabled?: boolean; // Backend uses this field
  is_recurring: boolean;
  next_available_at?: string | null;
}

/**
 * Response structure for available chores endpoint
 * Separates assigned chores from pool chores
 */
export interface AvailableChoresResponse {
  assigned: Array<{
    chore: Chore;
    assignment: Assignment;
    assignment_id: number;
  }>;
  pool: Array<{
    chore: Chore;
    assignment: Assignment | null;
    assignment_id: number | null;
  }>;
  total_count: number;
}

/**
 * Pending approval item - assignment-level data for parent approval screen
 */
export interface PendingApprovalItem {
  assignment: Assignment;
  assignment_id: number;
  chore: Chore;
  assignee: {
    id: number;
    username: string;
  };
  assignee_name: string;
}

/**
 * Response from completing a chore
 */
export interface CompleteChoreResponse {
  chore: Chore;
  assignment: Assignment;
  message: string;
}

/**
 * Response from approving/rejecting an assignment
 */
export interface AssignmentActionResponse {
  assignment: Assignment;
  chore: Chore;
  message: string;
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

  // Get available chores for child to claim (UPDATED for multi-assignment)
  getAvailableChores: async (): Promise<AvailableChoresResponse> => {
    try {
      const response = await apiClient.get('/chores/available');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch available chores:', error);
      throw error;
    }
  },

  // Complete a chore (UPDATED for multi-assignment response)
  completeChore: async (choreId: number): Promise<CompleteChoreResponse> => {
    try {
      const response = await apiClient.post(`/chores/${choreId}/complete`);
      return response.data;
    } catch (error) {
      console.error('Failed to complete chore:', error);
      throw error;
    }
  },

  // Get chores pending approval (parent only) (UPDATED for assignment-level data)
  getPendingApprovalChores: async (): Promise<PendingApprovalItem[]> => {
    try {
      const response = await apiClient.get('/chores/pending-approval');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch pending approval chores:', error);
      throw error;
    }
  },

  // ===== NEW MULTI-ASSIGNMENT METHODS =====

  /**
   * Approve an assignment (NEW - uses assignment_id instead of chore_id)
   * @param assignmentId - The assignment ID to approve
   * @param rewardValue - Optional custom reward value for range rewards
   */
  approveAssignment: async (assignmentId: number, rewardValue?: number): Promise<AssignmentActionResponse> => {
    try {
      const data: any = {};
      if (rewardValue !== undefined) {
        data.reward_value = rewardValue;
      }
      const response = await apiClient.post(`/assignments/${assignmentId}/approve`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to approve assignment:', error);
      throw error;
    }
  },

  /**
   * Reject an assignment (NEW - uses assignment_id instead of chore_id)
   * @param assignmentId - The assignment ID to reject
   * @param rejectionReason - Reason for rejection (required)
   */
  rejectAssignment: async (assignmentId: number, rejectionReason: string): Promise<AssignmentActionResponse> => {
    try {
      const data = {
        rejection_reason: rejectionReason
      };
      const response = await apiClient.post(`/assignments/${assignmentId}/reject`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to reject assignment:', error);
      throw error;
    }
  },

  // ===== DEPRECATED METHODS (for backward compatibility) =====

  /**
   * @deprecated Use approveAssignment() instead - this method is for backward compatibility only
   */
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

  /**
   * @deprecated Use rejectAssignment() instead - this method is for backward compatibility only
   */
  rejectChore: async (choreId: number, rejectionReason: string): Promise<Chore> => {
    try {
      const data = {
        rejection_reason: rejectionReason
      };
      const response = await apiClient.post(`/chores/${choreId}/reject`, data);
      return response.data;
    } catch (error) {
      console.error('Failed to reject chore:', error);
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

  // Create a new chore (parent only) (UPDATED for multi-assignment)
  createChore: async (choreData: {
    title: string;
    description?: string;
    reward?: number;
    is_range_reward: boolean;
    min_reward?: number;
    max_reward?: number;
    assignment_mode: AssignmentMode;  // NEW: Required for multi-assignment
    assignee_ids: number[];  // NEW: Array instead of single ID
    is_recurring: boolean;
    cooldown_days?: number;
  }): Promise<Chore> => {
    try {
      // Send as JSON directly - axios client already has JSON content-type
      const response = await apiClient.post('/chores', choreData);
      return response.data;
    } catch (error) {
      console.error('Failed to create chore:', error);
      throw error;
    }
  },

  // Update an existing chore (parent only) (UPDATED for multi-assignment)
  updateChore: async (choreId: number, choreData: {
    title?: string;
    description?: string;
    reward?: number;
    is_range_reward?: boolean;
    min_reward?: number;
    max_reward?: number;
    assignment_mode?: AssignmentMode;  // NEW: Optional for updates
    assignee_ids?: number[];  // NEW: Array instead of single ID
    is_recurring?: boolean;
    cooldown_days?: number;
    // Legacy fields (deprecated but kept for backward compatibility)
    assigned_to_id?: number;
    assignee_id?: number;
  }): Promise<Chore> => {
    try {
      // Send as JSON directly - axios client already has JSON content-type
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