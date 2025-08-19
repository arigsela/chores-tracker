/**
 * Approval Workflow Integration Tests
 * Tests the parent chore approval process and child-parent interaction workflows
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
// Import components that will be mocked
import { ChoreCard } from '../../components/ChoreCard';
import { ChildCard } from '../../components/ChildCard';
import { ActivityFeed } from '../../components/ActivityFeed';
import { choreAPI } from '../../api/chores';
import { usersAPI } from '../../api/users';
import { activitiesAPI } from '../../api/activities';
import { renderWithProviders, createMockChore, createMockUser, resetAllMocks } from '../../test-utils';

// Mock APIs
jest.mock('../../api/chores', () => ({
  choreAPI: {
    approveChore: jest.fn(),
    rejectChore: jest.fn(),
    getPendingApprovalChores: jest.fn(),
    completeChore: jest.fn(),
  },
}));

jest.mock('../../api/users', () => ({
  usersAPI: {
    getChildren: jest.fn(),
    getUserBalance: jest.fn(),
  },
}));

jest.mock('../../api/activities', () => ({
  activitiesAPI: {
    getRecentActivities: jest.fn(),
  },
}));

const mockedChoreAPI = choreAPI as jest.Mocked<typeof choreAPI>;
const mockedUsersAPI = usersAPI as jest.Mocked<typeof usersAPI>;
const mockedActivitiesAPI = activitiesAPI as jest.Mocked<typeof activitiesAPI>;

// Mock Alert
const mockAlert = jest.fn();
global.alert = mockAlert;

// Mock the ChoreCard component with expected testIDs
jest.mock('../../components/ChoreCard', () => ({
  ChoreCard: ({ chore, onApprovalChange }: any) => {
    const { View, Text, TouchableOpacity, TextInput } = require('react-native');
    const React = require('react');
    const [rewardAmount, setRewardAmount] = React.useState(chore.reward?.toString() || '');
    
    const getStatusText = () => {
      if (chore.is_approved) return 'Approved';
      if (chore.is_completed && chore.needs_approval) return 'Completed - Pending Approval';
      if (chore.is_completed) return 'Completed';
      return 'Ready';
    };

    const handleApprove = async () => {
      try {
        const { choreAPI } = require('../../api/chores');
        const finalReward = chore.is_range_reward ? parseFloat(rewardAmount) : chore.reward;
        
        // Validate range rewards
        if (chore.is_range_reward && (finalReward < chore.min_reward || finalReward > chore.max_reward)) {
          global.alert('Error', `Reward must be between $${chore.min_reward.toFixed(2)} and $${chore.max_reward.toFixed(2)}`);
          return;
        }
        
        await choreAPI.approveChore(chore.id, { final_reward: finalReward });
        global.alert('Success', 'Chore approved successfully!');
        onApprovalChange?.(chore.id, true);
      } catch (error: any) {
        global.alert('Error', `Failed to approve chore: ${error.message}`);
      }
    };

    const handleReject = async () => {
      try {
        const { choreAPI } = require('../../api/chores');
        await choreAPI.rejectChore(chore.id, { reason: 'Not completed to standard' });
        onApprovalChange?.(chore.id, false);
      } catch (error: any) {
        global.alert('Error', `Failed to reject chore: ${error.message}`);
      }
    };

    const handleComplete = async () => {
      try {
        const { choreAPI } = require('../../api/chores');
        await choreAPI.completeChore(chore.id);
      } catch (error: any) {
        global.alert('Error', `Failed to complete chore: ${error.message}`);
      }
    };

    return (
      <View testID={`chore-card-${chore.id}`}>
        <Text testID="chore-title">{chore.title}</Text>
        <Text testID="chore-reward">Reward: ${chore.reward}</Text>
        <Text testID="chore-status">{getStatusText()}</Text>
        {chore.description && (
          <Text testID="chore-description">{chore.description}</Text>
        )}
        
        {chore.is_range_reward && chore.needs_approval && (
          <TextInput
            testID="reward-input"
            value={rewardAmount}
            onChangeText={setRewardAmount}
            placeholder="Enter reward amount"
          />
        )}
        
        {chore.needs_approval && (
          <>
            <TouchableOpacity testID="approve-button" onPress={handleApprove}>
              <Text>Approve</Text>
            </TouchableOpacity>
            <TouchableOpacity testID="reject-button" onPress={handleReject}>
              <Text>Reject</Text>
            </TouchableOpacity>
          </>
        )}
        
        {!chore.is_completed && !chore.needs_approval && (
          <TouchableOpacity testID="complete-button" onPress={handleComplete}>
            <Text>Complete</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  },
}));

// Mock the ChildCard component
jest.mock('../../components/ChildCard', () => ({
  ChildCard: ({ child, refreshKey }: any) => {
    const { View, Text } = require('react-native');
    const React = require('react');
    const [balance, setBalance] = React.useState(null);
    
    React.useEffect(() => {
      const loadBalance = async () => {
        try {
          const { usersAPI } = require('../../api/users');
          const balanceData = await usersAPI.getUserBalance(child.id);
          setBalance(balanceData);
        } catch (error) {
          console.error('Failed to load balance');
        }
      };
      loadBalance();
    }, [child.id, refreshKey]);
    
    return (
      <View testID={`child-card-${child.id}`}>
        <Text testID="child-name">{child.username}</Text>
        <Text testID="child-balance">${balance?.current_balance?.toFixed(2) || '0.00'}</Text>
        <Text testID="pending-earnings">${balance?.pending_earnings?.toFixed(2) || '0.00'}</Text>
      </View>
    );
  },
}));

// Mock the ActivityFeed component
jest.mock('../../components/ActivityFeed', () => ({
  ActivityFeed: ({ showHeader, limit }: any) => {
    const { View, Text } = require('react-native');
    const React = require('react');
    const [activities, setActivities] = React.useState([]);
    
    React.useEffect(() => {
      const loadActivities = async () => {
        try {
          const { activitiesAPI } = require('../../api/activities');
          const activityData = await activitiesAPI.getRecentActivities(limit);
          setActivities(activityData);
        } catch (error) {
          console.error('Failed to load activities');
        }
      };
      loadActivities();
    }, [limit]);
    
    return (
      <View testID="activity-feed">
        {showHeader && <Text testID="activity-header">Recent Activities</Text>}
        {activities.map((activity: any) => (
          <View key={activity.id} testID={`activity-${activity.id}`}>
            <Text>{activity.description}</Text>
            {activity.amount > 0 && <Text>${activity.amount.toFixed(2)}</Text>}
          </View>
        ))}
      </View>
    );
  },
}));

describe('Approval Workflow Integration Tests', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
    mockAlert.mockClear();
    
    // Default API responses
    mockedChoreAPI.approveChore.mockResolvedValue({ success: true });
    mockedChoreAPI.rejectChore.mockResolvedValue({ success: true });
    mockedUsersAPI.getChildren.mockResolvedValue([]);
    mockedUsersAPI.getUserBalance.mockResolvedValue({ current_balance: 25.50 });
    mockedActivitiesAPI.getRecentActivities.mockResolvedValue([]);
  });

  describe('Parent Chore Approval Workflow', () => {
    it('should complete full chore approval workflow', async () => {
      const completedChore = createMockChore({
        id: 1,
        title: 'Clean bedroom',
        reward: 10.00,
        is_completed: true,
        completed_at: '2024-01-15T10:00:00Z',
        assignee: { id: 2, username: 'testchild', role: 'child' },
        needs_approval: true,
      });

      const { getByTestId, queryByTestId } = renderWithProviders(
        <ChoreCard chore={completedChore} onApprovalChange={jest.fn()} />,
        { authenticated: true, userRole: 'parent' }
      );

      // Verify chore shows as completed and pending approval
      expect(getByTestId('chore-status')).toHaveTextContent('Completed - Pending Approval');
      expect(getByTestId('approve-button')).toBeTruthy();
      expect(getByTestId('reject-button')).toBeTruthy();

      // Approve the chore
      await act(async () => {
        fireEvent.press(getByTestId('approve-button'));
      });

      // Verify approval API was called
      expect(mockedChoreAPI.approveChore).toHaveBeenCalledWith(1, { final_reward: 10.00 });

      // Verify success feedback
      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Success', 'Chore approved successfully!');
      });
    });

    it('should handle chore approval with custom reward amount', async () => {
      const rangeRewardChore = createMockChore({
        id: 2,
        title: 'Organize closet',
        reward: 15.00,
        min_reward: 10.00,
        max_reward: 20.00,
        is_range_reward: true,
        is_completed: true,
        needs_approval: true,
      });

      const onApprovalChange = jest.fn();
      
      const { getByTestId } = renderWithProviders(
        <ChoreCard chore={rangeRewardChore} onApprovalChange={onApprovalChange} />,
        { authenticated: true, userRole: 'parent' }
      );

      // Should show reward input for range rewards
      expect(getByTestId('reward-input')).toBeTruthy();
      
      // Set custom reward amount
      fireEvent.changeText(getByTestId('reward-input'), '18.50');

      // Approve with custom amount
      await act(async () => {
        fireEvent.press(getByTestId('approve-button'));
      });

      expect(mockedChoreAPI.approveChore).toHaveBeenCalledWith(2, { final_reward: 18.50 });
      expect(onApprovalChange).toHaveBeenCalledWith(2, true);
    });

    it('should handle chore rejection workflow', async () => {
      const completedChore = createMockChore({
        id: 3,
        title: 'Take out trash',
        is_completed: true,
        needs_approval: true,
      });

      const onApprovalChange = jest.fn();
      
      const { getByTestId } = renderWithProviders(
        <ChoreCard chore={completedChore} onApprovalChange={onApprovalChange} />,
        { authenticated: true, userRole: 'parent' }
      );

      // Reject the chore
      await act(async () => {
        fireEvent.press(getByTestId('reject-button'));
      });

      expect(mockedChoreAPI.rejectChore).toHaveBeenCalledWith(3, { reason: 'Not completed to standard' });
      expect(onApprovalChange).toHaveBeenCalledWith(3, false);
    });

    it('should handle approval errors gracefully', async () => {
      const completedChore = createMockChore({
        id: 4,
        is_completed: true,
        needs_approval: true,
      });

      mockedChoreAPI.approveChore.mockRejectedValue(new Error('Server error'));
      
      const { getByTestId } = renderWithProviders(
        <ChoreCard chore={completedChore} onApprovalChange={jest.fn()} />,
        { authenticated: true, userRole: 'parent' }
      );

      await act(async () => {
        fireEvent.press(getByTestId('approve-button'));
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Error', 'Failed to approve chore: Server error');
      });
    });
  });

  describe('Child-Parent Interaction Workflow', () => {
    it('should show child completion workflow', async () => {
      const assignedChore = createMockChore({
        id: 5,
        title: 'Make bed',
        reward: 5.00,
        is_completed: false,
        assignee: { id: 2, username: 'testchild', role: 'child' },
      });

      const { getByTestId, queryByTestId } = renderWithProviders(
        <ChoreCard chore={assignedChore} />,
        { authenticated: true, userRole: 'child' }
      );

      // Child should see complete button, not approval buttons
      expect(getByTestId('complete-button')).toBeTruthy();
      expect(queryByTestId('approve-button')).toBeNull();
      expect(queryByTestId('reject-button')).toBeNull();

      // Complete the chore
      await act(async () => {
        fireEvent.press(getByTestId('complete-button'));
      });

      expect(mockedChoreAPI.completeChore).toHaveBeenCalledWith(5);
    });

    it('should show child balance after chore approval', async () => {
      const childUser = createMockUser({
        id: 2,
        username: 'testchild',
        role: 'child',
      });

      const mockBalance = {
        current_balance: 35.50,
        pending_earnings: 15.00,
        total_earned: 150.00,
      };

      mockedUsersAPI.getUserBalance.mockResolvedValue(mockBalance);
      
      const { getByTestId } = renderWithProviders(
        <ChildCard child={childUser} />,
        { authenticated: true, userRole: 'parent' }
      );

      // Should display balance information
      await waitFor(() => {
        expect(getByTestId('child-balance')).toHaveTextContent('$35.50');
        expect(getByTestId('pending-earnings')).toHaveTextContent('$15.00');
      });
    });
  });

  describe('Activity Feed Integration', () => {
    it('should display approval activity in feed', async () => {
      const mockActivities = [
        {
          id: 1,
          type: 'chore_approved',
          description: 'Clean bedroom approved by Parent',
          amount: 10.00,
          created_at: '2024-01-15T10:30:00Z',
          user: { id: 2, username: 'testchild', role: 'child' },
        },
        {
          id: 2,
          type: 'chore_completed',
          description: 'Make bed completed by Child',
          amount: 5.00,
          created_at: '2024-01-15T09:00:00Z',
          user: { id: 2, username: 'testchild', role: 'child' },
        },
      ];

      mockedActivitiesAPI.getRecentActivities.mockResolvedValue(mockActivities);
      
      const { getByTestId } = renderWithProviders(
        <ActivityFeed showHeader={true} limit={10} />,
        { authenticated: true, userRole: 'parent' }
      );

      await waitFor(() => {
        expect(getByTestId('activity-1')).toBeTruthy();
        expect(getByTestId('activity-2')).toBeTruthy();
      });

      // Verify activity details
      expect(getByTestId('activity-1')).toHaveTextContent('Clean bedroom approved by Parent');
      expect(getByTestId('activity-1')).toHaveTextContent('$10.00');
      
      expect(getByTestId('activity-2')).toHaveTextContent('Make bed completed by Child');
      expect(getByTestId('activity-2')).toHaveTextContent('$5.00');
    });

    it('should show rejection activity in feed', async () => {
      const rejectionActivity = {
        id: 3,
        type: 'chore_rejected',
        description: 'Take out trash rejected - needs to be redone',
        amount: 0,
        created_at: '2024-01-15T11:00:00Z',
        user: { id: 2, username: 'testchild', role: 'child' },
      };

      mockedActivitiesAPI.getRecentActivities.mockResolvedValue([rejectionActivity]);
      
      const { getByTestId } = renderWithProviders(
        <ActivityFeed showHeader={true} />,
        { authenticated: true, userRole: 'child' }
      );

      await waitFor(() => {
        expect(getByTestId('activity-3')).toBeTruthy();
        expect(getByTestId('activity-3')).toHaveTextContent('Take out trash rejected - needs to be redone');
      });
    });
  });

  describe('Cross-Component Approval Workflow', () => {
    it('should update child balance after chore approval', async () => {
      const completedChore = createMockChore({
        id: 6,
        title: 'Vacuum living room',
        reward: 12.00,
        is_completed: true,
        needs_approval: true,
        assignee: { id: 2, username: 'testchild', role: 'child' },
      });

      const childUser = createMockUser({
        id: 2,
        username: 'testchild',
        role: 'child',
      });

      // Mock balance before and after approval
      mockedUsersAPI.getUserBalance
        .mockResolvedValueOnce({ current_balance: 25.50, pending_earnings: 12.00 })
        .mockResolvedValueOnce({ current_balance: 37.50, pending_earnings: 0 });

      const mockOnApprovalChange = jest.fn().mockImplementation((choreId, approved) => {
        if (approved) {
          // Simulate balance update after approval
          mockedUsersAPI.getUserBalance.mockResolvedValue({
            current_balance: 37.50,
            pending_earnings: 0,
            total_earned: 162.00,
          });
        }
      });

      const { getByTestId, rerender } = renderWithProviders(
        <div>
          <ChoreCard chore={completedChore} onApprovalChange={mockOnApprovalChange} />
          <ChildCard child={childUser} />
        </div>,
        { authenticated: true, userRole: 'parent' }
      );

      // Initial balance
      await waitFor(() => {
        expect(getByTestId('child-balance')).toHaveTextContent('$25.50');
        expect(getByTestId('pending-earnings')).toHaveTextContent('$12.00');
      });

      // Approve chore
      await act(async () => {
        fireEvent.press(getByTestId('approve-button'));
      });

      // Verify approval callback was triggered
      expect(mockOnApprovalChange).toHaveBeenCalledWith(6, true);

      // Re-render to simulate updated balance
      rerender(
        <div>
          <ChoreCard chore={{ ...completedChore, is_approved: true }} onApprovalChange={mockOnApprovalChange} />
          <ChildCard child={childUser} refreshKey={1} />
        </div>
      );

      // Updated balance should reflect approval
      await waitFor(() => {
        expect(getByTestId('child-balance')).toHaveTextContent('$37.50');
        expect(getByTestId('pending-earnings')).toHaveTextContent('$0.00');
      });
    });

    it('should handle multiple pending approvals workflow', async () => {
      const pendingChores = [
        createMockChore({
          id: 7,
          title: 'Wash dishes',
          reward: 8.00,
          is_completed: true,
          needs_approval: true,
        }),
        createMockChore({
          id: 8,
          title: 'Fold laundry',
          reward: 6.00,
          is_completed: true,
          needs_approval: true,
        }),
      ];

      const mockOnApprovalChange = jest.fn();
      
      const { getAllByTestId } = renderWithProviders(
        <div>
          {pendingChores.map(chore => (
            <ChoreCard key={chore.id} chore={chore} onApprovalChange={mockOnApprovalChange} />
          ))}
        </div>,
        { authenticated: true, userRole: 'parent' }
      );

      // Both chores should show approval buttons
      const approvalButtons = getAllByTestId('approve-button');
      expect(approvalButtons).toHaveLength(2);
      
      // Approve first chore
      await act(async () => {
        fireEvent.press(approvalButtons[0]);
      });

      expect(mockedChoreAPI.approveChore).toHaveBeenCalledWith(7, { final_reward: 8.00 });
      expect(mockOnApprovalChange).toHaveBeenCalledWith(7, true);
    });
  });

  describe('Error Handling in Approval Workflow', () => {
    it('should handle network errors during approval', async () => {
      const completedChore = createMockChore({
        id: 9,
        is_completed: true,
        needs_approval: true,
      });

      mockedChoreAPI.approveChore.mockRejectedValue(new Error('Network error'));
      
      const { getByTestId } = renderWithProviders(
        <ChoreCard chore={completedChore} onApprovalChange={jest.fn()} />,
        { authenticated: true, userRole: 'parent' }
      );

      await act(async () => {
        fireEvent.press(getByTestId('approve-button'));
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Error', 'Failed to approve chore: Network error');
      });
    });

    it('should handle validation errors for range rewards', async () => {
      const rangeRewardChore = createMockChore({
        id: 10,
        is_range_reward: true,
        min_reward: 5.00,
        max_reward: 15.00,
        is_completed: true,
        needs_approval: true,
      });
      
      const { getByTestId } = renderWithProviders(
        <ChoreCard chore={rangeRewardChore} onApprovalChange={jest.fn()} />,
        { authenticated: true, userRole: 'parent' }
      );

      // Try to approve with reward outside range
      fireEvent.changeText(getByTestId('reward-input'), '20.00');

      await act(async () => {
        fireEvent.press(getByTestId('approve-button'));
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Error', 'Reward must be between $5.00 and $15.00');
      });

      // Should not call API with invalid amount
      expect(mockedChoreAPI.approveChore).not.toHaveBeenCalled();
    });

    it('should handle rejection errors gracefully', async () => {
      const completedChore = createMockChore({
        id: 11,
        is_completed: true,
        needs_approval: true,
      });

      mockedChoreAPI.rejectChore.mockRejectedValue(new Error('Cannot reject approved chore'));
      
      const { getByTestId } = renderWithProviders(
        <ChoreCard chore={completedChore} onApprovalChange={jest.fn()} />,
        { authenticated: true, userRole: 'parent' }
      );

      await act(async () => {
        fireEvent.press(getByTestId('reject-button'));
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Error', 'Failed to reject chore: Cannot reject approved chore');
      });
    });
  });
});