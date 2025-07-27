import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { colors } from '../styles/colors';
import { typography } from '../styles/typography';

const RewardAmountModal = ({ visible, onClose, onConfirm, minAmount, maxAmount, defaultAmount }) => {
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (visible) {
      setAmount(defaultAmount?.toString() || minAmount?.toString() || '');
      setError('');
    }
  }, [visible, defaultAmount, minAmount]);

  const handleConfirm = () => {
    const numAmount = parseFloat(amount);
    
    if (isNaN(numAmount)) {
      setError('Please enter a valid number');
      return;
    }
    
    if (numAmount < minAmount || numAmount > maxAmount) {
      setError(`Amount must be between $${minAmount} and $${maxAmount}`);
      return;
    }
    
    onConfirm(numAmount);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.modalOverlay}
      >
        <View style={styles.modalContent}>
          <Text style={styles.title}>Select Reward Amount</Text>
          <Text style={styles.rangeText}>
            Choose amount between ${minAmount} and ${maxAmount}
          </Text>
          
          <View style={styles.inputContainer}>
            <Text style={styles.dollarSign}>$</Text>
            <TextInput
              style={styles.input}
              value={amount}
              onChangeText={(text) => {
                setAmount(text);
                setError('');
              }}
              keyboardType="decimal-pad"
              placeholder={minAmount?.toString()}
              autoFocus
            />
          </View>
          
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={onClose}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.button, styles.confirmButton]}
              onPress={handleConfirm}
            >
              <Text style={styles.confirmButtonText}>Approve</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 24,
    width: '90%',
    maxWidth: 400,
  },
  title: {
    ...typography.h3,
    color: colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  rangeText: {
    ...typography.body1,
    color: colors.textSecondary,
    marginBottom: 24,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  dollarSign: {
    ...typography.h3,
    color: colors.primary,
    marginRight: 8,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.divider,
    borderRadius: 8,
    padding: 12,
    fontSize: 18,
    backgroundColor: colors.background,
  },
  errorText: {
    ...typography.caption,
    color: colors.error,
    marginBottom: 16,
    textAlign: 'center',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: colors.background,
    marginRight: 8,
    borderWidth: 1,
    borderColor: colors.divider,
  },
  confirmButton: {
    backgroundColor: colors.primary,
    marginLeft: 8,
  },
  cancelButtonText: {
    ...typography.button,
    color: colors.text,
  },
  confirmButtonText: {
    ...typography.button,
    color: colors.white,
  },
});

export default RewardAmountModal;