/**
 * Authentication Flow Integration Tests
 * Tests complete authentication workflows using the actual SimpleNavigator
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { SimpleNavigator } from '../../navigation/SimpleNavigator';
import { authAPI } from '../../api/client';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { resetAllMocks, createMockUser, createMockApiParent, createMockApiChild } from '../../test-utils';

// Mock the auth API
jest.mock('../../api/client', () => ({
  authAPI: {
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
    getToken: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

// Mock the useAuth hook directly
const mockUseAuth = jest.fn();
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Export mockUseAuth for external access
export { mockUseAuth };

// Mock all screens as simple components
jest.mock('../../screens/LoginScreen', () => ({
  LoginScreen: ({ onNavigateToRegister }: any) => {
    const mockReact = require('react');
    const { View, Text, TouchableOpacity } = require('react-native');
    
    return (
      <View testID="login-screen">
        <Text>Login Screen</Text>
        <TouchableOpacity testID="navigate-to-register" onPress={onNavigateToRegister}>
          <Text>Go to Register</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="mock-login-success" onPress={async () => {
          try {
            const { useAuth } = require('../../contexts/AuthContext');
            const { login } = useAuth();
            await login('testuser', 'password');
          } catch (error) {
            console.log('Login failed:', error);
          }
        }}>
          <Text>Mock Login Success</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="mock-login-error" onPress={async () => {
          try {
            const { useAuth } = require('../../contexts/AuthContext');
            const { login } = useAuth();
            await login('baduser', 'badpass');
          } catch (error) {
            console.log('Expected login error');
          }
        }}>
          <Text>Mock Login Error</Text>
        </TouchableOpacity>
      </View>
    );
  },
}));

jest.mock('../../screens/RegisterScreen', () => ({
  RegisterScreen: ({ onBackToLogin }: any) => {
    const { View, Text, TouchableOpacity } = require('react-native');
    return (
      <View testID="register-screen">
        <Text>Register Screen</Text>
        <TouchableOpacity testID="back-to-login" onPress={onBackToLogin}>
          <Text>Back to Login</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="mock-register-success" onPress={() => {
          console.log('Mock registration success');
          onBackToLogin();
        }}>
          <Text>Mock Register Success</Text>
        </TouchableOpacity>
      </View>
    );
  },
}));

jest.mock('../../screens/HomeScreen', () => ({
  HomeScreen: ({ onNavigate }: any) => {
    const { View, Text, TouchableOpacity } = require('react-native');
    const { useAuth } = require('../../contexts/AuthContext');
    const { user, logout } = useAuth();

    return (
      <View testID="home-screen">
        <Text testID="welcome-message">Welcome, {user?.username || 'User'}!</Text>
        <Text testID="user-role">Role: {user?.role || 'unknown'}</Text>
        <TouchableOpacity testID="logout-button" onPress={logout}>
          <Text>Logout</Text>
        </TouchableOpacity>
        {onNavigate && (
          <TouchableOpacity testID="navigate-chores" onPress={() => onNavigate('Chores')}>
            <Text>Go to Chores</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  },
}));

// Mock other screens simply
jest.mock('../../screens/ChoresScreen', () => ({
  ChoresScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="chores-screen"><Text>Chores Screen</Text></View>;
  },
}));

jest.mock('../../screens/ChildrenScreen', () => ({
  ChildrenScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="children-screen"><Text>Children Screen</Text></View>;
  },
}));

jest.mock('../../screens/BalanceScreen', () => ({
  BalanceScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="balance-screen"><Text>Balance Screen</Text></View>;
  },
}));

jest.mock('../../screens/ProfileScreen', () => ({
  ProfileScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="profile-screen"><Text>Profile Screen</Text></View>;
  },
}));

jest.mock('../../screens/ApprovalsScreen', () => ({
  __esModule: true,
  default: () => {
    const { View, Text } = require('react-native');
    return <View testID="approvals-screen"><Text>Approvals Screen</Text></View>;
  },
}));

jest.mock('../../screens/AllowanceSummaryScreen', () => ({
  AllowanceSummaryScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="allowance-summary-screen"><Text>Allowance Summary</Text></View>;
  },
}));

jest.mock('../../screens/StatisticsScreen', () => ({
  StatisticsScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="statistics-screen"><Text>Statistics Screen</Text></View>;
  },
}));

describe('Authentication Flow Integration Tests', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
    
    // Reset AsyncStorage mocks
    (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);
    (AsyncStorage.setItem as jest.Mock).mockResolvedValue(undefined);
    (AsyncStorage.removeItem as jest.Mock).mockResolvedValue(undefined);
    
    // Default auth API behavior
    mockedAuthAPI.getToken.mockResolvedValue(null);
    mockedAuthAPI.getCurrentUser.mockResolvedValue(null);
    mockedAuthAPI.logout.mockResolvedValue(undefined);
  });

  describe('Authentication State Transitions', () => {
    it('should start with login screen when not authenticated', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      await waitFor(() => {
        expect(getByTestId('login-screen')).toBeTruthy();
        expect(queryByTestId('home-screen')).toBeNull();
        expect(queryByTestId('register-screen')).toBeNull();
      });
    });

    it('should transition to register screen and back to login', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Start at login
      expect(getByTestId('login-screen')).toBeTruthy();

      // Navigate to register
      fireEvent.press(getByTestId('navigate-to-register'));

      await waitFor(() => {
        expect(queryByTestId('login-screen')).toBeNull();
        expect(getByTestId('register-screen')).toBeTruthy();
      });

      // Navigate back to login
      fireEvent.press(getByTestId('back-to-login'));

      await waitFor(() => {
        expect(getByTestId('login-screen')).toBeTruthy();
        expect(queryByTestId('register-screen')).toBeNull();
      });
    });

    it('should transition to home screen after successful parent login', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'parent-token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.login.mockResolvedValue(loginResponse);
      
      // Start unauthenticated, will simulate login
      mockUseAuth.mockReturnValue({
        isAuthenticated: true, // Simulate post-login state
        isLoading: false,
        user: mockParent,
        login: jest.fn().mockResolvedValue(loginResponse),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });
      
      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Start at login
      expect(getByTestId('login-screen')).toBeTruthy();

      // Perform mock login
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-success'));
      });

      // Should transition to home
      await waitFor(() => {
        expect(queryByTestId('login-screen')).toBeNull();
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      // Verify user information
      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, testparent!');
      expect(getByTestId('user-role')).toHaveTextContent('Role: parent');

      // Verify API was called
      expect(mockedAuthAPI.login).toHaveBeenCalledWith('testuser', 'password');
    });

    it('should show parent-specific tabs after parent login', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'parent-token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.login.mockResolvedValue(loginResponse);
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      // Perform login
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-success'));
      });

      await waitFor(() => {
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      // Verify parent-specific tabs
      expect(getByText('Children')).toBeTruthy();
      expect(getByText('Approvals')).toBeTruthy();
      expect(getByText('Reports')).toBeTruthy();
      
      // Should not have child-specific Balance tab
      const { queryByText } = render(<SimpleNavigator />);
      expect(queryByText('Balance')).toBeNull();
    });

    it('should show child-specific interface after child login', async () => {
      const mockChild = createMockApiChild();
      const loginResponse = {
        access_token: 'child-token',
        token_type: 'bearer',
        user: mockChild,
      };

      mockedAuthAPI.login.mockResolvedValue(loginResponse);
      
      const { getByTestId, getByText, queryByText } = render(<SimpleNavigator />);

      // Perform login
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-success'));
      });

      await waitFor(() => {
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      // Verify user information shows child
      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, testchild!');
      expect(getByTestId('user-role')).toHaveTextContent('Role: child');

      // Verify child-specific interface
      expect(getByText('Balance')).toBeTruthy();
      expect(queryByText('Children')).toBeNull();
      expect(queryByText('Approvals')).toBeNull();
      expect(queryByText('Reports')).toBeNull();
    });
  });

  describe('Login Error Handling Integration', () => {
    it('should handle login failures gracefully', async () => {
      const loginError = new Error('Invalid credentials');
      mockedAuthAPI.login.mockRejectedValue(loginError);
      
      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Attempt login with error
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-error'));
      });

      // Should remain on login screen
      await waitFor(() => {
        expect(getByTestId('login-screen')).toBeTruthy();
        expect(queryByTestId('home-screen')).toBeNull();
      });

      expect(mockedAuthAPI.login).toHaveBeenCalledWith('baduser', 'badpass');
    });

    it('should handle network errors during login', async () => {
      mockedAuthAPI.login.mockRejectedValue(new Error('Network Error'));
      
      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      await act(async () => {
        fireEvent.press(getByTestId('mock-login-error'));
      });

      // Should remain on login screen
      expect(getByTestId('login-screen')).toBeTruthy();
      expect(queryByTestId('home-screen')).toBeNull();
    });
  });

  describe('Logout Integration Flow', () => {
    it('should complete logout flow and return to login', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'parent-token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.login.mockResolvedValue(loginResponse);
      
      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Login first
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-success'));
      });

      await waitFor(() => {
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      // Logout
      await act(async () => {
        fireEvent.press(getByTestId('logout-button'));
      });

      // Should return to login screen
      await waitFor(() => {
        expect(queryByTestId('home-screen')).toBeNull();
        expect(getByTestId('login-screen')).toBeTruthy();
      });

      // Verify logout API was called
      expect(mockedAuthAPI.logout).toHaveBeenCalled();
    });

    it('should handle logout errors gracefully', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'parent-token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.login.mockResolvedValue(loginResponse);
      mockedAuthAPI.logout.mockRejectedValue(new Error('Logout failed'));
      
      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Login first
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-success'));
      });

      await waitFor(() => {
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      // Logout (even with error should clear local state)
      await act(async () => {
        fireEvent.press(getByTestId('logout-button'));
      });

      // Should still return to login screen
      await waitFor(() => {
        expect(queryByTestId('home-screen')).toBeNull();
        expect(getByTestId('login-screen')).toBeTruthy();
      });
    });
  });

  describe('Session Persistence Integration', () => {
    it('should restore authenticated session on app start', async () => {
      const mockParent = createMockApiParent();
      const storedUser = {
        id: mockParent.id,
        username: mockParent.username,
        role: 'parent',
        email: mockParent.email,
        full_name: mockParent.full_name,
      };

      // Mock existing session
      mockedAuthAPI.getToken.mockResolvedValue('stored-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValue(mockParent);
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(JSON.stringify(storedUser));

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Should skip login and go to home
      await waitFor(() => {
        expect(queryByTestId('login-screen')).toBeNull();
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, testparent!');
    });

    it('should handle corrupted session data', async () => {
      mockedAuthAPI.getToken.mockResolvedValue('invalid-token');
      mockedAuthAPI.getCurrentUser.mockRejectedValue(new Error('Unauthorized'));
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('invalid-json');

      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Should fallback to login screen
      await waitFor(() => {
        expect(getByTestId('login-screen')).toBeTruthy();
        expect(queryByTestId('home-screen')).toBeNull();
      });
    });
  });

  describe('Cross-Screen Navigation Integration', () => {
    it('should navigate between screens after authentication', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'parent-token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.login.mockResolvedValue(loginResponse);
      
      const { getByTestId, getByText, queryByTestId } = render(<SimpleNavigator />);

      // Login
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-success'));
      });

      await waitFor(() => {
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      // Navigate to chores from home
      fireEvent.press(getByTestId('navigate-chores'));

      await waitFor(() => {
        expect(queryByTestId('home-screen')).toBeNull();
        expect(getByTestId('chores-screen')).toBeTruthy();
      });

      // Navigate to other parent screens via tabs
      fireEvent.press(getByText('Children'));
      expect(getByTestId('children-screen')).toBeTruthy();

      fireEvent.press(getByText('Approvals'));
      expect(getByTestId('approvals-screen')).toBeTruthy();

      fireEvent.press(getByText('Reports'));
      expect(getByTestId('allowance-summary-screen')).toBeTruthy();

      // Navigate back to home
      fireEvent.press(getByText('Home'));
      expect(getByTestId('home-screen')).toBeTruthy();
    });

    it('should maintain authentication state across navigation', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'parent-token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.login.mockResolvedValue(loginResponse);
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      // Login
      await act(async () => {
        fireEvent.press(getByTestId('mock-login-success'));
      });

      await waitFor(() => {
        expect(getByTestId('home-screen')).toBeTruthy();
      });

      // Navigate to different screens
      fireEvent.press(getByText('Profile'));
      expect(getByTestId('profile-screen')).toBeTruthy();

      fireEvent.press(getByText('Children'));
      expect(getByTestId('children-screen')).toBeTruthy();

      // Return to home and verify user is still authenticated
      fireEvent.press(getByText('Home'));
      expect(getByTestId('welcome-message')).toHaveTextContent('Welcome, testparent!');
      expect(getByTestId('user-role')).toHaveTextContent('Role: parent');
    });
  });
});