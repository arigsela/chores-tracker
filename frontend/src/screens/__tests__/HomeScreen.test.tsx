/**
 * HomeScreen Component Tests
 * Tests the main dashboard screen with role-based content, stats, and navigation
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { HomeScreen } from '../HomeScreen';
import { choreAPI } from '../../api/chores';
import { User } from '../../api/users';
import { renderWithCustomUser, renderWithProviders } from '../../test-utils';
import { createMockUser, createMockChore } from '../../test-utils/factories';

// Mock the useAuth hook to prevent AuthProvider context errors
jest.mock('../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../contexts/AuthContext'),
  useAuth: jest.fn(),
}));

const { useAuth } = require('../../contexts/AuthContext');
const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

// Mock the choreAPI
jest.mock('../../api/chores', () => ({
  choreAPI: {
    getPendingApprovalChores: jest.fn(),
    getMyChores: jest.fn(),
  },
}));

const mockedChoreAPI = choreAPI as jest.Mocked<typeof choreAPI>;

// Mock components to focus on HomeScreen logic
jest.mock('../../components/ActivityFeed', () => ({
  ActivityFeed: ({ refreshKey, showHeader, limit }: any) => {
    const { Text } = require('react-native');
    return (
      <Text testID="activity-feed">
        ActivityFeed refreshKey:{refreshKey} showHeader:{showHeader.toString()} limit:{limit}
      </Text>
    );
  },
}));

jest.mock('../../components/FinancialSummaryCards', () => ({
  FinancialSummaryCards: ({ refreshKey, onViewReports }: any) => {
    const { Text, TouchableOpacity } = require('react-native');
    return (
      <>
        <Text testID="financial-summary">FinancialSummaryCards refreshKey:{refreshKey}</Text>
        {onViewReports && (
          <TouchableOpacity onPress={onViewReports} testID="view-reports-button">
            <Text>View Reports</Text>
          </TouchableOpacity>
        )}
      </>
    );
  },
}));

describe('HomeScreen Component', () => {
  const mockOnNavigate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockedChoreAPI.getPendingApprovalChores.mockResolvedValue([]);
    mockedChoreAPI.getMyChores.mockResolvedValue([]);
    
    // Set up default mock for useAuth
    mockedUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: createMockUser({ username: 'testuser', role: 'parent' }),
      login: jest.fn(),
      logout: jest.fn(),
      checkAuthStatus: jest.fn(),
    });
  });

  describe('Basic Rendering', () => {
    it('should render welcome message with username', () => {
      const user = createMockUser({ username: 'testparent' });
      mockedUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });

      const { getByText } = render(<HomeScreen onNavigate={mockOnNavigate} />);

      expect(getByText('Welcome back,')).toBeTruthy();
      expect(getByText('testparent!')).toBeTruthy();
    });

    it('should render Quick Actions section', () => {
      const { getByText } = render(<HomeScreen onNavigate={mockOnNavigate} />);

      expect(getByText('Quick Actions')).toBeTruthy();
    });

    it('should render ActivityFeed component', () => {
      const { getByTestId } = render(<HomeScreen onNavigate={mockOnNavigate} />);

      const activityFeed = getByTestId('activity-feed');
      expect(activityFeed).toBeTruthy();
      expect(activityFeed.props.children).toContain('showHeader:true');
      expect(activityFeed.props.children).toContain('limit:10');
    });
  });

  describe('Parent User Interface', () => {
    it('should display parent-specific stats and actions', async () => {
      const parentUser = createMockUser({ role: 'parent' });
      const pendingChores = [createMockChore({ id: 1 }), createMockChore({ id: 2 })];
      const allChores = [
        createMockChore({ id: 1, is_completed: false }),
        createMockChore({ id: 2, is_completed: false }),
        createMockChore({ id: 3, is_completed: true }),
      ];

      mockedChoreAPI.getPendingApprovalChores.mockResolvedValue(pendingChores);
      mockedChoreAPI.getMyChores.mockResolvedValue(allChores);

      mockedUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });

      const { getByText, getByTestId } = render(<HomeScreen onNavigate={mockOnNavigate} />);

      await waitFor(() => {
        expect(getByText('Pending Approvals')).toBeTruthy();
        expect(getByText('Active Chores')).toBeTruthy();
        expect(getByText('2')).toBeTruthy(); // Pending approvals count
      });

      // Parent-specific actions
      expect(getByText('📝 Create New Chore')).toBeTruthy();
      expect(getByText('👨‍👩‍👧‍👦 Manage Children')).toBeTruthy();
      expect(getByText('📊 View Financial Reports')).toBeTruthy();
      expect(getByText('📈 View Statistics & Trends')).toBeTruthy();

      // Financial summary should be rendered for parents
      expect(getByTestId('financial-summary')).toBeTruthy();
    });

    it('should call API endpoints for parent stats', async () => {
      const parentUser = createMockUser({ role: 'parent' });

      renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        parentUser
      );

      await waitFor(() => {
        expect(mockedChoreAPI.getPendingApprovalChores).toHaveBeenCalledTimes(1);
        expect(mockedChoreAPI.getMyChores).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle financial summary navigation', async () => {
      const parentUser = createMockUser({ role: 'parent' });

      const { getByTestId } = renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        parentUser
      );

      await waitFor(() => {
        const viewReportsButton = getByTestId('view-reports-button');
        fireEvent.press(viewReportsButton);
        expect(mockOnNavigate).toHaveBeenCalledWith('Reports');
      });
    });
  });

  describe('Child User Interface', () => {
    it('should display child-specific stats and actions', async () => {
      const childUser = createMockUser({ id: 2, role: 'child', username: 'testchild' });
      const allChores = [
        createMockChore({ id: 1, assigned_to_id: 2, is_completed: false }),
        createMockChore({ id: 2, assignee_id: 2, is_completed: false }),
        createMockChore({ id: 3, assigned_to_id: 2, completed_at: '2024-01-15T10:00:00Z' }),
      ];

      mockedChoreAPI.getMyChores.mockResolvedValue(allChores);

      const { getByText, queryByTestId } = renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        childUser
      );

      await waitFor(() => {
        expect(getByText('Active Chores')).toBeTruthy();
        expect(getByText('Completed Today')).toBeTruthy();
        expect(getByText('2')).toBeTruthy(); // Active chores count
      });

      // Child-specific actions
      expect(getByText('✅ View Available Chores')).toBeTruthy();
      expect(getByText('💰 Check Balance')).toBeTruthy();

      // Child should not see parent-only features
      expect(queryByTestId('financial-summary')).toBeNull();
    });

    it('should not call getPendingApprovalChores for children', async () => {
      const childUser = createMockUser({ role: 'child' });

      renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        childUser
      );

      await waitFor(() => {
        expect(mockedChoreAPI.getPendingApprovalChores).not.toHaveBeenCalled();
        expect(mockedChoreAPI.getMyChores).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Navigation Integration', () => {
    it('should navigate to Chores screen when create chore action is pressed', () => {
      const parentUser = createMockUser({ role: 'parent' });

      const { getByText } = renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        parentUser
      );

      fireEvent.press(getByText('📝 Create New Chore'));
      expect(mockOnNavigate).toHaveBeenCalledWith('Chores');
    });

    it('should navigate to Balance screen when child presses check balance action', () => {
      const childUser = createMockUser({ role: 'child' });

      const { getByText } = renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        childUser
      );

      fireEvent.press(getByText('💰 Check Balance'));
      expect(mockOnNavigate).toHaveBeenCalledWith('Balance');
    });

    it('should handle undefined onNavigate prop gracefully', () => {
      const { getByText } = renderWithProviders(
        <HomeScreen />,
        { authenticated: true, userRole: 'parent' }
      );

      // Should not crash when navigation actions are pressed
      expect(() => {
        fireEvent.press(getByText('📝 Create New Chore'));
      }).not.toThrow();
    });
  });

  describe('Data Fetching and Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      mockedChoreAPI.getMyChores.mockRejectedValue(new Error('API Error'));
      mockedChoreAPI.getPendingApprovalChores.mockRejectedValue(new Error('API Error'));

      const { getByText } = renderWithProviders(
        <HomeScreen onNavigate={mockOnNavigate} />,
        { authenticated: true, userRole: 'parent' }
      );

      await waitFor(() => {
        // Should still render welcome message
        expect(getByText('Welcome back,')).toBeTruthy();
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[HomeScreen] Failed to fetch dashboard stats:',
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
    });

    it('should handle empty chores arrays', async () => {
      mockedChoreAPI.getMyChores.mockResolvedValue([]);
      mockedChoreAPI.getPendingApprovalChores.mockResolvedValue([]);

      const { getByText } = renderWithProviders(
        <HomeScreen onNavigate={mockOnNavigate} />,
        { authenticated: true, userRole: 'parent' }
      );

      await waitFor(() => {
        expect(getByText('0')).toBeTruthy();
        expect(getByText('Pending Approvals')).toBeTruthy();
        expect(getByText('Active Chores')).toBeTruthy();
      });
    });
  });

  describe('User State Handling', () => {
    it('should handle null user gracefully', () => {
      const { queryByText } = renderWithProviders(
        <HomeScreen onNavigate={mockOnNavigate} />,
        { authenticated: false }
      );

      // Should not crash with null user
      expect(queryByText('Welcome back,')).toBeTruthy();
    });
  });

  describe('Component Integration', () => {
    it('should pass correct props to ActivityFeed', () => {
      const { getByTestId } = renderWithProviders(
        <HomeScreen onNavigate={mockOnNavigate} />,
        { authenticated: true, userRole: 'parent' }
      );

      const activityFeed = getByTestId('activity-feed');
      expect(activityFeed.props.children).toContain('limit:10');
      expect(activityFeed.props.children).toContain('showHeader:true');
    });

    it('should pass correct props to FinancialSummaryCards for parents', () => {
      const parentUser = createMockUser({ role: 'parent' });

      const { getByTestId } = renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        parentUser
      );

      const financialSummary = getByTestId('financial-summary');
      expect(financialSummary.props.children).toContain('refreshKey:0');
    });

    it('should not render FinancialSummaryCards for children', () => {
      const childUser = createMockUser({ role: 'child' });

      const { queryByTestId } = renderWithCustomUser(
        <HomeScreen onNavigate={mockOnNavigate} />,
        childUser
      );

      expect(queryByTestId('financial-summary')).toBeNull();
    });
  });
});