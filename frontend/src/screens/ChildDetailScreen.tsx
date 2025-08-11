import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { ChildWithChores, ChildAllowanceSummary } from '../api/users';
import { Chore, choreAPI } from '../api/chores';
import { adjustmentAPI, Adjustment, AdjustmentTotal } from '../api/adjustments';
import ChoreCard from '../components/ChoreCard';
import AdjustmentFormScreen from './AdjustmentFormScreen';

interface ChildDetailScreenProps {
  child: ChildWithChores;
  onBack: () => void;
}

const ChildDetailScreen: React.FC<ChildDetailScreenProps> = ({ child, onBack }) => {
  const [activeTab, setActiveTab] = useState<'active' | 'pending' | 'completed' | 'adjustments'>('active');
  const [chores, setChores] = useState<Chore[]>([]);
  const [adjustments, setAdjustments] = useState<Adjustment[]>([]);
  const [adjustmentTotal, setAdjustmentTotal] = useState<AdjustmentTotal | null>(null);
  const [showAdjustmentForm, setShowAdjustmentForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchChores = async () => {
    try {
      const childChores = await choreAPI.getChildChores(child.id);
      setChores(childChores);
    } catch (error) {
      console.error('Failed to fetch child chores:', error);
      Alert.alert('Error', 'Failed to load chores');
    }
  };

  const fetchAdjustments = async () => {
    try {
      const [adjustmentsData, totalData] = await Promise.all([
        adjustmentAPI.getChildAdjustments(child.id),
        adjustmentAPI.getChildAdjustmentTotal(child.id),
      ]);
      setAdjustments(adjustmentsData);
      setAdjustmentTotal(totalData);
    } catch (error) {
      console.error('Failed to fetch adjustments:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchChores(), fetchAdjustments()]);
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchData();
  }, [child.id]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const handleApproveChore = async (choreId: number, rewardValue?: number) => {
    try {
      await choreAPI.approveChore(choreId, rewardValue);
      Alert.alert('Success', 'Chore approved successfully!');
      fetchChores(); // Refresh the list
    } catch (error) {
      console.error('Failed to approve chore:', error);
      Alert.alert('Error', 'Failed to approve chore');
    }
  };

  // Filter chores based on selected tab (handle both field names)
  const filteredChores = chores.filter((chore) => {
    const isCompleted = chore.is_completed || chore.completed_at || chore.completion_date;
    const isApproved = chore.is_approved || chore.approved_at;
    
    switch (activeTab) {
      case 'active':
        return !isCompleted;
      case 'pending':
        return isCompleted && !isApproved;
      case 'completed':
        return isApproved;
      default:
        return false;
    }
  });

  const handleAdjustmentSuccess = () => {
    setShowAdjustmentForm(false);
    fetchAdjustments();
  };

  const formatAmount = (amount: string) => {
    const value = parseFloat(amount);
    const isPositive = value >= 0;
    return {
      text: `${isPositive ? '+' : ''}$${Math.abs(value).toFixed(2)}`,
      color: isPositive ? '#4caf50' : '#f44336',
    };
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const renderTabButton = (tab: 'active' | 'pending' | 'completed' | 'adjustments', label: string) => (
    <TouchableOpacity
      style={[styles.tabButton, activeTab === tab && styles.activeTab]}
      onPress={() => setActiveTab(tab)}
    >
      <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{child.username}'s Chores</Text>
      </View>

      <View style={styles.tabs}>
        {renderTabButton('active', `Active (${chores.filter(c => !c.is_completed && !c.completed_at && !c.completion_date).length})`)}
        {renderTabButton('pending', `Pending (${chores.filter(c => (c.is_completed || c.completed_at || c.completion_date) && !c.is_approved && !c.approved_at).length})`)}
        {renderTabButton('completed', `Completed (${chores.filter(c => c.is_approved || c.approved_at).length})`)}
        {renderTabButton('adjustments', `Adjustments (${adjustments.length})`)}
      </View>

      {showAdjustmentForm ? (
        <AdjustmentFormScreen
          childId={child.id}
          onSuccess={handleAdjustmentSuccess}
          onCancel={() => setShowAdjustmentForm(false)}
        />
      ) : (
        <ScrollView
          style={styles.scrollView}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
          {activeTab === 'adjustments' ? (
            <>
              {adjustmentTotal && (
                <View style={styles.adjustmentSummary}>
                  <Text style={styles.summaryLabel}>Total Adjustments:</Text>
                  <Text style={[styles.summaryAmount, { color: formatAmount(adjustmentTotal.total_adjustments).color }]}>
                    {formatAmount(adjustmentTotal.total_adjustments).text}
                  </Text>
                </View>
              )}
              <TouchableOpacity
                style={styles.addAdjustmentButton}
                onPress={() => setShowAdjustmentForm(true)}
              >
                <Text style={styles.addAdjustmentText}>+ Add Adjustment</Text>
              </TouchableOpacity>
              {adjustments.length === 0 ? (
                <View style={styles.emptyState}>
                  <Text style={styles.emptyText}>No adjustments yet</Text>
                </View>
              ) : (
                adjustments.map((adjustment) => {
                  const { text, color } = formatAmount(adjustment.amount);
                  return (
                    <View key={adjustment.id} style={styles.adjustmentCard}>
                      <View style={styles.adjustmentHeader}>
                        <Text style={[styles.adjustmentAmount, { color }]}>{text}</Text>
                        <Text style={styles.adjustmentDate}>{formatDate(adjustment.created_at)}</Text>
                      </View>
                      <Text style={styles.adjustmentReason}>{adjustment.reason}</Text>
                    </View>
                  );
                })
              )}
            </>
          ) : (
            <>
              {filteredChores.length === 0 ? (
                <View style={styles.emptyState}>
                  <Text style={styles.emptyText}>
                    {activeTab === 'active' && 'No active chores'}
                    {activeTab === 'pending' && 'No chores pending approval'}
                    {activeTab === 'completed' && 'No completed chores'}
                  </Text>
                </View>
              ) : (
                filteredChores.map((chore) => (
            <View key={chore.id} style={styles.choreCardWrapper}>
              <ChoreCard chore={chore} />
              {activeTab === 'pending' && (
                <TouchableOpacity
                  style={styles.approveButton}
                  onPress={() => {
                    if (chore.is_range_reward && chore.min_reward && chore.max_reward) {
                      // For range rewards, prompt for value
                      Alert.prompt(
                        'Set Reward Amount',
                        `Enter reward amount between $${chore.min_reward} and $${chore.max_reward}`,
                        [
                          { text: 'Cancel', style: 'cancel' },
                          {
                            text: 'Approve',
                            onPress: (value) => {
                              const rewardValue = parseFloat(value || '0');
                              if (rewardValue >= chore.min_reward && rewardValue <= chore.max_reward) {
                                handleApproveChore(chore.id, rewardValue);
                              } else {
                                Alert.alert('Invalid Amount', `Please enter a value between $${chore.min_reward} and $${chore.max_reward}`);
                              }
                            },
                          },
                        ],
                        'plain-text',
                        '',
                        'decimal-pad'
                      );
                    } else {
                      // Fixed reward
                      Alert.alert(
                        'Approve Chore',
                        `Approve "${chore.title}" for $${chore.reward || 0}?`,
                        [
                          { text: 'Cancel', style: 'cancel' },
                          { text: 'Approve', onPress: () => handleApproveChore(chore.id) },
                        ]
                      );
                    }
                  }}
                >
                  <Text style={styles.approveButtonText}>Approve</Text>
                </TouchableOpacity>
              )}
                </View>
              ))
            )}
          </>
        )}
      </ScrollView>
      )}
    </View>
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
  header: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    marginRight: 16,
  },
  backText: {
    fontSize: 16,
    color: '#2196f3',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#2196f3',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
  },
  activeTabText: {
    color: '#2196f3',
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  emptyState: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
  choreCardWrapper: {
    marginBottom: 12,
  },
  approveButton: {
    backgroundColor: '#4caf50',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  approveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  adjustmentSummary: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryLabel: {
    fontSize: 16,
    color: '#666',
  },
  summaryAmount: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  addAdjustmentButton: {
    backgroundColor: '#2196f3',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 16,
  },
  addAdjustmentText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  adjustmentCard: {
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
  adjustmentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  adjustmentAmount: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  adjustmentDate: {
    fontSize: 12,
    color: '#999',
  },
  adjustmentReason: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});

export default ChildDetailScreen;