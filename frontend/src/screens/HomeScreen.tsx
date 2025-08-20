import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { useAuth } from '@/contexts/AuthContext';
import { choreAPI } from '@/api/chores';
import { ActivityFeed } from '@/components/ActivityFeed';
import { FinancialSummaryCards } from '@/components/FinancialSummaryCards';

type TabName = 'Home' | 'Chores' | 'Children' | 'Approvals' | 'Balance' | 'Profile' | 'Reports' | 'Statistics';

interface HomeScreenProps {
  onNavigate?: (tab: TabName) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ onNavigate }) => {
  const { user } = useAuth();
  const isParent = user?.role === 'parent';
  const [activeChoresCount, setActiveChoresCount] = useState(0);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);
  const [completedTodayCount, setCompletedTodayCount] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    fetchDashboardStats();
  }, [user, isParent]);

  const fetchDashboardStats = async () => {
    try {
      if (isParent) {
        // For parents: get pending approvals and total active chores
        const pendingChores = await choreAPI.getPendingApprovalChores();
        setPendingApprovalsCount(pendingChores.length);

        const allChores = await choreAPI.getMyChores();
        const activeChores = allChores.filter(c => 
          !c.is_disabled && 
          !c.completed_at && 
          !c.completion_date && 
          !c.is_completed
        );
        setActiveChoresCount(activeChores.length);
      } else {
        // For children: get active chores assigned to them
        const allChores = await choreAPI.getMyChores();
        
        // Filter for active chores assigned to this child
        const activeChores = allChores.filter(c => {
          // Check if chore is not completed
          const isNotCompleted = !c.completed_at && !c.completion_date && !c.is_completed;
          
          // Check assignment - handle both field names
          const assignedToUser = (
            (c.assigned_to_id && c.assigned_to_id === user?.id) ||
            (c.assignee_id && c.assignee_id === user?.id)
          );
          
          return isNotCompleted && assignedToUser;
        });
        setActiveChoresCount(activeChores.length);

        // Get completed chores from today
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
        const completedToday = allChores.filter(c => {
          const completionDate = c.completed_at || c.completion_date;
          if (!completionDate) return false;
          const choreDate = new Date(completionDate).toISOString().split('T')[0];
          return choreDate === today && (c.assigned_to_id === user?.id || c.assignee_id === user?.id);
        });
        setCompletedTodayCount(completedToday.length);
      }
      
      // Trigger activity feed refresh after stats update
      setRefreshKey(prev => prev + 1);
    } catch (error) {
      console.error('[HomeScreen] Failed to fetch dashboard stats:', error);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.header}>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.username}>{user?.username}!</Text>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{isParent ? pendingApprovalsCount : activeChoresCount}</Text>
            <Text style={styles.statLabel}>
              {isParent ? 'Pending Approvals' : 'Active Chores'}
            </Text>
          </View>
          
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{isParent ? activeChoresCount : completedTodayCount}</Text>
            <Text style={styles.statLabel}>
              {isParent ? 'Active Chores' : 'Completed Today'}
            </Text>
          </View>
        </View>

        {/* Financial Summary Cards for Parents */}
        {isParent && (
          <FinancialSummaryCards 
            refreshKey={refreshKey}
            onViewReports={() => {
              if (onNavigate) {
                onNavigate('Reports');
              }
            }}
          />
        )}

        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <TouchableOpacity 
            style={styles.actionCard}
            onPress={() => {
              if (onNavigate) {
                onNavigate('Chores');
              }
            }}
          >
            <Text style={styles.actionText}>
              {isParent 
                ? '📝 Create New Chore' 
                : '✅ View Available Chores'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.actionCard}
            onPress={() => {
              if (onNavigate) {
                onNavigate(isParent ? 'Children' : 'Balance');
              }
            }}
          >
            <Text style={styles.actionText}>
              {isParent 
                ? '👨‍👩‍👧‍👦 Manage Children' 
                : '💰 Check Balance'}
            </Text>
          </TouchableOpacity>
          {isParent && (
            <>
              <TouchableOpacity 
                style={styles.actionCard}
                onPress={() => {
                  if (onNavigate) {
                    onNavigate('Reports');
                  }
                }}
              >
                <Text style={styles.actionText}>
                  📊 View Financial Reports
                </Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.actionCard}
                onPress={() => {
                  if (onNavigate) {
                    onNavigate('Statistics');
                  }
                }}
              >
                <Text style={styles.actionText}>
                  📈 View Statistics & Trends
                </Text>
              </TouchableOpacity>
            </>
          )}
        </View>

        <View style={styles.activitySection}>
          <ActivityFeed 
            limit={10}
            showHeader={true}
            refreshKey={refreshKey}
          />
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    flexGrow: 1,
    padding: 20,
  },
  header: {
    marginBottom: 30,
  },
  greeting: {
    fontSize: 18,
    color: '#666',
  },
  username: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginHorizontal: 5,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  quickActions: {
    marginBottom: 20,
  },
  activitySection: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  actionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    cursor: 'pointer' as any, // For web
  },
  actionText: {
    fontSize: 16,
    color: '#333',
  },
});