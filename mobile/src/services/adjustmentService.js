import apiClient from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';
import { colors } from '../styles/colors';

export const adjustmentService = {
  async createAdjustment(childId, amount, reason) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.ADJUSTMENTS.CREATE, {
        child_id: childId,
        amount: parseFloat(amount),
        reason: reason.trim(),
      });
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      
      // Handle specific error cases
      if (error.response?.status === 400 && errorDetail?.includes('negative balance')) {
        return {
          success: false,
          error: 'This adjustment would result in a negative balance',
        };
      }
      
      return {
        success: false,
        error: errorDetail || 'Failed to create adjustment',
      };
    }
  },
  
  async getChildAdjustments(childId, limit = 20, skip = 0) {
    try {
      const response = await apiClient.get(
        API_ENDPOINTS.ADJUSTMENTS.LIST_BY_CHILD(childId),
        {
          params: { limit, skip },
        }
      );
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch adjustments',
        data: [],
      };
    }
  },
  
  // Helper to format adjustment display
  formatAdjustment(adjustment) {
    const sign = adjustment.amount >= 0 ? '+' : '';
    const color = adjustment.amount >= 0 ? colors.success : colors.error;
    
    return {
      displayAmount: `${sign}$${Math.abs(adjustment.amount).toFixed(2)}`,
      color,
      date: new Date(adjustment.created_at).toLocaleDateString(),
      time: new Date(adjustment.created_at).toLocaleTimeString(),
    };
  },
};