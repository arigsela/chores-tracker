import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  TouchableOpacity,
  TextInput,
  Modal,
} from 'react-native';
import { usersAPI, ChildWithChores, ChildAllowanceSummary } from '../api/users';
import ChildCard from '../components/ChildCard';
import ChildDetailScreen from './ChildDetailScreen';
import CreateChildScreen from './CreateChildScreen';

export const ChildrenScreen: React.FC = () => {
  const [children, setChildren] = useState<ChildWithChores[]>([]);
  const [allowanceSummary, setAllowanceSummary] = useState<ChildAllowanceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedChild, setSelectedChild] = useState<ChildWithChores | null>(null);
  const [showCreateChild, setShowCreateChild] = useState(false);
  const [resetPasswordModal, setResetPasswordModal] = useState<{ visible: boolean; child: ChildWithChores | null }>({ visible: false, child: null });
  const [newPassword, setNewPassword] = useState('');
  const [resetPasswordError, setResetPasswordError] = useState('');
  const [resetPasswordSuccess, setResetPasswordSuccess] = useState(false);

  const fetchData = async () => {
    try {
      const [childrenData, summaryData] = await Promise.all([
        usersAPI.getMyChildren(),
        usersAPI.getAllowanceSummary(),
      ]);
      setChildren(childrenData);
      setAllowanceSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch children data:', error);
      Alert.alert('Error', 'Failed to load children data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getTotalOwed = () => {
    return allowanceSummary.reduce((total, child) => total + child.balance_due, 0);
  };

  const handleResetPassword = (child: ChildWithChores) => {
    setResetPasswordModal({ visible: true, child });
    setNewPassword('');
    setResetPasswordError('');
    setResetPasswordSuccess(false);
  };

  const performPasswordReset = async () => {
    if (!resetPasswordModal.child) return;
    
    // Validate password
    if (!newPassword || newPassword.length < 3) {
      setResetPasswordError('Password must be at least 3 characters long');
      return;
    }
    
    setResetPasswordError('');
    
    try {
      await usersAPI.resetChildPassword(resetPasswordModal.child.id, newPassword);
      setResetPasswordSuccess(true);
      
      // Auto-close modal after 2 seconds on success
      setTimeout(() => {
        setResetPasswordModal({ visible: false, child: null });
        setNewPassword('');
        setResetPasswordSuccess(false);
      }, 2000);
    } catch (error) {
      console.error('Reset password error:', error);
      setResetPasswordError('Failed to reset password. Please try again.');
    }
  };

  const closePasswordResetModal = () => {
    setResetPasswordModal({ visible: false, child: null });
    setNewPassword('');
    setResetPasswordError('');
    setResetPasswordSuccess(false);
  };

  const getTotalPending = () => {
    return children.reduce((total, child) => {
      const pending = child.chores?.filter(c => 
        (c.is_completed || c.completed_at || c.completion_date) && 
        !c.is_approved && !c.approved_at
      ).length || 0;
      return total + pending;
    }, 0);
  };

  // If creating a new child, show the create form
  if (showCreateChild) {
    return (
      <CreateChildScreen
        onSuccess={() => {
          setShowCreateChild(false);
          fetchData(); // Refresh to show new child
        }}
        onCancel={() => setShowCreateChild(false)}
      />
    );
  }

  // If a child is selected, show the detail view
  if (selectedChild) {
    return (
      <ChildDetailScreen
        child={selectedChild}
        onBack={() => {
          setSelectedChild(null);
          fetchData(); // Refresh data when returning
        }}
      />
    );
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Summary Section */}
      <View style={styles.summarySection}>
        <Text style={styles.sectionTitle}>Family Overview</Text>
        <View style={styles.summaryCards}>
          <View style={[styles.summaryCard, styles.totalOwedCard]}>
            <Text style={styles.summaryValue}>${getTotalOwed().toFixed(2)}</Text>
            <Text style={styles.summaryLabel}>Total Owed</Text>
          </View>
          <View style={[styles.summaryCard, styles.pendingCard]}>
            <Text style={styles.summaryValue}>{getTotalPending()}</Text>
            <Text style={styles.summaryLabel}>Pending Approvals</Text>
          </View>
        </View>
      </View>

      {/* Children List */}
      <View style={styles.childrenSection}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Children ({children.length})</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowCreateChild(true)}
          >
            <Text style={styles.addButtonText}>+ Add Child</Text>
          </TouchableOpacity>
        </View>
        {children.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No children added yet</Text>
            <Text style={styles.emptySubtext}>
              Add children to start managing their chores and allowances
            </Text>
          </View>
        ) : (
          children.map((child) => {
            const summary = allowanceSummary.find(s => s.id === child.id);
            const enrichedChild = {
              ...child,
              balance_due: summary?.balance_due || 0,
              completed_chores: summary?.completed_chores || 0,
            };
            return (
              <ChildCard
                key={child.id}
                child={enrichedChild}
                onPress={() => setSelectedChild(child)}
                onResetPassword={() => handleResetPassword(enrichedChild)}
              />
            );
          })
        )}
      </View>

      {/* Allowance Details */}
      {allowanceSummary.length > 0 && (
        <View style={styles.allowanceSection}>
          <Text style={styles.sectionTitle}>Allowance Details</Text>
          {allowanceSummary.map((summary) => (
            <View key={summary.id} style={styles.allowanceCard}>
              <View style={styles.allowanceHeader}>
                <Text style={styles.childName}>{summary.username}</Text>
                <Text style={styles.balanceDue}>${summary.balance_due.toFixed(2)}</Text>
              </View>
              <View style={styles.allowanceDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Completed Chores:</Text>
                  <Text style={styles.detailValue}>{summary.completed_chores}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Total Earned:</Text>
                  <Text style={styles.detailValue}>${summary.total_earned.toFixed(2)}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Adjustments:</Text>
                  <Text style={styles.detailValue}>${summary.total_adjustments.toFixed(2)}</Text>
                </View>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Paid Out:</Text>
                  <Text style={styles.detailValue}>-${summary.paid_out.toFixed(2)}</Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Password Reset Modal */}
      <Modal
        visible={resetPasswordModal.visible}
        animationType="slide"
        transparent={true}
        onRequestClose={closePasswordResetModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Reset Password</Text>
            {resetPasswordModal.child && (
              <Text style={styles.modalSubtitle}>for {resetPasswordModal.child.username}</Text>
            )}
            
            {resetPasswordSuccess ? (
              <View style={styles.successContainer}>
                <Text style={styles.successText}>✓ Password reset successfully!</Text>
              </View>
            ) : (
              <>
                <TextInput
                  style={styles.passwordInput}
                  placeholder="Enter new password (min 3 characters)"
                  value={newPassword}
                  onChangeText={setNewPassword}
                  secureTextEntry={true}
                  autoFocus={true}
                />
                
                {resetPasswordError ? (
                  <Text style={styles.errorText}>{resetPasswordError}</Text>
                ) : null}
                
                <View style={styles.modalButtons}>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.cancelButton]}
                    onPress={closePasswordResetModal}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={[styles.modalButton, styles.resetButton]}
                    onPress={performPasswordReset}
                  >
                    <Text style={styles.resetButtonText}>Reset Password</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  summarySection: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  addButton: {
    backgroundColor: '#2196f3',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  summaryCards: {
    flexDirection: 'row',
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  totalOwedCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#2196f3',
  },
  pendingCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#ff9800',
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
  },
  childrenSection: {
    padding: 16,
    paddingTop: 0,
  },
  emptyState: {
    backgroundColor: '#fff',
    padding: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  allowanceSection: {
    padding: 16,
    paddingTop: 0,
  },
  allowanceCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  allowanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  childName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  balanceDue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2196f3',
  },
  allowanceDetails: {
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailLabel: {
    fontSize: 14,
    color: '#666',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    width: '90%',
    maxWidth: 400,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 8,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  passwordInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 8,
  },
  errorText: {
    color: '#dc3545',
    fontSize: 14,
    marginBottom: 12,
    textAlign: 'center',
  },
  successContainer: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  successText: {
    color: '#28a745',
    fontSize: 18,
    fontWeight: '600',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginTop: 16,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#f0f0f0',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  resetButton: {
    backgroundColor: '#2196f3',
  },
  resetButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});