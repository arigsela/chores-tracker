import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../store/authContext';
import { choreService } from '../../services/choreService';
import ChoreList from '../../components/chores/ChoreList';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const ChildHomeScreen = () => {
  const navigation = useNavigation();
  const { user } = useAuth();
  const [chores, setChores] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadChores = useCallback(async (showRefresh = false) => {
    try {
      if (showRefresh) setIsRefreshing(true);
      else setIsLoading(true);

      const result = await choreService.getChildChores(user?.id);
      
      if (result.success) {
        // Filter to show only active chores (created status)
        const activeChores = result.data.filter(chore => chore.status === 'created');
        setChores(activeChores);
      } else {
        Alert.alert('Error', result.error);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to load chores');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [user?.id]);

  useEffect(() => {
    if (user?.id) {
      loadChores();
    }
  }, [loadChores, user?.id]);

  const handleChorePress = (chore) => {
    // Navigate to chore detail screen (to be implemented)
    Alert.alert(
      chore.title,
      `${chore.description}\n\nReward: ${choreService.formatReward(
        chore.reward_type,
        chore.reward_amount,
        chore.max_reward_amount
      )}`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Mark Complete', onPress: () => handleComplete(chore.id) },
      ]
    );
  };

  const handleComplete = async (choreId) => {
    try {
      const result = await choreService.completeChore(choreId);
      if (result.success) {
        Alert.alert(
          'Success',
          'Great job! Your chore has been submitted for approval.',
          [{ text: 'OK', onPress: () => loadChores(true) }]
        );
      } else {
        Alert.alert('Error', result.error);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to complete chore');
    }
  };

  const calculateTotalPotentialReward = () => {
    return chores.reduce((total, chore) => {
      if (chore.reward_type === 'fixed') {
        return total + chore.reward_amount;
      } else if (chore.reward_type === 'range') {
        return total + chore.max_reward_amount;
      }
      return total;
    }, 0);
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <Text style={styles.greeting}>Hi {user?.username}! 👋</Text>
      <Text style={styles.subtitle}>Ready to complete some chores?</Text>
      
      <View style={styles.rewardBox}>
        <Text style={styles.rewardLabel}>Potential Rewards Today</Text>
        <Text style={styles.rewardAmount}>
          ${calculateTotalPotentialReward().toFixed(2)}
        </Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{chores.length}</Text>
          <Text style={styles.statLabel}>To Do</Text>
        </View>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ChoreList
        chores={chores}
        isLoading={isLoading}
        isRefreshing={isRefreshing}
        onRefresh={() => loadChores(true)}
        onChorePress={handleChorePress}
        showActions={true}
        onComplete={handleComplete}
        emptyMessage="No chores assigned yet. Check back later!"
        ListHeaderComponent={renderHeader}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    backgroundColor: colors.surface,
    padding: 20,
    marginBottom: 8,
  },
  greeting: {
    ...typography.h2,
    color: colors.text,
    marginBottom: 4,
  },
  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: 20,
  },
  rewardBox: {
    backgroundColor: colors.primaryLight,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  rewardLabel: {
    ...typography.label,
    color: 'white',
    opacity: 0.9,
  },
  rewardAmount: {
    ...typography.h1,
    color: 'white',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  statBox: {
    alignItems: 'center',
  },
  statNumber: {
    ...typography.h2,
    color: colors.primary,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 4,
  },
});

export default ChildHomeScreen;