import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Activity, activitiesAPI, ActivityListResponse } from '../api/activities';
import { ActivityCard } from './ActivityCard';

interface ActivityFeedProps {
  limit?: number;
  showHeader?: boolean;
  onActivityPress?: (activity: Activity) => void;
  refreshKey?: number; // Used to trigger external refreshes
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ 
  limit = 20,
  showHeader = true,
  onActivityPress,
  refreshKey = 0
}) => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchActivities = useCallback(async (offset = 0, isRefresh = false) => {
    try {
      setError(null);
      
      const response: ActivityListResponse = await activitiesAPI.getRecentActivities({
        limit,
        offset,
      });

      if (offset === 0) {
        setActivities(response.activities || []);
      } else {
        setActivities(prev => [...prev, ...(response.activities || [])]);
      }
      
      setHasMore(response.has_more);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
      setError('Failed to load recent activities');
      if (offset === 0) {
        setActivities([]);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities, refreshKey]);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    fetchActivities(0, true);
  }, [fetchActivities]);

  const handleLoadMore = useCallback(() => {
    if (!loadingMore && hasMore && (activities?.length || 0) > 0) {
      setLoadingMore(true);
      fetchActivities(activities?.length || 0);
    }
  }, [loadingMore, hasMore, activities?.length, fetchActivities]);

  const handleActivityPress = (activity: Activity) => {
    if (onActivityPress) {
      onActivityPress(activity);
    } else {
      // Default behavior: show activity details
      const details = [];
      if (activity.activity_data?.chore_title) {
        details.push(`Chore: ${activity.activity_data.chore_title}`);
      }
      if (activity.activity_data?.reward_amount !== undefined) {
        details.push(`Amount: $${activity.activity_data.reward_amount.toFixed(2)}`);
      }
      if (activity.activity_data?.rejection_reason) {
        details.push(`Reason: ${activity.activity_data.rejection_reason}`);
      }

      Alert.alert(
        'Activity Details',
        details.length > 0 ? details.join('\n\n') : activity.description,
        [{ text: 'OK' }]
      );
    }
  };

  const renderActivityCard = ({ item }: { item: Activity }) => (
    <ActivityCard
      activity={item}
      onPress={() => handleActivityPress(item)}
    />
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Text style={styles.emptyIcon}>📋</Text>
      <Text style={styles.emptyTitle}>No Recent Activity</Text>
      <Text style={styles.emptySubtitle}>
        Activity will appear here when chores are completed, approved, or created
      </Text>
    </View>
  );

  const renderErrorState = () => (
    <View style={styles.errorState}>
      <Text style={styles.errorIcon}>⚠️</Text>
      <Text style={styles.errorTitle}>Unable to Load Activities</Text>
      <Text style={styles.errorSubtitle}>{error}</Text>
      <TouchableOpacity style={styles.retryButton} onPress={() => fetchActivities()}>
        <Text style={styles.retryButtonText}>Try Again</Text>
      </TouchableOpacity>
    </View>
  );

  const renderLoadingFooter = () => {
    if (!loadingMore) return null;
    
    return (
      <View style={styles.loadingFooter}>
        <ActivityIndicator size="small" color="#2196f3" />
        <Text style={styles.loadingText}>Loading more activities...</Text>
      </View>
    );
  };

  if (loading && (activities?.length || 0) === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
        <Text style={styles.loadingText}>Loading recent activities...</Text>
      </View>
    );
  }

  if (error && (activities?.length || 0) === 0) {
    return renderErrorState();
  }

  return (
    <View style={styles.container}>
      {showHeader && (
        <View style={styles.header}>
          <Text style={styles.title}>Recent Activity</Text>
          {(activities?.length || 0) > 0 && (
            <Text style={styles.subtitle}>
              {activities?.length || 0} recent {(activities?.length || 0) === 1 ? 'activity' : 'activities'}
            </Text>
          )}
        </View>
      )}
      
      <FlatList
        data={activities || []}
        renderItem={renderActivityCard}
        keyExtractor={(item) => `activity-${item.id}`}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={['#2196f3']}
            tintColor="#2196f3"
          />
        }
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListEmptyComponent={renderEmptyState}
        ListFooterComponent={renderLoadingFooter}
        contentContainerStyle={(activities?.length || 0) === 0 ? styles.emptyContainer : styles.listContainer}
        scrollEnabled={true}
        nestedScrollEnabled={true}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#f8f9fa',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  emptyContainer: {
    flexGrow: 1,
  },
  listContainer: {
    paddingBottom: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    lineHeight: 20,
  },
  errorState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#f44336',
    marginBottom: 8,
    textAlign: 'center',
  },
  errorSubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: '#2196f3',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  loadingFooter: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
  },
});

export default ActivityFeed;