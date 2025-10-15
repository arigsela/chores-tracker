import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Chore, Assignment, AssignmentMode } from '@/api/chores';

interface ChoreCardProps {
  chore: Chore;
  assignment?: Assignment;
  assignmentId?: number;
  assignmentMode?: 'assigned' | 'pool' | AssignmentMode;
  onComplete?: (choreId: number, assignmentId?: number) => void;
  onEnable?: (choreId: number) => void;
  onDisable?: (choreId: number) => void;
  showCompleteButton?: boolean;
  showManageButtons?: boolean;
  isChild?: boolean;
}

export const ChoreCard: React.FC<ChoreCardProps> = ({
  chore,
  assignment,
  assignmentId,
  assignmentMode,
  onComplete,
  onEnable,
  onDisable,
  showCompleteButton = false,
  showManageButtons = false,
  isChild = false
}) => {
  const [isCompleting, setIsCompleting] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const getStatusText = () => {
    if (chore.is_disabled) return '🚫 Disabled';

    // Use assignment data if available (preferred for multi-assignment)
    if (assignment) {
      if (assignment.is_approved) return '✅ Approved';
      if (assignment.is_completed) return '⏳ Pending Approval';
    }

    // Fallback to chore-level data (for backward compatibility)
    if (chore.approved_at || chore.is_approved) return '✅ Approved';
    const isCompleted = chore.completed_at || chore.completion_date || chore.is_completed;
    if (isCompleted && !chore.approved_at && !chore.is_approved) return '⏳ Pending Approval';
    if (isCompleted) return '✓ Completed';

    if (chore.next_available_at) {
      const nextDate = new Date(chore.next_available_at);
      if (nextDate > new Date()) {
        return `🔒 Available ${nextDate.toLocaleDateString()}`;
      }
    }
    return '📋 Ready to Complete';
  };

  const getRewardText = () => {
    // Use assignment approval_reward if available (preferred for multi-assignment)
    if (assignment?.approval_reward) {
      return `$${assignment.approval_reward.toFixed(2)}`;
    }

    // Fallback to chore-level approval_reward (backward compatibility)
    if (chore.approval_reward) {
      return `$${chore.approval_reward.toFixed(2)}`;
    }

    // For approved range rewards (legacy method), show the final reward amount
    const isApproved = assignment?.is_approved || chore.approved_at || chore.is_approved;
    if (chore.is_range_reward && isApproved && chore.reward) {
      return `$${chore.reward.toFixed(2)}`;
    }

    // For pending range rewards, show the range
    if (chore.is_range_reward && chore.min_reward && chore.max_reward) {
      return `$${chore.min_reward.toFixed(2)} - $${chore.max_reward.toFixed(2)}`;
    }

    // For fixed rewards
    if (chore.reward) {
      return `$${chore.reward.toFixed(2)}`;
    }

    return 'No reward';
  };

  const isAvailableNow = () => {
    // Use assignment data if available (preferred for multi-assignment)
    if (assignment) {
      return !assignment.is_completed && !assignment.is_approved;
    }

    // Fallback to chore-level data (backward compatibility)
    const isCompleted = chore.completed_at || chore.completion_date || chore.is_completed;
    if (isCompleted) return false;
    if (chore.next_available_at) {
      return new Date(chore.next_available_at) <= new Date();
    }
    return true;
  };

  const getModeBadge = () => {
    // Don't show badge for single mode (default/traditional behavior)
    if (!assignmentMode || assignmentMode === 'single') return null;

    let badgeText = '';
    let badgeStyle = styles.modeBadgeMulti;

    if (assignmentMode === 'pool' || assignmentMode === 'unassigned') {
      badgeText = '🏊 Pool Chore';
      badgeStyle = styles.modeBadgePool;
    } else if (assignmentMode === 'assigned') {
      badgeText = '👤 Assigned to You';
      badgeStyle = styles.modeBadgeAssigned;
    } else if (assignmentMode === 'multi_independent') {
      badgeText = '👥 Personal Chore';
      badgeStyle = styles.modeBadgeMulti;
    }

    return (
      <View style={badgeStyle}>
        <Text style={styles.modeBadgeText}>{badgeText}</Text>
      </View>
    );
  };

  return (
    <View
      style={styles.card}
      testID="chore-card"
      accessible={true}
      accessibilityRole="button"
      accessibilityLabel={`Chore: ${chore.title}, Reward: ${getRewardText()}, Status: ${getStatusText()}`}
    >
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.title} accessibilityRole="header">{chore.title}</Text>
          {getModeBadge()}
        </View>
        <Text style={styles.reward} accessibilityLabel={`Reward: ${getRewardText()}`}>{getRewardText()}</Text>
      </View>

      {chore.description && (
        <Text style={styles.description} accessible={true}>{chore.description}</Text>
      )}

      {/* Show rejection reason if present */}
      {assignment?.rejection_reason && (
        <View
          style={styles.rejectionContainer}
          accessible={true}
          accessibilityRole="alert"
          accessibilityLabel={`This chore was rejected. Reason: ${assignment.rejection_reason}`}
        >
          <Text style={styles.rejectionLabel}>❌ Rejected:</Text>
          <Text style={styles.rejectionReason}>{assignment.rejection_reason}</Text>
        </View>
      )}

      <View style={styles.footer}>
        <Text style={styles.status}>{getStatusText()}</Text>

        {chore.is_recurring && (
          <Text style={styles.recurring}>
            🔄 Repeats every {chore.cooldown_days} day{chore.cooldown_days !== 1 ? 's' : ''}
          </Text>
        )}
      </View>

      {showCompleteButton && isAvailableNow() && onComplete && (
        <TouchableOpacity
          style={[styles.completeButton, isCompleting && styles.completingButton]}
          onPress={async () => {
            setIsCompleting(true);
            await onComplete(chore.id, assignmentId);
            setIsCompleting(false);
          }}
          testID="complete-chore-button"
          disabled={isCompleting}
          accessible={true}
          accessibilityRole="button"
          accessibilityLabel={assignmentMode === 'pool' || assignmentMode === 'unassigned' ? 'Claim and complete this chore' : 'Mark this chore as complete'}
          accessibilityHint="Double tap to complete this chore"
          accessibilityState={{ disabled: isCompleting }}
        >
          {isCompleting ? (
            <ActivityIndicator size="small" color="#fff" accessibilityLabel="Completing chore" />
          ) : (
            <Text style={styles.completeButtonText}>
              {assignmentMode === 'pool' || assignmentMode === 'unassigned' ? 'Claim & Complete' : 'Mark as Complete'}
            </Text>
          )}
        </TouchableOpacity>
      )}

      {showManageButtons && (
        <View style={styles.manageButtons}>
          {chore.is_disabled && onEnable && (
            <TouchableOpacity 
              style={[styles.enableButton, isProcessing && styles.processingButton]}
              onPress={async () => {
                setIsProcessing(true);
                await onEnable(chore.id);
                setIsProcessing(false);
              }}
              testID="enable-chore-button"
              disabled={isProcessing}
            >
              {isProcessing ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={styles.enableButtonText}>Enable Chore</Text>
              )}
            </TouchableOpacity>
          )}
          
          {!chore.is_disabled && onDisable && (
            <TouchableOpacity 
              style={[styles.disableButton, isProcessing && styles.processingButton]}
              onPress={async () => {
                setIsProcessing(true);
                await onDisable(chore.id);
                setIsProcessing(false);
              }}
              testID="disable-chore-button"
              disabled={isProcessing}
            >
              {isProcessing ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={styles.disableButtonText}>Disable Chore</Text>
              )}
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  titleContainer: {
    flex: 1,
    marginRight: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  reward: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  modeBadgeAssigned: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  modeBadgePool: {
    backgroundColor: '#5AC8FA',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  modeBadgeMulti: {
    backgroundColor: '#FF9500',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  modeBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
  },
  rejectionContainer: {
    backgroundColor: '#FFEBEE',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#FF3B30',
  },
  rejectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#D32F2F',
    marginBottom: 4,
  },
  rejectionReason: {
    fontSize: 13,
    color: '#B71C1C',
  },
  description: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  status: {
    fontSize: 12,
    color: '#999',
  },
  recurring: {
    fontSize: 12,
    color: '#666',
  },
  completeButton: {
    backgroundColor: '#34C759',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    marginTop: 12,
    alignItems: 'center',
  },
  completeButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  completingButton: {
    opacity: 0.7,
  },
  manageButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  enableButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  enableButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  disableButton: {
    flex: 1,
    backgroundColor: '#FF3B30',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  disableButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  processingButton: {
    opacity: 0.7,
  },
});