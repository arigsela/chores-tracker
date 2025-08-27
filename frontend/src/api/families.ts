import { apiClient } from './client';

export interface Family {
  id: number;
  name?: string;
  invite_code: string;
  invite_code_expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface FamilyMember {
  id: number;
  username: string;
  email?: string;
  is_parent: boolean;
  is_active: boolean;
  parent_id?: number;
  joined_at: string;
}

export interface FamilyMembers {
  family_id: number;
  family_name?: string;
  total_members: number;
  parents: FamilyMember[];
  children: FamilyMember[];
}

export interface FamilyContext {
  has_family: boolean;
  family?: Family;
  role: 'parent' | 'child' | 'no_family';
  can_invite: boolean;
  can_manage: boolean;
}

export interface FamilyStats {
  family_id: number;
  name?: string;
  invite_code: string;
  created_at: string;
  total_members: number;
  total_parents: number;
  total_children: number;
  total_chores: number;
  completed_chores: number;
  approved_chores: number;
  total_rewards_earned: number;
}

export interface InviteCodeResponse {
  invite_code: string;
  expires_at?: string;
  family_name?: string;
}

export interface JoinFamilyResponse {
  success: boolean;
  family_id: number;
  family_name?: string;
  message: string;
}

// Family API functions
export const familyAPI = {
  // Get user's family context
  getFamilyContext: async (): Promise<FamilyContext> => {
    const response = await apiClient.get('/families/context');
    return response.data;
  },

  // Create new family
  createFamily: async (name?: string): Promise<Family> => {
    const response = await apiClient.post('/families/create', { name });
    return response.data;
  },

  // Join family with invite code
  joinFamily: async (inviteCode: string): Promise<JoinFamilyResponse> => {
    const response = await apiClient.post('/families/join', { invite_code: inviteCode });
    return response.data;
  },

  // Get family members
  getFamilyMembers: async (): Promise<FamilyMembers> => {
    const response = await apiClient.get('/families/members');
    return response.data;
  },

  // Get family statistics
  getFamilyStats: async (): Promise<FamilyStats> => {
    const response = await apiClient.get('/families/stats');
    return response.data;
  },

  // Generate new invite code
  generateInviteCode: async (expiresInDays?: number): Promise<InviteCodeResponse> => {
    const response = await apiClient.post('/families/invite-code', 
      expiresInDays ? { expires_in_days: expiresInDays } : {}
    );
    return response.data;
  },

  // Remove family member
  removeFamilyMember: async (userId: number, reason?: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/families/remove-member', { 
      user_id: userId, 
      reason 
    });
    return response.data;
  },

  // Leave current family
  leaveFamily: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.delete('/families/leave');
    return response.data;
  },

  // Clean up expired invite codes
  cleanupInviteCodes: async (): Promise<{ cleaned_count: number; message: string }> => {
    const response = await apiClient.get('/families/cleanup-codes');
    return response.data;
  }
};

export default familyAPI;