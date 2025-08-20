/**
 * Integration Test Wrapper
 * Provides AuthProvider context for integration tests that need to render SimpleNavigator
 */

import React from 'react';
import { User } from '../types/User';

interface IntegrationTestWrapperProps {
  children: React.ReactNode;
  authState?: {
    isAuthenticated: boolean;
    isLoading: boolean;
    user: User | null;
    login: jest.MockedFunction<any>;
    logout: jest.MockedFunction<any>;
    checkAuthStatus: jest.MockedFunction<any>;
  };
}

// Default mock auth state
const defaultAuthState = {
  isAuthenticated: false,
  isLoading: false,
  user: null,
  login: jest.fn(),
  logout: jest.fn(),
  checkAuthStatus: jest.fn(),
};

// Simple wrapper that just renders children
// The actual mocking happens at the module level
export const IntegrationTestWrapper: React.FC<IntegrationTestWrapperProps> = ({ children }) => {
  return <>{children}</>;
};

// Helper function to render with integration test context
export const renderWithIntegrationContext = (
  ui: React.ReactElement,
  authState?: IntegrationTestWrapperProps['authState']
) => {
  const { render } = require('@testing-library/react-native');
  
  // Apply the auth state to the global mock before rendering
  const finalAuthState = { ...defaultAuthState, ...authState };
  
  // Get the mock function and apply the auth state
  const { mockUseAuth } = require('../__tests__/integration/authFlow.test.tsx');
  if (mockUseAuth) {
    mockUseAuth.mockReturnValue(finalAuthState);
  }
  
  return render(
    <IntegrationTestWrapper>
      {ui}
    </IntegrationTestWrapper>
  );
};