/**
 * LoginScreen Component Tests
 * Tests the authentication login screen including form validation, error handling, and navigation
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { LoginScreen } from '../LoginScreen';
import { AuthContext } from '../../contexts/AuthContext';

// Mock the Alert module
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Alert: {
      alert: jest.fn(),
    },
  };
});

const mockAlert = Alert.alert as jest.MockedFunction<typeof Alert.alert>;

// Mock AuthContext
const mockLogin = jest.fn();
const createMockAuthContext = (overrides = {}) => ({
  login: mockLogin,
  logout: jest.fn(),
  checkAuthStatus: jest.fn(),
  user: null,
  isAuthenticated: false,
  isLoading: false,
  ...overrides,
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode; authValue?: any }> = ({ 
  children, 
  authValue = createMockAuthContext() 
}) => (
  <AuthContext.Provider value={authValue}>
    {children}
  </AuthContext.Provider>
);

describe('LoginScreen Component', () => {
  const mockOnNavigateToRegister = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockAlert.mockClear();
  });

  describe('Basic Rendering', () => {
    it('should render login form with all required elements', () => {
      const { getByText, getByPlaceholderText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      expect(getByText('Chores Tracker')).toBeTruthy();
      expect(getByText('Sign in to your account')).toBeTruthy();
      expect(getByText('Username')).toBeTruthy();
      expect(getByText('Password')).toBeTruthy();
      expect(getByPlaceholderText('Enter your username')).toBeTruthy();
      expect(getByPlaceholderText('Enter your password')).toBeTruthy();
      expect(getByText('Sign In')).toBeTruthy();
      expect(getByText("Don't have an account? Sign Up")).toBeTruthy();
    });

    it('should render form inputs with correct properties', () => {
      const { getByPlaceholderText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');

      expect(usernameInput.props.autoCapitalize).toBe('none');
      expect(usernameInput.props.autoCorrect).toBe(false);
      expect(passwordInput.props.secureTextEntry).toBe(true);
      expect(passwordInput.props.autoCapitalize).toBe('none');
      expect(passwordInput.props.autoCorrect).toBe(false);
    });

    it('should have accessible elements with correct text content', () => {
      const { getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      // Header section
      expect(getByText('Chores Tracker')).toBeTruthy();
      expect(getByText('Sign in to your account')).toBeTruthy();
      
      // Form labels
      expect(getByText('Username')).toBeTruthy();
      expect(getByText('Password')).toBeTruthy();
      
      // Buttons
      expect(getByText('Sign In')).toBeTruthy();
      expect(getByText("Don't have an account? Sign Up")).toBeTruthy();
    });
  });

  describe('Form Input Handling', () => {
    it('should update username input value', () => {
      const { getByPlaceholderText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      
      fireEvent.changeText(usernameInput, 'testuser');
      expect(usernameInput.props.value).toBe('testuser');
    });

    it('should update password input value', () => {
      const { getByPlaceholderText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const passwordInput = getByPlaceholderText('Enter your password');
      
      fireEvent.changeText(passwordInput, 'password123');
      expect(passwordInput.props.value).toBe('password123');
    });

    it('should handle empty form submission', async () => {
      const { getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
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

    it('should handle partial form submission (username only)', async () => {
      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please enter both username and password'
      );
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('should handle partial form submission (password only)', async () => {
      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please enter both username and password'
      );
      expect(mockLogin).not.toHaveBeenCalled();
    });
  });

  describe('Authentication Flow', () => {
    it('should call login with correct credentials on successful submission', async () => {
      mockLogin.mockResolvedValueOnce(undefined);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
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
      expect(mockAlert).not.toHaveBeenCalled();
    });

    it('should handle login failure with specific error message', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Invalid credentials'
          }
        }
      };
      mockLogin.mockRejectedValueOnce(errorResponse);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'wrongpassword');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockLogin).toHaveBeenCalledWith('testuser', 'wrongpassword');
      expect(mockAlert).toHaveBeenCalledWith('Login Error', 'Invalid credentials');
    });

    it('should handle login failure with generic error message', async () => {
      const genericError = new Error('Network error');
      mockLogin.mockRejectedValueOnce(genericError);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
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
      expect(mockAlert).toHaveBeenCalledWith('Login Error', 'Login failed. Please try again.');
    });
  });

  describe('Loading State Management', () => {
    it('should show loading indicator during login process', async () => {
      let resolveLogin: () => void;
      const loginPromise = new Promise<void>((resolve) => {
        resolveLogin = resolve;
      });
      mockLogin.mockReturnValueOnce(loginPromise);

      const { getByPlaceholderText, getByText, queryByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      // Should show loading state
      expect(queryByText('Sign In')).toBeNull();
      expect(usernameInput.props.editable).toBe(false);
      expect(passwordInput.props.editable).toBe(false);

      // Complete the login
      await act(async () => {
        resolveLogin!();
      });
    });

    it('should disable form inputs during loading', async () => {
      let resolveLogin: () => void;
      const loginPromise = new Promise<void>((resolve) => {
        resolveLogin = resolve;
      });
      mockLogin.mockReturnValueOnce(loginPromise);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      const registerButton = getByText("Don't have an account? Sign Up");
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      // Inputs should be disabled
      expect(usernameInput.props.editable).toBe(false);
      expect(passwordInput.props.editable).toBe(false);
      expect(signInButton.props.disabled).toBe(true);
      expect(registerButton.props.disabled).toBe(true);

      // Complete the login
      await act(async () => {
        resolveLogin!();
      });
    });

    it('should re-enable form after failed login', async () => {
      const loginError = new Error('Login failed');
      mockLogin.mockRejectedValueOnce(loginError);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      // Wait for error handling
      await waitFor(() => {
        expect(usernameInput.props.editable).toBe(true);
        expect(passwordInput.props.editable).toBe(true);
        expect(signInButton.props.disabled).toBe(false);
      });
    });
  });

  describe('Navigation Handling', () => {
    it('should call onNavigateToRegister when register link is pressed', () => {
      const { getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const registerLink = getByText("Don't have an account? Sign Up");
      
      fireEvent.press(registerLink);
      
      expect(mockOnNavigateToRegister).toHaveBeenCalledTimes(1);
    });

    it('should not allow navigation during loading', async () => {
      let resolveLogin: () => void;
      const loginPromise = new Promise<void>((resolve) => {
        resolveLogin = resolve;
      });
      mockLogin.mockReturnValueOnce(loginPromise);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      const registerLink = getByText("Don't have an account? Sign Up");
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      // Try to navigate during loading
      fireEvent.press(registerLink);
      
      expect(mockOnNavigateToRegister).not.toHaveBeenCalled();
      expect(registerLink.props.disabled).toBe(true);

      // Complete the login
      await act(async () => {
        resolveLogin!();
      });
    });
  });

  describe('Form Validation Edge Cases', () => {
    it('should handle whitespace-only username', async () => {
      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, '   ');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please enter both username and password'
      );
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('should handle whitespace-only password', async () => {
      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, '   ');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please enter both username and password'
      );
      expect(mockLogin).not.toHaveBeenCalled();
    });

    it('should handle very long credentials', async () => {
      mockLogin.mockResolvedValueOnce(undefined);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      const longUsername = 'a'.repeat(100);
      const longPassword = 'b'.repeat(100);
      
      fireEvent.changeText(usernameInput, longUsername);
      fireEvent.changeText(passwordInput, longPassword);
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockLogin).toHaveBeenCalledWith(longUsername, longPassword);
    });
  });

  describe('Error Message Handling', () => {
    it('should handle malformed error response', async () => {
      const malformedError = {
        response: {
          data: null
        }
      };
      mockLogin.mockRejectedValueOnce(malformedError);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith('Login Error', 'Login failed. Please try again.');
    });

    it('should handle error without response', async () => {
      const networkError = new Error('Network request failed');
      mockLogin.mockRejectedValueOnce(networkError);

      const { getByPlaceholderText, getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const usernameInput = getByPlaceholderText('Enter your username');
      const passwordInput = getByPlaceholderText('Enter your password');
      const signInButton = getByText('Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(passwordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(signInButton);
      });

      expect(mockAlert).toHaveBeenCalledWith('Login Error', 'Login failed. Please try again.');
    });
  });

  describe('Accessibility and UX', () => {
    it('should maintain consistent component structure', () => {
      const { getByText } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      // Verify main structural elements
      expect(getByText('Chores Tracker')).toBeTruthy(); // Title
      expect(getByText('Sign in to your account')).toBeTruthy(); // Subtitle
      expect(getByText('Sign In')).toBeTruthy(); // Primary action
      expect(getByText("Don't have an account? Sign Up")).toBeTruthy(); // Secondary action
    });

    it('should handle prop changes correctly', () => {
      const { rerender } = render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={mockOnNavigateToRegister} />
        </TestWrapper>
      );

      const newNavigateHandler = jest.fn();
      
      rerender(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={newNavigateHandler} />
        </TestWrapper>
      );

      // Component should still render correctly with new props
      expect(render(
        <TestWrapper>
          <LoginScreen onNavigateToRegister={newNavigateHandler} />
        </TestWrapper>
      ).getByText('Chores Tracker')).toBeTruthy();
    });
  });
});