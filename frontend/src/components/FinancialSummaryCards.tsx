import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { reportsAPI, formatCurrency, AllowanceSummaryResponse } from '@/api/reports';

interface FinancialSummaryCardsProps {
  onViewReports?: () => void;
  refreshKey?: number;
}

export const FinancialSummaryCards: React.FC<FinancialSummaryCardsProps> = ({ 
  onViewReports,
  refreshKey = 0 
}) => {
  const [summaryData, setSummaryData] = useState<AllowanceSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFinancialSummary();
  }, [refreshKey]);

  const fetchFinancialSummary = async () => {
    try {
      setError(null);
      const data = await reportsAPI.getAllowanceSummary();
      setSummaryData(data);
    } catch (err) {
      console.error('Failed to fetch financial summary:', err);
      setError('Unable to load financial data');
    } finally {
      setLoading(false);
    }
  };

  const getChildrenWithBalances = () => {
    if (!summaryData) return [];
    return summaryData.child_summaries.filter(child => child.balance_due > 0);
  };

  const getPendingChoresTotalValue = () => {
    if (!summaryData) return 0;
    return summaryData.child_summaries.reduce(
      (total, child) => total + child.pending_chores_value, 
      0
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color="#2196f3" />
        <Text style={styles.loadingText}>Loading financial summary...</Text>
      </View>
    );
  }

  if (error || !summaryData) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Unable to load financial summary</Text>
        <TouchableOpacity style={styles.retryButton} onPress={fetchFinancialSummary}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const { family_summary } = summaryData;
  const childrenWithBalances = getChildrenWithBalances();
  const pendingValue = getPendingChoresTotalValue();

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Family Financial Summary</Text>
        {onViewReports && (
          <TouchableOpacity style={styles.viewReportsButton} onPress={onViewReports}>
            <Text style={styles.viewReportsText}>View Full Report</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.metricsContainer}>
        {/* Primary Financial Metrics */}
        <View style={styles.primaryMetrics}>
          <View style={[styles.metricCard, styles.balanceCard]}>
            <Text style={styles.primaryAmount}>{formatCurrency(family_summary.total_balance_due)}</Text>
            <Text style={styles.primaryLabel}>Total Balance Due</Text>
            <Text style={styles.metricSubtext}>
              {childrenWithBalances.length} of {family_summary.total_children} children have balances
            </Text>
          </View>
        </View>

        {/* Secondary Metrics Row */}
        <View style={styles.secondaryMetrics}>
          <View style={styles.smallMetricCard}>
            <Text style={[styles.secondaryAmount, styles.earningsAmount]}>
              {formatCurrency(family_summary.total_earned)}
            </Text>
            <Text style={styles.secondaryLabel}>Total Earned</Text>
          </View>

          <View style={styles.smallMetricCard}>
            <Text style={[
              styles.secondaryAmount, 
              family_summary.total_adjustments >= 0 ? styles.positiveAmount : styles.negativeAmount
            ]}>
              {formatCurrency(family_summary.total_adjustments)}
            </Text>
            <Text style={styles.secondaryLabel}>Adjustments</Text>
          </View>

          {pendingValue > 0 && (
            <View style={styles.smallMetricCard}>
              <Text style={[styles.secondaryAmount, styles.pendingAmount]}>
                {formatCurrency(pendingValue)}
              </Text>
              <Text style={styles.secondaryLabel}>Pending Approval</Text>
            </View>
          )}
        </View>

        {/* Children with Balances */}
        {childrenWithBalances.length > 0 && (
          <View style={styles.childrenBalancesContainer}>
            <Text style={styles.childrenBalancesTitle}>Balances Due:</Text>
            <View style={styles.childrenBalancesList}>
              {childrenWithBalances.map((child) => (
                <View key={child.id} style={styles.childBalanceItem}>
                  <Text style={styles.childBalanceName}>{child.username}</Text>
                  <Text style={styles.childBalanceAmount}>
                    {formatCurrency(child.balance_due)}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Quick Stats */}
        <View style={styles.quickStats}>
          <View style={styles.quickStat}>
            <Text style={styles.quickStatValue}>{family_summary.total_completed_chores}</Text>
            <Text style={styles.quickStatLabel}>Chores Completed</Text>
          </View>
          <View style={styles.quickStat}>
            <Text style={styles.quickStatValue}>{family_summary.total_children}</Text>
            <Text style={styles.quickStatLabel}>Children</Text>
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  viewReportsButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#2196f3',
    borderRadius: 6,
  },
  viewReportsText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  loadingContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    margin: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  loadingText: {
    marginTop: 8,
    fontSize: 14,
    color: '#666',
  },
  errorContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  errorText: {
    fontSize: 14,
    color: '#f44336',
    textAlign: 'center',
    marginBottom: 12,
  },
  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#2196f3',
    borderRadius: 6,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  metricsContainer: {
    gap: 12,
  },
  primaryMetrics: {
    alignItems: 'center',
  },
  metricCard: {
    alignItems: 'center',
    padding: 16,
    borderRadius: 8,
    minWidth: '100%',
  },
  balanceCard: {
    backgroundColor: '#e3f2fd',
    borderWidth: 1,
    borderColor: '#2196f3',
  },
  primaryAmount: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2196f3',
    marginBottom: 4,
  },
  primaryLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  metricSubtext: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  secondaryMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 8,
  },
  smallMetricCard: {
    flex: 1,
    minWidth: 80,
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  secondaryAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  secondaryLabel: {
    fontSize: 11,
    color: '#666',
    textAlign: 'center',
  },
  earningsAmount: {
    color: '#4caf50',
  },
  positiveAmount: {
    color: '#4caf50',
  },
  negativeAmount: {
    color: '#f44336',
  },
  pendingAmount: {
    color: '#ff9800',
  },
  childrenBalancesContainer: {
    marginTop: 8,
    padding: 12,
    backgroundColor: '#fff3e0',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ffcc02',
  },
  childrenBalancesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  childrenBalancesList: {
    gap: 4,
  },
  childBalanceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  childBalanceName: {
    fontSize: 13,
    color: '#1a1a1a',
  },
  childBalanceAmount: {
    fontSize: 13,
    fontWeight: '600',
    color: '#ff9800',
  },
  quickStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 8,
  },
  quickStat: {
    alignItems: 'center',
  },
  quickStatValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
  },
  quickStatLabel: {
    fontSize: 11,
    color: '#999',
    marginTop: 2,
  },
});

export default FinancialSummaryCards;