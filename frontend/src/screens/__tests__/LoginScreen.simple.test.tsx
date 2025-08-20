/**
 * LoginScreen Simple Component Tests
 * Basic tests for the authentication login screen
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { LoginScreen } from '../LoginScreen';
import { AuthProvider, useAuth } from '../../contexts/AuthContext';

// Mock React Native Alert
const mockAlert = jest.fn();

// Mock the Alert module
global.alert = mockAlert;

// Also mock it at the module level
jest.doMock('react-native', () => {
  const RN = jest.requireActual('react-native');
  const MockAlert = { alert: mockAlert };
  return Object.setPrototypeOf({ Alert: MockAlert }, RN);
});

// Mock the auth API
jest.mock('@/api/client', () => ({
  authAPI: {
    login: jest.fn(),
    logout: jest.fn(),
    getToken: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

// Mock the useAuth hook directly
const mockLogin = jest.fn();
jest.mock('../../contexts/AuthContext', () => ({
  ...jest.requireActual('../../contexts/AuthContext'),
  useAuth: () => ({
    login: mockLogin,
    logout: jest.fn(),
    user: null,
    isAuthenticated: false,
    isLoading: false,
  }),
}));

describe('LoginScreen (Basic Tests)', () => {
  const mockOnNavigateToRegister = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockAlert.mockClear();
    mockLogin.mockClear();
  });

  describe('Basic Rendering', () => {
    it('should render login form elements', () => {
      const { getByText, getByPlaceholderText } = render(
        <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
      );

      expect(getByText('Chores Tracker')).toBeTruthy();
      expect(getByText('Sign in to your account')).toBeTruthy();
      expect(getByPlaceholderText('Enter your username')).toBeTruthy();
      expect(getByPlaceholderText('Enter your password')).toBeTruthy();
      expect(getByText('Sign In')).toBeTruthy();
    });

    it('should have correct input properties', () => {
      const { getByPlaceholderText } = render(
        <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');

      expect(usernameInput.props.autoCapitalize).toBe('none');
      expect(passwordInput.props.secureTextEntry).toBe(true);
    });
  });

  describe('Form Validation', () => {
    it('should show error for empty credentials', async () => {
      const { getByText } = render(
        <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
      );

      const signInButton = getByText('Sign In');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please enter both username and password'
      );
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('should update input values correctly', () => {
      const { getByPlaceholderText } = render(
        <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');

      expect(usernameInput.props.value).toBe('testuser');
      expect(passwordInput.props.value).toBe('password123');
    });
  });

  describe('Authentication Flow', () => {
    it('should call login with correct credentials', async () => {
      mockLogin.mockResolvedValueOnce(undefined);

      const { getByPlaceholderText, getByText } = render(
        <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    });

    it('should handle login failure', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Invalid credentials'
          }
        }
      };
      mockLogin.mockRejectedValueOnce(errorResponse);

      const { getByPlaceholderText, getByText } = render(
        <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'wrongpassword');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith('Login Error', 'Invalid credentials');
    });
  });

  describe('Navigation', () => {
    it('should call onNavigateToRegister when register link is pressed', () => {
      const { getByText } = render(
        <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
      );

      const registerLink = getByText("Don't have an account? Sign Up");
      
      fireEvent.press(registerLink);
      
      expect(mockOnNavigateToRegister).toHaveBeenCalledTimes(1);
    });
  });
});