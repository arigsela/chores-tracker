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
  TextInput,
} from 'react-native';
import { Chore, choreAPI } from '../api/chores';
import { usersAPI, ChildWithChores } from '../api/users';
import { RejectChoreModal } from '../components/RejectChoreModal';

interface ApprovalCardProps {
  chore: Chore;
  childName: string;
  onApprove: (choreId: number, rewardValue?: number) => void;
  onReject: (choreId: number) => void;
}

const ApprovalCard: React.FC<ApprovalCardProps> = ({ chore, childName, onApprove, onReject }) => {
  const [customReward, setCustomReward] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  const handleApprove = () => {
    if (chore.is_range_reward) {
      if (showCustomInput) {
        const value = parseFloat(customReward);
        if (isNaN(value) || value < (chore.min_reward || 0) || value > (chore.max_reward || 0)) {
          Alert.alert(
            'Invalid Amount',
            `Please enter a value between $${chore.min_reward} and $${chore.max_reward}`
          );
          return;
        }
        onApprove(chore.id, value);
      } else {
        setShowCustomInput(true);
        setCustomReward(((chore.min_reward || 0) + (chore.max_reward || 0)) / 2 + '');
      }
    } else {
      onApprove(chore.id);
    }
  };

  const getRewardDisplay = () => {
    if (chore.is_range_reward) {
      return `$${chore.min_reward?.toFixed(2)} - $${chore.max_reward?.toFixed(2)}`;
    }
    return `$${chore.reward?.toFixed(2) || '0.00'}`;
  };

  const completedDate = chore.completion_date || chore.completed_at;
  const formattedDate = completedDate 
    ? new Date(completedDate).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    : 'Unknown';

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.choreInfo}>
          <Text style={styles.choreTitle}>{chore.title}</Text>
          <Text style={styles.childName}>Completed by: {childName}</Text>
          <Text style={styles.completedDate}>Completed: {formattedDate}</Text>
        </View>
        <View style={styles.rewardBadge}>
          <Text style={styles.rewardLabel}>Reward</Text>
          <Text style={styles.rewardAmount}>{getRewardDisplay()}</Text>
        </View>
      </View>

      {chore.description && (
        <Text style={styles.choreDescription}>{chore.description}</Text>
      )}

      {showCustomInput && chore.is_range_reward && (
        <View style={styles.customRewardContainer}>
          <Text style={styles.customRewardLabel}>Set reward amount:</Text>
          <View style={styles.customRewardInput}>
            <Text style={styles.dollarSign}>$</Text>
            <TextInput
              style={styles.rewardInput}
              value={customReward}
              onChangeText={setCustomReward}
              keyboardType="decimal-pad"
              placeholder="0.00"
              autoFocus
            />
          </View>
          <Text style={styles.rangeHint}>
            Range: ${chore.min_reward?.toFixed(2)} - ${chore.max_reward?.toFixed(2)}
          </Text>
        </View>
      )}

      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={[styles.button, styles.rejectButton]}
          onPress={() => onReject(chore.id)}
        >
          <Text style={styles.rejectButtonText}>Reject</Text>
        </TouchableOpacity>

        {showCustomInput && chore.is_range_reward ? (
          <>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={() => {
                setShowCustomInput(false);
                setCustomReward('');
              }}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.approveButton]}
              onPress={handleApprove}
            >
              <Text style={styles.approveButtonText}>Confirm</Text>
            </TouchableOpacity>
          </>
        ) : (
          <TouchableOpacity
            style={[styles.button, styles.approveButton]}
            onPress={handleApprove}
          >
            <Text style={styles.approveButtonText}>
              {chore.is_range_reward ? 'Set Amount' : 'Approve'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const ApprovalsScreen: React.FC = () => {
  const [pendingChores, setPendingChores] = useState<Chore[]>([]);
  const [children, setChildren] = useState<ChildWithChores[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedChores, setSelectedChores] = useState<Set<number>>(new Set());
  const [bulkMode, setBulkMode] = useState(false);
  
  // Rejection modal state
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [choreToReject, setChoreToReject] = useState<Chore | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [choresData, childrenData] = await Promise.all([
        choreAPI.getPendingApprovalChores(),
        usersAPI.getMyChildren(),
      ]);
      setPendingChores(choresData);
      setChildren(childrenData);
    } catch (error) {
      console.error('Failed to fetch pending approvals:', error);
      Alert.alert('Error', 'Failed to load pending approvals');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    setSelectedChores(new Set());
    setBulkMode(false);
    fetchData();
  };

  const getChildName = (choreId: number): string => {
    const chore = pendingChores.find(c => c.id === choreId);
    if (!chore) return 'Unknown';
    
    const childId = chore.assignee_id || chore.assigned_to_id;
    const child = children.find(c => c.id === childId);
    return child?.username || `Child #${childId}`;
  };

  const handleApprove = async (choreId: number, rewardValue?: number) => {
    try {
      await choreAPI.approveChore(choreId, rewardValue);
      
      // Remove from pending list immediately for better UX
      setPendingChores(prev => prev.filter(c => c.id !== choreId));
      
      const childName = getChildName(choreId);
      Alert.alert(
        'Success',
        `Chore approved for ${childName}${rewardValue ? ` ($${rewardValue.toFixed(2)})` : ''}!`
      );
    } catch (error) {
      console.error('Failed to approve chore:', error);
      Alert.alert('Error', 'Failed to approve chore');
      fetchData(); // Refresh on error to restore state
    }
  };

  const handleReject = (choreId: number) => {
    const chore = pendingChores.find(c => c.id === choreId);
    if (chore) {
      setChoreToReject(chore);
      setRejectModalVisible(true);
    }
  };

  const handleRejectConfirm = async (rejectionReason: string) => {
    if (!choreToReject) return;

    try {
      await choreAPI.rejectChore(choreToReject.id, rejectionReason);
      
      // Remove from pending list
      setPendingChores(prev => prev.filter(c => c.id !== choreToReject.id));
      
      // Close modal
      setRejectModalVisible(false);
      setChoreToReject(null);
      
      const childName = getChildName(choreToReject.id);
      Alert.alert(
        'Chore Rejected',
        `"${choreToReject.title}" has been rejected. ${childName} will need to complete it again.`
      );
    } catch (error) {
      console.error('Failed to reject chore:', error);
      Alert.alert('Error', 'Failed to reject chore');
      fetchData(); // Refresh on error to restore state
    }
  };

  const handleRejectCancel = () => {
    setRejectModalVisible(false);
    setChoreToReject(null);
  };

  const toggleChoreSelection = (choreId: number) => {
    const newSelection = new Set(selectedChores);
    if (newSelection.has(choreId)) {
      newSelection.delete(choreId);
    } else {
      newSelection.add(choreId);
    }
    setSelectedChores(newSelection);
  };

  const handleBulkApprove = async () => {
    if (selectedChores.size === 0) {
      Alert.alert('No Selection', 'Please select chores to approve');
      return;
    }

    // Check if any selected chores have range rewards
    const hasRangeRewards = pendingChores
      .filter(c => selectedChores.has(c.id))
      .some(c => c.is_range_reward);

    if (hasRangeRewards) {
      Alert.alert(
        'Range Rewards',
        'Some selected chores have range rewards. Please approve them individually to set specific amounts.',
        [{ text: 'OK' }]
      );
      return;
    }

    Alert.alert(
      'Bulk Approve',
      `Approve ${selectedChores.size} chore(s)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Approve All',
          onPress: async () => {
            const approvalPromises = Array.from(selectedChores).map(choreId =>
              choreAPI.approveChore(choreId).catch(err => {
                console.error(`Failed to approve chore ${choreId}:`, err);
                return null;
              })
            );

            const results = await Promise.all(approvalPromises);
            const successCount = results.filter(r => r !== null).length;

            setPendingChores(prev => 
              prev.filter(c => !selectedChores.has(c.id) || results[Array.from(selectedChores).indexOf(c.id)] === null)
            );

            setSelectedChores(new Set());
            setBulkMode(false);

            Alert.alert(
              'Bulk Approval Complete',
              `Successfully approved ${successCount} out of ${selectedChores.size} chores.`
            );
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
      </View>
    );
  }

  const totalPendingReward = pendingChores.reduce((sum, chore) => {
    if (chore.is_range_reward) {
      // Use average of range for estimate
      return sum + ((chore.min_reward || 0) + (chore.max_reward || 0)) / 2;
    }
    return sum + (chore.reward || 0);
  }, 0);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Pending Approvals</Text>
          <Text style={styles.subtitle}>
            {pendingChores.length} chore{pendingChores.length !== 1 ? 's' : ''} pending
          </Text>
        </View>
        {pendingChores.length > 0 && (
          <TouchableOpacity
            style={styles.bulkButton}
            onPress={() => {
              if (bulkMode) {
                setSelectedChores(new Set());
              }
              setBulkMode(!bulkMode);
            }}
          >
            <Text style={styles.bulkButtonText}>
              {bulkMode ? 'Cancel' : 'Bulk Select'}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {pendingChores.length > 0 && (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>Estimated Total Rewards</Text>
          <Text style={styles.summaryAmount}>${totalPendingReward.toFixed(2)}</Text>
          <Text style={styles.summaryNote}>
            *Range rewards shown at midpoint
          </Text>
        </View>
      )}

      {bulkMode && selectedChores.size > 0 && (
        <View style={styles.bulkActionBar}>
          <Text style={styles.bulkSelectionText}>
            {selectedChores.size} selected
          </Text>
          <TouchableOpacity
            style={styles.bulkApproveButton}
            onPress={handleBulkApprove}
          >
            <Text style={styles.bulkApproveButtonText}>Approve Selected</Text>
          </TouchableOpacity>
        </View>
      )}

      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {pendingChores.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>✅</Text>
            <Text style={styles.emptyText}>No pending approvals</Text>
            <Text style={styles.emptySubtext}>
              All completed chores have been reviewed
            </Text>
          </View>
        ) : (
          pendingChores.map((chore) => {
            const childId = chore.assignee_id || chore.assigned_to_id;
            const child = children.find(c => c.id === childId);
            const childName = child?.username || `Child #${childId}`;

            if (bulkMode) {
              return (
                <TouchableOpacity
                  key={chore.id}
                  onPress={() => toggleChoreSelection(chore.id)}
                  style={[
                    styles.selectableCard,
                    selectedChores.has(chore.id) && styles.selectedCard,
                  ]}
                >
                  <View style={styles.selectionIndicator}>
                    <View style={[
                      styles.checkbox,
                      selectedChores.has(chore.id) && styles.checkboxSelected,
                    ]}>
                      {selectedChores.has(chore.id) && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </View>
                  </View>
                  <ApprovalCard
                    chore={chore}
                    childName={childName}
                    onApprove={() => {}} // Disabled in bulk mode
                    onReject={() => {}} // Disabled in bulk mode
                  />
                </TouchableOpacity>
              );
            }

            return (
              <ApprovalCard
                key={chore.id}
                chore={chore}
                childName={childName}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            );
          })
        )}
      </ScrollView>

      <RejectChoreModal
        visible={rejectModalVisible}
        choreTitle={choreToReject?.title || ''}
        childName={choreToReject ? getChildName(choreToReject.id) : ''}
        onReject={handleRejectConfirm}
        onCancel={handleRejectCancel}
      />
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
  bulkButton: {
    backgroundColor: '#2196f3',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  bulkButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  summaryCard: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  summaryAmount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4caf50',
  },
  summaryNote: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
    marginTop: 4,
  },
  bulkActionBar: {
    backgroundColor: '#2196f3',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 8,
  },
  bulkSelectionText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  bulkApproveButton: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  bulkApproveButtonText: {
    color: '#2196f3',
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  card: {
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
  selectableCard: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  selectedCard: {
    opacity: 0.9,
  },
  selectionIndicator: {
    paddingRight: 12,
    justifyContent: 'center',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#ddd',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxSelected: {
    backgroundColor: '#2196f3',
    borderColor: '#2196f3',
  },
  checkmark: {
    color: '#fff',
    fontWeight: 'bold',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  choreInfo: {
    flex: 1,
  },
  choreTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  childName: {
    fontSize: 14,
    color: '#2196f3',
    marginBottom: 2,
  },
  completedDate: {
    fontSize: 12,
    color: '#999',
  },
  rewardBadge: {
    backgroundColor: '#e8f5e9',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  rewardLabel: {
    fontSize: 12,
    color: '#4caf50',
    marginBottom: 2,
  },
  rewardAmount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4caf50',
  },
  choreDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  customRewardContainer: {
    backgroundColor: '#f5f5f5',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  customRewardLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  customRewardInput: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    marginBottom: 8,
  },
  dollarSign: {
    fontSize: 18,
    color: '#666',
    marginRight: 4,
  },
  rewardInput: {
    flex: 1,
    fontSize: 18,
    paddingVertical: 10,
    color: '#333',
  },
  rangeHint: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  actionButtons: {
    flexDirection: 'row',
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  rejectButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#f44336',
  },
  rejectButtonText: {
    color: '#f44336',
    fontWeight: '600',
  },
  cancelButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#999',
  },
  cancelButtonText: {
    color: '#666',
    fontWeight: '600',
  },
  approveButton: {
    backgroundColor: '#4caf50',
  },
  approveButtonText: {
    color: '#fff',
    fontWeight: 'bold',
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

export default ApprovalsScreen;