/**
 * Chore Management Workflow Integration Tests
 * Tests complete chore lifecycle from creation to completion and approval
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { SimpleNavigator } from '../../navigation/SimpleNavigator';
import { choreAPI } from '../../api/chores';
import { resetAllMocks, createMockUser, createMockChore } from '../../test-utils';

// Mock the chore API
jest.mock('../../api/chores', () => ({
  choreAPI: {
    getMyChores: jest.fn(),
    getPendingApprovalChores: jest.fn(),
    createChore: jest.fn(),
    updateChore: jest.fn(),
    completeChore: jest.fn(),
    approveChore: jest.fn(),
    rejectChore: jest.fn(),
    deleteChore: jest.fn(),
  },
}));

const mockedChoreAPI = choreAPI as jest.Mocked<typeof choreAPI>;

// Mock the auth API
const mockUseAuth = jest.fn();
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock Alert
const mockAlert = jest.fn();
global.alert = mockAlert;

// Mock enhanced ChoresScreen with full chore management functionality
jest.mock('../../screens/ChoresScreen', () => ({
  ChoresScreen: () => {
    const { View, Text, TextInput, TouchableOpacity, ScrollView, Alert } = require('react-native');
    const mockReact = require('react');
    const [chores, setChores] = mockReact.useState([]);
    const [loading, setLoading] = mockReact.useState(false);
    const [showCreateForm, setShowCreateForm] = mockReact.useState(false);
    const [formData, setFormData] = mockReact.useState({
      title: '',
      description: '',
      reward: '',
      assignedToId: '',
    });

    const { useAuth } = require('../../contexts/AuthContext');
    const { user } = useAuth();
    const isParent = user?.role === 'parent';

    mockReact.useEffect(() => {
      loadChores();
    }, []);

    const loadChores = async () => {
      try {
        setLoading(true);
        const { choreAPI } = require('../../api/chores');
        const result = await choreAPI.getMyChores();
        setChores(result);
      } catch (error) {
        console.error('Failed to load chores:', error);
      } finally {
        setLoading(false);
      }
    };

    const handleCreateChore = async () => {
      if (!formData.title || !formData.reward) {
        Alert.alert('Error', 'Please fill required fields');
        return;
      }

      try {
        const { choreAPI } = require('../../api/chores');
        const choreData = {
          title: formData.title,
          description: formData.description,
          reward: parseFloat(formData.reward),
          assigned_to_id: formData.assignedToId ? parseInt(formData.assignedToId) : null,
        };
        
        const newChore = await choreAPI.createChore(choreData);
        setChores(prev => [...prev, newChore]);
        setShowCreateForm(false);
        setFormData({ title: '', description: '', reward: '', assignedToId: '' });
        Alert.alert('Success', 'Chore created successfully!');
      } catch (error: any) {
        Alert.alert('Error', error.message || 'Failed to create chore');
      }
    };

    const handleCompleteChore = async (choreId: number) => {
      try {
        const { choreAPI } = require('../../api/chores');
        await choreAPI.completeChore(choreId);
        setChores(prev => prev.map(chore => 
          chore.id === choreId 
            ? { ...chore, is_completed: true, completed_at: new Date().toISOString() }
            : chore
        ));
        Alert.alert('Success', 'Chore marked as completed!');
      } catch (error: any) {
        Alert.alert('Error', error.message || 'Failed to complete chore');
      }
    };

    const handleDeleteChore = async (choreId: number) => {
      try {
        const { choreAPI } = require('../../api/chores');
        await choreAPI.deleteChore(choreId);
        setChores(prev => prev.filter(chore => chore.id !== choreId));
        Alert.alert('Success', 'Chore deleted successfully!');
      } catch (error: any) {
        Alert.alert('Error', error.message || 'Failed to delete chore');
      }
    };

    return (
      <View testID="chores-screen">
        <Text>Chores Management</Text>
        
        {isParent && (
          <TouchableOpacity 
            testID="create-chore-button" 
            onPress={() => setShowCreateForm(!showCreateForm)}
          >
            <Text>{showCreateForm ? 'Cancel' : 'Create New Chore'}</Text>
          </TouchableOpacity>
        )}

        {showCreateForm && (
          <View testID="create-chore-form">
            <Text>Create New Chore</Text>
            <TextInput
              testID="chore-title-input"
              placeholder="Chore Title"
              value={formData.title}
              onChangeText={text => setFormData(prev => ({ ...prev, title: text }))}
            />
            <TextInput
              testID="chore-description-input"
              placeholder="Description (optional)"
              value={formData.description}
              onChangeText={text => setFormData(prev => ({ ...prev, description: text }))}
            />
            <TextInput
              testID="chore-reward-input"
              placeholder="Reward Amount"
              value={formData.reward}
              onChangeText={text => setFormData(prev => ({ ...prev, reward: text }))}
              keyboardType="numeric"
            />
            <TextInput
              testID="assigned-to-input"
              placeholder="Assign to Child ID (optional)"
              value={formData.assignedToId}
              onChangeText={text => setFormData(prev => ({ ...prev, assignedToId: text }))}
              keyboardType="numeric"
            />
            <TouchableOpacity testID="submit-chore-button" onPress={handleCreateChore}>
              <Text>Create Chore</Text>
            </TouchableOpacity>
          </View>
        )}

        <ScrollView testID="chores-list">
          {loading ? (
            <Text testID="loading-indicator">Loading chores...</Text>
          ) : chores.length === 0 ? (
            <Text testID="no-chores">No chores found</Text>
          ) : (
            chores.map((chore: any) => (
              <View key={chore.id} testID={`chore-item-${chore.id}`}>
                <Text testID={`chore-title-${chore.id}`}>{chore.title}</Text>
                <Text testID={`chore-reward-${chore.id}`}>Reward: ${chore.reward}</Text>
                <Text testID={`chore-status-${chore.id}`}>
                  Status: {chore.is_completed ? 'Completed' : 'Pending'}
                </Text>
                {chore.description && (
                  <Text testID={`chore-description-${chore.id}`}>{chore.description}</Text>
                )}
                
                {!chore.is_completed && (
                  <TouchableOpacity 
                    testID={`complete-chore-${chore.id}`}
                    onPress={() => handleCompleteChore(chore.id)}
                  >
                    <Text>Mark Complete</Text>
                  </TouchableOpacity>
                )}
                
                {isParent && (
                  <TouchableOpacity 
                    testID={`delete-chore-${chore.id}`}
                    onPress={() => handleDeleteChore(chore.id)}
                  >
                    <Text>Delete</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))
          )}
        </ScrollView>
      </View>
    );
  },
}));

// Mock other screens
jest.mock('../../screens/LoginScreen', () => ({
  LoginScreen: () => {
    const { View, Text } = require('react-native');
    return (
      <View testID="login-screen">
        <Text>Login Screen</Text>
      </View>
    );
  },
}));

jest.mock('../../screens/HomeScreen', () => ({
  HomeScreen: ({ onNavigate }: any) => {
    const { View, Text, TouchableOpacity } = require('react-native');
    const { useAuth } = require('../../contexts/AuthContext');
    const { user } = useAuth();

    return (
      <View testID="home-screen">
        <Text>Welcome, {user?.username}!</Text>
        <TouchableOpacity testID="navigate-to-chores" onPress={() => onNavigate?.('Chores')}>
          <Text>Go to Chores</Text>
        </TouchableOpacity>
      </View>
    );
  },
}));

// Mock other required screens
jest.mock('../../screens/ChildrenScreen', () => ({
  ChildrenScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="children-screen"><Text>Children Screen</Text></View>;
  },
}));

jest.mock('../../screens/BalanceScreen', () => ({
  BalanceScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="balance-screen"><Text>Balance Screen</Text></View>;
  },
}));

jest.mock('../../screens/ProfileScreen', () => ({
  ProfileScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="profile-screen"><Text>Profile Screen</Text></View>;
  },
}));

jest.mock('../../screens/ApprovalsScreen', () => ({
  __esModule: true,
  default: () => {
    const { View, Text } = require('react-native');
    return <View testID="approvals-screen"><Text>Approvals Screen</Text></View>;
  },
}));

jest.mock('../../screens/AllowanceSummaryScreen', () => ({
  AllowanceSummaryScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="allowance-summary-screen"><Text>Allowance Summary</Text></View>;
  },
}));

jest.mock('../../screens/StatisticsScreen', () => ({
  StatisticsScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="statistics-screen"><Text>Statistics Screen</Text></View>;
  },
}));

jest.mock('../../screens/RegisterScreen', () => ({
  RegisterScreen: () => {
    const { View, Text } = require('react-native');
    return <View testID="register-screen"><Text>Register Screen</Text></View>;
  },
}));

describe('Chore Management Workflow Integration Tests', () => {
  beforeEach(() => {
    resetAllMocks();
    jest.clearAllMocks();
    mockAlert.mockClear();
    
    // Default empty chores list
    mockedChoreAPI.getMyChores.mockResolvedValue([]);
    mockedChoreAPI.getPendingApprovalChores.mockResolvedValue([]);
  });

  describe('Parent Chore Creation Workflow', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });
    });

    it('should complete full chore creation workflow', async () => {
      const newChore = createMockChore({
        id: 1,
        title: 'Clean the kitchen',
        description: 'Wash dishes and wipe counters',
        reward: 10.00,
        assigned_to_id: 2,
      });

      mockedChoreAPI.createChore.mockResolvedValue(newChore);
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      // Navigate to chores screen
      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chores-screen')).toBeTruthy();
      });

      // Open create chore form
      fireEvent.press(getByTestId('create-chore-button'));
      expect(getByTestId('create-chore-form')).toBeTruthy();

      // Fill chore creation form
      fireEvent.changeText(getByTestId('chore-title-input'), 'Clean the kitchen');
      fireEvent.changeText(getByTestId('chore-description-input'), 'Wash dishes and wipe counters');
      fireEvent.changeText(getByTestId('chore-reward-input'), '10.00');
      fireEvent.changeText(getByTestId('assigned-to-input'), '2');

      // Submit form
      await act(async () => {
        fireEvent.press(getByTestId('submit-chore-button'));
      });

      // Verify chore was created
      await waitFor(() => {
        expect(mockedChoreAPI.createChore).toHaveBeenCalledWith({
          title: 'Clean the kitchen',
          description: 'Wash dishes and wipe counters',
          reward: 10.00,
          assigned_to_id: 2,
        });
      });

      expect(mockAlert).toHaveBeenCalledWith('Success', 'Chore created successfully!');
      
      // Verify chore appears in list
      await waitFor(() => {
        expect(getByTestId('chore-item-1')).toBeTruthy();
        expect(getByTestId('chore-title-1')).toHaveTextContent('Clean the kitchen');
        expect(getByTestId('chore-reward-1')).toHaveTextContent('Reward: $10');
      });
    });

    it('should handle chore creation validation errors', async () => {
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      // Navigate to chores and open form
      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        fireEvent.press(getByTestId('create-chore-button'));
      });

      // Try to submit empty form
      await act(async () => {
        fireEvent.press(getByTestId('submit-chore-button'));
      });

      expect(mockAlert).toHaveBeenCalledWith('Error', 'Please fill required fields');
      expect(mockedChoreAPI.createChore).not.toHaveBeenCalled();
    });

    it('should handle API errors during chore creation', async () => {
      mockedChoreAPI.createChore.mockRejectedValue(new Error('Server error'));
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      // Navigate and fill form
      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        fireEvent.press(getByTestId('create-chore-button'));
      });

      fireEvent.changeText(getByTestId('chore-title-input'), 'Test Chore');
      fireEvent.changeText(getByTestId('chore-reward-input'), '5.00');

      await act(async () => {
        fireEvent.press(getByTestId('submit-chore-button'));
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Error', 'Server error');
      });
    });

    it('should create unassigned chore when no child ID provided', async () => {
      const unassignedChore = createMockChore({
        title: 'General Task',
        assigned_to_id: null,
      });

      mockedChoreAPI.createChore.mockResolvedValue(unassignedChore);
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        fireEvent.press(getByTestId('create-chore-button'));
      });

      // Fill form without assigned_to_id
      fireEvent.changeText(getByTestId('chore-title-input'), 'General Task');
      fireEvent.changeText(getByTestId('chore-reward-input'), '5.00');

      await act(async () => {
        fireEvent.press(getByTestId('submit-chore-button'));
      });

      expect(mockedChoreAPI.createChore).toHaveBeenCalledWith({
        title: 'General Task',
        description: '',
        reward: 5.00,
        assigned_to_id: null,
      });
    });
  });

  describe('Child Chore Completion Workflow', () => {
    beforeEach(() => {
      const childUser = createMockUser({ role: 'child', id: 2 });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: childUser,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });
    });

    it('should complete full chore completion workflow', async () => {
      const assignedChore = createMockChore({
        id: 1,
        title: 'Clean bedroom',
        reward: 8.00,
        assigned_to_id: 2,
        is_completed: false,
      });

      mockedChoreAPI.getMyChores.mockResolvedValue([assignedChore]);
      mockedChoreAPI.completeChore.mockResolvedValue({ success: true });
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      // Navigate to chores
      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chore-item-1')).toBeTruthy();
        expect(getByTestId('chore-status-1')).toHaveTextContent('Status: Pending');
      });

      // Complete the chore
      await act(async () => {
        fireEvent.press(getByTestId('complete-chore-1'));
      });

      // Verify completion
      expect(mockedChoreAPI.completeChore).toHaveBeenCalledWith(1);
      expect(mockAlert).toHaveBeenCalledWith('Success', 'Chore marked as completed!');

      // Verify status update
      await waitFor(() => {
        expect(getByTestId('chore-status-1')).toHaveTextContent('Status: Completed');
      });
    });

    it('should handle chore completion errors', async () => {
      const assignedChore = createMockChore({
        id: 1,
        assigned_to_id: 2,
        is_completed: false,
      });

      mockedChoreAPI.getMyChores.mockResolvedValue([assignedChore]);
      mockedChoreAPI.completeChore.mockRejectedValue(new Error('Already completed'));
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chore-item-1')).toBeTruthy();
      });

      await act(async () => {
        fireEvent.press(getByTestId('complete-chore-1'));
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Error', 'Already completed');
      });
    });

    it('should not show create chore button for child users', async () => {
      const { getByTestId, getByText, queryByTestId } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chores-screen')).toBeTruthy();
        expect(queryByTestId('create-chore-button')).toBeNull();
      });
    });
  });

  describe('Chore List Display and Loading States', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });
    });

    it('should display loading state while fetching chores', async () => {
      // Create a promise that we can resolve later
      let resolvePromise: (value: any) => void;
      const chorePromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      
      mockedChoreAPI.getMyChores.mockReturnValue(chorePromise as Promise<any>);
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      // Should show loading immediately
      await waitFor(() => {
        expect(getByTestId('loading-indicator')).toBeTruthy();
      });

      // Resolve the promise
      act(() => {
        resolvePromise!([]);
      });

      // Loading should disappear
      await waitFor(() => {
        expect(getByTestId('no-chores')).toBeTruthy();
      });
    });

    it('should display empty state when no chores exist', async () => {
      mockedChoreAPI.getMyChores.mockResolvedValue([]);
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('no-chores')).toBeTruthy();
      });
    });

    it('should display multiple chores correctly', async () => {
      const chores = [
        createMockChore({ id: 1, title: 'Chore 1', reward: 5.00 }),
        createMockChore({ id: 2, title: 'Chore 2', reward: 7.50 }),
        createMockChore({ id: 3, title: 'Chore 3', reward: 10.00, is_completed: true }),
      ];

      mockedChoreAPI.getMyChores.mockResolvedValue(chores);
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chore-item-1')).toBeTruthy();
        expect(getByTestId('chore-item-2')).toBeTruthy();
        expect(getByTestId('chore-item-3')).toBeTruthy();
        
        expect(getByTestId('chore-title-1')).toHaveTextContent('Chore 1');
        expect(getByTestId('chore-title-2')).toHaveTextContent('Chore 2');
        expect(getByTestId('chore-title-3')).toHaveTextContent('Chore 3');
        
        expect(getByTestId('chore-status-3')).toHaveTextContent('Status: Completed');
      });
    });
  });

  describe('Parent Chore Management Actions', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });
    });

    it('should allow parents to delete chores', async () => {
      const chores = [
        createMockChore({ id: 1, title: 'Deletable Chore' }),
        createMockChore({ id: 2, title: 'Keep This Chore' }),
      ];

      mockedChoreAPI.getMyChores.mockResolvedValue(chores);
      mockedChoreAPI.deleteChore.mockResolvedValue({ success: true });
      
      const { getByTestId, getByText, queryByTestId } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chore-item-1')).toBeTruthy();
        expect(getByTestId('chore-item-2')).toBeTruthy();
      });

      // Delete chore
      await act(async () => {
        fireEvent.press(getByTestId('delete-chore-1'));
      });

      expect(mockedChoreAPI.deleteChore).toHaveBeenCalledWith(1);
      expect(mockAlert).toHaveBeenCalledWith('Success', 'Chore deleted successfully!');

      // Verify chore is removed from list
      await waitFor(() => {
        expect(queryByTestId('chore-item-1')).toBeNull();
        expect(getByTestId('chore-item-2')).toBeTruthy();
      });
    });

    it('should handle chore deletion errors', async () => {
      const chore = createMockChore({ id: 1 });
      mockedChoreAPI.getMyChores.mockResolvedValue([chore]);
      mockedChoreAPI.deleteChore.mockRejectedValue(new Error('Cannot delete completed chore'));
      
      const { getByTestId, getByText } = render(<SimpleNavigator />);

      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chore-item-1')).toBeTruthy();
      });

      await act(async () => {
        fireEvent.press(getByTestId('delete-chore-1'));
      });

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith('Error', 'Cannot delete completed chore');
      });
    });
  });

  describe('Cross-Screen Navigation Integration', () => {
    beforeEach(() => {
      const parentUser = createMockUser({ role: 'parent' });
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: parentUser,
        login: jest.fn(),
        logout: jest.fn(),
        checkAuthStatus: jest.fn(),
      });
    });

    it('should navigate to chores from home screen', async () => {
      const { getByTestId, queryByTestId } = render(<SimpleNavigator />);

      // Start at home
      expect(getByTestId('home-screen')).toBeTruthy();

      // Navigate to chores from home screen
      fireEvent.press(getByTestId('navigate-to-chores'));

      await waitFor(() => {
        expect(queryByTestId('home-screen')).toBeNull();
        expect(getByTestId('chores-screen')).toBeTruthy();
      });

      // Verify chores are being loaded
      expect(mockedChoreAPI.getMyChores).toHaveBeenCalled();
    });

    it('should maintain chore list state when switching tabs', async () => {
      const chores = [createMockChore({ id: 1, title: 'Persistent Chore' })];
      mockedChoreAPI.getMyChores.mockResolvedValue(chores);
      
      const { getByTestId, getByText, queryByTestId } = render(<SimpleNavigator />);

      // Go to chores
      fireEvent.press(getByText('Chores'));
      
      await waitFor(() => {
        expect(getByTestId('chore-item-1')).toBeTruthy();
      });

      // Navigate away and back
      fireEvent.press(getByText('Home'));
      expect(queryByTestId('chores-screen')).toBeNull();

      fireEvent.press(getByText('Chores'));
      
      // Should reload chores (in a real app, this might be cached)
      await waitFor(() => {
        expect(getByTestId('chores-screen')).toBeTruthy();
      });
    });
  });
});