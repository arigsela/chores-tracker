import apiClient from './client';

export interface Adjustment {
  id: number;
  child_id: number;
  parent_id: number;
  amount: string; // Decimal string from backend
  reason: string;
  created_at: string;
}

export interface AdjustmentCreate {
  child_id: number;
  amount: number;
  reason: string;
}

export interface AdjustmentTotal {
  child_id: number;
  total_adjustments: string; // Decimal string from backend
  currency: string;
}

export const adjustmentAPI = {
  // Create a new adjustment (parent only)
  createAdjustment: async (adjustmentData: AdjustmentCreate): Promise<Adjustment> => {
    try {
      const response = await apiClient.post('/adjustments/', adjustmentData);
      return response.data;
    } catch (error) {
      console.error('Failed to create adjustment:', error);
      throw error;
    }
  },

  // Get adjustments for a specific child (parent only)
  getChildAdjustments: async (
    childId: number,
    skip: number = 0,
    limit: number = 100
  ): Promise<Adjustment[]> => {
    try {
      const response = await apiClient.get(`/adjustments/child/${childId}`, {
        params: { skip, limit },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch child adjustments:', error);
      throw error;
    }
  },

  // Get total adjustments for a specific child (parent only)
  getChildAdjustmentTotal: async (childId: number): Promise<AdjustmentTotal> => {
    try {
      const response = await apiClient.get(`/adjustments/total/${childId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch adjustment total:', error);
      throw error;
    }
  },
};