/**
 * Test data factories
 * Provides consistent, realistic test data for components and integration tests
 */

import { Chore } from '@/api/chores';
import { User, ChildWithChores, ChildAllowanceSummary } from '@/api/users';
import { UserBalance } from '@/api/balance';

// User factory
export interface MockUser {
  id: number;
  username: string;
  role: 'parent' | 'child';
  email?: string;
  full_name?: string;
}

export const createMockUser = (overrides: Partial<MockUser> = {}): MockUser => ({
  id: 1,
  username: 'testuser',
  role: 'parent',
  email: 'test@example.com',
  full_name: 'Test User',
  ...overrides,
});

export const createMockParent = (overrides: Partial<MockUser> = {}): MockUser =>
  createMockUser({
    id: 1,
    username: 'testparent',
    role: 'parent',
    email: 'parent@test.com',
    full_name: 'Test Parent',
    ...overrides,
  });

export const createMockChild = (overrides: Partial<MockUser> = {}): MockUser =>
  createMockUser({
    id: 2,
    username: 'testchild',
    role: 'child',
    full_name: 'Test Child',
    ...overrides,
  });

// Users API specific factories
export const createMockApiUser = (overrides: Partial<User> = {}): User => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  is_active: true,
  is_parent: true,
  parent_id: null,
  ...overrides,
});

export const createMockApiParent = (overrides: Partial<User> = {}): User =>
  createMockApiUser({
    id: 1,
    username: 'testparent',
    email: 'parent@test.com',
    is_parent: true,
    parent_id: null,
    ...overrides,
  });

export const createMockApiChild = (overrides: Partial<User> = {}): User =>
  createMockApiUser({
    id: 2,
    username: 'testchild',
    email: null,
    is_parent: false,
    parent_id: 1,
    ...overrides,
  });

export const createMockChildWithChores = (overrides: Partial<ChildWithChores> = {}): ChildWithChores => ({
  ...createMockApiChild(),
  chores: [
    createMockChore({ id: 1, title: 'Child Chore 1', assigned_to_id: 2 }),
    createMockChore({ id: 2, title: 'Child Chore 2', assigned_to_id: 2 }),
  ],
  ...overrides,
});

export const createMockChildAllowanceSummary = (overrides: Partial<ChildAllowanceSummary> = {}): ChildAllowanceSummary => ({
  id: 2,
  username: 'testchild',
  completed_chores: 5,
  total_earned: 25.00,
  total_adjustments: 2.50,
  paid_out: 0.00,
  balance_due: 27.50,
  ...overrides,
});

export const createMockUserBalance = (overrides: Partial<UserBalance> = {}): UserBalance => ({
  balance: 27.50,
  total_earned: 25.00,
  adjustments: 2.50,
  paid_out: 0.00,
  pending_chores_value: 15.00,
  ...overrides,
});

// Chore factory
export const createMockChore = (overrides: Partial<Chore> = {}): Chore => ({
  id: 1,
  title: 'Test Chore',
  description: 'Test chore description',
  reward: 5.00,
  is_range_reward: false,
  min_reward: null,
  max_reward: null,
  cooldown_days: null,
  assigned_to_id: 2,
  assignee_id: 2,
  assigned_to_username: 'testchild',
  completed_at: null,
  completion_date: null,
  approved_at: null,
  approval_reward: null,
  rejection_reason: null,
  created_at: '2024-01-01T00:00:00Z',
  created_by_id: 1,
  creator_id: 1,
  is_active: true,
  is_completed: false,
  is_approved: false,
  is_disabled: false,
  is_recurring: false,
  next_available_at: null,
  ...overrides,
});

// Chore state variations
export const createCompletedChore = (overrides: Partial<Chore> = {}): Chore =>
  createMockChore({
    is_completed: true,
    completed_at: '2024-01-01T12:00:00Z',
    completion_date: '2024-01-01T12:00:00Z',
    ...overrides,
  });

export const createApprovedChore = (overrides: Partial<Chore> = {}): Chore =>
  createMockChore({
    is_completed: true,
    is_approved: true,
    completed_at: '2024-01-01T12:00:00Z',
    approved_at: '2024-01-01T13:00:00Z',
    approval_reward: 5.00,
    ...overrides,
  });

export const createDisabledChore = (overrides: Partial<Chore> = {}): Chore =>
  createMockChore({
    is_disabled: true,
    ...overrides,
  });

export const createRangeRewardChore = (overrides: Partial<Chore> = {}): Chore =>
  createMockChore({
    is_range_reward: true,
    reward: null,
    min_reward: 3.00,
    max_reward: 10.00,
    ...overrides,
  });

export const createRecurringChore = (overrides: Partial<Chore> = {}): Chore =>
  createMockChore({
    is_recurring: true,
    cooldown_days: 7,
    next_available_at: '2024-01-08T00:00:00Z',
    ...overrides,
  });

// Activity factory
export interface MockActivity {
  id: number;
  type: string;
  description: string;
  amount?: number;
  created_at: string;
  user_id?: number;
  chore_id?: number;
}

export const createMockActivity = (overrides: Partial<MockActivity> = {}): MockActivity => ({
  id: 1,
  type: 'chore_completed',
  description: 'Completed: Test Chore',
  amount: 5.00,
  created_at: '2024-01-01T12:00:00Z',
  user_id: 2,
  chore_id: 1,
  ...overrides,
});

