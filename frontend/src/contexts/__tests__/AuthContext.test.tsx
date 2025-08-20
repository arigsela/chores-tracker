/**
 * AuthContext Comprehensive Tests (Simplified Working Version)
 * Tests core authentication flows and state management
 */

import React from 'react';
import { render, act, waitFor } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthProvider, useAuth } from '../AuthContext';
import { authAPI } from '@/api/client';
import { resetAllMocks, createMockApiUser, createMockApiParent, createMockApiChild } from '../../test-utils';

// Mock the auth API
jest.mock('@/api/client', () => ({
  authAPI: {
    login: jest.fn(),
    logout: jest.fn(),
    getToken: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

// Test component to access AuthContext
const TestComponent = ({ onContextChange }: { onContextChange?: (context: any) => void }) => {
  const authContext = useAuth();
  
  React.useEffect(() => {
    if (onContextChange) {
      onContextChange(authContext);
    }
  }, [authContext, onContextChange]);

  return null; // Simplified for testing
};

describe('AuthContext (Core Tests)', () => {
  let mockOnContextChange: jest.Mock;

  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
    mockOnContextChange = jest.fn();
    
    // Reset AsyncStorage mocks
    (AsyncStorage.getItem as jest.Mock).mockClear();
    (AsyncStorage.setItem as jest.Mock).mockClear();
    (AsyncStorage.removeItem as jest.Mock).mockClear();
    
    // Reset authAPI mocks
    mockedAuthAPI.login.mockClear();
    mockedAuthAPI.logout.mockClear();
    mockedAuthAPI.getToken.mockClear();
    mockedAuthAPI.getCurrentUser.mockClear();
  });

  describe('Provider Setup and Hook Usage', () => {
    it('should provide context to children components', () => {
      let contextValue: any;
      
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { contextValue = ctx; }} />
        </AuthProvider>
      );

      expect(contextValue).toBeDefined();
      expect(contextValue.isAuthenticated).toBeDefined();
      expect(contextValue.isLoading).toBeDefined();
      expect(contextValue.user).toBeDefined();
      expect(contextValue.login).toBeInstanceOf(Function);
      expect(contextValue.logout).toBeInstanceOf(Function);
      expect(contextValue.checkAuthStatus).toBeInstanceOf(Function);
    });

    it('should throw error when useAuth is used outside provider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleSpy.mockRestore();
    });

    it('should initialize with default unauthenticated state', async () => {
      mockedAuthAPI.getToken.mockResolvedValue(null);
      let contextValue: any;
      
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { contextValue = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(contextValue.isLoading).toBe(false);
        expect(contextValue.isAuthenticated).toBe(false);
        expect(contextValue.user).toBeNull();
      });
    });
  });

  describe('Initial Authentication Check', () => {
    it('should check auth status on mount with valid token', async () => {
      const mockUser = createMockApiParent();
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValue(mockUser);

      let contextValue: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { contextValue = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(contextValue.isAuthenticated).toBe(true);
        expect(contextValue.user?.role).toBe('parent');
        expect(contextValue.user?.username).toBe(mockUser.username);
      });

      expect(mockedAuthAPI.getToken).toHaveBeenCalled();
      expect(mockedAuthAPI.getCurrentUser).toHaveBeenCalled();
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        '@chores_tracker:user',
        expect.stringContaining(mockUser.username)
      );
    });

    it('should handle no token on mount', async () => {
      mockedAuthAPI.getToken.mockResolvedValue(null);
      let contextValue: any;

      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { contextValue = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(contextValue.isAuthenticated).toBe(false);
        expect(contextValue.isLoading).toBe(false);
      });

      expect(mockedAuthAPI.getCurrentUser).not.toHaveBeenCalled();
    });

    it('should fallback to stored user data when API fails', async () => {
      const storedUser = {
        id: 1,
        username: 'storeduser',
        role: 'parent',
        email: 'stored@test.com',
      };

      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockRejectedValue(new Error('Network error'));
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(JSON.stringify(storedUser));

      let contextValue: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { contextValue = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(contextValue.isAuthenticated).toBe(true);
        expect(contextValue.user?.username).toBe('storeduser');
        expect(contextValue.user?.role).toBe('parent');
      });

      expect(AsyncStorage.getItem).toHaveBeenCalledWith('@chores_tracker:user');
    });

    it('should logout when API fails and no stored user', async () => {
      mockedAuthAPI.getToken.mockResolvedValue('invalid-token');
      mockedAuthAPI.getCurrentUser.mockRejectedValue(new Error('401 Unauthorized'));
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue(null);

      let contextValue: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { contextValue = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(contextValue.isAuthenticated).toBe(false);
      });

      expect(mockedAuthAPI.logout).toHaveBeenCalled();
    });
  });

  describe('Login Flow', () => {
    it('should handle successful parent login', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'new-token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockResolvedValue(loginResponse);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      // Perform login
      await act(async () => {
        await authContext.login('testparent', 'password123');
      });

      expect(mockedAuthAPI.login).toHaveBeenCalledWith('testparent', 'password123');
      expect(authContext.isAuthenticated).toBe(true);
      expect(authContext.user?.role).toBe('parent');
      expect(authContext.user?.username).toBe(mockParent.username);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        '@chores_tracker:user',
        expect.stringContaining(mockParent.username)
      );
    });

    it('should handle successful child login', async () => {
      const mockChild = createMockApiChild();
      const loginResponse = {
        access_token: 'child-token',
        token_type: 'bearer',
        user: mockChild,
      };

      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockResolvedValue(loginResponse);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      await act(async () => {
        await authContext.login('testchild', 'childpass');
      });

      expect(authContext.isAuthenticated).toBe(true);
      expect(authContext.user?.role).toBe('child');
      expect(authContext.user?.username).toBe(mockChild.username);
    });

    it('should handle login failure and throw error', async () => {
      const loginError = new Error('Invalid credentials');
      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockRejectedValue(loginError);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      await expect(
        act(async () => {
          await authContext.login('baduser', 'wrongpass');
        })
      ).rejects.toThrow('Invalid credentials');

      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.user).toBeNull();
    });
  });

  describe('Logout Flow', () => {
    it('should handle successful logout', async () => {
      // Setup authenticated state first
      const mockUser = createMockApiParent();
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValue(mockUser);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(authContext.isAuthenticated).toBe(true);
      });

      // Perform logout
      await act(async () => {
        await authContext.logout();
      });

      expect(mockedAuthAPI.logout).toHaveBeenCalled();
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('@chores_tracker:user');
      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.user).toBeNull();
    });

    it('should handle logout errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Setup authenticated state
      const mockUser = createMockApiParent();
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValue(mockUser);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isAuthenticated).toBe(true);
      });

      // Now mock logout to fail
      mockedAuthAPI.logout.mockRejectedValue(new Error('Logout failed'));

      // Logout should still work even if API call fails
      await act(async () => {
        await authContext.logout();
      });

      // The context should still be cleared even if API call fails
      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.user).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith('Logout error:', expect.any(Error));

      consoleSpy.mockRestore();
    });
  });

  describe('Manual Auth Status Check', () => {
    it('should refresh user data when checkAuthStatus is called', async () => {
      const initialUser = createMockApiParent({ username: 'olduser' });
      const updatedUser = createMockApiParent({ username: 'newuser' });

      // Initial setup
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValueOnce(initialUser);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.user?.username).toBe('olduser');
      });

      // Mock updated user data
      mockedAuthAPI.getCurrentUser.mockResolvedValueOnce(updatedUser);

      // Call checkAuthStatus manually
      await act(async () => {
        await authContext.checkAuthStatus();
      });

      expect(authContext.user?.username).toBe('newuser');
    });

    it('should handle token expiry during status check', async () => {
      // Setup authenticated state
      const mockUser = createMockApiParent();
      mockedAuthAPI.getToken.mockResolvedValueOnce('valid-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValueOnce(mockUser);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isAuthenticated).toBe(true);
      });

      // Simulate token expiry
      mockedAuthAPI.getToken.mockResolvedValueOnce(null);

      await act(async () => {
        await authContext.checkAuthStatus();
      });

      expect(authContext.isAuthenticated).toBe(false);
      expect(authContext.user).toBeNull();
    });
  });

  describe('Role-Based Access Control', () => {
    it('should correctly identify parent users', async () => {
      const mockParent = createMockApiParent();
      const loginResponse = {
        access_token: 'token',
        token_type: 'bearer',
        user: mockParent,
      };

      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockResolvedValue(loginResponse);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      await act(async () => {
        await authContext.login('parent', 'password');
      });

      expect(authContext.user?.role).toBe('parent');
      expect(authContext.user?.id).toBe(mockParent.id);
    });

    it('should correctly identify child users', async () => {
      const mockChild = createMockApiChild();
      const loginResponse = {
        access_token: 'token',
        token_type: 'bearer',
        user: mockChild,
      };

      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockResolvedValue(loginResponse);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      await act(async () => {
        await authContext.login('child', 'password');
      });

      expect(authContext.user?.role).toBe('child');
      expect(authContext.user?.id).toBe(mockChild.id);
    });

    it('should handle user data mapping correctly', async () => {
      const apiUser = {
        id: 123,
        username: 'testuser',
        is_parent: false,
        email: 'test@example.com',
        full_name: 'Test User Full Name',
      };

      const loginResponse = {
        access_token: 'token',
        token_type: 'bearer',
        user: apiUser,
      };

      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockResolvedValue(loginResponse);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      await act(async () => {
        await authContext.login('testuser', 'password');
      });

      expect(authContext.user).toEqual({
        id: 123,
        username: 'testuser',
        role: 'child',
        email: 'test@example.com',
        full_name: 'Test User Full Name',
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle AsyncStorage errors gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Mock the auth API to return token but AsyncStorage to fail
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockRejectedValue(new Error('API error'));
      (AsyncStorage.getItem as jest.Mock).mockRejectedValue(new Error('Storage error'));

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
        expect(authContext.isAuthenticated).toBe(false);
      });

      expect(consoleSpy).toHaveBeenCalledWith('Error checking auth status:', expect.any(Error));
      consoleSpy.mockRestore();
    });

    it('should handle malformed stored user data', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('invalid-json');
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockRejectedValue(new Error('API error'));

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
        expect(authContext.isAuthenticated).toBe(false);
      });

      // JSON.parse('invalid-json') throws an error which gets caught in the outer try-catch
      // This logs the error but doesn't call logout - the user is just set to unauthenticated
      expect(consoleSpy).toHaveBeenCalledWith('Error checking auth status:', expect.any(Error));
      
      consoleSpy.mockRestore();
    });

    it('should handle missing user data in login response', async () => {
      const incompleteResponse = {
        access_token: 'token',
        token_type: 'bearer',
        user: {
          id: 1,
          username: 'testuser',
          // Missing is_parent field
        },
      };

      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockResolvedValue(incompleteResponse);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      await act(async () => {
        await authContext.login('testuser', 'password');
      });

      expect(authContext.user?.role).toBe('child'); // Default when is_parent is falsy
    });
  });

  describe('Data Persistence', () => {
    it('should store user data in AsyncStorage after login', async () => {
      const mockUser = createMockApiParent();
      const loginResponse = {
        access_token: 'token',
        token_type: 'bearer',
        user: mockUser,
      };

      mockedAuthAPI.getToken.mockResolvedValue(null);
      mockedAuthAPI.login.mockResolvedValue(loginResponse);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isLoading).toBe(false);
      });

      await act(async () => {
        await authContext.login('testuser', 'password');
      });

      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        '@chores_tracker:user',
        JSON.stringify({
          id: mockUser.id,
          username: mockUser.username,
          role: 'parent',
          email: mockUser.email,
          full_name: mockUser.full_name,
        })
      );
    });

    it('should clear user data from AsyncStorage after logout', async () => {
      // Setup authenticated state
      const mockUser = createMockApiParent();
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValue(mockUser);
      mockedAuthAPI.logout.mockResolvedValue(undefined); // Ensure logout succeeds

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isAuthenticated).toBe(true);
      });

      await act(async () => {
        await authContext.logout();
      });

      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('@chores_tracker:user');
    });

    it('should update stored user data during checkAuthStatus', async () => {
      const mockUser = createMockApiParent();
      mockedAuthAPI.getToken.mockResolvedValue('valid-token');
      mockedAuthAPI.getCurrentUser.mockResolvedValue(mockUser);

      let authContext: any;
      render(
        <AuthProvider>
          <TestComponent onContextChange={(ctx) => { authContext = ctx; }} />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authContext.isAuthenticated).toBe(true);
      });

      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        '@chores_tracker:user',
        expect.stringContaining(mockUser.username)
      );
    });
  });
});