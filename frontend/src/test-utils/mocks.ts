/**
 * Mock implementations for testing
 * Centralized location for all mock functions and objects used across tests
 */

import { AuthContextType } from '@/contexts/AuthContext';
import { AxiosInstance } from 'axios';

// API Client Mock
export const mockApiClient: Partial<AxiosInstance> = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  patch: jest.fn(),
  request: jest.fn(),
  interceptors: {
    request: {
      use: jest.fn(),
      eject: jest.fn(),
    },
    response: {
      use: jest.fn(),
      eject: jest.fn(),
    },
  } as any,
};

// Auth Context Mock
export const mockAuthContext: AuthContextType = {
  isAuthenticated: false,
  isLoading: false,
  user: null,
  login: jest.fn(),
  logout: jest.fn(),
  checkAuthStatus: jest.fn(),
};

// Authenticated Auth Context Mock (for testing authenticated flows)
export const mockAuthenticatedContext: AuthContextType = {
  isAuthenticated: true,
  isLoading: false,
  user: {
    id: 1,
    username: 'testparent',
    role: 'parent',
    email: 'parent@test.com',
    full_name: 'Test Parent',
  },
  login: jest.fn(),
  logout: jest.fn(),
  checkAuthStatus: jest.fn(),
};

// Child User Auth Context Mock
export const mockChildAuthContext: AuthContextType = {
  isAuthenticated: true,
  isLoading: false,
  user: {
    id: 2,
    username: 'testchild',
    role: 'child',
    full_name: 'Test Child',
  },
  login: jest.fn(),
  logout: jest.fn(),
  checkAuthStatus: jest.fn(),
};

// AsyncStorage Mock
export const mockAsyncStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(),
  multiGet: jest.fn(),
  multiSet: jest.fn(),
  multiRemove: jest.fn(),
};

// Navigation Mock
export const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  dispatch: jest.fn(),
  setOptions: jest.fn(),
  isFocused: jest.fn(() => true),
  canGoBack: jest.fn(() => false),
  getId: jest.fn(),
  getParent: jest.fn(),
  getState: jest.fn(),
  push: jest.fn(),
  pop: jest.fn(),
  popToTop: jest.fn(),
  replace: jest.fn(),
  reset: jest.fn(),
  setParams: jest.fn(),
  addListener: jest.fn(),
  removeListener: jest.fn(),
};

// Route Mock
export const mockRoute = {
  key: 'test-route',
  name: 'TestScreen',
  params: {},
  path: undefined,
};

// Alert Mock
export const mockAlert = {
  alert: jest.fn(),
};

// API Response Mocks
export const mockApiResponses = {
  // Auth responses
  loginSuccess: {
    data: {
      access_token: 'mock-jwt-token',
      token_type: 'bearer',
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        full_name: 'Test User',
        is_parent: true,
      },
    },
  },
  
  loginError: {
    response: {
      status: 401,
      data: {
        detail: 'Invalid credentials',
      },
    },
  },

  // User responses
  currentUser: {
    data: {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      full_name: 'Test User',
      is_parent: true,
    },
  },

  // Chores responses
  choresSuccess: {
    data: [
      {
        id: 1,
        title: 'Test Chore',
        description: 'Test description',
        reward: 5.00,
        is_range_reward: false,
        is_recurring: false,
        is_disabled: false,
        created_at: '2024-01-01T00:00:00Z',
      },
    ],
  },

  // Balance responses
  balanceSuccess: {
    data: {
      current_balance: 25.50,
      pending_earnings: 10.00,
      total_earned: 100.00,
    },
  },

  // Activities responses
  activitiesSuccess: {
    data: [
      {
        id: 1,
        type: 'chore_completed',
        description: 'Completed: Test Chore',
        amount: 5.00,
        created_at: '2024-01-01T00:00:00Z',
      },
    ],
  },

  // Network error
  networkError: new Error('Network Error'),
};

// Reset all mocks helper
export const resetAllMocks = () => {
  jest.clearAllMocks();
  
  // Reset API client mocks
  Object.values(mockApiClient).forEach(mock => {
    if (jest.isMockFunction(mock)) {
      mock.mockReset();
    }
  });
  
  // Reset auth context mocks
  Object.values(mockAuthContext).forEach(mock => {
    if (jest.isMockFunction(mock)) {
      mock.mockReset();
    }
  });
  
  // Reset AsyncStorage mocks
  Object.values(mockAsyncStorage).forEach(mock => {
    if (jest.isMockFunction(mock)) {
      mock.mockReset();
    }
  });
  
  // Reset navigation mocks
  Object.values(mockNavigation).forEach(mock => {
    if (jest.isMockFunction(mock)) {
      mock.mockReset();
    }
  });
};

// Common mock implementations
export const mockImplementations = {
  // AsyncStorage successful operations
  asyncStorageSuccess: {
    getItem: jest.fn().mockResolvedValue(null),
    setItem: jest.fn().mockResolvedValue(undefined),
    removeItem: jest.fn().mockResolvedValue(undefined),
  },
  
  // API client successful responses
  apiClientSuccess: {
    get: jest.fn().mockResolvedValue(mockApiResponses.choresSuccess),
    post: jest.fn().mockResolvedValue(mockApiResponses.choresSuccess),
    put: jest.fn().mockResolvedValue(mockApiResponses.choresSuccess),
    delete: jest.fn().mockResolvedValue({ data: {} }),
  },
  
  // API client error responses
  apiClientError: {
    get: jest.fn().mockRejectedValue(mockApiResponses.networkError),
    post: jest.fn().mockRejectedValue(mockApiResponses.networkError),
    put: jest.fn().mockRejectedValue(mockApiResponses.networkError),
    delete: jest.fn().mockRejectedValue(mockApiResponses.networkError),
  },
};