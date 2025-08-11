import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { adjustmentAPI, Adjustment, AdjustmentTotal } from '../api/adjustments';
import { usersAPI, ChildWithChores } from '../api/users';
import AdjustmentFormScreen from './AdjustmentFormScreen';

const AdjustmentsListScreen: React.FC = () => {
  const [children, setChildren] = useState<ChildWithChores[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const [adjustments, setAdjustments] = useState<Adjustment[]>([]);
  const [adjustmentTotal, setAdjustmentTotal] = useState<AdjustmentTotal | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedChildId) {
      fetchAdjustments();
    }
  }, [selectedChildId]);

  const fetchData = async () => {
    try {
      const childrenData = await usersAPI.getMyChildren();
      setChildren(childrenData);
      
      // Auto-select first child if available
      if (childrenData.length > 0 && !selectedChildId) {
        setSelectedChildId(childrenData[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch children:', error);
      Alert.alert('Error', 'Failed to load children');
    } finally {
      setLoading(false);
    }
  };

  const fetchAdjustments = async () => {
    if (!selectedChildId) return;
    
    setLoading(true);
    try {
      const [adjustmentsData, totalData] = await Promise.all([
        adjustmentAPI.getChildAdjustments(selectedChildId),
        adjustmentAPI.getChildAdjustmentTotal(selectedChildId),
      ]);
      
      setAdjustments(adjustmentsData);
      setAdjustmentTotal(totalData);
    } catch (error) {
      console.error('Failed to fetch adjustments:', error);
      Alert.alert('Error', 'Failed to load adjustments');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchAdjustments();
  };

  const handleAdjustmentSuccess = () => {
    setShowForm(false);
    fetchAdjustments();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatAmount = (amount: string) => {
    const value = parseFloat(amount);
    const isPositive = value >= 0;
    return {
      text: `${isPositive ? '+' : ''}$${Math.abs(value).toFixed(2)}`,
      color: isPositive ? '#4caf50' : '#f44336',
    };
  };

  if (showForm) {
    return (
      <AdjustmentFormScreen
        childId={selectedChildId || undefined}
        onSuccess={handleAdjustmentSuccess}
        onCancel={() => setShowForm(false)}
      />
    );
  }

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
      </View>
    );
  }

  const selectedChild = children.find(c => c.id === selectedChildId);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Adjustments</Text>
          <Text style={styles.subtitle}>
            Manage bonuses and deductions
          </Text>
        </View>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowForm(true)}
        >
          <Text style={styles.addButtonText}>+ New</Text>
        </TouchableOpacity>
      </View>

      {/* Child Selector */}
      {children.length > 1 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.childSelectorContainer}
          contentContainerStyle={styles.childSelectorContent}
        >
          {children.map((child) => (
            <TouchableOpacity
              key={child.id}
              style={[
                styles.childTab,
                selectedChildId === child.id && styles.childTabActive,
              ]}
              onPress={() => setSelectedChildId(child.id)}
            >
              <Text
                style={[
                  styles.childTabText,
                  selectedChildId === child.id && styles.childTabTextActive,
                ]}
              >
                {child.username}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Summary Card */}
      {selectedChild && adjustmentTotal && (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>
            {selectedChild.username}'s Adjustments
          </Text>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Total Adjustments:</Text>
            <Text
              style={[
                styles.summaryAmount,
                { color: formatAmount(adjustmentTotal.total_adjustments).color },
              ]}
            >
              {formatAmount(adjustmentTotal.total_adjustments).text}
            </Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Current Balance:</Text>
            <Text style={styles.summaryAmount}>
              ${selectedChild.balance?.toFixed(2) || '0.00'}
            </Text>
          </View>
        </View>
      )}

      {/* Adjustments List */}
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {adjustments.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📊</Text>
            <Text style={styles.emptyText}>No adjustments yet</Text>
            <Text style={styles.emptySubtext}>
              Tap the "New" button to create a bonus or deduction
            </Text>
          </View>
        ) : (
          adjustments.map((adjustment) => {
            const { text, color } = formatAmount(adjustment.amount);
            return (
              <View key={adjustment.id} style={styles.adjustmentCard}>
                <View style={styles.adjustmentHeader}>
                  <View style={styles.adjustmentInfo}>
                    <Text style={[styles.adjustmentAmount, { color }]}>
                      {text}
                    </Text>
                    <Text style={styles.adjustmentDate}>
                      {formatDate(adjustment.created_at)}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.adjustmentBadge,
                      { backgroundColor: color === '#4caf50' ? '#e8f5e9' : '#ffebee' },
                    ]}
                  >
                    <Text
                      style={[
                        styles.adjustmentBadgeText,
                        { color },
                      ]}
                    >
                      {parseFloat(adjustment.amount) >= 0 ? 'Bonus' : 'Deduction'}
                    </Text>
                  </View>
                </View>
                <Text style={styles.adjustmentReason}>{adjustment.reason}</Text>
              </View>
            );
          })
        )}
      </ScrollView>
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
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  addButton: {
    backgroundColor: '#2196f3',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  childSelectorContainer: {
    backgroundColor: '#fff',
    maxHeight: 50,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  childSelectorContent: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 10,
  },
  childTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
  },
  childTabActive: {
    backgroundColor: '#2196f3',
  },
  childTabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
  },
  childTabTextActive: {
    color: '#fff',
  },
  summaryCard: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 4,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
  },
  summaryAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  scrollView: {
    flex: 1,
    padding: 16,
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
    alignItems: 'center',
    marginBottom: 8,
  },
  adjustmentInfo: {
    flex: 1,
  },
  adjustmentAmount: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  adjustmentDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  adjustmentBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  adjustmentBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  adjustmentReason: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  emptyState: {
    padding: 48,
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});

export default AdjustmentsListScreen;