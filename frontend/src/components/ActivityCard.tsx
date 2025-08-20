import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { Activity, getActivityIcon, getActivityColor, formatActivityTime } from '../api/activities';

interface ActivityCardProps {
  activity: Activity;
  onPress?: () => void;
}

export const ActivityCard: React.FC<ActivityCardProps> = ({ activity, onPress }) => {
  const icon = getActivityIcon(activity.activity_type);
  const color = getActivityColor(activity.activity_type);
  const timeAgo = formatActivityTime(activity.created_at);

  const getActivityDetails = () => {
    const { activity_data } = activity;
    switch (activity.activity_type) {
      case 'chore_approved':
        if (activity_data.reward_amount) {
          return `+$${activity_data.reward_amount.toFixed(2)}`;
        }
        break;
      case 'adjustment_applied':
        if (activity_data.amount !== undefined) {
          const amount = activity_data.amount;
          return amount >= 0 ? `+$${amount.toFixed(2)}` : `-$${Math.abs(amount).toFixed(2)}`;
        }
        break;
      case 'chore_created':
        if (activity_data.reward_amount) {
          return `$${activity_data.reward_amount.toFixed(2)}`;
        }
        break;
    }
    return null;
  };

  const activityDetails = getActivityDetails();
  const isMoneyActivity = activity.activity_type === 'chore_approved' || 
                         activity.activity_type === 'adjustment_applied';

  return (
    <TouchableOpacity 
      style={styles.container} 
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={onPress ? 0.7 : 1}
    >
      <View style={styles.content}>
        <View style={[styles.iconContainer, { backgroundColor: color + '20' }]}>
          <Text style={[styles.icon, { color }]}>{icon}</Text>
        </View>
        
        <View style={styles.textContainer}>
          <Text style={styles.description} numberOfLines={2}>
            {activity.description}
          </Text>
          
          <View style={styles.metaContainer}>
            <Text style={styles.userName}>
              {activity.user?.username}
            </Text>
            {activity.target_user && (
              <>
                <Text style={styles.arrow}> → </Text>
                <Text style={styles.targetUserName}>
                  {activity.target_user.username}
                </Text>
              </>
            )}
            <Text style={styles.dot}> • </Text>
            <Text style={styles.timeAgo}>{timeAgo}</Text>
          </View>
        </View>

        {activityDetails && (
          <View style={styles.amountContainer}>
            <Text style={[
              styles.amount,
              {
                color: isMoneyActivity && activity.activity_data.amount !== undefined && activity.activity_data.amount < 0 
                  ? '#F44336' 
                  : '#4CAF50'
              }
            ]}>
              {activityDetails}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginVertical: 4,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  content: {
    flexDirection: 'row',
    padding: 16,
    alignItems: 'center',
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  icon: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  textContainer: {
    flex: 1,
    marginRight: 12,
  },
  description: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1a1a1a',
    lineHeight: 20,
    marginBottom: 4,
  },
  metaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  userName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2196f3',
  },
  arrow: {
    fontSize: 12,
    color: '#999',
  },
  targetUserName: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4caf50',
  },
  dot: {
    fontSize: 12,
    color: '#999',
  },
  timeAgo: {
    fontSize: 12,
    color: '#666',
  },
  amountContainer: {
    alignItems: 'flex-end',
  },
  amount: {
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default ActivityCard;