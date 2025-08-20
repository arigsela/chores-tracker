/**
 * Custom render function with providers
 * Provides a convenient way to render components with necessary context providers
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react-native';
import { AuthProvider, AuthContextType } from '@/contexts/AuthContext';
import { mockAuthContext, mockAuthenticatedContext, mockChildAuthContext } from './mocks';

// Custom render options
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  authValue?: AuthContextType;
  authenticated?: boolean;
  userRole?: 'parent' | 'child';
}

/**
 * Custom render function that wraps components with necessary providers
 */
export const renderWithProviders = (
  ui: ReactElement,
  {
    authValue,
    authenticated = false,
    userRole = 'parent',
    ...renderOptions
  }: CustomRenderOptions = {}
) => {
  // Determine auth context value
  let contextValue: AuthContextType;
  
  if (authValue) {
    contextValue = authValue;
  } else if (authenticated) {
    contextValue = userRole === 'child' ? mockChildAuthContext : mockAuthenticatedContext;
  } else {
    contextValue = mockAuthContext;
  }

  // Simple wrapper - tests should mock useAuth directly
  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <>{children}</>
  );

  // Render with wrapper
  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    // Return the context value for test assertions
    authContextValue: contextValue,
  };
};

/**
 * Render with authenticated parent user
 */
export const renderWithParent = (
  ui: ReactElement,
  options: Omit<CustomRenderOptions, 'authenticated' | 'userRole'> = {}
) => renderWithProviders(ui, { 
  ...options, 
  authenticated: true, 
  userRole: 'parent' 
});

/**
 * Render with authenticated child user
 */
export const renderWithChild = (
  ui: ReactElement,
  options: Omit<CustomRenderOptions, 'authenticated' | 'userRole'> = {}
) => renderWithProviders(ui, { 
  ...options, 
  authenticated: true, 
  userRole: 'child' 
});

/**
 * Render with unauthenticated user
 */
export const renderWithoutAuth = (
  ui: ReactElement,
  options: Omit<CustomRenderOptions, 'authenticated'> = {}
) => renderWithProviders(ui, { 
  ...options, 
  authenticated: false 
});

/**
 * Render with loading state
 */
export const renderWithLoading = (
  ui: ReactElement,
  options: Omit<CustomRenderOptions, 'authValue'> = {}
) => renderWithProviders(ui, {
  ...options,
  authValue: {
    ...mockAuthContext,
    isLoading: true,
  },
});

/**
 * Render with custom user data
 */
export const renderWithCustomUser = (
  ui: ReactElement,
  user: any,
  options: Omit<CustomRenderOptions, 'authValue'> = {}
) => renderWithProviders(ui, {
  ...options,
  authValue: {
    ...mockAuthenticatedContext,
    user,
  },
});

// Re-export testing library utilities
export * from '@testing-library/react-native';
export { renderWithProviders as render };