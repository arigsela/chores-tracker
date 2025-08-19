/**
 * Test utilities index
 * Central export point for all testing utilities
 */

// Setup (automatically imported by Jest)
export * from './setup';

// Mocks
export * from './mocks';

// Data factories
export * from './factories';

// Custom render functions
export * from './renderWithProviders';

// Additional test utilities
export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const waitForNextTick = () => new Promise(resolve => setImmediate(resolve));

// Common test helpers
export const expectToBeCalledWith = (mockFn: jest.MockedFunction<any>, ...args: any[]) => {
  expect(mockFn).toHaveBeenCalledWith(...args);
};

export const expectToBeCalledTimes = (mockFn: jest.MockedFunction<any>, times: number) => {
  expect(mockFn).toHaveBeenCalledTimes(times);
};

// Async test helpers
export const waitForAsync = async (fn: () => void | Promise<void>, timeout = 1000) => {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      await fn();
      return;
    } catch (error) {
      await sleep(10);
    }
  }
  throw new Error('Async condition not met within timeout');
};

// Component test helpers
export const findByTestId = (container: any, testId: string) => {
  return container.getByTestId(testId);
};

export const queryByTestId = (container: any, testId: string) => {
  return container.queryByTestId(testId);
};

// Form test helpers
export const fillForm = async (getByTestId: any, formData: Record<string, string>) => {
  for (const [testId, value] of Object.entries(formData)) {
    const input = getByTestId(testId);
    // Simulate user typing
    input.props.onChangeText(value);
  }
};

// API test helpers
export const createMockApiCall = <T>(data: T, delay = 0) => {
  return jest.fn().mockImplementation(() => 
    new Promise(resolve => 
      setTimeout(() => resolve({ data }), delay)
    )
  );
};

export const createMockApiError = (error: any, delay = 0) => {
  return jest.fn().mockImplementation(() => 
    new Promise((_, reject) => 
      setTimeout(() => reject(error), delay)
    )
  );
};