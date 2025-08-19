/**
 * ActivityCard Component Tests
 * Tests the activity display component for showing user activity feed
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { ActivityCard } from '../ActivityCard';
import { Activity, ActivityTypes } from '../../api/activities';
import { mockDate, testDates } from '../../test-utils';

// Mock activity factory
const createMockActivity = (overrides: Partial<Activity> = {}): Activity => ({
  id: 1,
  user_id: 2,
  activity_type: ActivityTypes.CHORE_COMPLETED,
  description: 'Completed chore: Clean the kitchen',
  activity_data: {
    chore_id: 1,
    chore_title: 'Clean the kitchen',
    reward_amount: 5.00,
  },
  created_at: testDates.now,
  user: {
    id: 2,
    username: 'testchild',
    is_parent: false,
    email: 'child@test.com',
    is_active: true,
    parent_id: 1,
  },
  ...overrides,
});

describe('ActivityCard Component', () => {
  let restoreDate: () => void;

  beforeEach(() => {
    restoreDate = mockDate(testDates.now);
  });

  afterEach(() => {
    restoreDate();
  });

  describe('Basic Rendering', () => {
    it('should render activity description and user', () => {
      const activity = createMockActivity({
        description: 'Completed chore: Wash dishes',
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('Completed chore: Wash dishes')).toBeTruthy();
      expect(getByText('testchild')).toBeTruthy();
    });

    it('should display activity icon and proper styling', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_COMPLETED,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('✅')).toBeTruthy();
    });

    it('should show time ago information', () => {
      const activity = createMockActivity({
        created_at: testDates.now,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('Just now')).toBeTruthy();
    });

    it('should handle missing user gracefully', () => {
      const activity = createMockActivity({
        user: undefined,
      });

      const { getByText, queryByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('Completed chore: Clean the kitchen')).toBeTruthy();
      expect(queryByText('testchild')).toBeNull();
    });
  });

  describe('Activity Type Icons and Colors', () => {
    it('should display correct icon for chore completed', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_COMPLETED,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('✅')).toBeTruthy();
    });

    it('should display correct icon for chore approved', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_APPROVED,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('👍')).toBeTruthy();
    });

    it('should display correct icon for chore rejected', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_REJECTED,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('❌')).toBeTruthy();
    });

    it('should display correct icon for chore created', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_CREATED,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('📝')).toBeTruthy();
    });

    it('should display correct icon for adjustment applied', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.ADJUSTMENT_APPLIED,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('💰')).toBeTruthy();
    });

    it('should display default icon for unknown activity type', () => {
      const activity = createMockActivity({
        activity_type: 'unknown_type',
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('📋')).toBeTruthy();
    });
  });

  describe('Amount Display Logic', () => {
    it('should display reward amount for approved chores', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_APPROVED,
        activity_data: {
          reward_amount: 7.50,
        },
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('+$7.50')).toBeTruthy();
    });

    it('should display positive adjustment amount', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.ADJUSTMENT_APPLIED,
        activity_data: {
          amount: 10.00,
          reason: 'Bonus for good behavior',
        },
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('+$10.00')).toBeTruthy();
    });

    it('should display negative adjustment amount', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.ADJUSTMENT_APPLIED,
        activity_data: {
          amount: -5.00,
          reason: 'Penalty for misbehavior',
        },
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('-$5.00')).toBeTruthy();
    });

    it('should display reward amount for created chores', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_CREATED,
        activity_data: {
          chore_title: 'New chore',
          reward_amount: 3.00,
        },
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('$3.00')).toBeTruthy();
    });

    it('should not display amount when not available', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.CHORE_COMPLETED,
        activity_data: {
          chore_title: 'Clean room',
          // No reward_amount
        },
      });

      const { queryByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(queryByText(/\$/)).toBeNull();
    });

    it('should handle zero adjustment amount', () => {
      const activity = createMockActivity({
        activity_type: ActivityTypes.ADJUSTMENT_APPLIED,
        activity_data: {
          amount: 0,
          reason: 'Reset balance',
        },
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('+$0.00')).toBeTruthy();
    });
  });

  describe('Target User Display', () => {
    it('should display target user when present', () => {
      const activity = createMockActivity({
        target_user_id: 3,
        target_user: {
          id: 3,
          username: 'anothechild',
          is_parent: false,
          email: 'another@test.com',
          is_active: true,
          parent_id: 1,
        },
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('testchild')).toBeTruthy();
      expect(getByText(' → ')).toBeTruthy();
      expect(getByText('anothechild')).toBeTruthy();
    });

    it('should not display arrow when no target user', () => {
      const activity = createMockActivity({
        target_user: undefined,
      });

      const { queryByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(queryByText(' → ')).toBeNull();
    });
  });

  describe('Touch Interactions', () => {
    it('should call onPress when card is pressed', () => {
      const mockOnPress = jest.fn();
      const activity = createMockActivity();

      const { getByText } = render(
        <ActivityCard activity={activity} onPress={mockOnPress} />
      );

      fireEvent.press(getByText('Completed chore: Clean the kitchen'));
      expect(mockOnPress).toHaveBeenCalled();
    });

    it('should not be pressable when onPress is not provided', () => {
      const activity = createMockActivity();

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      // Should not throw when pressed without onPress
      fireEvent.press(getByText('Completed chore: Clean the kitchen'));
    });

    it('should handle onPress being undefined', () => {
      const activity = createMockActivity();

      const { getByText } = render(
        <ActivityCard activity={activity} onPress={undefined} />
      );

      // Should not throw when pressed with undefined onPress
      expect(() => {
        fireEvent.press(getByText('Completed chore: Clean the kitchen'));
      }).not.toThrow();
    });
  });

  describe('Time Formatting', () => {
    it('should show "Just now" for very recent activities', () => {
      const activity = createMockActivity({
        created_at: testDates.now,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('Just now')).toBeTruthy();
    });

    it('should show minutes ago for recent activities', () => {
      const minutesAgo = new Date(Date.now() - 30 * 60 * 1000).toISOString();
      const activity = createMockActivity({
        created_at: minutesAgo,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('30m ago')).toBeTruthy();
    });

    it('should show hours ago for activities within a day', () => {
      const hoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
      const activity = createMockActivity({
        created_at: hoursAgo,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('2h ago')).toBeTruthy();
    });

    it('should show days ago for activities within a week', () => {
      const daysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString();
      const activity = createMockActivity({
        created_at: daysAgo,
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('3d ago')).toBeTruthy();
    });
  });

  describe('Props Validation', () => {
    it('should handle activity with minimal data', () => {
      const minimalActivity: Activity = {
        id: 1,
        user_id: 1,
        activity_type: ActivityTypes.CHORE_COMPLETED,
        description: 'Basic activity',
        activity_data: {},
        created_at: testDates.now,
      };

      const { getByText } = render(
        <ActivityCard activity={minimalActivity} />
      );

      expect(getByText('Basic activity')).toBeTruthy();
      expect(getByText('✅')).toBeTruthy();
    });

    it('should handle activity with complex activity_data', () => {
      const activity = createMockActivity({
        activity_data: {
          chore_id: 1,
          chore_title: 'Complex chore',
          reward_amount: 15.50,
          adjustment_id: 2,
          amount: 10.00,
          reason: 'Multiple fields',
          rejection_reason: 'Not done properly',
          adjustment_type: 'bonus',
        },
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('Completed chore: Clean the kitchen')).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long descriptions with numberOfLines', () => {
      const activity = createMockActivity({
        description: 'This is a very long description that should be truncated when displayed in the activity card because it exceeds the typical length that fits nicely in the UI',
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      const descriptionElement = getByText(/This is a very long description/);
      expect(descriptionElement).toBeTruthy();
      expect(descriptionElement.props.numberOfLines).toBe(2);
    });

    it('should handle missing activity_data gracefully', () => {
      const activity = createMockActivity({
        activity_data: {},
      });

      const { getByText, queryByText } = render(
        <ActivityCard activity={activity} />
      );

      expect(getByText('Completed chore: Clean the kitchen')).toBeTruthy();
      expect(queryByText(/\$/)).toBeNull();
    });

    it('should handle invalid timestamp gracefully', () => {
      const activity = createMockActivity({
        created_at: 'invalid-date',
      });

      const { getByText } = render(
        <ActivityCard activity={activity} />
      );

      // Should not crash and still render the activity
      expect(getByText('Completed chore: Clean the kitchen')).toBeTruthy();
    });
  });
});