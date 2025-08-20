/**
 * Global test setup configuration
 * This file is loaded before all tests run to configure the testing environment
 */

import '@testing-library/jest-native/extend-expect';

// Mock react-native modules that don't work well in Jest (conditional for Expo)
try {
  jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');
} catch (e) {
  // Expo environment doesn't need this mock
}

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(),
  multiGet: jest.fn(),
  multiSet: jest.fn(),
  multiRemove: jest.fn(),
}));

// Mock axios globally for API client tests
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
    interceptors: {
      request: {
        use: jest.fn(),
        eject: jest.fn(),
      },
      response: {
        use: jest.fn(),
        eject: jest.fn(),
      },
    },
    defaults: {},
  };

  return {
    create: jest.fn(() => mockAxiosInstance),
    post: jest.fn(),
    get: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
    interceptors: {
      request: {
        use: jest.fn(),
        eject: jest.fn(),
      },
      response: {
        use: jest.fn(),
        eject: jest.fn(),
      },
    },
  };
});

// Mock Expo modules
jest.mock('expo-status-bar', () => ({
  StatusBar: 'StatusBar',
}));

// Mock React Navigation
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
    dispatch: jest.fn(),
  }),
  useRoute: () => ({
    params: {},
  }),
  useFocusEffect: jest.fn(),
}));

// Mock Alert for React Native (simplified for Expo)
global.alert = jest.fn();

// Global test timeout
jest.setTimeout(10000);

// Suppress console warnings during tests
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

beforeAll(() => {
  console.warn = (...args: any[]) => {
    // Suppress specific warnings that are expected in test environment
    const warningMessage = args[0];
    if (
      typeof warningMessage === 'string' &&
      (warningMessage.includes('Warning: ReactDOM.render is no longer supported') ||
       warningMessage.includes('Warning: componentWillReceiveProps has been renamed'))
    ) {
      return;
    }
    originalConsoleWarn(...args);
  };

  console.error = (...args: any[]) => {
    // Suppress specific errors that are expected in test environment
    const errorMessage = args[0];
    if (
      typeof errorMessage === 'string' &&
      (errorMessage.includes('Warning: React.createElement: type is invalid') ||
       errorMessage.includes('The above error occurred in the'))
    ) {
      return;
    }
    originalConsoleError(...args);
  };
});

afterAll(() => {
  console.warn = originalConsoleWarn;
  console.error = originalConsoleError;
});

// Clear all mocks between tests
afterEach(() => {
  jest.clearAllMocks();
});