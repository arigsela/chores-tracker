import apiClient from './client';

export interface UserBalance {
  balance: number;
  total_earned: number;
  adjustments: number;
  paid_out: number;
  pending_chores_value: number;
}

export const balanceAPI = {
  // Get current user's balance (child only)
  getMyBalance: async (): Promise<UserBalance> => {
    try {
      const response = await apiClient.get('/users/me/balance');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch balance:', error);
      throw error;
    }
  },
};