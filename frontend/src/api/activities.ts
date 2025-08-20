import { apiClient } from './client';

// Activity types
export interface Activity {
  id: number;
  user_id: number;
  activity_type: string;
  description: string;
  target_user_id?: number;
  activity_data: {
    chore_id?: number;
    chore_title?: string;
    reward_amount?: number;
    rejection_reason?: string;
    adjustment_id?: number;
    amount?: number;
    reason?: string;
    adjustment_type?: string;
  };
  created_at: string;
  user?: {
    id: number;
    username: string;
    is_parent: boolean;
    email?: string;
    is_active: boolean;
    parent_id?: number;
  };
  target_user?: {
    id: number;
    username: string;
    is_parent: boolean;
    email?: string;
    is_active: boolean;
    parent_id?: number;
  };
}

export interface ActivityListResponse {
  activities: Activity[];
  total_count?: number;
  has_more: boolean;
}

export interface ActivitySummaryResponse {
  activity_counts: Record<string, number>;
  total_activities: number;
  period_days: number;
}

export interface ActivityTypesResponse {
  activity_types: string[];
  descriptions: Record<string, string>;
}

// Activity type constants
export const ActivityTypes = {
  CHORE_COMPLETED: 'chore_completed',
  CHORE_APPROVED: 'chore_approved',
  CHORE_REJECTED: 'chore_rejected',
  CHORE_CREATED: 'chore_created',
  ADJUSTMENT_APPLIED: 'adjustment_applied',
} as const;

export const activitiesAPI = {
  /**
   * Get recent activities for the current user
   */
  getRecentActivities: async (params?: {
    limit?: number;
    offset?: number;
    activity_type?: string;
  }): Promise<ActivityListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.activity_type) searchParams.append('activity_type', params.activity_type);
    
    const response = await apiClient.get(`/activities/recent?${searchParams.toString()}`);
    return response.data;
  },

  /**
   * Get activity summary statistics
   */
  getActivitySummary: async (daysBack = 30): Promise<ActivitySummaryResponse> => {
    const response = await apiClient.get(`/activities/summary?days_back=${daysBack}`);
    return response.data;
  },

  /**
   * Get available activity types and descriptions
   */
  getActivityTypes: async (): Promise<ActivityTypesResponse> => {
    const response = await apiClient.get('/activities/types');
    return response.data;
  },

  /**
   * Get a specific activity by ID
   */
  getActivity: async (activityId: number): Promise<Activity> => {
    const response = await apiClient.get(`/activities/${activityId}`);
    return response.data;
  },
};

// Helper functions for activity display
export const getActivityIcon = (activityType: string): string => {
  switch (activityType) {
    case ActivityTypes.CHORE_COMPLETED:
      return '✅';
    case ActivityTypes.CHORE_APPROVED:
      return '👍';
    case ActivityTypes.CHORE_REJECTED:
      return '❌';
    case ActivityTypes.CHORE_CREATED:
      return '📝';
    case ActivityTypes.ADJUSTMENT_APPLIED:
      return '💰';
    default:
      return '📋';
  }
};

export const getActivityColor = (activityType: string): string => {
  switch (activityType) {
    case ActivityTypes.CHORE_COMPLETED:
      return '#4CAF50'; // Green
    case ActivityTypes.CHORE_APPROVED:
      return '#2196F3'; // Blue
    case ActivityTypes.CHORE_REJECTED:
      return '#F44336'; // Red
    case ActivityTypes.CHORE_CREATED:
      return '#FF9800'; // Orange
    case ActivityTypes.ADJUSTMENT_APPLIED:
      return '#9C27B0'; // Purple
    default:
      return '#757575'; // Gray
  }
};

export const formatActivityTime = (timestamp: string): string => {
  const now = new Date();
  const activityDate = new Date(timestamp);
  const diffInMinutes = Math.floor((now.getTime() - activityDate.getTime()) / (1000 * 60));
  
  if (diffInMinutes < 1) {
    return 'Just now';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  } else if (diffInMinutes < 1440) { // Less than 24 hours
    const hours = Math.floor(diffInMinutes / 60);
    return `${hours}h ago`;
  } else if (diffInMinutes < 10080) { // Less than 7 days
    const days = Math.floor(diffInMinutes / 1440);
    return `${days}d ago`;
  } else {
    return activityDate.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: activityDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  }
};