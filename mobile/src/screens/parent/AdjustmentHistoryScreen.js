import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRoute } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { adjustmentService } from '../../services/adjustmentService';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const AdjustmentHistoryScreen = () => {
  const route = useRoute();
  const { child } = route.params || {};
  
  const [adjustments, setAdjustments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  
  const ITEMS_PER_PAGE = 20;

  const fetchAdjustments = useCallback(async (isRefresh = false, skip = 0) => {
    if (!child?.id) return;
    
    try {
      if (isRefresh) {
        setRefreshing(true);
        setError(null);
      } else if (skip === 0) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }
      
      const result = await adjustmentService.getChildAdjustments(
        child.id,
        ITEMS_PER_PAGE,
        skip
      );
      
      if (result.success) {
        if (isRefresh || skip === 0) {
          setAdjustments(result.data);
        } else {
          setAdjustments(prev => [...prev, ...result.data]);
        }
        
        // Check if there are more items to load
        setHasMore(result.data.length === ITEMS_PER_PAGE);
      } else {
        setError(result.error);
      }
    } catch (error) {
      console.error('Error fetching adjustments:', error);
      setError('Failed to load adjustment history');
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [child?.id]);

  useEffect(() => {
    fetchAdjustments();
  }, [fetchAdjustments]);

  const handleRefresh = () => {
    fetchAdjustments(true);
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      fetchAdjustments(false, adjustments.length);
    }
  };

  const renderAdjustmentItem = ({ item }) => {
    const formatted = adjustmentService.formatAdjustment(item);
    const isPositive = item.amount >= 0;
    
    return (
      <View style={styles.adjustmentCard}>
        <View style={styles.adjustmentHeader}>
          <View style={[styles.iconContainer, isPositive ? styles.positiveIcon : styles.negativeIcon]}>
            <Icon 
              name={isPositive ? 'add-circle' : 'remove-circle'} 
              size={24} 
              color={isPositive ? colors.success : colors.error} 
            />
          </View>
          <View style={styles.adjustmentInfo}>
            <Text style={styles.adjustmentReason}>{item.reason}</Text>
            <Text style={styles.adjustmentDate}>
              {formatted.date} at {formatted.time}
            </Text>
          </View>
          <Text style={[styles.adjustmentAmount, { color: formatted.color }]}>
            {formatted.displayAmount}
          </Text>
        </View>
      </View>
    );
  };

  const renderFooter = () => {
    if (!loadingMore) return null;
    
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color={colors.primary} />
      </View>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="history" size={80} color={colors.textSecondary} />
      <Text style={styles.emptyTitle}>No Adjustments Yet</Text>
      <Text style={styles.emptySubtitle}>
        Balance adjustments will appear here
      </Text>
    </View>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <Text style={styles.headerTitle}>Adjustment History</Text>
      <Text style={styles.headerSubtitle}>
        for {child?.username || 'Unknown'}
      </Text>
    </View>
  );

  if (loading && !refreshing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  if (error && adjustments.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="error-outline" size={60} color={colors.error} />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={adjustments}
        renderItem={renderAdjustmentItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={[colors.primary]}
          />
        }
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmptyState}
        ListFooterComponent={renderFooter}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  errorText: {
    ...typography.body1,
    color: colors.error,
    textAlign: 'center',
    marginTop: 16,
  },
  listContent: {
    flexGrow: 1,
    paddingBottom: 20,
  },
  header: {
    padding: 16,
    backgroundColor: colors.surface,
    marginBottom: 8,
  },
  headerTitle: {
    ...typography.h2,
    color: colors.text,
    marginBottom: 4,
  },
  headerSubtitle: {
    ...typography.body2,
    color: colors.textSecondary,
  },
  adjustmentCard: {
    backgroundColor: colors.surface,
    marginHorizontal: 16,
    marginVertical: 4,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  adjustmentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  positiveIcon: {
    backgroundColor: colors.successLight,
  },
  negativeIcon: {
    backgroundColor: colors.errorLight,
  },
  adjustmentInfo: {
    flex: 1,
  },
  adjustmentReason: {
    ...typography.body1,
    color: colors.text,
    marginBottom: 4,
  },
  adjustmentDate: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  adjustmentAmount: {
    ...typography.h3,
    fontWeight: 'bold',
  },
  footerLoader: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingTop: 100,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    ...typography.body1,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});

export default AdjustmentHistoryScreen;