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
import { useError } from '../../contexts/ErrorContext';
import { choreService } from '../../services/choreService';
import ChoreList from '../../components/chores/ChoreList';
import { SkeletonList } from '../../components/common/SkeletonPlaceholder';
import ErrorView from '../../components/common/ErrorView';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const ParentHomeScreen = () => {
  const navigation = useNavigation();
  const { user } = useAuth();
  const { showError } = useError();
  const [chores, setChores] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const loadChores = useCallback(async (showRefresh = false) => {
    try {
      if (showRefresh) setIsRefreshing(true);
      else setIsLoading(true);
      
      setError(null);
      const result = await choreService.getAllChores();
      
      if (result.success) {
        setChores(result.data);
      } else {
        const errorMsg = result.error || 'Failed to load chores';
        setError(errorMsg);
        if (!showRefresh) {
          showError(errorMsg, {
            key: 'loadChores',
            retryCallback: () => loadChores(false),
          });
        }
      }
    } catch (error) {
      const errorMsg = error.message || 'Failed to load chores';
      setError(errorMsg);
      if (!showRefresh) {
        showError(error, {
          key: 'loadChores',
          retryCallback: () => loadChores(false),
        });
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [showError]);

  useEffect(() => {
    loadChores();
  }, [loadChores]);

  const handleChorePress = (chore) => {
    navigation.navigate('EditChore', { chore });
  };

  const handleApprove = async (choreId) => {
    const chore = chores.find(c => c.id === choreId);
    if (!chore) return;

    // For range rewards, we need to ask for the amount
    if (chore.reward_type === 'range') {
      // For now, approve with max amount
      // TODO: Implement custom input dialog
      Alert.alert(
        'Approve Chore',
        `This chore has a reward range of $${chore.reward_amount} - $${chore.max_reward_amount}. Approving with maximum amount.`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Approve',
            onPress: () => performApproval(choreId, chore.max_reward_amount),
          },
        ]
      );
    } else {
      await performApproval(choreId, chore.reward_amount);
    }
  };

  const performApproval = async (choreId, rewardAmount) => {
    try {
      const result = await choreService.approveChore(choreId, rewardAmount);
      if (result.success) {
        Alert.alert('Success', 'Chore approved successfully');
        loadChores(true);
      } else {
        Alert.alert('Error', result.error);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to approve chore');
    }
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <Text style={styles.greeting}>Welcome back, {user?.username}!</Text>
      <View style={styles.statsContainer}>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{chores.filter(c => c.status === 'pending').length}</Text>
          <Text style={styles.statLabel}>Pending</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{chores.filter(c => c.status === 'created').length}</Text>
          <Text style={styles.statLabel}>Active</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{chores.filter(c => c.status === 'approved').length}</Text>
          <Text style={styles.statLabel}>Completed</Text>
        </View>
      </View>
    </View>
  );

  if (isLoading && !isRefreshing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.greeting}>Welcome back, {user?.username}!</Text>
        </View>
        <SkeletonList count={5} />
      </SafeAreaView>
    );
  }

  if (error && !isRefreshing && chores.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <ErrorView 
          error={error}
          onRetry={() => loadChores(false)}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ChoreList
        chores={chores}
        isLoading={isLoading}
        isRefreshing={isRefreshing}
        onRefresh={() => loadChores(true)}
        onChorePress={handleChorePress}
        showActions={true}
        onApprove={handleApprove}
        onEdit={handleChorePress}
        showEditButton={true}
        emptyMessage="No chores created yet. Tap the + button to create your first chore!"
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
    marginBottom: 16,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statBox: {
    alignItems: 'center',
    flex: 1,
  },
  statNumber: {
    ...typography.h1,
    color: colors.primary,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 4,
  },
});

export default ParentHomeScreen;