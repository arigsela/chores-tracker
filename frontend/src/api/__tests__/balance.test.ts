/**
 * Balance API Module Tests (Simplified Working Version)
 * Tests core balance-related API operations
 */

import axios from 'axios';
import { balanceAPI } from '../balance';
import { 
  resetAllMocks, 
  createMockUserBalance,
  createMockApiResponse, 
  createMockApiError 
} from '../../test-utils';

// Get the mocked axios and client instance
const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockApiClient = (mockedAxios.create as jest.Mock).mock.results[0]?.value;

describe('Balance API Module (Core Tests)', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
    // Ensure mock client is reset properly
    if (mockApiClient) {
      mockApiClient.get.mockReset();
      mockApiClient.post.mockReset();
      mockApiClient.put.mockReset();
      mockApiClient.delete.mockReset();
    }
  });

  describe('getMyBalance', () => {
    it('should fetch current user balance successfully', async () => {
      const mockBalance = createMockUserBalance({
        balance: 35.75,
        total_earned: 30.00,
        adjustments: 5.75,
        paid_out: 0.00,
        pending_chores_value: 12.50,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(mockApiClient.get).toHaveBeenCalledWith('/users/me/balance');
      expect(result).toEqual(mockBalance);
      expect(result.balance).toBe(35.75);
      expect(result.total_earned).toBe(30.00);
      expect(result.adjustments).toBe(5.75);
      expect(result.paid_out).toBe(0.00);
      expect(result.pending_chores_value).toBe(12.50);
    });

    it('should handle zero balance correctly', async () => {
      const mockBalance = createMockUserBalance({
        balance: 0.00,
        total_earned: 0.00,
        adjustments: 0.00,
        paid_out: 0.00,
        pending_chores_value: 0.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.balance).toBe(0.00);
      expect(result.total_earned).toBe(0.00);
      expect(result.adjustments).toBe(0.00);
      expect(result.paid_out).toBe(0.00);
      expect(result.pending_chores_value).toBe(0.00);
    });

    it('should handle negative adjustments correctly', async () => {
      const mockBalance = createMockUserBalance({
        balance: 15.00,
        total_earned: 25.00,
        adjustments: -10.00,
        paid_out: 0.00,
        pending_chores_value: 5.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.adjustments).toBe(-10.00);
      expect(result.balance).toBe(15.00);
    });

    it('should handle balance with paid out amounts', async () => {
      const mockBalance = createMockUserBalance({
        balance: 10.00,
        total_earned: 50.00,
        adjustments: 5.00,
        paid_out: 45.00,
        pending_chores_value: 8.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.paid_out).toBe(45.00);
      expect(result.balance).toBe(10.00);
      expect(result.total_earned).toBe(50.00);
    });

    it('should handle pending chores value correctly', async () => {
      const mockBalance = createMockUserBalance({
        balance: 20.00,
        total_earned: 20.00,
        adjustments: 0.00,
        paid_out: 0.00,
        pending_chores_value: 25.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.pending_chores_value).toBe(25.00);
      expect(result.balance).toBe(20.00);
    });

    it('should handle large decimal amounts accurately', async () => {
      const mockBalance = createMockUserBalance({
        balance: 123.456,
        total_earned: 100.123,
        adjustments: 23.333,
        paid_out: 0.00,
        pending_chores_value: 45.678,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.balance).toBe(123.456);
      expect(result.total_earned).toBe(100.123);
      expect(result.adjustments).toBe(23.333);
      expect(result.pending_chores_value).toBe(45.678);
    });

    it('should handle very small decimal amounts', async () => {
      const mockBalance = createMockUserBalance({
        balance: 0.01,
        total_earned: 0.01,
        adjustments: 0.00,
        paid_out: 0.00,
        pending_chores_value: 0.05,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.balance).toBe(0.01);
      expect(result.total_earned).toBe(0.01);
      expect(result.pending_chores_value).toBe(0.05);
    });

    it('should handle realistic family allowance scenario', async () => {
      const mockBalance = createMockUserBalance({
        balance: 27.50,
        total_earned: 45.00,
        adjustments: 2.50,
        paid_out: 20.00,
        pending_chores_value: 15.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      // Verify balance calculation makes sense
      // total_earned + adjustments - paid_out = balance
      const expectedBalance = result.total_earned + result.adjustments - result.paid_out;
      expect(result.balance).toBe(expectedBalance);
      expect(result.pending_chores_value).toBeGreaterThan(0);
    });

    it('should handle malformed balance response', async () => {
      const malformedResponse = { data: null };
      mockApiClient.get.mockResolvedValue(malformedResponse);

      const result = await balanceAPI.getMyBalance();
      expect(result).toBeNull();
    });

    it('should handle incomplete balance data', async () => {
      const incompleteBalance = {
        balance: 10.00,
        // Missing other required fields
      };
      mockApiClient.get.mockResolvedValue(createMockApiResponse(incompleteBalance));

      const result = await balanceAPI.getMyBalance();
      expect(result.balance).toBe(10.00);
      expect(result).toEqual(incompleteBalance);
    });

    it('should handle balance with invalid data types', async () => {
      const invalidBalance = {
        balance: '25.00', // Should be number
        total_earned: 'invalid',
        adjustments: null,
        paid_out: undefined,
        pending_chores_value: false,
      };
      mockApiClient.get.mockResolvedValue(createMockApiResponse(invalidBalance));

      const result = await balanceAPI.getMyBalance();
      expect(result).toEqual(invalidBalance);
    });

    it('should handle network connectivity issues', async () => {
      const networkError = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(networkError);

      await expect(balanceAPI.getMyBalance()).rejects.toThrow('Network Error');
    });
  });

  describe('Data Validation', () => {
    it('should handle all numeric types correctly', async () => {
      const mockBalance = createMockUserBalance({
        balance: 123,
        total_earned: 100.5,
        adjustments: -10.25,
        paid_out: 0,
        pending_chores_value: 33.75,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(typeof result.balance).toBe('number');
      expect(typeof result.total_earned).toBe('number');
      expect(typeof result.adjustments).toBe('number');
      expect(typeof result.paid_out).toBe('number');
      expect(typeof result.pending_chores_value).toBe('number');
    });

    it('should preserve exact decimal precision from API', async () => {
      const mockBalance = createMockUserBalance({
        balance: 12.34,
        total_earned: 56.78,
        adjustments: 9.01,
        paid_out: 53.45,
        pending_chores_value: 2.22,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.balance).toBe(12.34);
      expect(result.total_earned).toBe(56.78);
      expect(result.adjustments).toBe(9.01);
      expect(result.paid_out).toBe(53.45);
      expect(result.pending_chores_value).toBe(2.22);
    });

    it('should handle negative balance scenarios', async () => {
      const mockBalance = createMockUserBalance({
        balance: -5.00,
        total_earned: 20.00,
        adjustments: -15.00,
        paid_out: 10.00,
        pending_chores_value: 8.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.balance).toBe(-5.00);
      expect(result.adjustments).toBe(-15.00);
    });

    it('should handle edge case with zero pending chores', async () => {
      const mockBalance = createMockUserBalance({
        balance: 50.00,
        total_earned: 50.00,
        adjustments: 0.00,
        paid_out: 0.00,
        pending_chores_value: 0.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      expect(result.pending_chores_value).toBe(0.00);
      expect(result.balance).toBe(50.00);
    });

    it('should validate balance calculation logic with complex scenario', async () => {
      const mockBalance = createMockUserBalance({
        balance: 17.25,
        total_earned: 75.50,
        adjustments: -8.25,
        paid_out: 50.00,
        pending_chores_value: 30.00,
      });

      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      const result = await balanceAPI.getMyBalance();

      // Verify the balance makes mathematical sense
      const calculatedBalance = result.total_earned + result.adjustments - result.paid_out;
      expect(result.balance).toBe(calculatedBalance);
      expect(result.pending_chores_value).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Performance and Caching', () => {
    it('should make a fresh API call on each request', async () => {
      const mockBalance = createMockUserBalance();
      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      // Make multiple calls
      await balanceAPI.getMyBalance();
      await balanceAPI.getMyBalance();
      await balanceAPI.getMyBalance();

      // Verify each call made a new request
      expect(mockApiClient.get).toHaveBeenCalledTimes(3);
      expect(mockApiClient.get).toHaveBeenCalledWith('/users/me/balance');
    });

    it('should handle concurrent balance requests', async () => {
      const mockBalance = createMockUserBalance();
      mockApiClient.get.mockResolvedValue(createMockApiResponse(mockBalance));

      // Make concurrent calls
      const promises = [
        balanceAPI.getMyBalance(),
        balanceAPI.getMyBalance(),
        balanceAPI.getMyBalance(),
      ];

      const results = await Promise.all(promises);

      expect(results).toHaveLength(3);
      expect(results.every(result => result.balance === mockBalance.balance)).toBe(true);
      expect(mockApiClient.get).toHaveBeenCalledTimes(3);
    });
  });
});