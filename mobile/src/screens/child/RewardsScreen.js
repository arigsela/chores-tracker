import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { choreService } from '../../services/choreService';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const RewardsScreen = () => {
  const navigation = useNavigation();
  const [rewards, setRewards] = useState([]);
  const [totalEarned, setTotalEarned] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRewards = useCallback(async () => {
    try {
      const result = await choreService.getAllChores();
      
      if (result.success && result.data) {
        // Filter only approved chores (these have rewards)
        const approvedChores = result.data.filter(chore => chore.status === 'approved');
        
        // Calculate total rewards
        const total = approvedChores.reduce((sum, chore) => {
          return sum + (chore.approved_reward_amount || 0);
        }, 0);
        
        setRewards(approvedChores);
        setTotalEarned(total);
      }
    } catch (error) {
      console.error('Error fetching rewards:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRewards();
  }, [fetchRewards]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchRewards();
  }, [fetchRewards]);

  const renderReward = ({ item }) => (
    <View style={styles.rewardCard}>
      <View style={styles.rewardIcon}>
        <Icon name="stars" size={24} color={colors.success} />
      </View>
      <View style={styles.rewardContent}>
        <Text style={styles.rewardTitle}>{item.title}</Text>
        <Text style={styles.rewardDate}>
          Completed on {new Date(item.updated_at).toLocaleDateString()}
        </Text>
      </View>
      <View style={styles.rewardAmount}>
        <Text style={styles.rewardAmountText}>
          ${item.approved_reward_amount}
        </Text>
      </View>
    </View>
  );

  const renderHeader = () => (
    <>
      <View style={styles.summaryCard}>
        <Icon name="account-balance-wallet" size={48} color={colors.primary} />
        <Text style={styles.summaryLabel}>Total Earned</Text>
        <Text style={styles.summaryAmount}>${totalEarned.toFixed(2)}</Text>
        <Text style={styles.summarySubtext}>
          From {rewards.length} completed chores
        </Text>
      </View>
      
      <TouchableOpacity
        style={styles.historyButton}
        onPress={() => navigation.navigate('RewardHistory')}
      >
        <Icon name="history" size={24} color={colors.primary} />
        <Text style={styles.historyButtonText}>View Full History</Text>
        <Icon name="chevron-right" size={24} color={colors.primary} />
      </TouchableOpacity>
    </>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="sentiment-satisfied-alt" size={80} color={colors.textSecondary} />
      <Text style={styles.emptyTitle}>No Rewards Yet</Text>
      <Text style={styles.emptySubtitle}>
        Complete chores to earn rewards!
      </Text>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={rewards}
        renderItem={renderReward}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[colors.primary]}
          />
        }
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmptyState}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    flexGrow: 1,
    paddingBottom: 20,
  },
  summaryCard: {
    backgroundColor: colors.primaryLight,
    margin: 16,
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
  },
  summaryLabel: {
    ...typography.body1,
    color: colors.primary,
    marginTop: 8,
  },
  summaryAmount: {
    ...typography.h1,
    color: colors.primary,
    marginTop: 4,
    fontWeight: 'bold',
  },
  summarySubtext: {
    ...typography.body2,
    color: colors.primary,
    marginTop: 4,
    opacity: 0.8,
  },
  rewardCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    marginHorizontal: 16,
    marginVertical: 4,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  rewardIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.successLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  rewardContent: {
    flex: 1,
  },
  rewardTitle: {
    ...typography.body1,
    color: colors.text,
    fontWeight: '500',
  },
  rewardDate: {
    ...typography.body2,
    color: colors.textSecondary,
    marginTop: 2,
  },
  rewardAmount: {
    backgroundColor: colors.success,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  rewardAmountText: {
    ...typography.body2,
    color: colors.white,
    fontWeight: 'bold',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingTop: 100,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    ...typography.body1,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  historyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  historyButtonText: {
    ...typography.body1,
    color: colors.text,
    flex: 1,
    marginLeft: 12,
    fontWeight: '500',
  },
});

export default RewardsScreen;