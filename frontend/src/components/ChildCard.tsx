import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { ChildWithChores } from '../api/users';

interface ChildCardProps {
  child: ChildWithChores & {
    completed_chores?: number;  // Allow override from allowance summary
    balance_due?: number;       // Allow override from allowance summary
  };
  onPress: () => void;
  onResetPassword?: () => void;
  pendingCount?: number; // Override calculated pending count
}

const ChildCard: React.FC<ChildCardProps> = (props) => {
  const { child, onPress, onResetPassword } = props;

  // Count active chores (not completed, not approved)
  const activeChores = child.chores?.filter(c => !c.is_completed).length || 0;

  // Use provided completed_chores if available (from allowance summary), otherwise calculate
  // Completed = approved chores
  const completedChores = child.completed_chores !== undefined
    ? child.completed_chores
    : (child.chores?.filter(c => c.is_approved).length || 0);

  // Use provided pendingCount if available, otherwise calculate from child.chores
  // Pending = completed but not yet approved
  const pendingApproval = props.pendingCount !== undefined
    ? props.pendingCount
    : (child.chores?.filter(c => c.is_completed && !c.is_approved).length || 0);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.name}>{child.username}</Text>
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>
            {child.is_active ? 'Active' : 'Inactive'}
          </Text>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}>
          <Text style={styles.statValue}>{activeChores}</Text>
          <Text style={styles.statLabel}>Active</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statValue, styles.pendingValue]}>{pendingApproval}</Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
        <View style={styles.stat}>
          <Text style={[styles.statValue, styles.completedValue]}>{completedChores}</Text>
          <Text style={styles.statLabel}>Completed</Text>
        </View>
      </View>

      <View style={styles.footer}>
        <TouchableOpacity onPress={onPress} style={styles.detailsButton}>
          <Text style={styles.viewDetails}>View Details →</Text>
        </TouchableOpacity>
        {onResetPassword && (
          <TouchableOpacity onPress={onResetPassword} style={styles.resetButton}>
            <Text style={styles.resetButtonText}>Reset Password</Text>
          </TouchableOpacity>
        )}
      </View>
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
    alignItems: 'center',
    marginBottom: 16,
  },
  name: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  statusBadge: {
    backgroundColor: '#e7f5e7',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    color: '#2e7d2e',
    fontWeight: '600',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#f0f0f0',
  },
  stat: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  pendingValue: {
    color: '#ff9800',
  },
  completedValue: {
    color: '#4caf50',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
  footer: {
    marginTop: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailsButton: {
    flex: 1,
  },
  viewDetails: {
    fontSize: 14,
    color: '#2196f3',
    fontWeight: '600',
    textAlign: 'center',
  },
  resetButton: {
    flex: 1,
    backgroundColor: '#dc3545',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  resetButtonText: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '600',
  },
});

export default ChildCard;