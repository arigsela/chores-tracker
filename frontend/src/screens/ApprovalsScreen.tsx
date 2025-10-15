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
import { Chore, choreAPI, PendingApprovalItem, Assignment } from '../api/chores';
import { usersAPI, ChildWithChores } from '../api/users';
import { familyAPI } from '../api/families';
import { RejectChoreModal } from '../components/RejectChoreModal';

interface ApprovalCardProps {
  chore: Chore;
  assignment: Assignment;
  assignmentId: number;
  childName: string;
  onApprove: (assignmentId: number, rewardValue?: number) => void;
  onReject: (assignmentId: number) => void;
  assignmentMode?: string; // For displaying mode badge
}

const ApprovalCard: React.FC<ApprovalCardProps> = ({
  chore,
  assignment,
  assignmentId,
  childName,
  onApprove,
  onReject,
  assignmentMode
}) => {
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
        onApprove(assignmentId, value);
      } else {
        setShowCustomInput(true);
        setCustomReward(((chore.min_reward || 0) + (chore.max_reward || 0)) / 2 + '');
      }
    } else {
      onApprove(assignmentId);
    }
  };

  const getRewardDisplay = () => {
    if (chore.is_range_reward) {
      return `$${chore.min_reward?.toFixed(2)} - $${chore.max_reward?.toFixed(2)}`;
    }
    return `$${chore.reward?.toFixed(2) || '0.00'}`;
  };

  const completedDate = assignment.completion_date || chore.completion_date || chore.completed_at;
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
          {assignmentMode === 'multi_independent' && (
            <View style={styles.modeBadge}>
              <Text style={styles.modeBadgeText}>Multi-Child Chore</Text>
            </View>
          )}
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
          onPress={() => onReject(assignmentId)}
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
  // NEW: Changed from Chore[] to PendingApprovalItem[]
  const [pendingItems, setPendingItems] = useState<PendingApprovalItem[]>([]);
  const [children, setChildren] = useState<ChildWithChores[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  // NEW: Changed from chore IDs to assignment IDs
  const [selectedAssignments, setSelectedAssignments] = useState<Set<number>>(new Set());
  const [bulkMode, setBulkMode] = useState(false);

  // Rejection modal state
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [itemToReject, setItemToReject] = useState<PendingApprovalItem | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // First get family context to understand if user has a family
      const familyCtx = await familyAPI.getFamilyContext();

      // Use family children if user has family, otherwise fallback to personal children
      const childrenEndpoint = familyCtx.has_family
        ? usersAPI.getFamilyChildren()
        : usersAPI.getMyChildren();

      // NEW: getPendingApprovalChores now returns PendingApprovalItem[]
      const [pendingData, childrenData] = await Promise.all([
        choreAPI.getPendingApprovalChores(),
        childrenEndpoint,
      ]);
      setPendingItems(pendingData);
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
    setSelectedAssignments(new Set());
    setBulkMode(false);
    fetchData();
  };

  // NEW: Uses assignment_id instead of chore_id
  const handleApprove = async (assignmentId: number, rewardValue?: number) => {
    try {
      await choreAPI.approveAssignment(assignmentId, rewardValue);

      // Find the item being approved for success message
      const item = pendingItems.find(i => i.assignment_id === assignmentId);

      // Remove from pending list immediately for better UX
      setPendingItems(prev => prev.filter(i => i.assignment_id !== assignmentId));

      const childName = item?.assignee_name || 'Unknown';
      const choreTitle = item?.chore.title || 'Unknown';
      Alert.alert(
        'Success',
        `Approved "${choreTitle}" for ${childName}${rewardValue ? ` ($${rewardValue.toFixed(2)})` : ''}!`
      );
    } catch (error) {
      console.error('Failed to approve assignment:', error);
      Alert.alert('Error', 'Failed to approve assignment');
      fetchData(); // Refresh on error to restore state
    }
  };

  // NEW: Uses assignment_id instead of chore_id
  const handleReject = (assignmentId: number) => {
    const item = pendingItems.find(i => i.assignment_id === assignmentId);
    if (item) {
      setItemToReject(item);
      setRejectModalVisible(true);
    }
  };

  const handleRejectConfirm = async (rejectionReason: string) => {
    if (!itemToReject) return;

    try {
      await choreAPI.rejectAssignment(itemToReject.assignment_id, rejectionReason);

      // Remove from pending list
      setPendingItems(prev => prev.filter(i => i.assignment_id !== itemToReject.assignment_id));

      // Close modal
      setRejectModalVisible(false);
      setItemToReject(null);

      const childName = itemToReject.assignee_name;
      const choreTitle = itemToReject.chore.title;
      Alert.alert(
        'Assignment Rejected',
        `"${choreTitle}" has been rejected. ${childName} will need to complete it again.`
      );
    } catch (error) {
      console.error('Failed to reject assignment:', error);
      Alert.alert('Error', 'Failed to reject assignment');
      fetchData(); // Refresh on error to restore state
    }
  };

  const handleRejectCancel = () => {
    setRejectModalVisible(false);
    setItemToReject(null);
  };

  // NEW: Uses assignment IDs instead of chore IDs
  const toggleAssignmentSelection = (assignmentId: number) => {
    const newSelection = new Set(selectedAssignments);
    if (newSelection.has(assignmentId)) {
      newSelection.delete(assignmentId);
    } else {
      newSelection.add(assignmentId);
    }
    setSelectedAssignments(newSelection);
  };

  const handleBulkApprove = async () => {
    if (selectedAssignments.size === 0) {
      Alert.alert('No Selection', 'Please select assignments to approve');
      return;
    }

    // Check if any selected assignments have range rewards
    const hasRangeRewards = pendingItems
      .filter(i => selectedAssignments.has(i.assignment_id))
      .some(i => i.chore.is_range_reward);

    if (hasRangeRewards) {
      Alert.alert(
        'Range Rewards',
        'Some selected assignments have range rewards. Please approve them individually to set specific amounts.',
        [{ text: 'OK' }]
      );
      return;
    }

    Alert.alert(
      'Bulk Approve',
      `Approve ${selectedAssignments.size} assignment(s)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Approve All',
          onPress: async () => {
            const approvalPromises = Array.from(selectedAssignments).map(assignmentId =>
              choreAPI.approveAssignment(assignmentId).catch(err => {
                console.error(`Failed to approve assignment ${assignmentId}:`, err);
                return null;
              })
            );

            const results = await Promise.all(approvalPromises);
            const successCount = results.filter(r => r !== null).length;

            setPendingItems(prev =>
              prev.filter(i => !selectedAssignments.has(i.assignment_id) || results[Array.from(selectedAssignments).indexOf(i.assignment_id)] === null)
            );

            setSelectedAssignments(new Set());
            setBulkMode(false);

            Alert.alert(
              'Bulk Approval Complete',
              `Successfully approved ${successCount} out of ${selectedAssignments.size} assignments.`
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

  const totalPendingReward = pendingItems.reduce((sum, item) => {
    const chore = item.chore;
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
            {pendingItems.length} assignment{pendingItems.length !== 1 ? 's' : ''} pending
          </Text>
        </View>
        {pendingItems.length > 0 && (
          <TouchableOpacity
            style={styles.bulkButton}
            onPress={() => {
              if (bulkMode) {
                setSelectedAssignments(new Set());
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

      {pendingItems.length > 0 && (
        <View style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>Estimated Total Rewards</Text>
          <Text style={styles.summaryAmount}>${totalPendingReward.toFixed(2)}</Text>
          <Text style={styles.summaryNote}>
            *Range rewards shown at midpoint
          </Text>
        </View>
      )}

      {bulkMode && selectedAssignments.size > 0 && (
        <View style={styles.bulkActionBar}>
          <Text style={styles.bulkSelectionText}>
            {selectedAssignments.size} selected
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
        {pendingItems.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>✅</Text>
            <Text style={styles.emptyText}>No pending approvals</Text>
            <Text style={styles.emptySubtext}>
              All completed assignments have been reviewed
            </Text>
          </View>
        ) : (
          pendingItems.map((item) => {
            const { chore, assignment, assignment_id, assignee_name } = item;

            if (bulkMode) {
              return (
                <TouchableOpacity
                  key={assignment_id}
                  onPress={() => toggleAssignmentSelection(assignment_id)}
                  style={[
                    styles.selectableCard,
                    selectedAssignments.has(assignment_id) && styles.selectedCard,
                  ]}
                >
                  <View style={styles.selectionIndicator}>
                    <View style={[
                      styles.checkbox,
                      selectedAssignments.has(assignment_id) && styles.checkboxSelected,
                    ]}>
                      {selectedAssignments.has(assignment_id) && (
                        <Text style={styles.checkmark}>✓</Text>
                      )}
                    </View>
                  </View>
                  <ApprovalCard
                    chore={chore}
                    assignment={assignment}
                    assignmentId={assignment_id}
                    childName={assignee_name}
                    assignmentMode={chore.assignment_mode}
                    onApprove={() => {}} // Disabled in bulk mode
                    onReject={() => {}} // Disabled in bulk mode
                  />
                </TouchableOpacity>
              );
            }

            return (
              <ApprovalCard
                key={assignment_id}
                chore={chore}
                assignment={assignment}
                assignmentId={assignment_id}
                childName={assignee_name}
                assignmentMode={chore.assignment_mode}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            );
          })
        )}
      </ScrollView>

      <RejectChoreModal
        visible={rejectModalVisible}
        choreTitle={itemToReject?.chore.title || ''}
        childName={itemToReject?.assignee_name || ''}
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
  modeBadge: {
    backgroundColor: '#FFA726',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 6,
    alignSelf: 'flex-start',
  },
  modeBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#fff',
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