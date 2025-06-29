import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  Alert,
  Animated,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../store/authContext';
import { useError } from '../../contexts/ErrorContext';
import { useToast } from '../../contexts/ToastContext';
import { choreService } from '../../services/choreService';
import ChoreList from '../../components/chores/ChoreList';
import { SkeletonList } from '../../components/common/SkeletonPlaceholder';
import ErrorView from '../../components/common/ErrorView';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const ChildHomeScreen = () => {
  const navigation = useNavigation();
  const { user } = useAuth();
  const { showError } = useError();
  const { showSuccess, showError: showToastError } = useToast();
  const [chores, setChores] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  
  // Animations
  const headerOpacity = useRef(new Animated.Value(1)).current;
  const rewardScale = useRef(new Animated.Value(1)).current;
  
  useEffect(() => {
    // Simple fade in on mount
    headerOpacity.setValue(0);
    Animated.timing(headerOpacity, {
      toValue: 1,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, []);

  const loadChores = useCallback(async (showRefresh = false) => {
    try {
      if (showRefresh) setIsRefreshing(true);
      else setIsLoading(true);
      
      setError(null);
      const result = await choreService.getChildChores(user?.id);
      
      if (result.success) {
        // Filter to show only active chores (created status)
        const activeChores = result.data.filter(chore => chore.status === 'created');
        setChores(activeChores);
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
  }, [user?.id, showError]);

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
        // Animate reward box
        Animated.sequence([
          Animated.spring(rewardScale, {
            toValue: 1.1,
            tension: 100,
            friction: 5,
            useNativeDriver: true,
          }),
          Animated.spring(rewardScale, {
            toValue: 1,
            tension: 100,
            friction: 5,
            useNativeDriver: true,
          }),
        ]).start();
        
        showSuccess('Great job! Your chore has been submitted for approval.');
        setTimeout(() => {
          loadChores(true);
        }, 500);
      } else {
        showToastError(result.error || 'Failed to complete chore');
      }
    } catch (error) {
      showToastError('Failed to complete chore');
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
    <Animated.View style={[styles.header, { opacity: headerOpacity }]}>
      <Text style={styles.greeting}>Hi {user?.username}! 👋</Text>
      <Text style={styles.subtitle}>Ready to complete some chores?</Text>
      
      <Animated.View 
        style={[
          styles.rewardBox,
          { transform: [{ scale: rewardScale }] }
        ]}
      >
        <Text style={styles.rewardLabel}>Potential Rewards Today</Text>
        <Text style={styles.rewardAmount}>
          ${calculateTotalPotentialReward().toFixed(2)}
        </Text>
      </Animated.View>

      <View style={styles.statsContainer}>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{chores.length}</Text>
          <Text style={styles.statLabel}>To Do</Text>
        </View>
      </View>
    </Animated.View>
  );

  if (isLoading && !isRefreshing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.greeting}>Hi {user?.username}! 👋</Text>
          <Text style={styles.subtitle}>Loading your chores...</Text>
        </View>
        <SkeletonList count={4} />
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