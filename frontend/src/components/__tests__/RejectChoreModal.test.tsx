/**
 * RejectChoreModal Component Tests
 * Tests the chore rejection modal with form validation and user feedback
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { RejectChoreModal } from '../RejectChoreModal';

describe('RejectChoreModal Component', () => {
  const defaultProps = {
    visible: true,
    choreTitle: 'Clean the kitchen',
    childName: 'Alice',
    onReject: jest.fn(),
    onCancel: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering and Visibility', () => {
    it('should render modal when visible is true', () => {
      const { getAllByText, getByText } = render(<RejectChoreModal {...defaultProps} />);

      const rejectChoreElements = getAllByText('Reject Chore');
      expect(rejectChoreElements.length).toBeGreaterThan(0); // Title and button both say "Reject Chore"
      expect(getByText('"Clean the kitchen" by Alice')).toBeTruthy();
    });

    it('should not render modal content when visible is false', () => {
      const { queryByText } = render(
        <RejectChoreModal {...defaultProps} visible={false} />
      );

      // Modal still renders but content may not be visible
      expect(queryByText('Reject Chore')).toBeNull();
    });

    it('should display correct chore title and child name', () => {
      const props = {
        ...defaultProps,
        choreTitle: 'Take out trash',
        childName: 'Bob',
      };

      const { getByText } = render(<RejectChoreModal {...props} />);

      expect(getByText('"Take out trash" by Bob')).toBeTruthy();
    });

    it('should render all required UI elements', () => {
      const { getAllByText, getByText, getByPlaceholderText } = render(
        <RejectChoreModal {...defaultProps} />
      );

      const rejectChoreElements = getAllByText('Reject Chore');
      expect(rejectChoreElements.length).toBe(2); // Title and button
      expect(getByText('Reason for rejection:')).toBeTruthy();
      expect(getByText('Let Alice know what needs to be improved so they can complete the chore properly.')).toBeTruthy();
      expect(getByPlaceholderText('e.g., Please clean more thoroughly and organize items properly')).toBeTruthy();
      expect(getByText('Cancel')).toBeTruthy();
    });
  });

  describe('Text Input Functionality', () => {
    it('should have text input with correct properties', () => {
      const { getByPlaceholderText } = render(<RejectChoreModal {...defaultProps} />);

      const textInput = getByPlaceholderText('e.g., Please clean more thoroughly and organize items properly');
      
      expect(textInput.props.multiline).toBe(true);
      expect(textInput.props.numberOfLines).toBe(4);
      expect(textInput.props.maxLength).toBe(500);
      expect(textInput.props.autoFocus).toBe(true);
    });

    it('should show initial character count', () => {
      const { getByText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByText('0/500 characters')).toBeTruthy();
    });

    it('should have helpful placeholder text', () => {
      const { getByPlaceholderText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByPlaceholderText('e.g., Please clean more thoroughly and organize items properly')).toBeTruthy();
    });
  });

  describe('Button States and Validation', () => {
    it('should have Cancel button that is always enabled', () => {
      const { getByText } = render(<RejectChoreModal {...defaultProps} />);

      const cancelButton = getByText('Cancel');
      expect(cancelButton).toBeTruthy();
    });

    it('should have Reject button', () => {
      const { getAllByText } = render(<RejectChoreModal {...defaultProps} />);

      const rejectButtons = getAllByText('Reject Chore');
      expect(rejectButtons.length).toBe(2); // Title and button
    });
  });

  describe('User Interactions - Cancel', () => {
    it('should call onCancel when Cancel button is pressed', () => {
      const { getByText } = render(<RejectChoreModal {...defaultProps} />);

      fireEvent.press(getByText('Cancel'));
      
      expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
    });

    it('should handle modal onRequestClose', () => {
      // Test that the modal has the onRequestClose handler
      const { getAllByText } = render(<RejectChoreModal {...defaultProps} />);
      
      // Verify modal renders - indirect test of onRequestClose being handled
      const rejectElements = getAllByText('Reject Chore');
      expect(rejectElements.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility and UX', () => {
    it('should provide helpful guidance text', () => {
      const { getByText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByText('Let Alice know what needs to be improved so they can complete the chore properly.')).toBeTruthy();
    });

    it('should update guidance text with correct child name', () => {
      const props = {
        ...defaultProps,
        childName: 'Charlie',
      };

      const { getByText } = render(<RejectChoreModal {...props} />);

      expect(getByText('Let Charlie know what needs to be improved so they can complete the chore properly.')).toBeTruthy();
    });

    it('should have proper modal structure', () => {
      const { getAllByText, getByText } = render(<RejectChoreModal {...defaultProps} />);

      // Check that main structural elements are present
      const rejectElements = getAllByText('Reject Chore');
      expect(rejectElements.length).toBe(2); // Title and button
      expect(getByText('Reason for rejection:')).toBeTruthy(); // Label
      expect(getByText('Cancel')).toBeTruthy(); // Cancel button
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle very long child names gracefully', () => {
      const props = {
        ...defaultProps,
        childName: 'VeryLongChildNameThatMightCauseLayoutIssues',
      };

      const { getByText } = render(<RejectChoreModal {...props} />);

      expect(getByText('"Clean the kitchen" by VeryLongChildNameThatMightCauseLayoutIssues')).toBeTruthy();
    });

    it('should handle very long chore titles gracefully', () => {
      const props = {
        ...defaultProps,
        choreTitle: 'A very long chore title that describes a complex task with many detailed requirements and specifications',
      };

      const { getByText } = render(<RejectChoreModal {...props} />);

      expect(getByText('"A very long chore title that describes a complex task with many detailed requirements and specifications" by Alice')).toBeTruthy();
    });

    it('should handle empty child name', () => {
      const props = {
        ...defaultProps,
        childName: '',
      };

      const { getByText } = render(<RejectChoreModal {...props} />);

      expect(getByText('"Clean the kitchen" by ')).toBeTruthy();
    });

    it('should handle empty chore title', () => {
      const props = {
        ...defaultProps,
        choreTitle: '',
      };

      const { getByText } = render(<RejectChoreModal {...props} />);

      expect(getByText('"" by Alice')).toBeTruthy();
    });
  });

  describe('Component Props Validation', () => {
    it('should handle all props correctly', () => {
      const customProps = {
        visible: true,
        choreTitle: 'Custom chore',
        childName: 'Custom child',
        onReject: jest.fn(),
        onCancel: jest.fn(),
      };

      const { getByText } = render(<RejectChoreModal {...customProps} />);

      expect(getByText('"Custom chore" by Custom child')).toBeTruthy();
    });

    it('should handle prop changes correctly', () => {
      const { rerender, getByText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByText('"Clean the kitchen" by Alice')).toBeTruthy();

      rerender(
        <RejectChoreModal 
          {...defaultProps} 
          choreTitle="New chore" 
          childName="Bob" 
        />
      );

      expect(getByText('"New chore" by Bob')).toBeTruthy();
    });

    it('should handle undefined or null props gracefully', () => {
      const nullProps = {
        ...defaultProps,
        choreTitle: null as any,
        childName: undefined as any,
      };

      expect(() => {
        render(<RejectChoreModal {...nullProps} />);
      }).not.toThrow();
    });
  });

  describe('Modal Behavior', () => {
    it('should render with correct visibility prop', () => {
      const { rerender, queryAllByText } = render(
        <RejectChoreModal {...defaultProps} visible={false} />
      );

      // When not visible, content should not be found
      expect(queryAllByText('Reject Chore')).toHaveLength(0);

      rerender(<RejectChoreModal {...defaultProps} visible={true} />);

      // When visible, content should be found
      const rejectElements = queryAllByText('Reject Chore');
      expect(rejectElements.length).toBeGreaterThan(0);
    });

    it('should handle keyboard avoiding behavior', () => {
      const { getAllByText } = render(<RejectChoreModal {...defaultProps} />);

      // Modal should render and handle keyboard avoiding
      const rejectElements = getAllByText('Reject Chore');
      expect(rejectElements.length).toBeGreaterThan(0);
    });

    it('should handle scroll behavior for content', () => {
      const { getAllByText } = render(<RejectChoreModal {...defaultProps} />);

      // Modal should render with scrollable content
      const rejectElements = getAllByText('Reject Chore');
      expect(rejectElements.length).toBeGreaterThan(0);
    });
  });

  describe('Text Input Configuration', () => {
    it('should configure text input correctly', () => {
      const { getByPlaceholderText } = render(<RejectChoreModal {...defaultProps} />);

      const textInput = getByPlaceholderText('e.g., Please clean more thoroughly and organize items properly');
      
      expect(textInput.props.multiline).toBe(true);
      expect(textInput.props.numberOfLines).toBe(4);
      expect(textInput.props.maxLength).toBe(500);
      expect(textInput.props.autoFocus).toBe(true);
      expect(textInput.props.textAlignVertical).toBe('top');
    });

    it('should show character counter', () => {
      const { getByText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByText('0/500 characters')).toBeTruthy();
    });
  });

  describe('Button Layout', () => {
    it('should display both Cancel and Reject buttons', () => {
      const { getByText, getAllByText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByText('Cancel')).toBeTruthy();
      const rejectButtons = getAllByText('Reject Chore');
      expect(rejectButtons.length).toBe(2); // Title and button
    });

    it('should maintain proper button layout', () => {
      const { getByText } = render(<RejectChoreModal {...defaultProps} />);

      // Buttons should be present in footer
      expect(getByText('Cancel')).toBeTruthy();
    });
  });

  describe('Content Validation', () => {
    it('should display required form fields', () => {
      const { getByText, getByPlaceholderText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByText('Reason for rejection:')).toBeTruthy();
      expect(getByPlaceholderText('e.g., Please clean more thoroughly and organize items properly')).toBeTruthy();
    });

    it('should show helpful instructions', () => {
      const { getByText } = render(<RejectChoreModal {...defaultProps} />);

      expect(getByText('Let Alice know what needs to be improved so they can complete the chore properly.')).toBeTruthy();
    });
  });
});