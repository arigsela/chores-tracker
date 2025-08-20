import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import {
  reportsAPI,
  AllowanceSummaryResponse,
  formatCurrency,
  formatDate,
  formatDateTime,
} from '@/api/reports';

export const AllowanceSummaryScreen: React.FC = () => {
  const { user } = useAuth();
  const [summaryData, setSummaryData] = useState<AllowanceSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchAllowanceSummary();
  }, []);

  const fetchAllowanceSummary = async () => {
    try {
      setError(null);
      const data = await reportsAPI.getAllowanceSummary();
      setSummaryData(data);
    } catch (err) {
      console.error('Failed to fetch allowance summary:', err);
      setError('Failed to load allowance summary');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAllowanceSummary();
  };

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      setExporting(true);
      const exportData = await reportsAPI.exportAllowanceSummary({ format });
      
      // For web, create a download link
      const blob = new Blob([exportData.content], { type: exportData.content_type });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = exportData.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      Alert.alert('Success', `Export completed: ${exportData.filename}`);
    } catch (err) {
      console.error('Export failed:', err);
      Alert.alert('Error', 'Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  const renderFamilySummary = () => {
    if (!summaryData) return null;

    const { family_summary } = summaryData;

    return (
      <View style={styles.summaryCard}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Family Financial Summary</Text>
          <View style={styles.periodInfo}>
            {family_summary.period_start && (
              <Text style={styles.periodText}>
                Period: {formatDate(family_summary.period_start)} - {formatDate(family_summary.period_end || '')}
              </Text>
            )}
          </View>
        </View>
        
        <View style={styles.metricsContainer}>
          <View style={styles.metricRow}>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>{family_summary.total_children}</Text>
              <Text style={styles.metricLabel}>Children</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>{family_summary.total_completed_chores}</Text>
              <Text style={styles.metricLabel}>Chores Completed</Text>
            </View>
          </View>
          
          <View style={styles.metricRow}>
            <View style={styles.metric}>
              <Text style={[styles.metricValue, styles.positiveAmount]}>
                {formatCurrency(family_summary.total_earned)}
              </Text>
              <Text style={styles.metricLabel}>Total Earned</Text>
            </View>
            <View style={styles.metric}>
              <Text style={[
                styles.metricValue, 
                family_summary.total_adjustments >= 0 ? styles.positiveAmount : styles.negativeAmount
              ]}>
                {formatCurrency(family_summary.total_adjustments)}
              </Text>
              <Text style={styles.metricLabel}>Adjustments</Text>
            </View>
          </View>
          
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Total Balance Due</Text>
            <Text style={[styles.totalAmount, styles.balanceAmount]}>
              {formatCurrency(family_summary.total_balance_due)}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  const renderChildSummary = (child: any, index: number) => {
    return (
      <View key={child.id} style={styles.childCard}>
        <View style={styles.childHeader}>
          <Text style={styles.childName}>{child.username}</Text>
          {child.last_activity_date && (
            <Text style={styles.lastActivity}>
              Last activity: {formatDateTime(child.last_activity_date)}
            </Text>
          )}
        </View>
        
        <View style={styles.childMetrics}>
          <View style={styles.childMetricRow}>
            <Text style={styles.childMetricLabel}>Completed Chores</Text>
            <Text style={styles.childMetricValue}>{child.completed_chores}</Text>
          </View>
          
          <View style={styles.childMetricRow}>
            <Text style={styles.childMetricLabel}>Total Earned</Text>
            <Text style={[styles.childMetricValue, styles.positiveAmount]}>
              {formatCurrency(child.total_earned)}
            </Text>
          </View>
          
          <View style={styles.childMetricRow}>
            <Text style={styles.childMetricLabel}>Adjustments</Text>
            <Text style={[
              styles.childMetricValue, 
              child.total_adjustments >= 0 ? styles.positiveAmount : styles.negativeAmount
            ]}>
              {formatCurrency(child.total_adjustments)}
            </Text>
          </View>
          
          {child.pending_chores_value > 0 && (
            <View style={styles.childMetricRow}>
              <Text style={styles.childMetricLabel}>Pending Approval</Text>
              <Text style={[styles.childMetricValue, styles.pendingAmount]}>
                {formatCurrency(child.pending_chores_value)}
              </Text>
            </View>
          )}
          
          <View style={[styles.childMetricRow, styles.balanceRow]}>
            <Text style={styles.balanceLabel}>Balance Due</Text>
            <Text style={[styles.balanceAmount, styles.childBalance]}>
              {formatCurrency(child.balance_due)}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  const renderExportButtons = () => {
    return (
      <View style={styles.exportContainer}>
        <Text style={styles.exportTitle}>Export Data</Text>
        <View style={styles.exportButtons}>
          <TouchableOpacity 
            style={[styles.exportButton, styles.csvButton]} 
            onPress={() => handleExport('csv')}
            disabled={exporting}
          >
            <Text style={styles.exportButtonText}>
              {exporting ? 'Exporting...' : 'Export CSV'}
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.exportButton, styles.jsonButton]} 
            onPress={() => handleExport('json')}
            disabled={exporting}
          >
            <Text style={styles.exportButtonText}>
              {exporting ? 'Exporting...' : 'Export JSON'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (user?.role !== 'parent') {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Access Denied</Text>
          <Text style={styles.errorText}>Only parents can view allowance summaries.</Text>
        </View>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
        <Text style={styles.loadingText}>Loading allowance summary...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Unable to Load Summary</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchAllowanceSummary}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (!summaryData) {
    return (
      <View style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>No Data Available</Text>
          <Text style={styles.errorText}>No allowance data found.</Text>
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
        <Text style={styles.title}>Allowance Summary</Text>
        <Text style={styles.subtitle}>Financial overview for your family</Text>
      </View>

      {renderFamilySummary()}
      
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Per-Child Breakdown</Text>
        {summaryData.child_summaries.map((child, index) => renderChildSummary(child, index))}
      </View>

      {renderExportButtons()}
      
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
  cardHeader: {
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  periodInfo: {
    marginBottom: 8,
  },
  periodText: {
    fontSize: 14,
    color: '#666',
  },
  metricsContainer: {
    gap: 16,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    marginHorizontal: 4,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  totalAmount: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  balanceAmount: {
    color: '#2196f3',
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
  section: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  childCard: {
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
  childHeader: {
    marginBottom: 16,
  },
  childName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  lastActivity: {
    fontSize: 12,
    color: '#666',
  },
  childMetrics: {
    gap: 8,
  },
  childMetricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  childMetricLabel: {
    fontSize: 14,
    color: '#666',
  },
  childMetricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  balanceRow: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  balanceLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  childBalance: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  exportContainer: {
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
  exportTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  exportButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  exportButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  csvButton: {
    backgroundColor: '#4caf50',
  },
  jsonButton: {
    backgroundColor: '#2196f3',
  },
  exportButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  bottomPadding: {
    height: 32,
  },
});