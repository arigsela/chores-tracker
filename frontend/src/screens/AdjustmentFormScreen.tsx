import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { adjustmentAPI, AdjustmentCreate } from '../api/adjustments';
import { usersAPI, ChildWithChores } from '../api/users';

interface AdjustmentFormScreenProps {
  childId?: number;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const AdjustmentFormScreen: React.FC<AdjustmentFormScreenProps> = ({
  childId,
  onSuccess,
  onCancel,
}) => {
  const [children, setChildren] = useState<ChildWithChores[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(childId || null);
  const [amount, setAmount] = useState('');
  const [isPositive, setIsPositive] = useState(true);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingChildren, setLoadingChildren] = useState(true);

  useEffect(() => {
    fetchChildren();
  }, []);

  const fetchChildren = async () => {
    try {
      const childrenData = await usersAPI.getMyChildren();
      setChildren(childrenData);
      
      // If only one child, auto-select them
      if (childrenData.length === 1 && !selectedChildId) {
        setSelectedChildId(childrenData[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch children:', error);
      Alert.alert('Error', 'Failed to load children');
    } finally {
      setLoadingChildren(false);
    }
  };

  const handleSubmit = async () => {
    // Validation
    if (!selectedChildId) {
      Alert.alert('Validation Error', 'Please select a child');
      return;
    }

    const amountValue = parseFloat(amount);
    if (isNaN(amountValue) || amountValue <= 0) {
      Alert.alert('Validation Error', 'Please enter a valid amount');
      return;
    }

    if (amountValue > 999.99) {
      Alert.alert('Validation Error', 'Amount cannot exceed $999.99');
      return;
    }

    if (!reason.trim() || reason.trim().length < 3) {
      Alert.alert('Validation Error', 'Please enter a reason (at least 3 characters)');
      return;
    }

    if (reason.length > 500) {
      Alert.alert('Validation Error', 'Reason cannot exceed 500 characters');
      return;
    }

    // Prepare adjustment data
    const adjustmentData: AdjustmentCreate = {
      child_id: selectedChildId,
      amount: isPositive ? amountValue : -amountValue,
      reason: reason.trim(),
    };

    setLoading(true);
    try {
      await adjustmentAPI.createAdjustment(adjustmentData);
      
      const childName = children.find(c => c.id === selectedChildId)?.username || 'Child';
      const adjustmentType = isPositive ? 'bonus' : 'deduction';
      
      Alert.alert(
        'Success',
        `${isPositive ? 'Bonus' : 'Deduction'} of $${amountValue.toFixed(2)} has been applied to ${childName}'s balance.`,
        [
          {
            text: 'OK',
            onPress: () => {
              // Reset form
              setAmount('');
              setReason('');
              setIsPositive(true);
              
              if (onSuccess) {
                onSuccess();
              }
            },
          },
        ]
      );
    } catch (error: any) {
      console.error('Failed to create adjustment:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create adjustment';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (amount || reason) {
      Alert.alert(
        'Discard Changes?',
        'Are you sure you want to discard your changes?',
        [
          { text: 'Keep Editing', style: 'cancel' },
          {
            text: 'Discard',
            style: 'destructive',
            onPress: () => {
              if (onCancel) {
                onCancel();
              }
            },
          },
        ]
      );
    } else {
      if (onCancel) {
        onCancel();
      }
    }
  };

  if (loadingChildren) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Create Adjustment</Text>
          <Text style={styles.subtitle}>
            Apply a bonus or deduction to a child's balance
          </Text>
        </View>

        {/* Child Selection */}
        {!childId && children.length > 1 && (
          <View style={styles.section}>
            <Text style={styles.label}>Select Child</Text>
            <View style={styles.childSelector}>
              {children.map((child) => (
                <TouchableOpacity
                  key={child.id}
                  style={[
                    styles.childOption,
                    selectedChildId === child.id && styles.childOptionSelected,
                  ]}
                  onPress={() => setSelectedChildId(child.id)}
                >
                  <Text
                    style={[
                      styles.childOptionText,
                      selectedChildId === child.id && styles.childOptionTextSelected,
                    ]}
                  >
                    {child.username}
                  </Text>
                  <Text style={styles.childBalance}>
                    Balance: ${child.balance?.toFixed(2) || '0.00'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Adjustment Type */}
        <View style={styles.section}>
          <Text style={styles.label}>Adjustment Type</Text>
          <View style={styles.typeSelector}>
            <TouchableOpacity
              style={[
                styles.typeButton,
                isPositive && styles.typeButtonPositive,
              ]}
              onPress={() => setIsPositive(true)}
            >
              <Text
                style={[
                  styles.typeButtonText,
                  isPositive && styles.typeButtonTextActive,
                ]}
              >
                ➕ Bonus
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.typeButton,
                !isPositive && styles.typeButtonNegative,
              ]}
              onPress={() => setIsPositive(false)}
            >
              <Text
                style={[
                  styles.typeButtonText,
                  !isPositive && styles.typeButtonTextActive,
                ]}
              >
                ➖ Deduction
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Amount Input */}
        <View style={styles.section}>
          <Text style={styles.label}>Amount</Text>
          <View style={styles.amountInput}>
            <Text style={[styles.dollarSign, !isPositive && styles.negative]}>
              {isPositive ? '+$' : '-$'}
            </Text>
            <TextInput
              style={styles.amountField}
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
              placeholder="0.00"
              placeholderTextColor="#999"
              maxLength={6}
            />
          </View>
          <Text style={styles.hint}>Maximum: $999.99</Text>
        </View>

        {/* Reason Input */}
        <View style={styles.section}>
          <Text style={styles.label}>Reason</Text>
          <TextInput
            style={styles.reasonInput}
            value={reason}
            onChangeText={setReason}
            placeholder={
              isPositive
                ? "e.g., Bonus for extra help with groceries"
                : "e.g., Deduction for not completing homework"
            }
            placeholderTextColor="#999"
            multiline
            numberOfLines={4}
            maxLength={500}
            textAlignVertical="top"
          />
          <Text style={styles.characterCount}>
            {reason.length}/500 characters
          </Text>
        </View>

        {/* Common Reasons (Quick Select) */}
        <View style={styles.section}>
          <Text style={styles.label}>Quick Select</Text>
          <View style={styles.quickReasons}>
            {isPositive ? (
              <>
                <TouchableOpacity
                  style={styles.quickReasonChip}
                  onPress={() => setReason('Bonus for extra help')}
                >
                  <Text style={styles.quickReasonText}>Extra help</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.quickReasonChip}
                  onPress={() => setReason('Good behavior bonus')}
                >
                  <Text style={styles.quickReasonText}>Good behavior</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.quickReasonChip}
                  onPress={() => setReason('Academic achievement bonus')}
                >
                  <Text style={styles.quickReasonText}>Good grades</Text>
                </TouchableOpacity>
              </>
            ) : (
              <>
                <TouchableOpacity
                  style={styles.quickReasonChip}
                  onPress={() => setReason('Penalty for misbehavior')}
                >
                  <Text style={styles.quickReasonText}>Misbehavior</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.quickReasonChip}
                  onPress={() => setReason('Deduction for incomplete chores')}
                >
                  <Text style={styles.quickReasonText}>Incomplete chores</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.quickReasonChip}
                  onPress={() => setReason('Lost item replacement')}
                >
                  <Text style={styles.quickReasonText}>Lost item</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.button, styles.cancelButton]}
            onPress={handleCancel}
            disabled={loading}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[
              styles.button,
              isPositive ? styles.submitButtonPositive : styles.submitButtonNegative,
              loading && styles.buttonDisabled,
            ]}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.submitButtonText}>
                Apply {isPositive ? 'Bonus' : 'Deduction'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 16,
    padding: 16,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#e0e0e0',
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  childSelector: {
    gap: 10,
  },
  childOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 8,
  },
  childOptionSelected: {
    borderColor: '#2196f3',
    backgroundColor: '#e3f2fd',
  },
  childOptionText: {
    fontSize: 16,
    color: '#333',
  },
  childOptionTextSelected: {
    fontWeight: 'bold',
    color: '#2196f3',
  },
  childBalance: {
    fontSize: 14,
    color: '#666',
  },
  typeSelector: {
    flexDirection: 'row',
    gap: 10,
  },
  typeButton: {
    flex: 1,
    paddingVertical: 12,
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 8,
    alignItems: 'center',
  },
  typeButtonPositive: {
    borderColor: '#4caf50',
    backgroundColor: '#e8f5e9',
  },
  typeButtonNegative: {
    borderColor: '#f44336',
    backgroundColor: '#ffebee',
  },
  typeButtonText: {
    fontSize: 16,
    color: '#666',
  },
  typeButtonTextActive: {
    fontWeight: 'bold',
  },
  amountInput: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
  },
  dollarSign: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4caf50',
    marginRight: 8,
  },
  negative: {
    color: '#f44336',
  },
  amountField: {
    flex: 1,
    fontSize: 24,
    paddingVertical: 12,
    color: '#333',
  },
  hint: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  reasonInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 100,
    backgroundColor: '#fff',
    color: '#333',
  },
  characterCount: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
    textAlign: 'right',
  },
  quickReasons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  quickReasonChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 16,
  },
  quickReasonText: {
    fontSize: 14,
    color: '#333',
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    padding: 16,
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#666',
    fontWeight: '600',
  },
  submitButtonPositive: {
    backgroundColor: '#4caf50',
  },
  submitButtonNegative: {
    backgroundColor: '#f44336',
  },
  submitButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: 'bold',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
});

export default AdjustmentFormScreen;