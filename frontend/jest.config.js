module.exports = {
  preset: 'jest-expo',
  
  // Transform patterns for React Native and Expo modules
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg)'
  ],
  
  // Setup files
  setupFilesAfterEnv: [
    '@testing-library/jest-native/extend-expect',
    '<rootDir>/src/test-utils/setup.ts'
  ],
  
  // Module mapping
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  
  // Test environment
  testEnvironment: 'jsdom',
  
  // Coverage configuration
  collectCoverage: false, // Enable with --coverage flag
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/test-utils/**',
    '!src/**/__tests__/**',
    '!src/**/*.test.{ts,tsx}',
    '!src/index.ts',
  ],
  
  // Coverage thresholds (set to current levels to prevent CI failures)
  // TODO: Gradually increase these as we improve test coverage
  coverageThreshold: {
    global: {
      statements: 25,
      branches: 25,
      functions: 25,
      lines: 25,
    },
    // Well-tested API modules should maintain high coverage
    'src/api/balance.ts': {
      statements: 95,
      branches: 95,
      functions: 95,
      lines: 95,
    },
    'src/api/chores.ts': {
      statements: 95,
      branches: 95,
      functions: 95,
      lines: 95,
    },
    // Components should maintain high coverage
    'src/components/**/*.tsx': {
      statements: 85,
      branches: 80,
      functions: 85,
      lines: 85,
    },
    // Contexts should maintain high coverage
    'src/contexts/**/*.tsx': {
      statements: 95,
      branches: 85,
      functions: 95,
      lines: 95,
    },
  },
  
  // Coverage reporters
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json',
  ],
  
  // Coverage directory
  coverageDirectory: '<rootDir>/coverage',
  
  // Test file patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}',
  ],
  
  // Module file extensions
  moduleFileExtensions: [
    'ts',
    'tsx',
    'js',
    'jsx',
    'json',
  ],
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: false,
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Restore mocks after each test
  restoreMocks: true,
};
