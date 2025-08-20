/**
 * SimpleNavigator Component Tests
 * Tests navigation logic, authentication routing, and role-based tab visibility
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { SimpleNavigator } from '../SimpleNavigator';
import { createMockUser, resetAllMocks } from '../../test-utils';

// Mock the useAuth hook
const mockUseAuth = jest.fn();
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock all screen components to focus on navigation logic
jest.mock('../../screens/LoginScreen', () => ({
  LoginScreen: ({ onNavigateToRegister }: any) => {
    const { Text, TouchableOpacity } = require('react-native');
    return (
      <>
        <Text testID="login-screen">LoginScreen</Text>
        <TouchableOpacity onPress={onNavigateToRegister} testID="navigate-to-register">
          <Text>Go to Register</Text>
        </TouchableOpacity>
      </>
    );
  },
}));

jest.mock('../../screens/RegisterScreen', () => ({
  RegisterScreen: ({ onBackToLogin }: any) => {
    const { Text, TouchableOpacity } = require('react-native');
    return (
      <>
        <Text testID="register-screen">RegisterScreen</Text>
        <TouchableOpacity onPress={onBackToLogin} testID="back-to-login">
          <Text>Back to Login</Text>
        </TouchableOpacity>
      </>
    );
  },
}));

jest.mock('../../screens/HomeScreen', () => ({
  HomeScreen: ({ onNavigate }: any) => {
    const { Text, TouchableOpacity } = require('react-native');
    return (
      <>
        <Text testID="home-screen">HomeScreen</Text>
        {onNavigate && (
          <TouchableOpacity onPress={() => onNavigate('Chores')} testID="home-navigate">
            <Text>Navigate from Home</Text>
          </TouchableOpacity>
        )}
      </>
    );
  },
}));

jest.mock('../../screens/ChoresScreen', () => ({
  ChoresScreen: () => {
    const { Text } = require('react-native');
    return <Text testID="chores-screen">ChoresScreen</Text>;
  },
}));

jest.mock('../../screens/ChildrenScreen', () => ({
  ChildrenScreen: () => {
    const { Text } = require('react-native');
    return <Text testID="children-screen">ChildrenScreen</Text>;
  },
}));

jest.mock('../../screens/BalanceScreen', () => ({
  BalanceScreen: () => {
    const { Text } = require('react-native');
    return <Text testID="balance-screen">BalanceScreen</Text>;
  },
}));

jest.mock('../../screens/ProfileScreen', () => ({
  ProfileScreen: () => {
    const { Text } = require('react-native');
    return <Text testID="profile-screen">ProfileScreen</Text>;
  },
}));

jest.mock('../../screens/ApprovalsScreen', () => ({
  __esModule: true,
  default: () => {
    const { Text } = require('react-native');
    return <Text testID="approvals-screen">ApprovalsScreen</Text>;
  },
}));

jest.mock('../../screens/AllowanceSummaryScreen', () => ({
  AllowanceSummaryScreen: () => {
    const { Text } = require('react-native');
    return <Text testID="allowance-summary-screen">AllowanceSummaryScreen</Text>;
  },
}));

jest.mock('../../screens/StatisticsScreen', () => ({
  StatisticsScreen: () => {
    const { Text } = require('react-native');
    return <Text testID="statistics-screen">StatisticsScreen</Text>;
  },
}));

describe('SimpleNavigator Component', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
    mockUseAuth.mockClear();
  });

  describe('Authentication Routing', () => {
    it('should render LoginScreen when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
      });

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      expect(getByTestId('login-screen')).toBeTruthy();
      expect(queryByTestId('register-screen')).toBeNull();
      expect(queryByTestId('home-screen')).toBeNull();
    });

    it('should switch to RegisterScreen when login navigation is triggered', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
      });

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Initially on login screen
      expect(getByTestId('login-screen')).toBeTruthy();

      // Navigate to register
      fireEvent.press(getByTestId('navigate-to-register'));

      expect(queryByTestId('login-screen')).toBeNull();
      expect(getByTestId('register-screen')).toBeTruthy();
    });

    it('should switch back to LoginScreen from RegisterScreen', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
      });

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Navigate to register first
      fireEvent.press(getByTestId('navigate-to-register'));
      expect(getByTestId('register-screen')).toBeTruthy();

      // Navigate back to login
      fireEvent.press(getByTestId('back-to-login'));

      expect(getByTestId('login-screen')).toBeTruthy();
      expect(queryByTestId('register-screen')).toBeNull();
    });

    it('should render main app when authenticated', () => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      expect(queryByTestId('login-screen')).toBeNull();
      expect(queryByTestId('register-screen')).toBeNull();
      expect(getByTestId('home-screen')).toBeTruthy();
    });

    it('should render app header when authenticated', () => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });

      const { getByText } = render(<SimpleNavigator />);

      expect(getByText('Chores Tracker')).toBeTruthy();
    });
  });

  describe('Tab Navigation Basics', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });
    });

    it('should render all common tabs for authenticated users', () => {
      const { getByText } = render(<SimpleNavigator />);

      // Common tabs available to all users
      expect(getByText('Home')).toBeTruthy();
      expect(getByText('Chores')).toBeTruthy();
      expect(getByText('Profile')).toBeTruthy();
    });

    it('should start with Home tab active by default', () => {
      const { getByTestId } = render(<SimpleNavigator />);

      expect(getByTestId('home-screen')).toBeTruthy();
    });

    it('should switch to Chores tab when pressed', () => {
      const { getByText, getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Initially on Home
      expect(getByTestId('home-screen')).toBeTruthy();

      // Switch to Chores
      fireEvent.press(getByText('Chores'));

      expect(queryByTestId('home-screen')).toBeNull();
      expect(getByTestId('chores-screen')).toBeTruthy();
    });

    it('should switch to Profile tab when pressed', () => {
      const { getByText, getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Switch to Profile
      fireEvent.press(getByText('Profile'));

      expect(queryByTestId('home-screen')).toBeNull();
      expect(getByTestId('profile-screen')).toBeTruthy();
    });

    it('should handle navigation between multiple tabs', () => {
      const { getByText, getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Start at Home
      expect(getByTestId('home-screen')).toBeTruthy();

      // Navigate to Chores
      fireEvent.press(getByText('Chores'));
      expect(getByTestId('chores-screen')).toBeTruthy();
      expect(queryByTestId('home-screen')).toBeNull();

      // Navigate to Profile
      fireEvent.press(getByText('Profile'));
      expect(getByTestId('profile-screen')).toBeTruthy();
      expect(queryByTestId('chores-screen')).toBeNull();

      // Navigate back to Home
      fireEvent.press(getByText('Home'));
      expect(getByTestId('home-screen')).toBeTruthy();
      expect(queryByTestId('profile-screen')).toBeNull();
    });
  });

  describe('Parent User Navigation', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });
    });

    it('should render parent-specific tabs', () => {
      const { getByText } = render(<SimpleNavigator />);

      // Parent-specific tabs
      expect(getByText('Children')).toBeTruthy();
      expect(getByText('Approvals')).toBeTruthy();
      expect(getByText('Reports')).toBeTruthy();
    });

    it('should not render child-specific Balance tab for parents', () => {
      const { queryByText } = render(<SimpleNavigator />);

      expect(queryByText('Balance')).toBeNull();
    });

    it('should navigate to ChildrenScreen when Children tab is pressed', () => {
      const { getByText, getByTestId } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Children'));
      expect(getByTestId('children-screen')).toBeTruthy();
    });

    it('should navigate to ApprovalsScreen when Approvals tab is pressed', () => {
      const { getByText, getByTestId } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Approvals'));
      expect(getByTestId('approvals-screen')).toBeTruthy();
    });

    it('should navigate to AllowanceSummaryScreen when Reports tab is pressed', () => {
      const { getByText, getByTestId } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Reports'));
      expect(getByTestId('allowance-summary-screen')).toBeTruthy();
    });
  });

  describe('Child User Navigation', () => {
    beforeEach(() => {
      const childUser = createMockUser({ role: 'child' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: childUser,
      });
    });

    it('should render child-specific Balance tab', () => {
      const { getByText } = render(<SimpleNavigator />);

      expect(getByText('Balance')).toBeTruthy();
    });

    it('should not render parent-specific tabs for children', () => {
      const { queryByText } = render(<SimpleNavigator />);

      expect(queryByText('Children')).toBeNull();
      expect(queryByText('Approvals')).toBeNull();
      expect(queryByText('Reports')).toBeNull();
    });

    it('should navigate to BalanceScreen when Balance tab is pressed', () => {
      const { getByText, getByTestId } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Balance'));
      expect(getByTestId('balance-screen')).toBeTruthy();
    });
  });

  describe('Active Tab State Management', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });
    });

    it('should apply active styles to the current tab', () => {
      const { getByText } = render(<SimpleNavigator />);

      const homeTab = getByText('Home').parent?.parent; // TouchableOpacity container
      expect(homeTab?.props.style).toEqual(
        expect.objectContaining({
          borderTopWidth: 2,
          borderTopColor: '#007AFF',
        })
      );
    });

    it('should update active styles when switching tabs', () => {
      const { getByText } = render(<SimpleNavigator />);

      // Switch to Chores tab
      fireEvent.press(getByText('Chores'));

      const choresTab = getByText('Chores').parent?.parent; // TouchableOpacity container
      expect(choresTab?.props.style).toEqual(
        expect.objectContaining({
          borderTopWidth: 2,
          borderTopColor: '#007AFF',
        })
      );
    });

    it('should show active label styles for the current tab', () => {
      const { getByText } = render(<SimpleNavigator />);

      const homeLabel = getByText('Home');
      expect(homeLabel.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            color: '#007AFF',
            fontWeight: '600',
          })
        ])
      );
    });
  });

  describe('Screen Navigation Integration', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });
    });

    it('should handle navigation prop from HomeScreen', () => {
      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Initially on Home
      expect(getByTestId('home-screen')).toBeTruthy();

      // Use navigation from HomeScreen
      fireEvent.press(getByTestId('home-navigate'));

      // Should navigate to Chores
      expect(queryByTestId('home-screen')).toBeNull();
      expect(getByTestId('chores-screen')).toBeTruthy();
    });

    it('should update active tab state when navigating from screens', () => {
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      // Navigate from HomeScreen to Chores
      fireEvent.press(getByTestId('home-navigate'));

      // Check that Chores tab is now active
      const choresLabel = getByText('Chores');
      expect(choresLabel.props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            color: '#007AFF',
            fontWeight: '600',
          })
        ])
      );
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle missing user data gracefully', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: null,
      });

      const { getByTestId } = render(<SimpleNavigator />);

      // Should still render but might have different behavior
      // The component should handle null user gracefully
      expect(() => {
        // Component should not crash with null user
        const element = getByTestId('home-screen');
        expect(element).toBeTruthy();
      }).not.toThrow();
    });

    it('should handle undefined user role gracefully', () => {
      const userWithoutRole = createMockUser({ role: undefined as any });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: userWithoutRole,
      });

      const { getByText, queryByText } = render(<SimpleNavigator />);

      // Should default to child behavior when role is undefined
      expect(getByText('Balance')).toBeTruthy();
      expect(queryByText('Children')).toBeNull();
    });

    it('should render default screen for unknown tab states', () => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });

      const { getByTestId } = render(<SimpleNavigator />);

      // The default case in renderScreen should render HomeScreen
      expect(getByTestId('home-screen')).toBeTruthy();
    });

    it('should handle rapid tab switching without errors', () => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });

      const { getByText } = render(<SimpleNavigator />);

      // Rapidly switch between tabs
      expect(() => {
        fireEvent.press(getByText('Chores'));
        fireEvent.press(getByText('Profile'));
        fireEvent.press(getByText('Home'));
        fireEvent.press(getByText('Children'));
        fireEvent.press(getByText('Home'));
      }).not.toThrow();
    });
  });

  describe('UI Elements and Styling', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
      });
    });

    it('should render tab icons correctly', () => {
      const { getByText } = render(<SimpleNavigator />);

      // Check that emoji icons are rendered
      expect(getByText('🏠')).toBeTruthy(); // Home
      expect(getByText('✅')).toBeTruthy(); // Chores  
      expect(getByText('👨‍👩‍👧‍👦')).toBeTruthy(); // Children
      expect(getByText('✔️')).toBeTruthy(); // Approvals
      expect(getByText('📊')).toBeTruthy(); // Reports
      expect(getByText('👤')).toBeTruthy(); // Profile
    });

    it('should render correct child-specific icon', () => {
      const childUser = createMockUser({ role: 'child' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: childUser,
      });

      const { getByText } = render(<SimpleNavigator />);

      expect(getByText('💰')).toBeTruthy(); // Balance
    });

    it('should render header with correct title', () => {
      const { getByText } = render(<SimpleNavigator />);

      expect(getByText('Chores Tracker')).toBeTruthy();
    });

    it('should not render header when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
      });

      const { queryByText } = render(<SimpleNavigator />);

      expect(queryByText('Chores Tracker')).toBeNull();
    });
  });
});