import { apiClient } from './client';

// Statistics API types
export interface WeeklyDataPoint {
  week_start: string;
  week_end: string;
  completed_chores: number;
  total_earned: number;
  total_adjustments: number;
  net_amount: number;
  active_children: number;
  average_per_chore: number;
}

export interface WeeklySummary {
  total_chores: number;
  total_earned: number;
  total_adjustments: number;
  average_per_week: number;
  trend_direction: 'increasing' | 'decreasing' | 'stable';
}

export interface WeeklyStatsResponse {
  weeks_analyzed: number;
  weekly_data: WeeklyDataPoint[];
  summary: WeeklySummary;
}

export interface MonthlyDataPoint {
  month: string;
  year: number;
  month_number: number;
  completed_chores: number;
  total_earned: number;
  total_adjustments: number;
  net_amount: number;
  active_children: number;
  average_per_chore: number;
}

export interface MonthlySummary {
  total_chores: number;
  total_earned: number;
  total_adjustments: number;
  average_per_month: number;
  trend_direction: 'increasing' | 'decreasing' | 'stable';
}

export interface MonthlyStatsResponse {
  months_analyzed: number;
  monthly_data: MonthlyDataPoint[];
  summary: MonthlySummary;
}

export interface TrendData {
  direction: 'increasing' | 'decreasing' | 'stable';
  growth_rate: number;
  consistency_score: number;
}

export interface TrendAnalysisResponse {
  period: 'weekly' | 'monthly';
  periods_analyzed: number;
  chore_completion_trend: TrendData;
  earnings_trend: TrendData;
  insights: string[];
  data_points: any[];
}

export const statisticsAPI = {
  /**
   * Get weekly statistics for family chore completion
   */
  getWeeklyStats: async (params?: {
    weeks_back?: number;
    child_id?: number;
  }): Promise<WeeklyStatsResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.weeks_back) searchParams.append('weeks_back', params.weeks_back.toString());
    if (params?.child_id) searchParams.append('child_id', params.child_id.toString());
    
    const response = await apiClient.get(`/statistics/weekly-summary?${searchParams.toString()}`);
    return response.data;
  },

  /**
   * Get monthly statistics for family chore completion
   */
  getMonthlyStats: async (params?: {
    months_back?: number;
    child_id?: number;
  }): Promise<MonthlyStatsResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.months_back) searchParams.append('months_back', params.months_back.toString());
    if (params?.child_id) searchParams.append('child_id', params.child_id.toString());
    
    const response = await apiClient.get(`/statistics/monthly-summary?${searchParams.toString()}`);
    return response.data;
  },

  /**
   * Get trend analysis (simplified version - commenting out until backend is fixed)
   */
  // getTrendAnalysis: async (params?: {
  //   period?: 'weekly' | 'monthly';
  //   child_id?: number;
  // }): Promise<TrendAnalysisResponse> => {
  //   const searchParams = new URLSearchParams();
  //   if (params?.period) searchParams.append('period', params.period);
  //   if (params?.child_id) searchParams.append('child_id', params.child_id.toString());
    
  //   const response = await apiClient.get(`/statistics/trends?${searchParams.toString()}`);
  //   return response.data;
  // },
};

// Helper functions for display
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount);
};

export const formatPercentage = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
};

export const formatWeekRange = (startDate: string, endDate: string): string => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  const startMonth = start.toLocaleDateString('en-US', { month: 'short' });
  const endMonth = end.toLocaleDateString('en-US', { month: 'short' });
  
  if (startMonth === endMonth) {
    return `${startMonth} ${start.getDate()}-${end.getDate()}`;
  }
  
  return `${startMonth} ${start.getDate()} - ${endMonth} ${end.getDate()}`;
};

export const getTrendIcon = (direction: string): string => {
  switch (direction) {
    case 'increasing': return '📈';
    case 'decreasing': return '📉';
    case 'stable': return '📊';
    default: return '📊';
  }
};

export const getTrendColor = (direction: string): string => {
  switch (direction) {
    case 'increasing': return '#4caf50'; // Green
    case 'decreasing': return '#f44336'; // Red
    case 'stable': return '#2196f3'; // Blue
    default: return '#666';
  }
};

export const calculateWeekOverWeekChange = (data: WeeklyDataPoint[]): number => {
  if (data.length < 2) return 0;
  
  const current = data[0]?.completed_chores || 0;
  const previous = data[1]?.completed_chores || 0;
  
  if (previous === 0) return current > 0 ? 100 : 0;
  
  return ((current - previous) / previous) * 100;
};

export const calculateMonthOverMonthChange = (data: MonthlyDataPoint[]): number => {
  if (data.length < 2) return 0;
  
  const current = data[0]?.completed_chores || 0;
  const previous = data[1]?.completed_chores || 0;
  
  if (previous === 0) return current > 0 ? 100 : 0;
  
  return ((current - previous) / previous) * 100;
};