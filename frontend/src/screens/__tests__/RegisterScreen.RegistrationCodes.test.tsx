/**
 * Registration Code Tests for RegisterScreen
 * Tests the new beta registration code functionality
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

describe('RegisterScreen Registration Code Tests', () => {
  const mockOnBackToLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockAlert.mockClear();
    mockedAxios.post.mockClear();
  });

  const fillValidFormWithoutCode = (getByPlaceholderText: any) => {
    const usernameInput = getByPlaceholderText('Choose a username');
    const emailInput = getByPlaceholderText('Enter your email');
    const passwordInput = getByPlaceholderText('Min 8 characters');
    const confirmPasswordInput = getByPlaceholderText('Re-enter your password');
    
    fireEvent.changeText(usernameInput, 'testuser');
    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.changeText(confirmPasswordInput, 'password123');
  };

  const fillValidFormWithCode = (getByPlaceholderText: any, code: string = 'BETA2024') => {
    fillValidFormWithoutCode(getByPlaceholderText);
    const registrationCodeInput = getByPlaceholderText('Enter your beta code');
    fireEvent.changeText(registrationCodeInput, code);
  };

  describe('Registration Code Field', () => {
    it('should render registration code field with correct attributes', () => {
      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      // Check field exists
      const registrationCodeInput = getByPlaceholderText('Enter your beta code');
      expect(registrationCodeInput).toBeTruthy();

      // Check label
      expect(getByText('Registration Code *')).toBeTruthy();

      // Check helper text
      expect(getByText('Contact admin for a valid beta registration code')).toBeTruthy();

      // Check input properties
      expect(registrationCodeInput.props.autoCapitalize).toBe('characters');
      expect(registrationCodeInput.props.autoCorrect).toBe(false);
    });

    it('should update registration code input value', () => {
      const { getByPlaceholderText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      const registrationCodeInput = getByPlaceholderText('Enter your beta code');
      
      fireEvent.changeText(registrationCodeInput, 'BETA2024');
      expect(registrationCodeInput.props.value).toBe('BETA2024');
    });
  });

  describe('Form Validation with Registration Code', () => {
    it('should show error when registration code is missing', async () => {
      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      fillValidFormWithoutCode(getByPlaceholderText);
      // Don't fill registration code

      const createAccountButton = getByText('Create Account');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Error',
        'Please fill in all required fields including the registration code'
      );
    });

    it('should proceed with API call when registration code is provided', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { message: 'Success' } });

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      fillValidFormWithCode(getByPlaceholderText, 'BETA2024');

      const createAccountButton = getByText('Create Account');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      // Verify axios was called with registration code
      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.stringContaining('registration_code=BETA2024'),
        expect.any(Object)
      );
    });

    it('should trim whitespace from registration code', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { message: 'Success' } });

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      fillValidFormWithCode(getByPlaceholderText, '  BETA2024  '); // With spaces

      const createAccountButton = getByText('Create Account');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      // Verify axios was called with trimmed registration code
      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.stringContaining('registration_code=BETA2024'), // No spaces
        expect.any(Object)
      );
    });
  });

  describe('Registration Code Error Handling', () => {
    it('should handle invalid registration code error', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Invalid registration code. Please contact admin for a valid beta code.'
          }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(errorResponse);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      fillValidFormWithCode(getByPlaceholderText, 'INVALID_CODE');

      const createAccountButton = getByText('Create Account');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Registration Error',
        'Invalid registration code. Please contact admin for a valid beta code.'
      );
    });

    it('should handle registration code required error', async () => {
      const errorResponse = {
        response: {
          data: {
            detail: 'Registration code is required during beta period'
          }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(errorResponse);

      const { getByPlaceholderText, getByText } = render(
        <RegisterScreen onBackToLogin={mockOnBackToLogin} />
      );

      fillValidFormWithCode(getByPlaceholderText, ''); // Empty code

      const createAccountButton = getByText('Create Account');
      
      await act(async () => {
        fireEvent.press(createAccountButton);
      });

      expect(mockAlert).toHaveBeenCalledWith(
        'Registration Error',
        'Registration code is required during beta period'
      );
    });
  });

  describe('Registration Code Case Handling', () => {
    it('should work with different case variations', async () => {
      mockedAxios.post.mockResolvedValue({ data: { message: 'Success' } });

      const testCodes = ['beta2024', 'Beta2024', 'BETA2024', 'bEtA2024'];

      for (const testCode of testCodes) {
        const { getByPlaceholderText, getByText } = render(
          <RegisterScreen onBackToLogin={mockOnBackToLogin} />
        );

        fillValidFormWithCode(getByPlaceholderText, testCode);

        const createAccountButton = getByText('Create Account');
        
        await act(async () => {
          fireEvent.press(createAccountButton);
        });

        // Should proceed to API call regardless of case
        expect(mockedAxios.post).toHaveBeenCalledWith(
          expect.any(String),
          expect.stringContaining(`registration_code=${testCode}`),
          expect.any(Object)
        );

        mockedAxios.post.mockClear();
      }
    });
  });
});