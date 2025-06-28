import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';
import { choreService } from '../../services/choreService';

const ChoreCard = ({ chore, onPress, showActions = false, onComplete, onApprove }) => {
  const statusColor = choreService.getStatusColor(chore.status);
  const statusLabel = choreService.getStatusLabel(chore.status);
  const rewardText = choreService.formatReward(
    chore.reward_type,
    chore.reward_amount,
    chore.max_reward_amount
  );

  const renderRecurrence = () => {
    if (chore.recurrence === 'once') return null;
    
    const recurrenceIcons = {
      daily: 'repeat',
      weekly: 'event-repeat',
      monthly: 'date-range',
    };
    
    return (
      <View style={styles.recurrenceContainer}>
        <Icon
          name={recurrenceIcons[chore.recurrence] || 'repeat'}
          size={16}
          color={colors.textSecondary}
        />
        <Text style={styles.recurrenceText}>{chore.recurrence}</Text>
      </View>
    );
  };

  const renderActions = () => {
    if (!showActions) return null;

    return (
      <View style={styles.actionsContainer}>
        {chore.status === 'created' && onComplete && (
          <TouchableOpacity
            style={[styles.actionButton, styles.completeButton]}
            onPress={() => onComplete(chore.id)}
          >
            <Icon name="check" size={20} color="white" />
            <Text style={styles.actionButtonText}>Complete</Text>
          </TouchableOpacity>
        )}
        {chore.status === 'pending' && onApprove && (
          <TouchableOpacity
            style={[styles.actionButton, styles.approveButton]}
            onPress={() => onApprove(chore.id)}
          >
            <Icon name="check-circle" size={20} color="white" />
            <Text style={styles.actionButtonText}>Approve</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <TouchableOpacity
      style={[styles.container, { borderLeftColor: statusColor }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={1}>
          {chore.title}
        </Text>
        <View style={[styles.statusBadge, { backgroundColor: statusColor }]}>
          <Text style={styles.statusText}>{statusLabel}</Text>
        </View>
      </View>

      <Text style={styles.description} numberOfLines={2}>
        {chore.description}
      </Text>

      <View style={styles.footer}>
        <View style={styles.footerLeft}>
          {chore.assignee_name && (
            <View style={styles.assigneeContainer}>
              <Icon name="person" size={16} color={colors.textSecondary} />
              <Text style={styles.assigneeText}>{chore.assignee_name}</Text>
            </View>
          )}
          {renderRecurrence()}
        </View>

        <View style={styles.rewardContainer}>
          <Icon name="attach-money" size={18} color={colors.secondary} />
          <Text style={styles.rewardText}>{rewardText}</Text>
        </View>
      </View>

      {renderActions()}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    borderLeftWidth: 4,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 3,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    ...typography.h3,
    color: colors.text,
    flex: 1,
    marginRight: 8,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    ...typography.caption,
    color: 'white',
    fontWeight: '600',
  },
  description: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  footerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  assigneeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 16,
  },
  assigneeText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginLeft: 4,
  },
  recurrenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  recurrenceText: {
    ...typography.caption,
    color: colors.textSecondary,
    marginLeft: 4,
    textTransform: 'capitalize',
  },
  rewardContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rewardText: {
    ...typography.label,
    color: colors.secondary,
    marginLeft: 4,
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginLeft: 8,
  },
  completeButton: {
    backgroundColor: colors.primary,
  },
  approveButton: {
    backgroundColor: colors.secondary,
  },
  actionButtonText: {
    ...typography.label,
    color: 'white',
    marginLeft: 4,
    fontWeight: '600',
  },
});

export default ChoreCard;