/**
 * RegisterScreen Component Tests
 * Tests the user registration screen including form validation, API integration, and navigation
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import axios from 'axios';
import { RegisterScreen } from '../RegisterScreen';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

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

describe('RegisterScreen Component', () => {
  const mockOnBackToLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockAlert.mockClear();
    mockedAxios.post.mockClear();
  });

  describe('Basic Rendering', () => {
    it('should render registration form with all required elements', () => {
      const { getByText, getByPlaceholderText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      expect(getByText('Create Account')).toBeTruthy();
      expect(getByText('Sign up to get started')).toBeTruthy();
      expect(getByText('Username *')).toBeTruthy();
      expect(getByText('Email *')).toBeTruthy();
      expect(getByText('Password *')).toBeTruthy();
      expect(getByText('Confirm Password *')).toBeTruthy();
      expect(getByPlaceholderText('Choose a username')).toBeTruthy();
      expect(getByPlaceholderText('Enter your email')).toBeTruthy();
      expect(getByPlaceholderText('Min 8 characters')).toBeTruthy();
      expect(getByPlaceholderText('Re-enter your password')).toBeTruthy();
      expect(getByText('Create Account')).toBeTruthy();
      expect(getByText('Already have an account? Sign In')).toBeTruthy();
    });

    it('should render form inputs with correct properties', () => {
      const { getByPlaceholderText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');

      expect(usernameInput.props.autoCapitalize).toBe('none');
      expect(usernameInput.props.autoCorrect).toBe(false);
      expect(emailInput.props.keyboardType).toBe('email-address');
      expect(emailInput.props.autoCapitalize).toBe('none');
      expect(passwordInput.props.secureTextEntry).toBe(true);
      expect(confirmPasswordInput.props.secureTextEntry).toBe(true);
    });

    it('should have all form fields marked as required', () => {
      const { getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      expect(getByText('Username *')).toBeTruthy();
      expect(getByText('Email *')).toBeTruthy();
      expect(getByText('Password *')).toBeTruthy();
      expect(getByText('Confirm Password *')).toBeTruthy();
    });
  });

  describe('Form Input Handling', () => {
    it('should update username input value', () => {
      const { getByPlaceholderText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      
      fireEvent.changeText(usernameInput, 'testuser');
      expect(usernameInput.props.value).toBe('testuser');
    });

    it('should update email input value', () => {
      const { getByPlaceholderText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const emailInput = getByPlaceholderText('Enter your email');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      expect(emailInput.props.value).toBe('test@example.com');
    });

    it('should update password input value', () => {
      const { getByPlaceholderText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const passwordInput = getByPlaceholderText('Min 8 characters');
      
      fireEvent.changeText(passwordInput, 'password123');
      expect(passwordInput.props.value).toBe('password123');
    });

    it('should update confirm password input value', () => {
      const { getByPlaceholderText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      
      fireEvent.changeText(confirmPasswordInput, 'password123');
      expect(confirmPasswordInput.props.value).toBe('password123');
    });
  });

  describe('Form Validation', () => {
    it('should show error for empty required fields', async () => {
      const { getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const createAccountButton = getByText('Create Account');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please fill in all required fields'
      );
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    it('should show error for missing username', async () => {
      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please fill in all required fields'
      );
    });

    it('should show error for mismatched passwords', async () => {
      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'differentpassword');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Passwords do not match'
      );
    });

    it('should show error for password too short', async () => {
      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'short');
      fireEvent.changeText(confirmPasswordInput, 'short');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Password must be at least 8 characters long'
      );
    });

    it('should show error for invalid email format', async () => {
      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'invalid-email');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please enter a valid email address'
      );
    });

    it('should validate email format correctly with various invalid formats', async () => {
      const invalidEmails = ['test', 'test@', '@example.com', 'test@example', 'test..test@example.com'];
      
      for (const invalidEmail of invalidEmails) {
        const { getByPlaceholderText, getByText } = render(
          <RegisterScreen onBackToLogin={mockOnBackToLogin} />
        );

        const usernameInput = getByPlaceholderText('Choose a username');
        const emailInput = getByPlaceholderText('Enter your email');
        const passwordInput = getByPlaceholderText('Min 8 characters');
        const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
        const createAccountButton = getByText('Create Account');
        
        fireEvent.changeText(usernameInput, 'testuser');
        fireEvent.changeText(emailInput, invalidEmail);
        fireEvent.changeText(passwordInput, 'password123');
        fireEvent.changeText(confirmPasswordInput, 'password123');
        
        await act(async () => {
          fireEvent.press(createAccountButton);
        });

        expect(mockAlert).toHaveBeenCalledWith(
          'Error',
          'Please enter a valid email address'
        );
        
        mockAlert.mockClear();
      }
    });

    it('should accept valid email formats', async () => {
      const validEmails = ['test@example.com', 'user.name@domain.co.uk', 'test+tag@gmail.com'];
      
      mockedAxios.post.mockResolvedValue({ data: { message: 'Success' } });
      
      for (const validEmail of validEmails) {
        const { getByPlaceholderText, getByText } = render(
          <RegisterScreen onBackToLogin={mockOnBackToLogin} />
        );

        const usernameInput = getByPlaceholderText('Choose a username');
        const emailInput = getByPlaceholderText('Enter your email');
        const passwordInput = getByPlaceholderText('Min 8 characters');
        const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
        const createAccountButton = getByText('Create Account');
        
        fireEvent.changeText(usernameInput, 'testuser');
        fireEvent.changeText(emailInput, validEmail);
        fireEvent.changeText(passwordInput, 'password123');
        fireEvent.changeText(confirmPasswordInput, 'password123');
        
        await act(async () => {
          fireEvent.press(createAccountButton);
        });

        // Should not show email validation error
        expect(mockAlert).not.toHaveBeenCalledWith(
          'Error',
          'Please enter a valid email address'
        );
        
        mockAlert.mockClear();
        mockedAxios.post.mockClear();
      }
    });
  });

  describe('Registration Flow', () => {
    it('should call API with correct data on successful validation', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { message: 'Success' } });

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/users/register',
        'username=testuser&password=password123&email=test%40example.com&is_parent=true',
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
    });

    it('should show success alert and navigate to login on successful registration', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { message: 'Success' } });

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Success',
        'Your account has been created successfully! Please sign in.',
        [
          {
            text: 'OK',
            onPress: mockOnBackToLogin,
          },
        ]
      );
    });

    it('should handle registration error with specific message', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Username already exists'
          }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(errorResponse);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'existinguser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith('Registration Error', 'Username already exists');
    });

    it('should handle registration error with array of validation errors', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: [
              { msg: 'Email already registered' }
            ]
          }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(errorResponse);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'existing@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith('Registration Error', 'Email already registered');
    });

    it('should handle generic registration error', async () => {
      const networkError = new Error('Network error');
      mockedAxios.post.mockRejectedValueOnce(networkError);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith('Registration Error', 'Registration failed. Please try again.');
    });
  });

  describe('Loading State Management', () => {
    it('should show loading indicator during registration', async () => {
      let resolveRegistration: () => void;
      const registrationPromise = new Promise<void>((resolve) => {
        resolveRegistration = resolve;
      });
      mockedAxios.post.mockReturnValueOnce(registrationPromise as any);

      const { getByPlaceholderText, getByText, queryByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      // Should show loading state
      expect(queryByText('Create Account')).toBeNull();
      expect(usernameInput.props.editable).toBe(false);
      expect(emailInput.props.editable).toBe(false);
      expect(passwordInput.props.editable).toBe(false);
      expect(confirmPasswordInput.props.editable).toBe(false);

      // Complete the registration
      await act(async () => {
        resolveRegistration!();
      });
    });

    it('should disable all inputs during loading', async () => {
      let resolveRegistration: () => void;
      const registrationPromise = new Promise<void>((resolve) => {
        resolveRegistration = resolve;
      });
      mockedAxios.post.mockReturnValueOnce(registrationPromise as any);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      const loginLink = getByText('Already have an account? Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      // All inputs should be disabled
      expect(usernameInput.props.editable).toBe(false);
      expect(emailInput.props.editable).toBe(false);
      expect(passwordInput.props.editable).toBe(false);
      expect(confirmPasswordInput.props.editable).toBe(false);
      expect(createAccountButton.props.disabled).toBe(true);
      expect(loginLink.props.disabled).toBe(true);

      // Complete the registration
      await act(async () => {
        resolveRegistration!();
      });
    });

    it('should re-enable form after failed registration', async () => {
      const registrationError = new Error('Registration failed');
      mockedAxios.post.mockRejectedValueOnce(registrationError);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      // Wait for error handling
      await waitFor(() => {
        expect(usernameInput.props.editable).toBe(true);
        expect(emailInput.props.editable).toBe(true);
        expect(passwordInput.props.editable).toBe(true);
        expect(confirmPasswordInput.props.editable).toBe(true);
        expect(createAccountButton.props.disabled).toBe(false);
      });
    });
  });

  describe('Navigation Handling', () => {
    it('should call onBackToLogin when login link is pressed', () => {
      const { getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const loginLink = getByText('Already have an account? Sign In');
      
      fireEvent.press(loginLink);
      
      expect(mockOnBackToLogin).toHaveBeenCalledTimes(1);
    });

    it('should not allow navigation during loading', async () => {
      let resolveRegistration: () => void;
      const registrationPromise = new Promise<void>((resolve) => {
        resolveRegistration = resolve;
      });
      mockedAxios.post.mockReturnValueOnce(registrationPromise as any);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      const loginLink = getByText('Already have an account? Sign In');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, 'password123');
      fireEvent.changeText(confirmPasswordInput, 'password123');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      // Try to navigate during loading
      fireEvent.press(loginLink);
      
      expect(mockOnBackToLogin).not.toHaveBeenCalled();
      expect(loginLink.props.disabled).toBe(true);

      // Complete the registration
      await act(async () => {
        resolveRegistration!();
      });
    });
  });

  describe('Edge Cases and Form Validation', () => {
    it('should handle whitespace-only inputs', async () => {
      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, '   ');
      fireEvent.changeText(emailInput, '   ');
      fireEvent.changeText(passwordInput, '   ');
      fireEvent.changeText(confirmPasswordInput, '   ');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please fill in all required fields'
      );
    });

    it('should handle very long inputs', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { message: 'Success' } });

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      const longUsername = 'a'.repeat(100);
      const longEmail = 'a'.repeat(50) + '@example.com';
      const longPassword = 'b'.repeat(100);
      
      fireEvent.changeText(usernameInput, longUsername);
      fireEvent.changeText(emailInput, longEmail);
      fireEvent.changeText(passwordInput, longPassword);
      fireEvent.changeText(confirmPasswordInput, longPassword);
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockedAxios.post).toHaveBeenCalled();
    });

    it('should handle exact 8 character password', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { message: 'Success' } });

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const usernameInput = getByPlaceholderText('Choose a username');
      const emailInput = getByPlaceholderText('Enter your email');
      const passwordInput = getByPlaceholderText('Min 8 characters');
      const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
      const createAccountButton = getByText('Create Account');
      
      fireEvent.changeText(usernameInput, 'testuser');
      fireEvent.changeText(emailInput, 'test@example.com');
      fireEvent.changeText(passwordInput, '12345678');
      fireEvent.changeText(confirmPasswordInput, '12345678');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockedAxios.post).toHaveBeenCalled();
      expect(mockAlert).not.toHaveBeenCalledWith(
        'Error',
        'Password must be at least 8 characters long'
      );
    });
  });

  describe('Accessibility and UX', () => {
    it('should maintain consistent component structure', () => {
      const { getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      // Verify main structural elements
      expect(getByText('Create Account')).toBeTruthy(); // Title
      expect(getByText('Sign up to get started')).toBeTruthy(); // Subtitle
      expect(getByText('Create Account')).toBeTruthy(); // Primary action
      expect(getByText('Already have an account? Sign In')).toBeTruthy(); // Secondary action
    });

    it('should handle prop changes correctly', () => {
      const { rerender } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const newBackHandler = jest.fn();
      
      rerender(
        <RegisterScreen onBackToLogin={newBackHandler} />
      );

      // Component should still render correctly with new props
      expect(render(
        <RegisterScreen onBackToLogin={newBackHandler} />
      ).getByText('Create Account')).toBeTruthy();
    });
  });
});