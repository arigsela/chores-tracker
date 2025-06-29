import React, { useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Swipeable from 'react-native-gesture-handler/Swipeable';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';
import { useScalePress } from '../../hooks/useAnimation';

const AnimatedChoreCard = ({
  chore,
  onPress,
  onComplete,
  onApprove,
  onEdit,
  onDisable,
  showActions = false,
  showEditButton = false,
}) => {
  const { scale, onPressIn, onPressOut } = useScalePress();
  const swipeableRef = useRef(null);

  const renderRightActions = (progress, dragX) => {
    if (!showActions) return null;

    const trans = dragX.interpolate({
      inputRange: [-200, -100, -50, 0],
      outputRange: [0, 0, 0.5, 1],
    });

    return (
      <View style={styles.rightActionsContainer}>
        {onEdit && showEditButton && (
          <Animated.View
            style={[
              styles.actionButton,
              {
                transform: [{ scale: trans }],
                opacity: trans,
              },
            ]}
          >
            <TouchableOpacity
              style={[styles.action, styles.editAction]}
              onPress={() => {
                swipeableRef.current?.close();
                onEdit(chore);
              }}
            >
              <Icon name="edit" size={24} color={colors.white} />
            </TouchableOpacity>
          </Animated.View>
        )}
        
        {onDisable && chore.status !== 'disabled' && (
          <Animated.View
            style={[
              styles.actionButton,
              {
                transform: [{ scale: trans }],
                opacity: trans,
              },
            ]}
          >
            <TouchableOpacity
              style={[styles.action, styles.disableAction]}
              onPress={() => {
                swipeableRef.current?.close();
                onDisable(chore.id);
              }}
            >
              <Icon name="block" size={24} color={colors.white} />
            </TouchableOpacity>
          </Animated.View>
        )}
      </View>
    );
  };

  const getStatusIcon = () => {
    switch (chore.status) {
      case 'completed':
      case 'approved':
        return 'check-circle';
      case 'pending':
        return 'hourglass-empty';
      case 'disabled':
        return 'block';
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (chore.status) {
      case 'completed':
      case 'approved':
        return colors.success;
      case 'pending':
        return colors.warning;
      case 'disabled':
        return colors.disabled;
      default:
        return colors.primary;
    }
  };

  const cardContent = (
    <Animated.View style={{ transform: [{ scale }] }}>
      <TouchableOpacity
        style={[
          styles.container,
          chore.status === 'disabled' && styles.disabledContainer,
        ]}
        onPress={onPress}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        activeOpacity={1}
      >
        <View style={styles.header}>
          <Text 
            style={[
              styles.title,
              chore.status === 'disabled' && styles.disabledText,
            ]}
            numberOfLines={1}
          >
            {chore.title}
          </Text>
          {getStatusIcon() && (
            <Icon
              name={getStatusIcon()}
              size={20}
              color={getStatusColor()}
            />
          )}
        </View>

        {chore.description ? (
          <Text 
            style={[
              styles.description,
              chore.status === 'disabled' && styles.disabledText,
            ]} 
            numberOfLines={2}
          >
            {chore.description}
          </Text>
        ) : null}

        <View style={styles.footer}>
          <View style={styles.reward}>
            <Icon name="attach-money" size={16} color={colors.success} />
            <Text style={styles.rewardText}>
              {chore.reward_type === 'range'
                ? `$${chore.reward_amount} - $${chore.max_reward_amount}`
                : `$${chore.reward_amount}`}
            </Text>
          </View>

          {chore.recurrence === 'recurring' && (
            <View style={styles.recurrence}>
              <Icon name="repeat" size={16} color={colors.primary} />
              <Text style={styles.recurrenceText}>
                Every {chore.cooldown_days === 1 ? 'day' : `${chore.cooldown_days} days`}
              </Text>
            </View>
          )}
        </View>

        {showActions && (
          <View style={styles.actions}>
            {onComplete && chore.status === 'created' && (
              <TouchableOpacity
                style={[styles.actionButton, styles.completeButton]}
                onPress={() => onComplete(chore.id)}
              >
                <Icon name="done" size={20} color={colors.white} />
                <Text style={styles.actionText}>Complete</Text>
              </TouchableOpacity>
            )}
            
            {onApprove && chore.status === 'pending' && (
              <TouchableOpacity
                style={[styles.actionButton, styles.approveButton]}
                onPress={() => onApprove(chore.id)}
              >
                <Icon name="check" size={20} color={colors.white} />
                <Text style={styles.actionText}>Approve</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </TouchableOpacity>
    </Animated.View>
  );

  if (showActions && (onEdit || onDisable)) {
    return (
      <Swipeable
        ref={swipeableRef}
        renderRightActions={renderRightActions}
        overshootRight={false}
      >
        {cardContent}
      </Swipeable>
    );
  }

  return cardContent;
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 3,
  },
  disabledContainer: {
    opacity: 0.7,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    ...typography.h4,
    color: colors.text,
    flex: 1,
    marginRight: 8,
  },
  disabledText: {
    textDecorationLine: 'line-through',
    color: colors.textSecondary,
  },
  description: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  reward: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rewardText: {
    ...typography.caption,
    color: colors.success,
    marginLeft: 4,
    fontWeight: '600',
  },
  recurrence: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  recurrenceText: {
    ...typography.caption,
    color: colors.primary,
    marginLeft: 4,
  },
  actions: {
    flexDirection: 'row',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginRight: 8,
  },
  completeButton: {
    backgroundColor: colors.primary,
  },
  approveButton: {
    backgroundColor: colors.success,
  },
  actionText: {
    ...typography.caption,
    color: colors.white,
    marginLeft: 4,
    fontWeight: '600',
  },
  rightActionsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  action: {
    justifyContent: 'center',
    alignItems: 'center',
    width: 60,
    height: '100%',
    marginLeft: 8,
    borderRadius: 12,
  },
  editAction: {
    backgroundColor: colors.info,
  },
  disableAction: {
    backgroundColor: colors.error,
  },
});

export default AnimatedChoreCard;