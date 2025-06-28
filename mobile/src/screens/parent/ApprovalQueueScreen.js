import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  Alert,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { choreService } from '../../services/choreService';
import ChoreCard from '../../components/chores/ChoreCard';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const ApprovalQueueScreen = () => {
  const [pendingChores, setPendingChores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPendingChores = useCallback(async () => {
    try {
      const result = await choreService.getAllChores();
      
      if (result.success && result.data) {
        // Filter only pending chores
        const pending = result.data.filter(chore => chore.status === 'pending');
        setPendingChores(pending);
      } else {
        Alert.alert('Error', result.error || 'Failed to load pending chores');
      }
    } catch (error) {
      console.error('Error fetching pending chores:', error);
      Alert.alert('Error', 'Failed to load pending chores');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchPendingChores();
  }, [fetchPendingChores]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchPendingChores();
  }, [fetchPendingChores]);

  const handleApprove = useCallback(async (chore) => {
    try {
      let rewardAmount = chore.reward_amount;
      
      // For range rewards, use the max amount
      if (chore.reward_type === 'range' && chore.max_reward_amount) {
        rewardAmount = chore.max_reward_amount;
        
        Alert.alert(
          'Approve Chore',
          `Approving with maximum reward of $${rewardAmount}`,
          [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Approve',
              onPress: async () => {
                await choreService.approveChore(chore.id, rewardAmount);
                Alert.alert('Success', 'Chore approved successfully!');
                fetchPendingChores();
              },
            },
          ]
        );
      } else {
        // Fixed reward - approve directly
        await choreService.approveChore(chore.id, rewardAmount);
        Alert.alert('Success', 'Chore approved successfully!');
        fetchPendingChores();
      }
    } catch (error) {
      console.error('Error approving chore:', error);
      Alert.alert('Error', 'Failed to approve chore');
    }
  }, [fetchPendingChores]);

  const renderChore = ({ item }) => (
    <ChoreCard
      chore={item}
      showActions={true}
      onApprove={() => handleApprove(item)}
    />
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="check-circle" size={80} color={colors.textSecondary} />
      <Text style={styles.emptyTitle}>No Pending Approvals</Text>
      <Text style={styles.emptySubtitle}>
        All chores have been reviewed
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
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Approval Queue</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{pendingChores.length}</Text>
        </View>
      </View>

      <FlatList
        data={pendingChores}
        renderItem={renderChore}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[colors.primary]}
          />
        }
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  headerTitle: {
    ...typography.h2,
    color: colors.text,
  },
  badge: {
    backgroundColor: colors.primary,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 4,
    minWidth: 24,
    alignItems: 'center',
  },
  badgeText: {
    ...typography.body2,
    color: colors.white,
    fontWeight: 'bold',
  },
  listContent: {
    flexGrow: 1,
    paddingBottom: 20,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
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
});

export default ApprovalQueueScreen;