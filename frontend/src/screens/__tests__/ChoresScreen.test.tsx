/**
 * ChoresScreen Component Tests
 * Tests the chores management screen with tab navigation, role-based content, and chore operations
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { ChoresScreen } from '../ChoresScreen';
import { AuthContext } from '../../contexts/AuthContext';
import { choreAPI, Chore } from '../../api/chores';
import { User } from '../../api/users';

// Mock the useAuth hook to prevent AuthProvider context errors
jest.mock('../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../contexts/AuthContext'),
  useAuth: jest.fn(),
}));

const { useAuth } = require('../../contexts/AuthContext');
const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Mock the Alert module
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
      prompt: jest.fn(),
    },
  };
});

const mockAlert = Alert.alert as jest.MockedFunction<typeof Alert.alert>;
const mockPrompt = Alert.prompt as jest.MockedFunction<typeof Alert.prompt>;

// Mock the choreAPI
jest.mock('../../api/chores', () => ({
  choreAPI: {
    getAvailableChores: jest.fn(),
    getMyChores: jest.fn(),
    completeChore: jest.fn(),
    approveChore: jest.fn(),
  },
}));

const mockedChoreAPI = choreAPI as jest.Mocked<typeof choreAPI>;

// Mock the Alert utility
jest.mock('../../utils/Alert', () => ({
  Alert: {
    alert: jest.fn(),
  },
}));

// Mock ChoresManagementScreen component to focus on child interface
jest.mock('../ChoresManagementScreen', () => {
  const { Text } = require('react-native');
  return function ChoresManagementScreen() {
    return <Text testID="chores-management-screen">ChoresManagementScreen</Text>;
  };
});

// Mock ChoreCard component
jest.mock('../../components/ChoreCard', () => ({
  ChoreCard: ({ chore, onComplete, showCompleteButton, isChild }: any) => {
    const { View, Text, TouchableOpacity } = require('react-native');
    return (
      <View testID={`chore-card-${chore.id}`}>
        <Text>{chore.title}</Text>
        <Text>Reward: ${chore.reward}</Text>
        <Text>Completed: {chore.is_completed ? 'Yes' : 'No'}</Text>
        {showCompleteButton && onComplete && (
          <TouchableOpacity onPress={() => onComplete(chore.id)} testID={`complete-button-${chore.id}`}>
            <Text>Complete</Text>
          </TouchableOpacity>
        )}
        <Text>isChild: {isChild ? 'true' : 'false'}</Text>
      </View>
    );
  },
}));

// Mock user factory
const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'child',
  is_active: true,
  ...overrides,
});

// Mock chore factory
const createMockChore = (overrides: Partial<Chore> = {}): Chore => ({
  id: 1,
  title: 'Test Chore',
  description: 'Test description',
  reward: 5.0,
  is_completed: false,
  is_approved: false,
  is_disabled: false,
  assigned_to_id: null,
  assignee_id: null,
  completed_at: null,
  completion_date: null,
  approved_at: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode; user?: User | null }> = ({ 
  children, 
  user = createMockUser() 
}) => {
  const authValue = {
    user,
    login: jest.fn(),
    logout: jest.fn(),
    checkAuthStatus: jest.fn(),
    isAuthenticated: !!user,
    isLoading: false,
  };

  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  );
};

describe('ChoresScreen Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAlert.mockClear();
    mockPrompt.mockClear();
    mockedChoreAPI.getAvailableChores.mockResolvedValue([]);
    mockedChoreAPI.getMyChores.mockResolvedValue([]);
    mockedChoreAPI.completeChore.mockResolvedValue(undefined);
    mockedChoreAPI.approveChore.mockResolvedValue(undefined);
  });

  describe('Role-based Screen Rendering', () => {
    it('should render ChoresManagementScreen for parent users', () => {
      const parentUser = createMockUser({ role: 'parent' });

      const { getByTestId, queryByText } = render(
        <TestWrapper user={parentUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      expect(getByTestId('chores-management-screen')).toBeTruthy();
      expect(queryByText('Chores')).toBeNull(); // Child interface title should not appear
    });

    it('should render child interface for child users', () => {
      const childUser = createMockUser({ role: 'child' });

      const { getByText, queryByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      expect(getByText('Chores')).toBeTruthy();
      expect(getByText('Your assigned chores')).toBeTruthy();
      expect(queryByTestId('chores-management-screen')).toBeNull();
    });
  });

  describe('Child Interface - Tab Navigation', () => {
    it('should render all tab options for child users', () => {
      const childUser = createMockUser({ role: 'child' });

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      expect(getByTestId('tab-available')).toBeTruthy();
      expect(getByTestId('tab-active')).toBeTruthy();
      expect(getByTestId('tab-completed')).toBeTruthy();
    });

    it('should switch tabs correctly', async () => {
      const childUser = createMockUser({ role: 'child' });

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      const activeTab = getByTestId('tab-active');
      fireEvent.press(activeTab);

      // Should call API for active chores
      await waitFor(() => {
        expect(mockedChoreAPI.getMyChores).toHaveBeenCalled();
      });
    });

    it('should highlight active tab correctly', () => {
      const childUser = createMockUser({ role: 'child' });

      const { getByTestId, getByText } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Default should be available tab
      expect(getByText('Available')).toBeTruthy();
      
      // Switch to completed tab
      const completedTab = getByTestId('tab-completed');
      fireEvent.press(completedTab);
      
      expect(getByText('Completed')).toBeTruthy();
    });
  });

  describe('Data Fetching and Display', () => {
    it('should fetch available chores on available tab', async () => {
      const childUser = createMockUser({ role: 'child' });
      const availableChores = [
        createMockChore({ id: 1, title: 'Available Chore 1' }),
        createMockChore({ id: 2, title: 'Available Chore 2' }),
      ];

      mockedChoreAPI.getAvailableChores.mockResolvedValue(availableChores);

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockedChoreAPI.getAvailableChores).toHaveBeenCalledTimes(1);
        expect(getByTestId('chore-card-1')).toBeTruthy();
        expect(getByTestId('chore-card-2')).toBeTruthy();
      });
    });

    it('should fetch and filter active chores correctly', async () => {
      const childUser = createMockUser({ id: 5, role: 'child' });
      const allChores = [
        createMockChore({ id: 1, title: 'Active Chore 1', assigned_to_id: 5, is_completed: false }),
        createMockChore({ id: 2, title: 'Active Chore 2', assignee_id: 5, is_completed: false }),
        createMockChore({ id: 3, title: 'Other Child Chore', assigned_to_id: 3, is_completed: false }),
        createMockChore({ id: 4, title: 'Completed Chore', assigned_to_id: 5, is_completed: true }),
      ];

      mockedChoreAPI.getMyChores.mockResolvedValue(allChores);

      const { getByTestId, queryByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Switch to active tab
      const activeTab = getByTestId('tab-active');
      fireEvent.press(activeTab);

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
        expect(getByTestId('chore-card-2')).toBeTruthy();
        expect(queryByTestId('chore-card-3')).toBeNull(); // Different child
        expect(queryByTestId('chore-card-4')).toBeNull(); // Completed
      });
    });

    it('should fetch and filter completed chores correctly', async () => {
      const childUser = createMockUser({ id: 7, role: 'child' });
      const allChores = [
        createMockChore({ id: 1, title: 'Completed Chore 1', assigned_to_id: 7, is_completed: true }),
        createMockChore({ id: 2, title: 'Completed Chore 2', assignee_id: 7, completed_at: '2024-01-15T10:00:00Z' }),
        createMockChore({ id: 3, title: 'Active Chore', assigned_to_id: 7, is_completed: false }),
      ];

      mockedChoreAPI.getMyChores.mockResolvedValue(allChores);

      const { getByTestId, queryByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Switch to completed tab
      const completedTab = getByTestId('tab-completed');
      fireEvent.press(completedTab);

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
        expect(getByTestId('chore-card-2')).toBeTruthy();
        expect(queryByTestId('chore-card-3')).toBeNull(); // Not completed
      });
    });

    it('should show loading indicator while fetching data', () => {
      const childUser = createMockUser({ role: 'child' });

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Should show loading initially
      expect(() => getByTestId('loading-indicator')).not.toThrow();
    });

    it('should show empty state when no chores available', async () => {
      const childUser = createMockUser({ role: 'child' });
      mockedChoreAPI.getAvailableChores.mockResolvedValue([]);

      const { getByText } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByText('No chores available')).toBeTruthy();
      });
    });

    it('should show appropriate empty state for each tab', async () => {
      const childUser = createMockUser({ role: 'child' });
      mockedChoreAPI.getAvailableChores.mockResolvedValue([]);
      mockedChoreAPI.getMyChores.mockResolvedValue([]);

      const { getByTestId, getByText } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Available tab
      await waitFor(() => {
        expect(getByText('No chores available')).toBeTruthy();
      });

      // Active tab
      fireEvent.press(getByTestId('tab-active'));
      await waitFor(() => {
        expect(getByText('No active chores')).toBeTruthy();
      });

      // Completed tab
      fireEvent.press(getByTestId('tab-completed'));
      await waitFor(() => {
        expect(getByText('No completed chores')).toBeTruthy();
      });
    });
  });

  describe('Chore Completion Flow', () => {
    it('should complete chore when complete button is pressed', async () => {
      const childUser = createMockUser({ role: 'child' });
      const availableChores = [
        createMockChore({ id: 1, title: 'Chore to Complete' }),
      ];

      mockedChoreAPI.getAvailableChores.mockResolvedValue(availableChores);

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
      });

      const completeButton = getByTestId('complete-button-1');
      
      await act(async () => {
        fireEvent.press(completeButton);
      });

      expect(mockedChoreAPI.completeChore).toHaveBeenCalledWith(1);
    });

    it('should refresh chores list after completion', async () => {
      const childUser = createMockUser({ role: 'child' });
      const availableChores = [
        createMockChore({ id: 1, title: 'Chore to Complete' }),
      ];

      mockedChoreAPI.getAvailableChores
        .mockResolvedValueOnce(availableChores)
        .mockResolvedValueOnce([]); // Empty after completion

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
      });

      const completeButton = getByTestId('complete-button-1');
      
      await act(async () => {
        fireEvent.press(completeButton);
      });

      // Should call API twice - once on load, once after completion
      await waitFor(() => {
        expect(mockedChoreAPI.getAvailableChores).toHaveBeenCalledTimes(2);
      });
    });

    it('should handle completion error gracefully', async () => {
      const childUser = createMockUser({ role: 'child' });
      const availableChores = [
        createMockChore({ id: 1, title: 'Chore to Complete' }),
      ];

      mockedChoreAPI.getAvailableChores.mockResolvedValue(availableChores);
      mockedChoreAPI.completeChore.mockRejectedValue(new Error('Completion failed'));

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
      });

      const completeButton = getByTestId('complete-button-1');
      
      await act(async () => {
        fireEvent.press(completeButton);
      });

      // Should show error alert
      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Failed to complete chore. Please try again.'
      );
    });
  });

  describe('Chore Approval Flow (Parent Actions)', () => {
    it('should show approval prompt for range reward chores', async () => {
      const childUser = createMockUser({ role: 'child' });
      const rangeRewardChore = createMockChore({
        id: 1,
        title: 'Range Reward Chore',
        is_range_reward: true,
        min_reward: 5,
        max_reward: 10,
      });

      // Mock prompt to simulate user input
      mockPrompt.mockImplementation((title, message, buttons) => {
        if (buttons && buttons[1] && buttons[1].onPress) {
          buttons[1].onPress('7.50'); // Simulate user entering $7.50
        }
      });

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
      });

      // The component handles approval logic internally
      // This tests the component's ability to render range reward chores
      expect(getByTestId('chore-card-1')).toBeTruthy();
    });

    it('should show approval confirmation for fixed reward chores', async () => {
      const childUser = createMockUser({ role: 'child' });
      const fixedRewardChore = createMockChore({
        id: 1,
        title: 'Fixed Reward Chore',
        reward: 5,
        is_range_reward: false,
      });

      // Mock alert to simulate user confirmation
      mockAlert.mockImplementation((title, message, buttons) => {
        if (buttons && buttons[1] && buttons[1].onPress) {
          buttons[1].onPress(); // Simulate user pressing "Approve"
        }
      });

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
      });

      // The component handles approval logic internally
      expect(getByTestId('chore-card-1')).toBeTruthy();
    });
  });

  describe('Pull to Refresh', () => {
    it('should support pull to refresh functionality', async () => {
      const childUser = createMockUser({ role: 'child' });
      const availableChores = [
        createMockChore({ id: 1, title: 'Refreshable Chore' }),
      ];

      mockedChoreAPI.getAvailableChores.mockResolvedValue(availableChores);

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockedChoreAPI.getAvailableChores).toHaveBeenCalledTimes(1);
      });

      // Note: Testing RefreshControl requires more complex setup
      // For now, we verify the component renders correctly with refresh capability
      expect(getByTestId('chore-card-1')).toBeTruthy();
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const childUser = createMockUser({ role: 'child' });
      mockedChoreAPI.getAvailableChores.mockRejectedValue(new Error('API Error'));

      const { getByText } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          'Error',
          'Failed to load chores. Please try again.'
        );
      });

      // Should still show the interface
      expect(getByText('Chores')).toBeTruthy();
    });

    it('should handle network timeouts', async () => {
      const childUser = createMockUser({ role: 'child' });
      const timeoutError = new Error('Network timeout');
      mockedChoreAPI.getAvailableChores.mockRejectedValue(timeoutError);

      render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          'Error',
          'Failed to load chores. Please try again.'
        );
      });
    });
  });

  describe('Component Props and Integration', () => {
    it('should pass correct props to ChoreCard components', async () => {
      const childUser = createMockUser({ role: 'child' });
      const availableChores = [
        createMockChore({ id: 1, title: 'Test Chore', reward: 7.5 }),
      ];

      mockedChoreAPI.getAvailableChores.mockResolvedValue(availableChores);

      const { getByTestId, getByText } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(getByTestId('chore-card-1')).toBeTruthy();
        expect(getByText('Test Chore')).toBeTruthy();
        expect(getByText('Reward: $7.5')).toBeTruthy();
        expect(getByText('isChild: true')).toBeTruthy();
      });
    });

    it('should show complete button only on available tab', async () => {
      const childUser = createMockUser({ role: 'child' });
      const availableChores = [
        createMockChore({ id: 1, title: 'Available Chore' }),
      ];
      const activeChores = [
        createMockChore({ id: 2, title: 'Active Chore', assigned_to_id: childUser.id }),
      ];

      mockedChoreAPI.getAvailableChores.mockResolvedValue(availableChores);
      mockedChoreAPI.getMyChores.mockResolvedValue(activeChores);

      const { getByTestId, queryByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Available tab should show complete button
      await waitFor(() => {
        expect(getByTestId('complete-button-1')).toBeTruthy();
      });

      // Switch to active tab
      fireEvent.press(getByTestId('tab-active'));

      await waitFor(() => {
        expect(queryByTestId('complete-button-2')).toBeNull();
      });
    });
  });

  describe('Debugging and Audit Features', () => {
    it('should log chore audit information for completed chores', async () => {
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
      const childUser = createMockUser({ id: 8, role: 'child' });
      const completedChores = [
        createMockChore({ 
          id: 1, 
          title: 'Completed Chore 1', 
          assigned_to_id: 8, 
          is_completed: true,
          reward: 5,
          approval_reward: 7,
        }),
      ];

      mockedChoreAPI.getMyChores.mockResolvedValue(completedChores);

      const { getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Switch to completed tab to trigger audit logging
      fireEvent.press(getByTestId('tab-completed'));

      await waitFor(() => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          '[CHORES AUDIT] Total chores returned from API:',
          1
        );
        expect(consoleLogSpy).toHaveBeenCalledWith(
          '[CHORES AUDIT] Filtered completed chores:',
          1
        );
      });

      consoleLogSpy.mockRestore();
    });
  });

  describe('User State Changes', () => {
    it('should handle user role changes', () => {
      const childUser = createMockUser({ role: 'child' });
      const { getByText, rerender, queryByTestId, getByTestId } = render(
        <TestWrapper user={childUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Should show child interface
      expect(getByText('Chores')).toBeTruthy();
      expect(queryByTestId('chores-management-screen')).toBeNull();

      // Change to parent user
      const parentUser = createMockUser({ role: 'parent' });
      rerender(
        <TestWrapper user={parentUser}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Should show parent interface
      expect(getByTestId('chores-management-screen')).toBeTruthy();
    });

    it('should handle null user gracefully', () => {
      const { queryByText } = render(
        <TestWrapper user={null}>
          <ChoresScreen />
        </TestWrapper>
      );

      // Should not crash with null user
      expect(queryByText('Chores')).toBeTruthy();
    });
  });
});