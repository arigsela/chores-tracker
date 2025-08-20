/**
 * ChoreCard Component Tests
 * Tests the primary reusable component for displaying chore information
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { ChoreCard } from '../ChoreCard';
import {
  createMockChore,
  createCompletedChore,
  createApprovedChore,
  createDisabledChore,
  createRangeRewardChore,
  createRecurringChore,
  mockDate,
  testDates,
} from '../../test-utils';

describe('ChoreCard Component', () => {
  let restoreDate: () => void;

  beforeEach(() => {
    restoreDate = mockDate(testDates.now);
  });

  afterEach(() => {
    restoreDate();
  });

  describe('Basic Rendering', () => {
    it('should render chore title and basic information', () => {
      const chore = createMockChore({
        title: 'Clean the Kitchen',
        description: 'Wash dishes and wipe counters',
        reward: 5.00,
      });

      const { getByText, getByTestId } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByTestId('chore-card')).toBeTruthy();
      expect(getByText('Clean the Kitchen')).toBeTruthy();
      expect(getByText('Wash dishes and wipe counters')).toBeTruthy();
      expect(getByText('$5.00')).toBeTruthy();
    });

    it('should render without description when description is null', () => {
      const chore = createMockChore({
        title: 'Simple Chore',
        description: null,
      });

      const { getByText, queryByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('Simple Chore')).toBeTruthy();
      expect(queryByText('Wash dishes and wipe counters')).toBeNull();
    });

    it('should handle missing reward gracefully', () => {
      const chore = createMockChore({
        reward: null,
        is_range_reward: false,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('No reward')).toBeTruthy();
    });
  });

  describe('Status Display Logic', () => {
    it('should show "Disabled" status for disabled chores', () => {
      const chore = createDisabledChore();

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('🚫 Disabled')).toBeTruthy();
    });

    it('should show "Approved" status for approved chores', () => {
      const chore = createApprovedChore();

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('✅ Approved')).toBeTruthy();
    });

    it('should show "Pending Approval" for completed but not approved chores', () => {
      const chore = createCompletedChore({
        is_approved: false,
        approved_at: null,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('⏳ Pending Approval')).toBeTruthy();
    });

    it('should show "Ready to Complete" for available chores', () => {
      const chore = createMockChore({
        is_completed: false,
        completed_at: null,
        completion_date: null,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('📋 Ready to Complete')).toBeTruthy();
    });

    it('should show future availability date for scheduled recurring chores', () => {
      const futureDate = '2024-01-05T00:00:00Z';
      const chore = createRecurringChore({
        next_available_at: futureDate,
        is_completed: false,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText(/🔒 Available/)).toBeTruthy();
    });

    it('should show "Ready to Complete" when chore is available now', () => {
      const pastDate = '2023-12-30T00:00:00Z';
      const chore = createRecurringChore({
        next_available_at: pastDate,
        is_completed: false,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('📋 Ready to Complete')).toBeTruthy();
    });
  });

  describe('Reward Display Logic', () => {
    it('should display fixed reward amount', () => {
      const chore = createMockChore({
        reward: 7.50,
        is_range_reward: false,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('$7.50')).toBeTruthy();
    });

    it('should display range for unapproved range rewards', () => {
      const chore = createRangeRewardChore({
        min_reward: 5.00,
        max_reward: 15.00,
        is_approved: false,
        approved_at: null,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('$5.00 - $15.00')).toBeTruthy();
    });

    it('should display final approved amount for approved range rewards', () => {
      const chore = createRangeRewardChore({
        is_approved: true,
        approved_at: '2024-01-01T13:00:00Z',
        reward: 8.00, // Final approved amount
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('$8.00')).toBeTruthy();
    });

    it('should display approval_reward when available', () => {
      const chore = createApprovedChore({
        approval_reward: 12.50,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('$12.50')).toBeTruthy();
    });
  });

  describe('Recurring Chore Display', () => {
    it('should show recurring information for recurring chores', () => {
      const chore = createRecurringChore({
        cooldown_days: 3,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('🔄 Repeats every 3 days')).toBeTruthy();
    });

    it('should handle singular day correctly', () => {
      const chore = createRecurringChore({
        cooldown_days: 1,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('🔄 Repeats every 1 day')).toBeTruthy();
    });

    it('should not show recurring info for non-recurring chores', () => {
      const chore = createMockChore({
        is_recurring: false,
      });

      const { queryByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(queryByText(/🔄 Repeats/)).toBeNull();
    });
  });

  describe('Complete Button Functionality', () => {
    it('should show complete button when showCompleteButton is true and chore is available', () => {
      const chore = createMockChore({
        is_completed: false,
        completed_at: null,
      });

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          onComplete={jest.fn()}
        />
      );

      expect(getByTestId('complete-chore-button')).toBeTruthy();
    });

    it('should not show complete button when chore is completed', () => {
      const chore = createCompletedChore();

      const { queryByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          onComplete={jest.fn()}
        />
      );

      expect(queryByTestId('complete-chore-button')).toBeNull();
    });

    it('should not show complete button when chore is not available yet', () => {
      const futureDate = '2024-01-05T00:00:00Z';
      const chore = createRecurringChore({
        next_available_at: futureDate,
        is_completed: false,
      });

      const { queryByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          onComplete={jest.fn()}
        />
      );

      expect(queryByTestId('complete-chore-button')).toBeNull();
    });

    it('should call onComplete when complete button is pressed', async () => {
      const mockOnComplete = jest.fn().mockResolvedValue(undefined);
      const chore = createMockChore({
        id: 42,
        is_completed: false,
      });

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          onComplete={mockOnComplete}
        />
      );

      await act(async () => {
        fireEvent.press(getByTestId('complete-chore-button'));
      });

      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalledWith(42);
      });
    });

    it('should handle async complete operation', async () => {
      const mockOnComplete = jest.fn().mockResolvedValue(undefined);
      const chore = createMockChore();

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          onComplete={mockOnComplete}
        />
      );

      const button = getByTestId('complete-chore-button');
      
      await act(async () => {
        fireEvent.press(button);
      });

      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalled();
      });
    });

    it('should not show complete button when showCompleteButton is false', () => {
      const chore = createMockChore();

      const { queryByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={false}
          onComplete={jest.fn()}
        />
      );

      expect(queryByTestId('complete-chore-button')).toBeNull();
    });
  });

  describe('Manage Buttons Functionality', () => {
    it('should show enable button for disabled chores', () => {
      const chore = createDisabledChore();

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showManageButtons={true}
          onEnable={jest.fn()}
        />
      );

      expect(getByTestId('enable-chore-button')).toBeTruthy();
    });

    it('should show disable button for enabled chores', () => {
      const chore = createMockChore({
        is_disabled: false,
      });

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showManageButtons={true}
          onDisable={jest.fn()}
        />
      );

      expect(getByTestId('disable-chore-button')).toBeTruthy();
    });

    it('should call onEnable when enable button is pressed', async () => {
      const mockOnEnable = jest.fn().mockResolvedValue(undefined);
      const chore = createDisabledChore({ id: 24 });

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showManageButtons={true}
          onEnable={mockOnEnable}
        />
      );

      await act(async () => {
        fireEvent.press(getByTestId('enable-chore-button'));
      });

      await waitFor(() => {
        expect(mockOnEnable).toHaveBeenCalledWith(24);
      });
    });

    it('should call onDisable when disable button is pressed', async () => {
      const mockOnDisable = jest.fn().mockResolvedValue(undefined);
      const chore = createMockChore({ id: 36, is_disabled: false });

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showManageButtons={true}
          onDisable={mockOnDisable}
        />
      );

      await act(async () => {
        fireEvent.press(getByTestId('disable-chore-button'));
      });

      await waitFor(() => {
        expect(mockOnDisable).toHaveBeenCalledWith(36);
      });
    });

    it('should handle async manage operations', async () => {
      const mockOnEnable = jest.fn().mockResolvedValue(undefined);
      const chore = createDisabledChore();

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showManageButtons={true}
          onEnable={mockOnEnable}
        />
      );

      const button = getByTestId('enable-chore-button');
      
      await act(async () => {
        fireEvent.press(button);
      });

      await waitFor(() => {
        expect(mockOnEnable).toHaveBeenCalled();
      });
    });

    it('should not show manage buttons when showManageButtons is false', () => {
      const chore = createDisabledChore();

      const { queryByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showManageButtons={false}
        />
      );

      expect(queryByTestId('enable-chore-button')).toBeNull();
      expect(queryByTestId('disable-chore-button')).toBeNull();
    });
  });

  describe('Props Validation and Defaults', () => {
    it('should handle all props being undefined/false', () => {
      const chore = createMockChore();

      const { getByTestId, queryByTestId } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByTestId('chore-card')).toBeTruthy();
      expect(queryByTestId('complete-chore-button')).toBeNull();
      expect(queryByTestId('enable-chore-button')).toBeNull();
      expect(queryByTestId('disable-chore-button')).toBeNull();
    });

    it('should handle isChild prop correctly', () => {
      const chore = createMockChore();

      const { getByTestId } = render(
        <ChoreCard chore={chore} isChild={true} />
      );

      // isChild prop doesn't affect rendering directly in current implementation
      // but is available for future child-specific features
      expect(getByTestId('chore-card')).toBeTruthy();
    });

    it('should use default prop values correctly', () => {
      const chore = createMockChore();

      const { queryByTestId } = render(
        <ChoreCard chore={chore} />
      );

      // Default showCompleteButton = false
      expect(queryByTestId('complete-chore-button')).toBeNull();
      
      // Default showManageButtons = false  
      expect(queryByTestId('enable-chore-button')).toBeNull();
      expect(queryByTestId('disable-chore-button')).toBeNull();
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle chore with multiple completion indicators', () => {
      const chore = createMockChore({
        is_completed: true,
        completed_at: '2024-01-01T12:00:00Z',
        completion_date: '2024-01-01T11:00:00Z',
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('⏳ Pending Approval')).toBeTruthy();
    });

    it('should handle chore with multiple approval indicators', () => {
      const chore = createMockChore({
        is_completed: true,
        is_approved: true,
        approved_at: '2024-01-01T13:00:00Z',
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('✅ Approved')).toBeTruthy();
    });

    it('should handle missing callback functions gracefully', () => {
      const chore = createMockChore();

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          // onComplete not provided
        />
      );

      // Button should not render if callback is not provided
      expect(() => getByTestId('complete-chore-button')).toThrow();
    });

    it('should handle range reward with missing min/max values', () => {
      const chore = createMockChore({
        is_range_reward: true,
        min_reward: null,
        max_reward: null,
        reward: 10.00,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('$10.00')).toBeTruthy();
    });

    it('should handle zero cooldown days', () => {
      const chore = createRecurringChore({
        cooldown_days: 0,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText('🔄 Repeats every 0 days')).toBeTruthy();
    });

    it('should handle future next_available_at correctly', () => {
      const futureDate = '2024-01-10T00:00:00Z';
      const chore = createMockChore({
        next_available_at: futureDate,
        is_completed: false,
      });

      const { getByText } = render(
        <ChoreCard chore={chore} />
      );

      expect(getByText(/🔒 Available/)).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('should have proper testID attributes for testing', () => {
      const chore = createMockChore();

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          showManageButtons={true}
          onComplete={jest.fn()}
          onEnable={jest.fn()}
          onDisable={jest.fn()}
        />
      );

      expect(getByTestId('chore-card')).toBeTruthy();
      expect(getByTestId('complete-chore-button')).toBeTruthy();
      
      // Note: Enable/disable buttons depend on chore state
      if (chore.is_disabled) {
        expect(getByTestId('enable-chore-button')).toBeTruthy();
      } else {
        expect(getByTestId('disable-chore-button')).toBeTruthy();
      }
    });

    it('should handle button interactions correctly', async () => {
      const mockOnComplete = jest.fn().mockResolvedValue(undefined);
      const chore = createMockChore();

      const { getByTestId } = render(
        <ChoreCard 
          chore={chore} 
          showCompleteButton={true}
          onComplete={mockOnComplete}
        />
      );

      const button = getByTestId('complete-chore-button');
      expect(button).toBeTruthy();
      
      await act(async () => {
        fireEvent.press(button);
      });

      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalled();
      });
    });
  });
});