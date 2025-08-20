/**
 * FinancialSummaryCards Component Tests
 * Tests the financial summary display component for family allowance tracking
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { FinancialSummaryCards } from '../FinancialSummaryCards';
import { reportsAPI, AllowanceSummaryResponse } from '../../api/reports';

// Mock the reports API
jest.mock('../../api/reports', () => ({
  reportsAPI: {
    getAllowanceSummary: jest.fn(),
  },
  formatCurrency: jest.fn((amount: number) => `$${amount.toFixed(2)}`),
}));

const mockedReportsAPI = reportsAPI as jest.Mocked<typeof reportsAPI>;

// Mock financial data factory
const createMockFinancialData = (overrides: Partial<AllowanceSummaryResponse> = {}): AllowanceSummaryResponse => ({
  family_summary: {
    total_children: 3,
    total_earned: 150.00,
    total_adjustments: 25.00,
    total_balance_due: 175.00,
    total_completed_chores: 42,
    period_start: '2024-01-01',
    period_end: '2024-01-31',
  },
  child_summaries: [
    {
      id: 1,
      username: 'alice',
      completed_chores: 15,
      total_earned: 75.00,
      total_adjustments: 10.00,
      paid_out: 0.00,
      balance_due: 85.00,
      pending_chores_value: 15.00,
      last_activity_date: '2024-01-30T10:00:00Z',
    },
    {
      id: 2,
      username: 'bob',
      completed_chores: 12,
      total_earned: 60.00,
      total_adjustments: 5.00,
      paid_out: 0.00,
      balance_due: 65.00,
      pending_chores_value: 10.00,
      last_activity_date: '2024-01-29T14:00:00Z',
    },
    {
      id: 3,
      username: 'charlie',
      completed_chores: 15,
      total_earned: 15.00,
      total_adjustments: 10.00,
      paid_out: 0.00,
      balance_due: 25.00,
      pending_chores_value: 5.00,
      last_activity_date: '2024-01-28T16:00:00Z',
    },
  ],
  ...overrides,
});

describe('FinancialSummaryCards Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedReportsAPI.getAllowanceSummary.mockResolvedValue(createMockFinancialData());
  });

  describe('Basic Rendering and Loading', () => {
    it('should show loading state initially', () => {
      const { getByText } = render(<FinancialSummaryCards />);

      expect(getByText('Loading financial summary...')).toBeTruthy();
    });

    it('should render family financial summary after loading', async () => {
      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('Family Financial Summary')).toBeTruthy();
        expect(getByText('$175.00')).toBeTruthy(); // Total balance due
        expect(getByText('Total Balance Due')).toBeTruthy();
      });
    });

    it('should display title correctly', async () => {
      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('Family Financial Summary')).toBeTruthy();
      });
    });

    it('should call API on mount', async () => {
      render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(mockedReportsAPI.getAllowanceSummary).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Financial Data Display', () => {
    it('should display primary financial metrics correctly', async () => {
      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('$175.00')).toBeTruthy(); // Total balance due
        expect(getByText('Total Balance Due')).toBeTruthy();
        expect(getByText('3 of 3 children have balances')).toBeTruthy();
      });
    });

    it('should display secondary financial metrics', async () => {
      const { getByText, getAllByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('$150.00')).toBeTruthy(); // Total earned
        expect(getByText('Total Earned')).toBeTruthy();
        const adjustmentAmounts = getAllByText('$25.00');
        expect(adjustmentAmounts.length).toBeGreaterThan(0); // May appear multiple times (adjustments + child balance)
        expect(getByText('Adjustments')).toBeTruthy();
      });
    });

    it('should display pending approval amount when present', async () => {
      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('$30.00')).toBeTruthy(); // Pending total (15+10+5)
        expect(getByText('Pending Approval')).toBeTruthy();
      });
    });

    it('should hide pending approval when no pending value', async () => {
      const dataWithNoPending = createMockFinancialData({
        child_summaries: [
          {
            id: 1,
            username: 'alice',
            completed_chores: 15,
            total_earned: 75.00,
            total_adjustments: 10.00,
            paid_out: 0.00,
            balance_due: 85.00,
            pending_chores_value: 0, // No pending value
          },
        ],
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(dataWithNoPending);

      const { queryByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(queryByText('Pending Approval')).toBeNull();
      });
    });

    it('should display quick stats correctly', async () => {
      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('42')).toBeTruthy(); // Total completed chores
        expect(getByText('Chores Completed')).toBeTruthy();
        expect(getByText('3')).toBeTruthy(); // Total children
        expect(getByText('Children')).toBeTruthy();
      });
    });
  });

  describe('Children with Balances Display', () => {
    it('should display children with balances', async () => {
      const { getByText, getAllByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('Balances Due:')).toBeTruthy();
        expect(getByText('alice')).toBeTruthy();
        expect(getByText('$85.00')).toBeTruthy();
        expect(getByText('bob')).toBeTruthy();
        expect(getByText('$65.00')).toBeTruthy();
        expect(getByText('charlie')).toBeTruthy();
        const amounts25 = getAllByText('$25.00');
        expect(amounts25.length).toBeGreaterThan(0); // Charlie's balance (and possibly adjustments)
      });
    });

    it('should hide children balances section when no children have balances', async () => {
      const dataWithNoBalances = createMockFinancialData({
        family_summary: {
          total_children: 2,
          total_earned: 100.00,
          total_adjustments: 0,
          total_balance_due: 0,
          total_completed_chores: 20,
        },
        child_summaries: [
          {
            id: 1,
            username: 'alice',
            completed_chores: 10,
            total_earned: 50.00,
            total_adjustments: 0,
            paid_out: 50.00,
            balance_due: 0, // No balance
            pending_chores_value: 0,
          },
          {
            id: 2,
            username: 'bob',
            completed_chores: 10,
            total_earned: 50.00,
            total_adjustments: 0,
            paid_out: 50.00,
            balance_due: 0, // No balance
            pending_chores_value: 0,
          },
        ],
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(dataWithNoBalances);

      const { queryByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(queryByText('Balances Due:')).toBeNull();
      });
    });

    it('should display correct children count text', async () => {
      const dataWithPartialBalances = createMockFinancialData({
        family_summary: {
          total_children: 3,
          total_earned: 150.00,
          total_adjustments: 25.00,
          total_balance_due: 90.00,
          total_completed_chores: 42,
        },
        child_summaries: [
          {
            id: 1,
            username: 'alice',
            completed_chores: 15,
            total_earned: 75.00,
            total_adjustments: 10.00,
            paid_out: 0.00,
            balance_due: 85.00, // Has balance
            pending_chores_value: 15.00,
          },
          {
            id: 2,
            username: 'bob',
            completed_chores: 12,
            total_earned: 60.00,
            total_adjustments: 5.00,
            paid_out: 60.00,
            balance_due: 5.00, // Has small balance
            pending_chores_value: 10.00,
          },
          {
            id: 3,
            username: 'charlie',
            completed_chores: 15,
            total_earned: 15.00,
            total_adjustments: 10.00,
            paid_out: 25.00,
            balance_due: 0, // No balance
            pending_chores_value: 5.00,
          },
        ],
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(dataWithPartialBalances);

      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('2 of 3 children have balances')).toBeTruthy();
      });
    });
  });

  describe('View Reports Button', () => {
    it('should display View Reports button when onViewReports provided', async () => {
      const mockOnViewReports = jest.fn();

      const { getByText } = render(
        <FinancialSummaryCards onViewReports={mockOnViewReports} />
      );

      await waitFor(() => {
        expect(getByText('View Full Report')).toBeTruthy();
      });
    });

    it('should not display View Reports button when onViewReports not provided', async () => {
      const { queryByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(queryByText('View Full Report')).toBeNull();
      });
    });

    it('should call onViewReports when button is pressed', async () => {
      const mockOnViewReports = jest.fn();

      const { getByText } = render(
        <FinancialSummaryCards onViewReports={mockOnViewReports} />
      );

      await waitFor(() => {
        expect(getByText('View Full Report')).toBeTruthy();
      });

      fireEvent.press(getByText('View Full Report'));
      expect(mockOnViewReports).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error Handling', () => {
    it('should display error state when API fails', async () => {
      mockedReportsAPI.getAllowanceSummary.mockRejectedValueOnce(new Error('Network error'));

      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('Unable to load financial summary')).toBeTruthy();
        expect(getByText('Retry')).toBeTruthy();
      });
    });

    it('should retry when retry button is pressed', async () => {
      mockedReportsAPI.getAllowanceSummary
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(createMockFinancialData());

      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('Retry')).toBeTruthy();
      });

      fireEvent.press(getByText('Retry'));

      await waitFor(() => {
        expect(getByText('Family Financial Summary')).toBeTruthy();
      });

      expect(mockedReportsAPI.getAllowanceSummary).toHaveBeenCalledTimes(2);
    });

    it('should handle API returning null data', async () => {
      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(null as any);

      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('Unable to load financial summary')).toBeTruthy();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refetch data when refreshKey changes', async () => {
      const { rerender } = render(<FinancialSummaryCards refreshKey={1} />);

      await waitFor(() => {
        expect(mockedReportsAPI.getAllowanceSummary).toHaveBeenCalledTimes(1);
      });

      rerender(<FinancialSummaryCards refreshKey={2} />);

      await waitFor(() => {
        expect(mockedReportsAPI.getAllowanceSummary).toHaveBeenCalledTimes(2);
      });
    });

    it('should handle rapid refresh key changes', async () => {
      const { rerender } = render(<FinancialSummaryCards refreshKey={1} />);

      rerender(<FinancialSummaryCards refreshKey={2} />);
      rerender(<FinancialSummaryCards refreshKey={3} />);
      rerender(<FinancialSummaryCards refreshKey={4} />);

      await waitFor(() => {
        expect(mockedReportsAPI.getAllowanceSummary).toHaveBeenCalled();
      });
    });
  });

  describe('Amount Calculations', () => {
    it('should calculate pending chores total correctly', async () => {
      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        // 15.00 + 10.00 + 5.00 = 30.00
        expect(getByText('$30.00')).toBeTruthy();
        expect(getByText('Pending Approval')).toBeTruthy();
      });
    });

    it('should handle zero pending amounts correctly', async () => {
      const dataWithZeroPending = createMockFinancialData({
        child_summaries: [
          {
            id: 1,
            username: 'alice',
            completed_chores: 15,
            total_earned: 75.00,
            total_adjustments: 10.00,
            paid_out: 0.00,
            balance_due: 85.00,
            pending_chores_value: 0,
          },
        ],
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(dataWithZeroPending);

      const { queryByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(queryByText('Pending Approval')).toBeNull();
      });
    });

    it('should filter children with balances correctly', async () => {
      const mixedBalanceData = createMockFinancialData({
        child_summaries: [
          {
            id: 1,
            username: 'alice',
            completed_chores: 15,
            total_earned: 75.00,
            total_adjustments: 10.00,
            paid_out: 0.00,
            balance_due: 85.00, // Has balance
            pending_chores_value: 15.00,
          },
          {
            id: 2,
            username: 'bob',
            completed_chores: 12,
            total_earned: 60.00,
            total_adjustments: 5.00,
            paid_out: 65.00,
            balance_due: 0, // No balance
            pending_chores_value: 10.00,
          },
        ],
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(mixedBalanceData);

      const { getByText, queryByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('alice')).toBeTruthy();
        expect(getByText('$85.00')).toBeTruthy();
        expect(queryByText('bob')).toBeNull(); // Bob has no balance
      });
    });
  });

  describe('Edge Cases and Data Validation', () => {
    it('should handle empty child summaries', async () => {
      const emptyData = createMockFinancialData({
        family_summary: {
          total_children: 0,
          total_earned: 0,
          total_adjustments: 0,
          total_balance_due: 0,
          total_completed_chores: 0,
        },
        child_summaries: [],
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(emptyData);

      const { getByText, queryByText, getAllByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        const zeroAmounts = getAllByText('$0.00');
        expect(zeroAmounts.length).toBeGreaterThan(0); // Multiple $0.00 amounts expected
        expect(getByText('0 of 0 children have balances')).toBeTruthy();
        expect(queryByText('Balances Due:')).toBeNull();
      });
    });

    it('should handle negative adjustments correctly', async () => {
      const negativeAdjustmentData = createMockFinancialData({
        family_summary: {
          total_children: 1,
          total_earned: 100.00,
          total_adjustments: -25.00, // Negative adjustment
          total_balance_due: 75.00,
          total_completed_chores: 20,
        },
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(negativeAdjustmentData);

      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('$-25.00')).toBeTruthy(); // Should show negative
        expect(getByText('Adjustments')).toBeTruthy();
      });
    });

    it('should handle large numbers correctly', async () => {
      const largeNumberData = createMockFinancialData({
        family_summary: {
          total_children: 10,
          total_earned: 9999.99,
          total_adjustments: 1234.56,
          total_balance_due: 11234.55,
          total_completed_chores: 999,
        },
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(largeNumberData);

      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('$11234.55')).toBeTruthy();
        expect(getByText('999')).toBeTruthy();
        expect(getByText('10')).toBeTruthy();
      });
    });

    it('should handle undefined optional fields gracefully', async () => {
      const dataWithUndefinedFields = createMockFinancialData({
        family_summary: {
          total_children: 1,
          total_earned: 100.00,
          total_adjustments: 0,
          total_balance_due: 100.00,
          total_completed_chores: 10,
          period_start: undefined,
          period_end: undefined,
        },
      });

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(dataWithUndefinedFields);

      const { getByText, getAllByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        expect(getByText('Family Financial Summary')).toBeTruthy();
        const hundredAmounts = getAllByText('$100.00');
        expect(hundredAmounts.length).toBeGreaterThan(0); // Both earned and balance_due are $100.00
      });
    });

    it('should handle malformed financial data gracefully', async () => {
      const malformedData = {
        family_summary: {
          total_children: 'invalid', // Wrong type
          total_earned: null, // Null value
          total_adjustments: undefined, // Undefined value
          total_balance_due: 100.00,
          total_completed_chores: 10,
        },
        child_summaries: [
          {
            id: 1,
            username: 'alice',
            balance_due: 'not_a_number', // Invalid balance
            pending_chores_value: null,
          },
        ],
      } as any;

      mockedReportsAPI.getAllowanceSummary.mockResolvedValueOnce(malformedData);

      const { getByText } = render(<FinancialSummaryCards />);

      await waitFor(() => {
        // Should not crash and attempt to render
        expect(getByText('Family Financial Summary')).toBeTruthy();
      });
    });
  });
});