// Activity type variations
export const createChoreCompletedActivity = (overrides: Partial<MockActivity> = {}): MockActivity =>
  createMockActivity({
    type: 'chore_completed',
    description: 'Completed: Test Chore',
    amount: 5.00,
    ...overrides,
  });

export const createChoreApprovedActivity = (overrides: Partial<MockActivity> = {}): MockActivity =>
  createMockActivity({
    type: 'chore_approved',
    description: 'Approved: Test Chore',
    amount: 5.00,
    ...overrides,
  });

export const createBalanceAdjustmentActivity = (overrides: Partial<MockActivity> = {}): MockActivity =>
  createMockActivity({
    type: 'balance_adjustment',
    description: 'Balance adjustment: Bonus for good behavior',
    amount: 10.00,
    chore_id: undefined,
    ...overrides,
  });

// Balance factory
export interface MockBalance {
  current_balance: number;
  pending_earnings: number;
  total_earned: number;
  total_spent?: number;
}

export const createMockBalance = (overrides: Partial<MockBalance> = {}): MockBalance => ({
  current_balance: 25.50,
  pending_earnings: 10.00,
  total_earned: 100.00,
  total_spent: 75.00,
  ...overrides,
});

// Adjustment factory
export interface MockAdjustment {
  id: number;
  amount: number;
  reason: string;
  created_at: string;
  created_by_id: number;
  user_id: number;
}

export const createMockAdjustment = (overrides: Partial<MockAdjustment> = {}): MockAdjustment => ({
  id: 1,
  amount: 10.00,
  reason: 'Bonus for good behavior',
  created_at: '2024-01-01T12:00:00Z',
  created_by_id: 1,
  user_id: 2,
  ...overrides,
});

// API Response factories
export const createMockApiResponse = <T>(data: T, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {} as any,
});

export const createMockApiError = (message = 'API Error', status = 500) => {
  const error = new Error(message);
  (error as any).response = {
    data: {
      detail: message,
    },
    status,
    statusText: status === 401 ? 'Unauthorized' : 'Internal Server Error',
  };
  (error as any).isAxiosError = true;
  return error;
};

// Login response factory
export const createMockLoginResponse = (user: MockUser = createMockParent()) => 
  createMockApiResponse({
    access_token: 'mock-jwt-token-12345',
    token_type: 'bearer',
    user: {
      ...user,
      is_parent: user.role === 'parent',
    },
  });

// Arrays of test data
export const createMockChoreList = (count = 3): Chore[] =>
  Array.from({ length: count }, (_, index) =>
    createMockChore({
      id: index + 1,
      title: `Test Chore ${index + 1}`,
      reward: (index + 1) * 2.5,
    })
  );

export const createMockActivityList = (count = 5): MockActivity[] =>
  Array.from({ length: count }, (_, index) =>
    createMockActivity({
      id: index + 1,
      description: `Activity ${index + 1}`,
      amount: (index + 1) * 2.0,
      created_at: new Date(Date.now() - index * 24 * 60 * 60 * 1000).toISOString(),
    })
  );

export const createMockChildrenList = (count = 2): MockUser[] =>
  Array.from({ length: count }, (_, index) =>
    createMockChild({
      id: index + 2,
      username: `child${index + 1}`,
      full_name: `Test Child ${index + 1}`,
    })
  );

// Users API list generators
export const createMockChildWithChoresList = (count = 2): ChildWithChores[] =>
  Array.from({ length: count }, (_, index) =>
    createMockChildWithChores({
      id: index + 2,
      username: `child${index + 1}`,
      chores: [
        createMockChore({
          id: index * 2 + 1,
          title: `Chore ${index * 2 + 1} for Child ${index + 1}`,
          assigned_to_id: index + 2,
        }),
        createMockChore({
          id: index * 2 + 2,
          title: `Chore ${index * 2 + 2} for Child ${index + 1}`,
          assigned_to_id: index + 2,
        }),
      ],
    })
  );

export const createMockAllowanceSummaryList = (count = 2): ChildAllowanceSummary[] =>
  Array.from({ length: count }, (_, index) =>
    createMockChildAllowanceSummary({
      id: index + 2,
      username: `child${index + 1}`,
      completed_chores: (index + 1) * 3,
      total_earned: (index + 1) * 15.00,
      total_adjustments: (index + 1) * 2.50,
      balance_due: (index + 1) * 17.50,
    })
  );

// Date utilities for consistent test dates
export const testDates = {
  now: '2024-01-01T12:00:00Z',
  yesterday: '2023-12-31T12:00:00Z',
  tomorrow: '2024-01-02T12:00:00Z',
  lastWeek: '2023-12-25T12:00:00Z',
  nextWeek: '2024-01-08T12:00:00Z',
};

// Mock date function for consistent testing
export const mockDate = (dateString: string = testDates.now) => {
  const mockDateObj = new Date(dateString);
  const originalDate = Date;
  
  // @ts-ignore
  global.Date = class extends Date {
    constructor(date?: string | number | Date) {
      if (date) {
        super(date);
      } else {
        super(mockDateObj);
      }
    }
    
    static now() {
      return mockDateObj.getTime();
    }
  } as any;
  
  return () => {
    global.Date = originalDate;
  };
};