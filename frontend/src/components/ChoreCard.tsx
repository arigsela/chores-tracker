import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Chore } from '@/api/chores';

interface ChoreCardProps {
  chore: Chore;
  onComplete?: (choreId: number) => void;
  showCompleteButton?: boolean;
  isChild?: boolean;
}

export const ChoreCard: React.FC<ChoreCardProps> = ({ 
  chore, 
  onComplete, 
  showCompleteButton = false,
  isChild = false 
}) => {
  const [isCompleting, setIsCompleting] = useState(false);
  const getStatusText = () => {
    if (chore.approved_at) return '✅ Approved';
    if (chore.completed_at && !chore.approved_at) return '⏳ Pending Approval';
    if (chore.completed_at) return '✓ Completed';
    if (chore.next_available_at) {
      const nextDate = new Date(chore.next_available_at);
      if (nextDate > new Date()) {
        return `🔒 Available ${nextDate.toLocaleDateString()}`;
      }
    }
    return '📋 Ready to Complete';
  };

  const getRewardText = () => {
    if (chore.approval_reward) {
      return `$${chore.approval_reward.toFixed(2)}`;
    }
    if (chore.is_range_reward && chore.min_reward && chore.max_reward) {
      return `$${chore.min_reward.toFixed(2)} - $${chore.max_reward.toFixed(2)}`;
    }
    if (chore.reward) {
      return `$${chore.reward.toFixed(2)}`;
    }
    return 'No reward';
  };

  const isAvailableNow = () => {
    if (chore.completed_at) return false;
    if (chore.next_available_at) {
      return new Date(chore.next_available_at) <= new Date();
    }
    return true;
  };

  return (
    <View style={styles.card} testID="chore-card">
      <View style={styles.header}>
        <Text style={styles.title}>{chore.title}</Text>
        <Text style={styles.reward}>{getRewardText()}</Text>
      </View>
      
      {chore.description && (
        <Text style={styles.description}>{chore.description}</Text>
      )}
      
      <View style={styles.footer}>
        <Text style={styles.status}>{getStatusText()}</Text>
        
        {chore.is_recurring && (
          <Text style={styles.recurring}>
            🔄 Repeats every {chore.cooldown_days} day{chore.cooldown_days !== 1 ? 's' : ''}
          </Text>
        )}
      </View>

      {showCompleteButton && isAvailableNow() && !chore.completed_at && onComplete && (
        <TouchableOpacity 
          style={[styles.completeButton, isCompleting && styles.completingButton]}
          onPress={async () => {
            setIsCompleting(true);
            await onComplete(chore.id);
            setIsCompleting(false);
          }}
          testID="complete-chore-button"
          disabled={isCompleting}
        >
          {isCompleting ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.completeButtonText}>Mark as Complete</Text>
          )}
        </TouchableOpacity>
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
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    marginRight: 8,
  },
  reward: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#007AFF',
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
});