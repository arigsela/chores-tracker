import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import {
  statisticsAPI,
  WeeklyStatsResponse,
  MonthlyStatsResponse,
  formatCurrency,
  formatPercentage,
  formatWeekRange,
  getTrendIcon,
  getTrendColor,
  calculateWeekOverWeekChange,
  calculateMonthOverMonthChange,
} from '@/api/statistics';

type ViewMode = 'weekly' | 'monthly';

const { width: screenWidth } = Dimensions.get('window');

export const StatisticsScreen: React.FC = () => {
  const { user } = useAuth();
  const [viewMode, setViewMode] = useState<ViewMode>('weekly');
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStatsResponse | null>(null);
  const [monthlyStats, setMonthlyStats] = useState<MonthlyStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, [viewMode]);

  const fetchStatistics = async () => {
    try {
      setError(null);
      
      if (viewMode === 'weekly') {
        const data = await statisticsAPI.getWeeklyStats({ weeks_back: 8 });
        setWeeklyStats(data);
      } else {
        const data = await statisticsAPI.getMonthlyStats({ months_back: 6 });
        setMonthlyStats(data);
      }
    } catch (err) {
      console.error('[StatisticsScreen] Failed to fetch statistics:', err);
      setError('Failed to load statistics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStatistics();
  };

  const renderModeSelector = () => (
    <View style={styles.modeSelector}>
      <TouchableOpacity
        style={[styles.modeButton, viewMode === 'weekly' && styles.activeModeButton]}
        onPress={() => setViewMode('weekly')}
      >
        <Text style={[styles.modeText, viewMode === 'weekly' && styles.activeModeText]}>
          Weekly View
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.modeButton, viewMode === 'monthly' && styles.activeModeButton]}
        onPress={() => setViewMode('monthly')}
      >
        <Text style={[styles.modeText, viewMode === 'monthly' && styles.activeModeText]}>
          Monthly View
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderSummaryCard = () => {
    const summary = viewMode === 'weekly' ? weeklyStats?.summary : monthlyStats?.summary;
    if (!summary) return null;

    const data = viewMode === 'weekly' ? weeklyStats?.weekly_data || [] : monthlyStats?.monthly_data || [];
    const periodChange = viewMode === 'weekly' 
      ? calculateWeekOverWeekChange(data)
      : calculateMonthOverMonthChange(data);

    const trendColor = getTrendColor(summary.trend_direction);
    const trendIcon = getTrendIcon(summary.trend_direction);

    return (
      <View style={styles.summaryCard}>
        <View style={styles.summaryHeader}>
          <Text style={styles.summaryTitle}>
            {viewMode === 'weekly' ? 'Weekly' : 'Monthly'} Summary
          </Text>
          <View style={[styles.trendIndicator, { backgroundColor: trendColor + '20' }]}>
            <Text style={styles.trendIcon}>{trendIcon}</Text>
            <Text style={[styles.trendText, { color: trendColor }]}>
              {summary.trend_direction}
            </Text>
          </View>
        </View>

        <View style={styles.summaryMetrics}>
          <View style={styles.summaryMetric}>
            <Text style={styles.metricValue}>{summary.total_chores}</Text>
            <Text style={styles.metricLabel}>Total Chores</Text>
          </View>
          
          <View style={styles.summaryMetric}>
            <Text style={[styles.metricValue, styles.earningsValue]}>
              {formatCurrency(summary.total_earned)}
            </Text>
            <Text style={styles.metricLabel}>Total Earned</Text>
          </View>
          
          <View style={styles.summaryMetric}>
            <Text style={[
              styles.metricValue, 
              summary.total_adjustments >= 0 ? styles.positiveValue : styles.negativeValue
            ]}>
              {formatCurrency(summary.total_adjustments)}
            </Text>
            <Text style={styles.metricLabel}>Adjustments</Text>
          </View>
        </View>

        <View style={styles.averageSection}>
          <Text style={styles.averageLabel}>
            Average per {viewMode === 'weekly' ? 'week' : 'month'}:
          </Text>
          <Text style={styles.averageValue}>
            {viewMode === 'weekly' ? summary.average_per_week.toFixed(1) : summary.average_per_month.toFixed(1)} chores
          </Text>
        </View>

        {Math.abs(periodChange) > 0 && (
          <View style={styles.changeIndicator}>
            <Text style={styles.changeLabel}>
              {viewMode === 'weekly' ? 'Week-over-week' : 'Month-over-month'} change:
            </Text>
            <Text style={[
              styles.changeValue,
              { color: periodChange >= 0 ? '#4caf50' : '#f44336' }
            ]}>
              {formatPercentage(periodChange)}
            </Text>
          </View>
        )}
      </View>
    );
  };

  const renderPeriodCard = (item: any, index: number) => {
    const isWeekly = viewMode === 'weekly';
    const title = isWeekly 
      ? formatWeekRange(item.week_start, item.week_end)
      : item.month;

    return (
      <View key={index} style={styles.periodCard}>
        <View style={styles.periodHeader}>
          <Text style={styles.periodTitle}>{title}</Text>
          <View style={styles.periodStats}>
            <Text style={styles.periodChores}>{item.completed_chores} chores</Text>
            <Text style={styles.periodChildren}>
              {item.active_children} active {item.active_children === 1 ? 'child' : 'children'}
            </Text>
          </View>
        </View>

        <View style={styles.periodMetrics}>
          <View style={styles.periodMetric}>
            <Text style={styles.periodMetricLabel}>Earned</Text>
            <Text style={[styles.periodMetricValue, styles.earningsColor]}>
              {formatCurrency(item.total_earned)}
            </Text>
          </View>

          <View style={styles.periodMetric}>
            <Text style={styles.periodMetricLabel}>Adjustments</Text>
            <Text style={[
              styles.periodMetricValue,
              item.total_adjustments >= 0 ? styles.positiveColor : styles.negativeColor
            ]}>
              {formatCurrency(item.total_adjustments)}
            </Text>
          </View>

          <View style={styles.periodMetric}>
            <Text style={styles.periodMetricLabel}>Net Amount</Text>
            <Text style={[styles.periodMetricValue, styles.netAmountColor]}>
              {formatCurrency(item.net_amount)}
            </Text>
          </View>

          <View style={styles.periodMetric}>
            <Text style={styles.periodMetricLabel}>Avg/Chore</Text>
            <Text style={styles.periodMetricValue}>
              {item.completed_chores > 0 ? formatCurrency(item.average_per_chore) : '$0.00'}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  const renderDataList = () => {
    const data = viewMode === 'weekly' ? weeklyStats?.weekly_data : monthlyStats?.monthly_data;
    if (!data || data.length === 0) {
      return (
        <View style={styles.noDataContainer}>
          <Text style={styles.noDataText}>
            No {viewMode} data available for the selected period.
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.dataList}>
        <Text style={styles.dataListTitle}>
          {viewMode === 'weekly' ? 'Weekly' : 'Monthly'} Breakdown
        </Text>
        {data.map((item, index) => renderPeriodCard(item, index))}
      </View>
    );
  };

  if (user?.role !== 'parent') {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Access Denied</Text>
          <Text style={styles.errorText}>Only parents can view statistics.</Text>
        </View>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
        <Text style={styles.loadingText}>Loading statistics...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Unable to Load Statistics</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchStatistics}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          colors={['#2196f3']}
          tintColor="#2196f3"
        />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>Family Statistics</Text>
        <Text style={styles.subtitle}>Track your family's chore completion trends</Text>
      </View>

      {renderModeSelector()}
      {renderSummaryCard()}
      {renderDataList()}
      
      <View style={styles.bottomPadding} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#f44336',
    marginBottom: 8,
    textAlign: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
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
    fontSize: 16,
    fontWeight: '600',
  },
  modeSelector: {
    flexDirection: 'row',
    margin: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  modeButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeModeButton: {
    backgroundColor: '#2196f3',
  },
  modeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  activeModeText: {
    color: '#fff',
  },
  summaryCard: {
    backgroundColor: '#fff',
    margin: 16,
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  trendIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  trendIcon: {
    marginRight: 6,
    fontSize: 16,
  },
  trendText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  summaryMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  summaryMetric: {
    flex: 1,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  earningsValue: {
    color: '#4caf50',
  },
  positiveValue: {
    color: '#4caf50',
  },
  negativeValue: {
    color: '#f44336',
  },
  averageSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    marginBottom: 12,
  },
  averageLabel: {
    fontSize: 14,
    color: '#666',
  },
  averageValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  changeIndicator: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  changeLabel: {
    fontSize: 14,
    color: '#666',
  },
  changeValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  dataList: {
    margin: 16,
  },
  dataListTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  periodCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  periodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  periodTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
    flex: 1,
  },
  periodStats: {
    alignItems: 'flex-end',
  },
  periodChores: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2196f3',
    marginBottom: 2,
  },
  periodChildren: {
    fontSize: 12,
    color: '#666',
  },
  periodMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  },
  periodMetric: {
    minWidth: '22%',
    alignItems: 'center',
    marginBottom: 8,
  },
  periodMetricLabel: {
    fontSize: 10,
    color: '#666',
    marginBottom: 4,
    textAlign: 'center',
  },
  periodMetricValue: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1a1a1a',
    textAlign: 'center',
  },
  earningsColor: {
    color: '#4caf50',
  },
  positiveColor: {
    color: '#4caf50',
  },
  negativeColor: {
    color: '#f44336',
  },
  netAmountColor: {
    color: '#2196f3',
  },
  noDataContainer: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 40,
    borderRadius: 12,
    alignItems: 'center',
  },
  noDataText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  bottomPadding: {
    height: 32,
  },
});