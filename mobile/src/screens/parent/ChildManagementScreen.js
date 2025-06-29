import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useAuth } from '../../store/authContext';
import { userService } from '../../services/userService';
import { choreService } from '../../services/choreService';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const ChildManagementScreen = () => {
  const { user } = useAuth();
  const [children, setChildren] = useState([]);
  const [childStats, setChildStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [selectedChild, setSelectedChild] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  
  // Form fields for new child
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Form fields for edit
  const [editUsername, setEditUsername] = useState('');
  
  // Form fields for reset password
  const [resetPassword, setResetPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');

  const fetchChildren = useCallback(async () => {
    try {
      const result = await userService.getChildren();
      if (result.success) {
        setChildren(result.data);
        // Fetch stats for each child
        await fetchChildrenStats(result.data);
      }
    } catch (error) {
      console.error('Error fetching children:', error);
      Alert.alert('Error', 'Failed to load children');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const fetchChildrenStats = async (childrenList) => {
    const stats = {};
    
    for (const child of childrenList) {
      try {
        // Get all chores for the child
        const choresResult = await choreService.getAllChores();
        if (choresResult.success) {
          const childChores = choresResult.data.filter(
            chore => chore.assignee_id === child.id
          );
          
          const completed = childChores.filter(c => c.status === 'approved').length;
          const totalEarned = childChores
            .filter(c => c.status === 'approved')
            .reduce((sum, c) => sum + (c.approved_reward_amount || 0), 0);
          
          stats[child.id] = {
            totalChores: childChores.length,
            completedChores: completed,
            totalEarned: totalEarned,
            pendingChores: childChores.filter(c => c.status === 'pending').length,
          };
        }
      } catch (error) {
        console.error(`Error fetching stats for child ${child.id}:`, error);
        stats[child.id] = {
          totalChores: 0,
          completedChores: 0,
          totalEarned: 0,
          pendingChores: 0,
        };
      }
    }
    
    setChildStats(stats);
  };

  useEffect(() => {
    fetchChildren();
  }, [fetchChildren]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchChildren();
  }, [fetchChildren]);

  const validateForm = () => {
    if (!newUsername.trim()) {
      Alert.alert('Error', 'Please enter a username');
      return false;
    }
    if (newUsername.length < 3) {
      Alert.alert('Error', 'Username must be at least 3 characters');
      return false;
    }
    if (!newPassword) {
      Alert.alert('Error', 'Please enter a password');
      return false;
    }
    if (newPassword.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters');
      return false;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return false;
    }
    return true;
  };

  const handleCreateChild = async () => {
    if (!validateForm()) return;

    setIsCreating(true);
    try {
      const result = await userService.createChild({
        username: newUsername.trim(),
        password: newPassword,
      });

      if (result.success) {
        Alert.alert('Success', 'Child account created successfully!');
        setShowAddModal(false);
        resetForm();
        fetchChildren();
      } else {
        Alert.alert('Error', result.error || 'Failed to create child account');
      }
    } catch (error) {
      console.error('Error creating child:', error);
      Alert.alert('Error', 'Failed to create child account');
    } finally {
      setIsCreating(false);
    }
  };

  const resetForm = () => {
    setNewUsername('');
    setNewPassword('');
    setConfirmPassword('');
    setEditUsername('');
    setResetPassword('');
    setResetConfirmPassword('');
  };

  const handleEditChild = (child) => {
    setSelectedChild(child);
    setEditUsername(child.username);
    setShowEditModal(true);
  };

  const handleUpdateUsername = async () => {
    if (!editUsername.trim()) {
      Alert.alert('Error', 'Please enter a username');
      return;
    }

    Alert.alert(
      'Update Not Available',
      'Username editing is not yet supported by the backend API. This feature will be available in a future update.',
      [{ text: 'OK' }]
    );
    setShowEditModal(false);
  };

  const handleResetPassword = (child) => {
    setSelectedChild(child);
    setResetPassword('');
    setResetConfirmPassword('');
    setShowResetPasswordModal(true);
  };

  const handleUpdatePassword = async () => {
    if (!resetPassword) {
      Alert.alert('Error', 'Please enter a new password');
      return;
    }
    if (resetPassword.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters');
      return;
    }
    if (resetPassword !== resetConfirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    setIsUpdating(true);
    try {
      // For now, show that the feature is pending
      Alert.alert(
        'Success',
        `Password reset functionality will be implemented soon. For now, please remember the new password would be: ${resetPassword}`,
        [{ text: 'OK', onPress: () => setShowResetPasswordModal(false) }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to reset password');
    } finally {
      setIsUpdating(false);
    }
  };

  const renderChildCard = ({ item }) => {
    const stats = childStats[item.id] || {
      totalChores: 0,
      completedChores: 0,
      totalEarned: 0,
      pendingChores: 0,
    };

    return (
      <TouchableOpacity style={styles.childCard} activeOpacity={0.7}>
        <View style={styles.childHeader}>
          <View style={styles.avatarContainer}>
            <Icon name="person" size={40} color={colors.primary} />
          </View>
          <View style={styles.childInfo}>
            <Text style={styles.childName}>{item.username}</Text>
            <Text style={styles.childSubtext}>
              {stats.pendingChores > 0 
                ? `${stats.pendingChores} chores pending approval`
                : 'No pending chores'}
            </Text>
          </View>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{stats.totalChores}</Text>
            <Text style={styles.statLabel}>Total</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{stats.completedChores}</Text>
            <Text style={styles.statLabel}>Done</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>${stats.totalEarned.toFixed(2)}</Text>
            <Text style={styles.statLabel}>Earned</Text>
          </View>
        </View>

        <View style={styles.cardActions}>
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => handleEditChild(item)}
          >
            <Icon name="edit" size={20} color={colors.primary} />
            <Text style={styles.actionText}>Edit</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => handleResetPassword(item)}
          >
            <Icon name="lock-reset" size={20} color={colors.primary} />
            <Text style={styles.actionText}>Reset Password</Text>
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  const renderAddModal = () => (
    <Modal
      visible={showAddModal}
      transparent
      animationType="slide"
      onRequestClose={() => setShowAddModal(false)}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.modalContainer}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowAddModal(false)}
        >
          <View style={styles.modalContent} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add New Child</Text>
              <TouchableOpacity onPress={() => setShowAddModal(false)}>
                <Icon name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>

            <View style={styles.modalForm}>
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Username</Text>
                <TextInput
                  style={styles.input}
                  value={newUsername}
                  onChangeText={setNewUsername}
                  placeholder="Enter username"
                  placeholderTextColor={colors.textSecondary}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Password</Text>
                <TextInput
                  style={styles.input}
                  value={newPassword}
                  onChangeText={setNewPassword}
                  placeholder="Enter password"
                  placeholderTextColor={colors.textSecondary}
                  secureTextEntry
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Confirm Password</Text>
                <TextInput
                  style={styles.input}
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  placeholder="Confirm password"
                  placeholderTextColor={colors.textSecondary}
                  secureTextEntry
                />
              </View>

              <TouchableOpacity
                style={[styles.createButton, isCreating && styles.buttonDisabled]}
                onPress={handleCreateChild}
                disabled={isCreating}
              >
                {isCreating ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <>
                    <Icon name="person-add" size={20} color="white" />
                    <Text style={styles.createButtonText}>Create Account</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </KeyboardAvoidingView>
    </Modal>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="people" size={80} color={colors.textSecondary} />
      <Text style={styles.emptyTitle}>No Children Yet</Text>
      <Text style={styles.emptySubtitle}>
        Add your first child to start assigning chores
      </Text>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        data={children}
        renderItem={renderChildCard}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[colors.primary]}
          />
        }
        ListEmptyComponent={renderEmptyState}
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setShowAddModal(true)}
      >
        <Icon name="add" size={24} color="white" />
      </TouchableOpacity>

      {renderAddModal()}
      {renderEditModal()}
      {renderResetPasswordModal()}
    </SafeAreaView>
  );

  function renderEditModal() {
    return (
  <Modal
    visible={showEditModal}
    transparent
    animationType="slide"
    onRequestClose={() => setShowEditModal(false)}
  >
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.modalContainer}
    >
      <TouchableOpacity
        style={styles.modalOverlay}
        activeOpacity={1}
        onPress={() => setShowEditModal(false)}
      >
        <View style={styles.modalContent} onStartShouldSetResponder={() => true}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Edit Child</Text>
            <TouchableOpacity onPress={() => setShowEditModal(false)}>
              <Icon name="close" size={24} color={colors.text} />
            </TouchableOpacity>
          </View>

          <View style={styles.modalForm}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Username</Text>
              <TextInput
                style={styles.input}
                value={editUsername}
                onChangeText={setEditUsername}
                placeholder="Enter new username"
                placeholderTextColor={colors.textSecondary}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <TouchableOpacity
              style={styles.createButton}
              onPress={handleUpdateUsername}
            >
              <Icon name="save" size={20} color="white" />
              <Text style={styles.createButtonText}>Update Username</Text>
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    </KeyboardAvoidingView>
  </Modal>
    );
  }

  function renderResetPasswordModal() {
    return (
  <Modal
    visible={showResetPasswordModal}
    transparent
    animationType="slide"
    onRequestClose={() => setShowResetPasswordModal(false)}
  >
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.modalContainer}
    >
      <TouchableOpacity
        style={styles.modalOverlay}
        activeOpacity={1}
        onPress={() => setShowResetPasswordModal(false)}
      >
        <View style={styles.modalContent} onStartShouldSetResponder={() => true}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              Reset Password for {selectedChild?.username}
            </Text>
            <TouchableOpacity onPress={() => setShowResetPasswordModal(false)}>
              <Icon name="close" size={24} color={colors.text} />
            </TouchableOpacity>
          </View>

          <View style={styles.modalForm}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>New Password</Text>
              <TextInput
                style={styles.input}
                value={resetPassword}
                onChangeText={setResetPassword}
                placeholder="Enter new password"
                placeholderTextColor={colors.textSecondary}
                secureTextEntry
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Confirm New Password</Text>
              <TextInput
                style={styles.input}
                value={resetConfirmPassword}
                onChangeText={setResetConfirmPassword}
                placeholder="Confirm new password"
                placeholderTextColor={colors.textSecondary}
                secureTextEntry
              />
            </View>

            <TouchableOpacity
              style={[styles.createButton, isUpdating && styles.buttonDisabled]}
              onPress={handleUpdatePassword}
              disabled={isUpdating}
            >
              {isUpdating ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <Icon name="lock-reset" size={20} color="white" />
                  <Text style={styles.createButtonText}>Reset Password</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    </KeyboardAvoidingView>
  </Modal>
    );
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    flexGrow: 1,
    paddingBottom: 80,
  },
  childCard: {
    backgroundColor: colors.surface,
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    padding: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 3,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  childHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  childInfo: {
    flex: 1,
  },
  childName: {
    ...typography.h3,
    color: colors.text,
    marginBottom: 4,
  },
  childSubtext: {
    ...typography.body2,
    color: colors.textSecondary,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: colors.border,
  },
  statBox: {
    alignItems: 'center',
  },
  statNumber: {
    ...typography.h2,
    color: colors.primary,
  },
  statLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 4,
  },
  cardActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  actionText: {
    ...typography.body2,
    color: colors.primary,
    marginLeft: 8,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    ...typography.h3,
    color: colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    ...typography.body1,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 4,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  modalContainer: {
    flex: 1,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    paddingHorizontal: 20,
    paddingBottom: Platform.OS === 'ios' ? 40 : 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    ...typography.h2,
    color: colors.text,
  },
  modalForm: {
    paddingBottom: 20,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    ...typography.label,
    color: colors.text,
    marginBottom: 8,
  },
  input: {
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  createButton: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingVertical: 16,
    marginTop: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  createButtonText: {
    ...typography.button,
    color: 'white',
    marginLeft: 8,
  },
});

export default ChildManagementScreen;