import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  FlatList,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { format, startOfWeek, startOfMonth, isAfter, parseISO } from 'date-fns';
import { useAuth } from '../../store/authContext';
import { choreService } from '../../services/choreService';
import { userService } from '../../services/userService';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const RewardHistoryScreen = () => {
  const navigation = useNavigation();
  const { user } = useAuth();
  const isParent = user?.is_parent;
  
  const [completedChores, setCompletedChores] = useState([]);
  const [children, setChildren] = useState([]);
  const [selectedChild, setSelectedChild] = useState('all');
  const [selectedPeriod, setSelectedPeriod] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [statistics, setStatistics] = useState({
    totalEarned: 0,
    totalPending: 0,
    totalApproved: 0,
    choreCount: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    calculateStatistics();
  }, [completedChores, selectedChild, selectedPeriod]);

  const loadData = async (refresh = false) => {
    try {
      if (refresh) setIsRefreshing(true);
      else setIsLoading(true);

      if (isParent) {
        // Load children list
        const childrenResult = await userService.getChildren();
        if (childrenResult.success) {
          setChildren(childrenResult.data);
        }

        // Load all completed chores
        const choresResult = await choreService.getAllChildrenCompletedChores();
        if (choresResult.success) {
          setCompletedChores(choresResult.data);
        }
      } else {
        // Child view - load their own completed chores
        const choresResult = await choreService.getChildChores();
        if (choresResult.success) {
          const completed = choresResult.data.filter(chore => chore.is_completed);
          setCompletedChores(completed);
        }
      }
    } catch (error) {
      console.error('Error loading reward history:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const getFilteredChores = () => {
    let filtered = [...completedChores];

    // Filter by child (parent view only)
    if (isParent && selectedChild !== 'all') {
      filtered = filtered.filter(chore => chore.assignee_id === parseInt(selectedChild));
    }

    // Filter by time period
    if (selectedPeriod !== 'all' && filtered.length > 0) {
      const now = new Date();
      let startDate;

      switch (selectedPeriod) {
        case 'week':
          startDate = startOfWeek(now, { weekStartsOn: 0 }); // Sunday
          break;
        case 'month':
          startDate = startOfMonth(now);
          break;
        default:
          startDate = null;
      }

      if (startDate) {
        filtered = filtered.filter(chore => {
          const choreDate = chore.completed_at ? parseISO(chore.completed_at) : null;
          return choreDate && isAfter(choreDate, startDate);
        });
      }
    }

    // Sort by completion date (newest first)
    return filtered.sort((a, b) => {
      const dateA = a.completed_at ? new Date(a.completed_at) : new Date();
      const dateB = b.completed_at ? new Date(b.completed_at) : new Date();
      return dateB - dateA;
    });
  };

  const calculateStatistics = () => {
    const filtered = getFilteredChores();
    
    const stats = filtered.reduce((acc, chore) => {
      const amount = chore.is_approved 
        ? (chore.approved_reward_amount || chore.reward || 0)
        : (chore.reward_type === 'range' ? chore.max_reward_amount : chore.reward_amount);
      
      if (chore.is_approved) {
        acc.totalApproved += amount;
        acc.totalEarned += amount;
      } else {
        acc.totalPending += amount;
      }
      
      acc.choreCount += 1;
      return acc;
    }, {
      totalEarned: 0,
      totalPending: 0,
      totalApproved: 0,
      choreCount: 0,
    });

    setStatistics(stats);
  };

  const renderStatCard = (title, amount, color, icon) => (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <View style={styles.statHeader}>
        <Icon name={icon} size={20} color={color} />
        <Text style={styles.statTitle}>{title}</Text>
      </View>
      <Text style={[styles.statAmount, { color }]}>${amount.toFixed(2)}</Text>
    </View>
  );

  const renderFilters = () => (
    <View style={styles.filtersContainer}>
      {isParent && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow}>
          <TouchableOpacity
            style={[styles.filterChip, selectedChild === 'all' && styles.filterChipActive]}
            onPress={() => setSelectedChild('all')}
          >
            <Text style={[styles.filterText, selectedChild === 'all' && styles.filterTextActive]}>
              All Children
            </Text>
          </TouchableOpacity>
          {children.map(child => (
            <TouchableOpacity
              key={child.id}
              style={[styles.filterChip, selectedChild === child.id.toString() && styles.filterChipActive]}
              onPress={() => setSelectedChild(child.id.toString())}
            >
              <Text style={[styles.filterText, selectedChild === child.id.toString() && styles.filterTextActive]}>
                {child.username}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}
      
      <View style={styles.periodFilters}>
        <TouchableOpacity
          style={[styles.periodChip, selectedPeriod === 'all' && styles.periodChipActive]}
          onPress={() => setSelectedPeriod('all')}
        >
          <Text style={[styles.periodText, selectedPeriod === 'all' && styles.periodTextActive]}>
            All Time
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.periodChip, selectedPeriod === 'week' && styles.periodChipActive]}
          onPress={() => setSelectedPeriod('week')}
        >
          <Text style={[styles.periodText, selectedPeriod === 'week' && styles.periodTextActive]}>
            This Week
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.periodChip, selectedPeriod === 'month' && styles.periodChipActive]}
          onPress={() => setSelectedPeriod('month')}
        >
          <Text style={[styles.periodText, selectedPeriod === 'month' && styles.periodTextActive]}>
            This Month
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderChoreItem = ({ item }) => {
    const amount = item.is_approved 
      ? (item.approved_reward_amount || item.reward || 0)
      : (item.reward_type === 'range' ? item.max_reward_amount : item.reward_amount);
    
    const choreDate = item.completed_at ? parseISO(item.completed_at) : new Date();
    const assigneeName = isParent && item.assignee_name ? item.assignee_name : null;

    return (
      <View style={styles.choreItem}>
        <View style={styles.choreItemLeft}>
          <Text style={styles.choreTitle}>{item.title}</Text>
          <View style={styles.choreMetadata}>
            <Text style={styles.choreDate}>
              {format(choreDate, 'MMM d, yyyy')}
            </Text>
            {assigneeName && (
              <Text style={styles.choreAssignee}> • {assigneeName}</Text>
            )}
          </View>
        </View>
        <View style={styles.choreItemRight}>
          <Text style={[styles.choreAmount, { color: item.is_approved ? colors.success : colors.warning }]}>
            ${amount.toFixed(2)}
          </Text>
          <Text style={[styles.choreStatus, { color: item.is_approved ? colors.success : colors.warning }]}>
            {item.is_approved ? 'Approved' : 'Pending'}
          </Text>
        </View>
      </View>
    );
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  const filteredChores = getFilteredChores();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Reward History</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => loadData(true)}
            colors={[colors.primary]}
            tintColor={colors.primary}
          />
        }
      >
        {/* Statistics Cards */}
        <View style={styles.statsContainer}>
          {renderStatCard('Total Earned', statistics.totalApproved, colors.success, 'attach-money')}
          {renderStatCard('Pending', statistics.totalPending, colors.warning, 'hourglass-empty')}
        </View>

        <View style={styles.summaryContainer}>
          <Text style={styles.summaryText}>
            {statistics.choreCount} chore{statistics.choreCount !== 1 ? 's' : ''} completed
          </Text>
        </View>

        {/* Filters */}
        {renderFilters()}

        {/* Transactions List */}
        <View style={styles.transactionsContainer}>
          <Text style={styles.sectionTitle}>Transactions</Text>
          
          {filteredChores.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="receipt" size={48} color={colors.textSecondary} />
              <Text style={styles.emptyText}>No completed chores found</Text>
              <Text style={styles.emptySubtext}>
                {selectedPeriod !== 'all' ? 'Try selecting a different time period' : 'Complete some chores to see them here'}
              </Text>
            </View>
          ) : (
            <FlatList
              data={filteredChores}
              renderItem={renderChoreItem}
              keyExtractor={(item) => item.id.toString()}
              scrollEnabled={false}
              ItemSeparatorComponent={() => <View style={styles.separator} />}
            />
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.text,
  },
  content: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 20,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
  },
  statHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statTitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginLeft: 8,
    textTransform: 'uppercase',
  },
  statAmount: {
    ...typography.h2,
    fontWeight: '700',
  },
  summaryContainer: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  summaryText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  filtersContainer: {
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  filterRow: {
    marginBottom: 12,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: colors.surface,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterText: {
    ...typography.label,
    color: colors.text,
  },
  filterTextActive: {
    color: 'white',
  },
  periodFilters: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  periodChip: {
    flex: 1,
    paddingVertical: 10,
    backgroundColor: colors.surface,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  periodChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  periodText: {
    ...typography.label,
    color: colors.text,
  },
  periodTextActive: {
    color: 'white',
  },
  transactionsContainer: {
    flex: 1,
    backgroundColor: colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingHorizontal: 16,
    minHeight: 300,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.text,
    marginBottom: 16,
  },
  choreItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
  },
  choreItemLeft: {
    flex: 1,
    marginRight: 16,
  },
  choreTitle: {
    ...typography.body,
    color: colors.text,
    marginBottom: 4,
  },
  choreMetadata: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  choreDate: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  choreAssignee: {
    ...typography.caption,
    color: colors.primary,
  },
  choreItemRight: {
    alignItems: 'flex-end',
  },
  choreAmount: {
    ...typography.h4,
    fontWeight: '600',
    marginBottom: 2,
  },
  choreStatus: {
    ...typography.caption,
    textTransform: 'uppercase',
  },
  separator: {
    height: 1,
    backgroundColor: colors.border,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: 16,
  },
  emptySubtext: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 8,
    textAlign: 'center',
  },
});

export default RewardHistoryScreen;