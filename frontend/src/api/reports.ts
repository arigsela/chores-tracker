import { apiClient } from './client';

// Reports API types
export interface FamilyFinancialSummary {
  total_children: number;
  total_earned: number;
  total_adjustments: number;
  total_balance_due: number;
  total_completed_chores: number;
  period_start?: string;
  period_end?: string;
}

export interface ChildAllowanceSummary {
  id: number;
  username: string;
  completed_chores: number;
  total_earned: number;
  total_adjustments: number;
  paid_out: number;
  balance_due: number;
  pending_chores_value: number;
  last_activity_date?: string;
}

export interface AllowanceSummaryResponse {
  family_summary: FamilyFinancialSummary;
  child_summaries: ChildAllowanceSummary[];
}

export interface ExportResponse {
  content: string;
  content_type: string;
  filename: string;
}

export interface RewardHistoryItem {
  type: 'chore_earning' | 'adjustment';
  date: string;
  amount: number;
  description: string;
  chore_id?: number;
  chore_title?: string;
  adjustment_id?: number;
  reason?: string;
}

export const reportsAPI = {
  /**
   * Get comprehensive allowance summary for the family
   */
  getAllowanceSummary: async (params?: {
    date_from?: string;
    date_to?: string;
    child_id?: number;
  }): Promise<AllowanceSummaryResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.date_from) searchParams.append('date_from', params.date_from);
    if (params?.date_to) searchParams.append('date_to', params.date_to);
    if (params?.child_id) searchParams.append('child_id', params.child_id.toString());
    
    const response = await apiClient.get(`/reports/allowance-summary?${searchParams.toString()}`);
    return response.data;
  },

  /**
   * Export allowance summary data
   */
  exportAllowanceSummary: async (params?: {
    format?: 'csv' | 'json';
    date_from?: string;
    date_to?: string;
    child_id?: number;
  }): Promise<ExportResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.format) searchParams.append('format', params.format);
    if (params?.date_from) searchParams.append('date_from', params.date_from);
    if (params?.date_to) searchParams.append('date_to', params.date_to);
    if (params?.child_id) searchParams.append('child_id', params.child_id.toString());
    
    const response = await apiClient.get(`/reports/export/allowance-summary?${searchParams.toString()}`);
    return response.data;
  },

  /**
   * Get reward history for a specific child
   */
  getRewardHistory: async (
    childId: number,
    params?: {
      date_from?: string;
      date_to?: string;
      limit?: number;
    }
  ): Promise<RewardHistoryItem[]> => {
    const searchParams = new URLSearchParams();
    if (params?.date_from) searchParams.append('date_from', params.date_from);
    if (params?.date_to) searchParams.append('date_to', params.date_to);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    
    const response = await apiClient.get(`/reports/reward-history/${childId}?${searchParams.toString()}`);
    return response.data;
  },
};

// Helper functions for display
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount);
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};