import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';

interface RejectChoreModalProps {
  visible: boolean;
  choreTitle: string;
  childName: string;
  onReject: (rejectionReason: string) => void;
  onCancel: () => void;
}

export const RejectChoreModal: React.FC<RejectChoreModalProps> = ({
  visible,
  choreTitle,
  childName,
  onReject,
  onCancel,
}) => {
  const [rejectionReason, setRejectionReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      return; // Don't submit empty reason
    }
    
    setSubmitting(true);
    onReject(rejectionReason.trim());
    
    // Reset state after submission
    setRejectionReason('');
    setSubmitting(false);
  };

  const handleCancel = () => {
    setRejectionReason('');
    setSubmitting(false);
    onCancel();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={handleCancel}
    >
      <KeyboardAvoidingView
        style={styles.overlay}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.modalContainer}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <View style={styles.modal}>
              <View style={styles.header}>
                <Text style={styles.title}>Reject Chore</Text>
                <Text style={styles.subtitle}>
                  "{choreTitle}" by {childName}
                </Text>
              </View>

              <View style={styles.body}>
                <Text style={styles.label}>Reason for rejection:</Text>
                <Text style={styles.helpText}>
                  Let {childName} know what needs to be improved so they can complete the chore properly.
                </Text>
                
                <TextInput
                  style={styles.textInput}
                  value={rejectionReason}
                  onChangeText={setRejectionReason}
                  placeholder="e.g., Please clean more thoroughly and organize items properly"
                  placeholderTextColor="#999"
                  multiline
                  numberOfLines={4}
                  maxLength={500}
                  autoFocus
                  textAlignVertical="top"
                />
                
                <Text style={styles.characterCount}>
                  {rejectionReason.length}/500 characters
                </Text>
              </View>

              <View style={styles.footer}>
                <TouchableOpacity
                  style={[styles.button, styles.cancelButton]}
                  onPress={handleCancel}
                  disabled={submitting}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[
                    styles.button,
                    styles.rejectButton,
                    (!rejectionReason.trim() || submitting) && styles.disabledButton,
                  ]}
                  onPress={handleReject}
                  disabled={!rejectionReason.trim() || submitting}
                >
                  <Text style={[
                    styles.rejectButtonText,
                    (!rejectionReason.trim() || submitting) && styles.disabledButtonText,
                  ]}>
                    {submitting ? 'Rejecting...' : 'Reject Chore'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  modal: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 0,
    minWidth: 320,
    maxWidth: 400,
    maxHeight: '80%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 16,
  },
  header: {
    padding: 24,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  body: {
    padding: 24,
    paddingTop: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  helpText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
    lineHeight: 20,
  },
  textInput: {
    backgroundColor: '#f8f8f8',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#333',
    minHeight: 100,
    marginBottom: 8,
  },
  characterCount: {
    fontSize: 12,
    color: '#999',
    textAlign: 'right',
  },
  footer: {
    flexDirection: 'row',
    padding: 24,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    marginRight: 12,
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  rejectButton: {
    backgroundColor: '#f44336',
  },
  rejectButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  disabledButton: {
    backgroundColor: '#f5f5f5',
    borderColor: '#e0e0e0',
  },
  disabledButtonText: {
    color: '#ccc',
  },
});