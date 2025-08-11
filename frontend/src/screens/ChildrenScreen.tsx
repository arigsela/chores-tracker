import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { usersAPI, ChildWithChores, ChildAllowanceSummary } from '../api/users';
import ChildCard from '../components/ChildCard';
import ChildDetailScreen from './ChildDetailScreen';

export const ChildrenScreen: React.FC = () => {
  const [children, setChildren] = useState<ChildWithChores[]>([]);
  const [allowanceSummary, setAllowanceSummary] = useState<ChildAllowanceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedChild, setSelectedChild] = useState<ChildWithChores | null>(null);

  const fetchData = async () => {
    try {
      const [childrenData, summaryData] = await Promise.all([
        usersAPI.getMyChildren(),
        usersAPI.getAllowanceSummary(),
      ]);
      setChildren(childrenData);
      setAllowanceSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch children data:', error);
      Alert.alert('Error', 'Failed to load children data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getTotalOwed = () => {
    return allowanceSummary.reduce((total, child) => total + child.balance_due, 0);
  };

  const getTotalPending = () => {
    return children.reduce((total, child) => {
      const pending = child.chores?.filter(c => 
        (c.is_completed || c.completed_at || c.completion_date) && 
        !c.is_approved && !c.approved_at
      ).length || 0;
      return total + pending;
    }, 0);
  };

  // If a child is selected, show the detail view
  if (selectedChild) {
    return (
      <ChildDetailScreen
        child={selectedChild}
        onBack={() => {
          setSelectedChild(null);
          fetchData(); // Refresh data when returning
        }}
      />
    );
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Summary Section */}
      <View style={styles.summarySection}>
        <Text style={styles.sectionTitle}>Family Overview</Text>
        <View style={styles.summaryCards}>
          <View style={[styles.summaryCard, styles.totalOwedCard]}>
            <Text style={styles.summaryValue}>${getTotalOwed().toFixed(2)}</Text>
            <Text style={styles.summaryLabel}>Total Owed</Text>
          </View>
          <View style={[styles.summaryCard, styles.pendingCard]}>
            <Text style={styles.summaryValue}>{getTotalPending()}</Text>
            <Text style={styles.summaryLabel}>Pending Approvals</Text>
          </View>
        </View>
      </View>

      {/* Children List */}
      <View style={styles.childrenSection}>
        <Text style={styles.sectionTitle}>Children ({children.length})</Text>
        {children.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No children added yet</Text>
            <Text style={styles.emptySubtext}>
              Add children to start managing their chores and allowances
            </Text>
          </View>
        ) : (
          children.map((child) => {
            const summary = allowanceSummary.find(s => s.id === child.id);
            const enrichedChild = {
              ...child,
              balance_due: summary?.balance_due || 0,
              completed_chores: summary?.completed_chores || 0,
            };
            return (
              <ChildCard
                key={child.id}
                child={enrichedChild}
                onPress={() => setSelectedChild(child)}
              />
            );
          })
        )}
      </View>

      {/* Allowance Details */}
      {allowanceSummary.length > 0 && (
        <View style={styles.allowanceSection}>
          <Text style={styles.sectionTitle}>Allowance Details</Text>
          {allowanceSummary.map((summary) => (
            <View key={summary.id} style={styles.allowanceCard}>
              <View style={styles.allowanceHeader}>
                <Text style={styles.childName}>{summary.username}</Text>
                <Text style={styles.balanceDue}>${summary.balance_due.toFixed(2)}</Text>
              </View>
              <View style={styles.allowanceDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Completed Chores:</Text>
                  <Text style={styles.detailValue}>{summary.completed_chores}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Total Earned:</Text>
                  <Text style={styles.detailValue}>${summary.total_earned.toFixed(2)}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Adjustments:</Text>
                  <Text style={styles.detailValue}>${summary.total_adjustments.toFixed(2)}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Paid Out:</Text>
                  <Text style={styles.detailValue}>-${summary.paid_out.toFixed(2)}</Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  summarySection: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  summaryCards: {
    flexDirection: 'row',
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  totalOwedCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#2196f3',
  },
  pendingCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#ff9800',
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
  },
  childrenSection: {
    padding: 16,
    paddingTop: 0,
  },
  emptyState: {
    backgroundColor: '#fff',
    padding: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  allowanceSection: {
    padding: 16,
    paddingTop: 0,
  },
  allowanceCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  allowanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  childName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  balanceDue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2196f3',
  },
  allowanceDetails: {
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
});