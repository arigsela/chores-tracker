import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl
} from 'react-native';
import { Alert } from '../utils/Alert';
import { useAuth } from '@/contexts/AuthContext';
import { choreAPI, Chore, AvailableChoresResponse, Assignment } from '@/api/chores';
import { ChoreCard } from '@/components/ChoreCard';
import ChoresManagementScreen from './ChoresManagementScreen';

type TabType = 'available' | 'active' | 'completed';

// Child-specific chores component to avoid hooks ordering issues
const ChildChoresView: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('available');
  const [chores, setChores] = useState<Chore[]>([]);
  // New state for multi-assignment support
  const [assignedChores, setAssignedChores] = useState<Array<{chore: Chore; assignment: Assignment; assignment_id: number}>>([]);
  const [poolChores, setPoolChores] = useState<Array<{chore: Chore; assignment: Assignment | null; assignment_id: number | null}>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchChores = async (refresh = false) => {
    try {
      if (refresh) setIsRefreshing(true);
      else setIsLoading(true);

      let fetchedChores: Chore[] = [];

      // Child view only (parent returns early above)
      if (activeTab === 'available') {
        // NEW: Handle multi-assignment response structure
        const availableResponse: AvailableChoresResponse = await choreAPI.getAvailableChores();
        setAssignedChores(availableResponse.assigned);
        setPoolChores(availableResponse.pool);
        // For backward compatibility with existing rendering logic
        fetchedChores = [];
      } else {
        // Fetch all assigned chores and filter
        const allChores = await choreAPI.getMyChores();

        if (activeTab === 'active') {
          fetchedChores = allChores.filter(c => {
            // For multi-assignment: check if user has an active (not completed) assignment
            if (c.assignments && c.assignments.length > 0) {
              const userAssignment = c.assignments.find(a => a.assignee_id === user?.id);
              if (userAssignment) {
                // User has assignment - show if not completed
                return !userAssignment.is_completed;
              }
              // No assignment for this user - don't show
              return false;
            }

            // Legacy fallback (for backward compatibility with old data)
            const isNotCompleted = !c.completed_at && !c.completion_date && !c.is_completed;
            const assignedToUser = (
              (c.assigned_to_id && c.assigned_to_id === user?.id) ||
              (c.assignee_id && c.assignee_id === user?.id)
            );
            return isNotCompleted && assignedToUser;
          });
        } else if (activeTab === 'completed') {
          fetchedChores = allChores.filter(c => {
            // For multi-assignment: check if user has a completed assignment
            if (c.assignments && c.assignments.length > 0) {
              const userAssignment = c.assignments.find(a => a.assignee_id === user?.id);
              if (userAssignment) {
                // User has assignment - show if completed
                return userAssignment.is_completed;
              }
              // No assignment for this user - don't show
              return false;
            }

            // Legacy fallback (for backward compatibility with old data)
            return (
              (c.completed_at || c.completion_date || c.is_completed) &&
              (c.assigned_to_id === user?.id || c.assignee_id === user?.id)
            );
          });

          // DEBUG: Log completed chores for balance audit
          if (activeTab === 'completed') {
            console.log('[CHORES AUDIT] Total chores returned from API:', allChores.length);
            console.log('[CHORES AUDIT] Filtered completed chores:', fetchedChores.length);

            let totalRewardSum = 0;
            const choreDetails = fetchedChores.map(chore => {
              // For multi-assignment, get user's specific assignment reward
              let rewardAmount = 0;
              if (chore.assignments && chore.assignments.length > 0) {
                const userAssignment = chore.assignments.find(a => a.assignee_id === user?.id);
                rewardAmount = userAssignment?.approval_reward || chore.reward || 0;
              } else {
                // Legacy: use chore-level reward
                rewardAmount = chore.approval_reward || chore.reward || 0;
              }

              totalRewardSum += rewardAmount;
              return {
                id: chore.id,
                title: chore.title,
                reward: chore.reward,
                approval_reward: chore.approval_reward,
                used_reward: rewardAmount,
                completed_at: chore.completed_at,
                completion_date: chore.completion_date,
                approved_at: chore.approved_at,
                is_approved: chore.is_approved,
                is_completed: chore.is_completed
              };
            });

            console.log('[CHORES AUDIT] Completed chores breakdown:', choreDetails);
            console.log('[CHORES AUDIT] Manual sum of visible chore rewards:', totalRewardSum);
          }
        }
      }

      setChores(fetchedChores);
    } catch (error) {
      console.error('Failed to fetch chores:', error);
      Alert.alert('Error', 'Failed to load chores. Please try again.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchChores();
  }, [activeTab]);

  // Get user role status
  const isParent = user?.role === 'parent';

  const handleCompleteChore = async (choreId: number, assignmentId?: number) => {
    try {
      setIsLoading(true);
      // NEW: Handle new response structure with assignment data
      const response = await choreAPI.completeChore(choreId);

      // Display backend message (explains claim vs. complete)
      if (response.message) {
        Alert.alert('Success', response.message);
      }

      // Refresh the chores list
      fetchChores(true);
    } catch (error) {
      console.error('Failed to complete chore:', error);
      Alert.alert('Error', 'Failed to complete chore. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveChore = async (chore: Chore) => {
    if (chore.is_range_reward && chore.min_reward && chore.max_reward) {
      // For range rewards, parent needs to select amount
      Alert.prompt(
        'Approve Chore',
        `Enter reward amount between $${chore.min_reward} and $${chore.max_reward}:`,
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Approve',
            onPress: async (value) => {
              const amount = parseFloat(value || '0');
              if (amount >= chore.min_reward && amount <= chore.max_reward) {
                try {
                  await choreAPI.approveChore(chore.id, amount);
                  Alert.alert('Success', 'Chore approved!');
                  fetchChores(true);
                } catch (error) {
                  Alert.alert('Error', 'Failed to approve chore.');
                }
              } else {
                Alert.alert('Invalid Amount', `Please enter an amount between $${chore.min_reward} and $${chore.max_reward}`);
              }
            }
          }
        ],
        'plain-text',
        '',
        'numeric'
      );
    } else {
      // Fixed reward
      Alert.alert(
        'Approve Chore',
        `Approve this chore with reward of $${chore.reward}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Approve',
            onPress: async () => {
              try {
                await choreAPI.approveChore(chore.id);
                Alert.alert('Success', 'Chore approved!');
                fetchChores(true);
              } catch (error) {
                Alert.alert('Error', 'Failed to approve chore.');
              }
            }
          }
        ]
      );
    }
  };

  const renderTab = (tab: TabType, label: string) => (
    <TouchableOpacity
      key={tab}
      style={[styles.tab, activeTab === tab && styles.activeTab]}
      onPress={() => setActiveTab(tab)}
      testID={`tab-${tab}`}
    >
      <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
        {label}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Chores</Text>
        <Text style={styles.subtitle}>
          {isParent ? 'Manage family chores' : 'Your assigned chores'}
        </Text>
      </View>

      <View style={styles.tabs}>
        {renderTab('available', isParent ? 'Pending Approval' : 'Available')}
        {renderTab('active', 'Active')}
        {renderTab('completed', 'Completed')}
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={() => fetchChores(true)} />
        }
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#007AFF" />
          </View>
        ) : activeTab === 'available' ? (
          // NEW: Multi-assignment view for "available" tab
          assignedChores.length === 0 && poolChores.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No chores available</Text>
            </View>
          ) : (
            <View style={styles.choresList}>
              {/* Assigned Chores Section */}
              {assignedChores.length > 0 && (
                <>
                  <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Your Assigned Chores</Text>
                    <View style={styles.sectionBadge}>
                      <Text style={styles.sectionBadgeText}>{assignedChores.length}</Text>
                    </View>
                  </View>
                  {assignedChores.map(({ chore, assignment, assignment_id }) => (
                    <ChoreCard
                      key={`assigned-${assignment_id}`}
                      chore={chore}
                      assignment={assignment}
                      assignmentId={assignment_id}
                      onComplete={() => handleCompleteChore(chore.id, assignment_id)}
                      showCompleteButton={true}
                      isChild={true}
                      assignmentMode="assigned"
                    />
                  ))}
                </>
              )}

              {/* Pool Chores Section */}
              {poolChores.length > 0 && (
                <>
                  <View style={[styles.sectionHeader, assignedChores.length > 0 && styles.sectionHeaderSpacing]}>
                    <Text style={styles.sectionTitle}>Available Pool Chores</Text>
                    <View style={styles.sectionBadge}>
                      <Text style={styles.sectionBadgeText}>{poolChores.length}</Text>
                    </View>
                  </View>
                  <Text style={styles.sectionSubtitle}>First to complete claims the chore</Text>
                  {poolChores.map(({ chore, assignment, assignment_id }) => (
                    <ChoreCard
                      key={`pool-${chore.id}`}
                      chore={chore}
                      assignment={assignment}
                      assignmentId={assignment_id}
                      onComplete={() => handleCompleteChore(chore.id, assignment_id)}
                      showCompleteButton={true}
                      isChild={true}
                      assignmentMode="pool"
                    />
                  ))}
                </>
              )}
            </View>
          )
        ) : chores.length === 0 ? (
          // Active/Completed tabs empty state
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              {activeTab === 'active'
                ? 'No active chores'
                : 'No completed chores'}
            </Text>
          </View>
        ) : (
          // Active/Completed tabs chore list
          <View style={styles.choresList}>
            {chores.map(chore => (
              <ChoreCard
                key={chore.id}
                chore={chore}
                onComplete={!isParent && activeTab === 'available' ? handleCompleteChore : undefined}
                showCompleteButton={!isParent && activeTab === 'available'}
                isChild={!isParent}
              />
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    paddingBottom: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  tab: {
    flex: 1,
    paddingVertical: 15,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 14,
    color: '#999',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 50,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 50,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
  choresList: {
    padding: 20,
  },
  // NEW: Multi-assignment section styles
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sectionHeaderSpacing: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  sectionBadge: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    minWidth: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sectionBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    marginTop: -8,
  },
});

// Main component that delegates to the appropriate view
export const ChoresScreen: React.FC = () => {
  const { user } = useAuth();
  const isParent = user?.role === 'parent';
  
  // Always render the same structure to avoid hooks violations
  return isParent ? <ChoresManagementScreen /> : <ChildChoresView />;
};