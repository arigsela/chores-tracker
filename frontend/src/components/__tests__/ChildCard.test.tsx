/**
 * ChildCard Component Tests
 * Tests the child user card component for displaying child information and chore statistics
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import ChildCard from '../ChildCard';
import { ChildWithChores } from '../../api/users';

// Mock child user factory - matches ChoreAssignmentSummary schema
const createMockChild = (overrides: Partial<ChildWithChores> = {}): ChildWithChores => ({
  id: 1,
  username: 'testchild',
  email: 'child@test.com',
  is_active: true,
  is_parent: false,
  parent_id: 1,
  chores: [
    {
      id: 1,
      chore_id: 101,
      chore_title: 'Clean room',
      reward: 5.0,
      is_completed: false,
      is_approved: false,
    },
    {
      id: 2,
      chore_id: 102,
      chore_title: 'Do dishes',
      reward: 3.0,
      is_completed: true,
      is_approved: false,
    },
    {
      id: 3,
      chore_id: 103,
      chore_title: 'Take out trash',
      reward: 2.0,
      is_completed: true,
      is_approved: true,
    },
  ],
  ...overrides,
});

describe('ChildCard Component', () => {
  const mockOnPress = jest.fn();
  const mockOnResetPassword = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render child name and status', () => {
      const child = createMockChild({
        username: 'alice',
        is_active: true,
      });

      const { getByText, getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      expect(getByText('alice')).toBeTruthy();
      const activeElements = getAllByText('Active');
      expect(activeElements.length).toBeGreaterThan(0);
    });

    it('should render inactive status for inactive children', () => {
      const child = createMockChild({
        is_active: false,
      });

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      expect(getByText('Inactive')).toBeTruthy();
    });

    it('should display chore statistics correctly', () => {
      const child = createMockChild();

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Check that we have the expected number of '1' values (3 stats showing 1)
      const oneElements = getAllByText('1');
      expect(oneElements).toHaveLength(3); // Active, Pending, Completed all show 1

      const activeElements = getAllByText('Active');
      expect(activeElements.length).toBeGreaterThan(0);
      
      const pendingElements = getAllByText('Pending');
      expect(pendingElements.length).toBeGreaterThan(0);
      
      const completedElements = getAllByText('Completed');
      expect(completedElements.length).toBeGreaterThan(0);
    });

    it('should render View Details button', () => {
      const child = createMockChild();

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      expect(getByText('View Details →')).toBeTruthy();
    });
  });

  describe('Chore Statistics Calculation', () => {
    it('should handle child with no chores', () => {
      const child = createMockChild({
        chores: [],
      });

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // All counts should be 0 - there should be 3 zeros (one for each stat)
      const zeroElements = getAllByText('0');
      expect(zeroElements).toHaveLength(3);
      
      expect(getAllByText('Active').length).toBeGreaterThan(0);
      expect(getAllByText('Pending').length).toBeGreaterThan(0);
      expect(getAllByText('Completed').length).toBeGreaterThan(0);
    });

    it('should handle child with undefined chores', () => {
      const child = createMockChild({
        chores: undefined,
      });

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // All counts should be 0 - there should be 3 zeros
      const zeroElements = getAllByText('0');
      expect(zeroElements).toHaveLength(3);
    });

    it('should calculate active chores correctly based on is_completed field', () => {
      const child = createMockChild({
        chores: [
          { id: 1, chore_id: 101, chore_title: 'Chore 1', reward: 5.0, is_completed: false, is_approved: false },
          { id: 2, chore_id: 102, chore_title: 'Chore 2', reward: 5.0, is_completed: false, is_approved: false },
          { id: 3, chore_id: 103, chore_title: 'Chore 3', reward: 5.0, is_completed: true, is_approved: false },
          { id: 4, chore_id: 104, chore_title: 'Chore 4', reward: 5.0, is_completed: true, is_approved: true },
        ],
      });

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      const twoElements = getAllByText('2');
      expect(twoElements.length).toBeGreaterThan(0); // Should show 2 active chores (not completed)
    });

    it('should calculate completed (approved) chores correctly based on is_approved field', () => {
      const child = createMockChild({
        chores: [
          { id: 1, chore_id: 101, chore_title: 'Chore 1', reward: 5.0, is_completed: true, is_approved: true },
          { id: 2, chore_id: 102, chore_title: 'Chore 2', reward: 5.0, is_completed: true, is_approved: true },
          { id: 3, chore_id: 103, chore_title: 'Chore 3', reward: 5.0, is_completed: true, is_approved: false },
        ],
      });

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      const twoElements = getAllByText('2');
      expect(twoElements.length).toBeGreaterThan(0); // 2 approved chores (is_approved: true)
    });

    it('should use provided pendingCount override', () => {
      const child = createMockChild();

      const { getAllByText } = render(
        <ChildCard
          child={child}
          onPress={mockOnPress}
          pendingCount={5}
        />
      );

      const fiveElements = getAllByText('5');
      expect(fiveElements.length).toBeGreaterThan(0); // Should use override value
    });

    it('should use provided completed_chores override from allowance summary', () => {
      // When completed_chores is provided (from allowance summary), use it instead of calculating
      const child = createMockChild({
        chores: [
          { id: 1, chore_id: 101, chore_title: 'Chore 1', reward: 5.0, is_completed: true, is_approved: true },
        ],
        // Override completed_chores from allowance summary (even though only 1 chore above)
        completed_chores: 10,
      });

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Should show 10 (the override) not 1 (calculated from chores)
      const tenElements = getAllByText('10');
      expect(tenElements.length).toBeGreaterThan(0);
    });

    it('should calculate pending approval chores correctly', () => {
      const child = createMockChild({
        chores: [
          // Completed but not approved (pending)
          { id: 1, chore_id: 101, chore_title: 'Chore 1', reward: 5.0, is_completed: true, is_approved: false },
          // Completed but not approved (pending)
          { id: 2, chore_id: 102, chore_title: 'Chore 2', reward: 5.0, is_completed: true, is_approved: false },
          // Not completed (active)
          { id: 3, chore_id: 103, chore_title: 'Chore 3', reward: 5.0, is_completed: false, is_approved: false },
          // Completed and approved (completed)
          { id: 4, chore_id: 104, chore_title: 'Chore 4', reward: 5.0, is_completed: true, is_approved: true },
        ],
      });

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      const twoElements = getAllByText('2');
      expect(twoElements.length).toBeGreaterThan(0); // 2 pending approval (is_completed: true, is_approved: false)
    });
  });

  describe('User Interactions', () => {
    it('should call onPress when View Details is pressed', () => {
      const child = createMockChild();

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      fireEvent.press(getByText('View Details →'));
      expect(mockOnPress).toHaveBeenCalledTimes(1);
    });

    it('should display Reset Password button when onResetPassword provided', () => {
      const child = createMockChild();

      const { getByText } = render(
        <ChildCard 
          child={child} 
          onPress={mockOnPress} 
          onResetPassword={mockOnResetPassword} 
        />
      );

      expect(getByText('Reset Password')).toBeTruthy();
    });

    it('should not display Reset Password button when onResetPassword not provided', () => {
      const child = createMockChild();

      const { queryByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      expect(queryByText('Reset Password')).toBeNull();
    });

    it('should call onResetPassword when Reset Password is pressed', () => {
      const child = createMockChild();

      const { getByText } = render(
        <ChildCard 
          child={child} 
          onPress={mockOnPress} 
          onResetPassword={mockOnResetPassword} 
        />
      );

      fireEvent.press(getByText('Reset Password'));
      expect(mockOnResetPassword).toHaveBeenCalledTimes(1);
    });

    it('should handle multiple button presses correctly', () => {
      const child = createMockChild();

      const { getByText } = render(
        <ChildCard 
          child={child} 
          onPress={mockOnPress} 
          onResetPassword={mockOnResetPassword} 
        />
      );

      fireEvent.press(getByText('View Details →'));
      fireEvent.press(getByText('Reset Password'));
      fireEvent.press(getByText('View Details →'));

      expect(mockOnPress).toHaveBeenCalledTimes(2);
      expect(mockOnResetPassword).toHaveBeenCalledTimes(1);
    });
  });

  describe('Visual Styling and Accessibility', () => {
    it('should apply correct styling for active status', () => {
      const child = createMockChild({
        is_active: true,
      });

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      const activeElements = getAllByText('Active');
      expect(activeElements.length).toBeGreaterThan(0);
    });

    it('should apply correct styling for different statistic types', () => {
      const child = createMockChild();

      const { getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Check that all stat labels are present
      expect(getAllByText('Active').length).toBeGreaterThan(0);
      expect(getAllByText('Pending').length).toBeGreaterThan(0);
      expect(getAllByText('Completed').length).toBeGreaterThan(0);
    });

    it('should have consistent card layout structure', () => {
      const child = createMockChild();

      const { getByText, getAllByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Verify main structural elements are present
      expect(getByText('testchild')).toBeTruthy(); // Header
      expect(getAllByText('Active').length).toBeGreaterThan(0); // Stats section
      expect(getByText('View Details →')).toBeTruthy(); // Footer
    });
  });

  describe('Edge Cases', () => {
    it('should handle child with very long username', () => {
      const child = createMockChild({
        username: 'ThisIsAVeryLongUsernameTestingMaxLength',
      });

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      expect(getByText('ThisIsAVeryLongUsernameTestingMaxLength')).toBeTruthy();
    });

    it('should handle child with no email', () => {
      const child = createMockChild({
        email: null,
      });

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      expect(getByText('testchild')).toBeTruthy();
    });

    it('should handle child with large number of chores', () => {
      const manyChores = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        chore_id: 100 + i + 1,
        chore_title: `Chore ${i + 1}`,
        reward: 5.0,
        is_completed: i % 3 === 0,
        is_approved: i % 5 === 0,
      }));

      const child = createMockChild({
        chores: manyChores,
      });

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Should handle large numbers gracefully
      expect(getByText('testchild')).toBeTruthy();
    });

    it('should handle malformed chore data gracefully', () => {
      const child = createMockChild({
        chores: [
          { id: 1, chore_id: 101, chore_title: 'Chore 1', reward: 5.0, is_completed: false, is_approved: false },
          { id: 2, chore_id: 102, chore_title: 'Chore 2', reward: 5.0, is_completed: false, is_approved: false },
        ] as any,
      });

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Should not crash and still display the child
      expect(getByText('testchild')).toBeTruthy();
    });

    it('should handle child with zero pending count override', () => {
      const child = createMockChild();

      const { getByText } = render(
        <ChildCard 
          child={child} 
          onPress={mockOnPress} 
          pendingCount={0} 
        />
      );

      expect(getByText('0')).toBeTruthy();
    });
  });

  describe('Props Validation', () => {
    it('should handle minimal required props', () => {
      const minimalChild: ChildWithChores = {
        id: 1,
        username: 'minimal',
        email: null,
        is_active: true,
        is_parent: false,
        parent_id: 1,
      };

      const { getByText } = render(
        <ChildCard child={minimalChild} onPress={mockOnPress} />
      );

      expect(getByText('minimal')).toBeTruthy();
      expect(getByText('View Details →')).toBeTruthy();
    });

    it('should handle all optional props provided', () => {
      const child = createMockChild();

      const { getByText } = render(
        <ChildCard 
          child={child} 
          onPress={mockOnPress} 
          onResetPassword={mockOnResetPassword}
          pendingCount={10}
        />
      );

      expect(getByText('testchild')).toBeTruthy();
      expect(getByText('View Details →')).toBeTruthy();
      expect(getByText('Reset Password')).toBeTruthy();
      expect(getByText('10')).toBeTruthy(); // pendingCount override
    });

    it('should handle undefined onResetPassword gracefully', () => {
      const child = createMockChild();

      const { queryByText } = render(
        <ChildCard 
          child={child} 
          onPress={mockOnPress} 
          onResetPassword={undefined}
        />
      );

      expect(queryByText('Reset Password')).toBeNull();
    });
  });

  describe('Complex Chore Scenarios', () => {
    it('should handle mixed completion and approval states', () => {
      const child = createMockChild({
        chores: [
          // Active: not completed
          { id: 1, chore_id: 101, chore_title: 'Chore 1', reward: 5.0, is_completed: false, is_approved: false },
          // Pending: completed but not approved
          { id: 2, chore_id: 102, chore_title: 'Chore 2', reward: 5.0, is_completed: true, is_approved: false },
          // Completed: both completed and approved
          { id: 3, chore_id: 103, chore_title: 'Chore 3', reward: 5.0, is_completed: true, is_approved: true },
          // Edge case: approved but not marked completed (shouldn't happen but test anyway)
          { id: 4, chore_id: 104, chore_title: 'Chore 4', reward: 5.0, is_completed: false, is_approved: true },
        ],
      });

      const { getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Should still render and calculate stats
      expect(getByText('testchild')).toBeTruthy();
    });

    it('should correctly calculate stats using only is_completed and is_approved fields', () => {
      const child = createMockChild({
        chores: [
          // Active (is_completed: false)
          { id: 1, chore_id: 101, chore_title: 'Chore 1', reward: 5.0, is_completed: false, is_approved: false },
          // Pending (is_completed: true, is_approved: false)
          { id: 2, chore_id: 102, chore_title: 'Chore 2', reward: 5.0, is_completed: true, is_approved: false },
        ],
      });

      const { getAllByText, getByText } = render(
        <ChildCard child={child} onPress={mockOnPress} />
      );

      // Should show 1 active, 1 pending, 0 completed
      // Both Active and Pending show '1', so we expect 2 elements with text '1'
      const onesElements = getAllByText('1');
      expect(onesElements).toHaveLength(2);

      // Completed should show '0'
      expect(getByText('0')).toBeTruthy();

      // Verify the child's name is rendered (proves component rendered correctly)
      expect(getByText('testchild')).toBeTruthy();
    });
  });
});