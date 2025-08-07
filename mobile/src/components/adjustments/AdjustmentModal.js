import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Animated,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';
import { adjustmentService } from '../../services/adjustmentService';
import { useToast } from '../../contexts/ToastContext';

const PRESET_AMOUNTS = [5, 10, 20, -5, -10];
const MAX_REASON_LENGTH = 500;

const AdjustmentModal = ({ visible, onClose, child, onSuccess }) => {
  const { showSuccess, showError } = useToast();
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Animations
  const slideAnim = useRef(new Animated.Value(300)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  
  React.useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible]);
  
  const handleClose = () => {
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: 300,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onClose();
      // Reset form
      setAmount('');
      setReason('');
    });
  };
  
  const handlePresetAmount = (preset) => {
    setAmount(preset.toString());
  };
  
  const handleSubmit = async () => {
    // Validation
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount === 0) {
      showError('Please enter a valid amount');
      return;
    }
    
    if (numAmount < -999.99 || numAmount > 999.99) {
      showError('Amount must be between -$999.99 and $999.99');
      return;
    }
    
    if (reason.trim().length < 3) {
      showError('Please provide a reason (at least 3 characters)');
      return;
    }
    
    setIsSubmitting(true);
    
    const result = await adjustmentService.createAdjustment(
      child.id,
      numAmount,
      reason
    );
    
    if (result.success) {
      showSuccess('Balance adjusted successfully');
      onSuccess(numAmount);
      handleClose();
    } else {
      showError(result.error);
    }
    
    setIsSubmitting(false);
  };
  
  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={handleClose}
    >
      <Animated.View style={[styles.overlay, { opacity: fadeAnim }]}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <Animated.View
            style={[
              styles.container,
              { transform: [{ translateY: slideAnim }] },
            ]}
          >
            <View style={styles.header}>
              <Text style={styles.title}>Adjust Balance</Text>
              <TouchableOpacity onPress={handleClose}>
                <Icon name="close" size={24} color={colors.text} />
              </TouchableOpacity>
            </View>
            
            <Text style={styles.childName}>
              For: {child?.username}
            </Text>
            
            <View style={styles.amountSection}>
              <Text style={styles.label}>Amount</Text>
              <View style={styles.amountInputRow}>
                <TextInput
                  style={styles.amountInput}
                  value={amount}
                  onChangeText={setAmount}
                  keyboardType="numeric"
                  placeholder="0.00"
                  placeholderTextColor={colors.textSecondary}
                />
                <Text style={styles.dollarSign}>$</Text>
              </View>
              
              <View style={styles.presetRow}>
                {PRESET_AMOUNTS.map((preset) => (
                  <TouchableOpacity
                    key={preset}
                    style={[
                      styles.presetButton,
                      preset < 0 && styles.negativePreset,
                    ]}
                    onPress={() => handlePresetAmount(preset)}
                  >
                    <Text
                      style={[
                        styles.presetText,
                        preset < 0 && styles.negativeText,
                      ]}
                    >
                      {preset > 0 ? '+' : ''}${Math.abs(preset)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            
            <View style={styles.reasonSection}>
              <View style={styles.reasonHeader}>
                <Text style={styles.label}>Reason</Text>
                <Text style={styles.charCount}>
                  {reason.length}/{MAX_REASON_LENGTH}
                </Text>
              </View>
              <TextInput
                style={styles.reasonInput}
                value={reason}
                onChangeText={setReason}
                placeholder="Enter reason for adjustment..."
                placeholderTextColor={colors.textSecondary}
                multiline
                maxLength={MAX_REASON_LENGTH}
              />
            </View>
            
            <View style={styles.actions}>
              <TouchableOpacity
                style={[styles.button, styles.cancelButton]}
                onPress={handleClose}
                disabled={isSubmitting}
              >
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.button, styles.submitButton]}
                onPress={handleSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Text style={styles.submitText}>Adjust Balance</Text>
                )}
              </TouchableOpacity>
            </View>
          </Animated.View>
        </KeyboardAvoidingView>
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  keyboardView: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: Platform.OS === 'ios' ? 40 : 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    ...typography.h3,
    color: colors.text,
  },
  childName: {
    ...typography.body1,
    color: colors.primary,
    marginBottom: 20,
  },
  amountSection: {
    marginBottom: 20,
  },
  label: {
    ...typography.label,
    color: colors.text,
    marginBottom: 8,
  },
  amountInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  amountInput: {
    flex: 1,
    ...typography.h2,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.divider,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    textAlign: 'right',
  },
  dollarSign: {
    ...typography.h2,
    color: colors.textSecondary,
    marginLeft: 8,
  },
  presetRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  presetButton: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  negativePreset: {
    backgroundColor: colors.errorLight,
  },
  presetText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
  },
  negativeText: {
    color: colors.error,
  },
  reasonSection: {
    marginBottom: 24,
  },
  reasonHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  charCount: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  reasonInput: {
    ...typography.body1,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.divider,
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: colors.background,
    marginRight: 8,
  },
  submitButton: {
    backgroundColor: colors.primary,
    marginLeft: 8,
  },
  cancelText: {
    ...typography.button,
    color: colors.text,
  },
  submitText: {
    ...typography.button,
    color: colors.white,
  },
});

export default AdjustmentModal;