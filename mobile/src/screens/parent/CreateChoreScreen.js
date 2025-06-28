import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Switch,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Picker } from '@react-native-picker/picker';
import { choreService } from '../../services/choreService';
import { userService } from '../../services/userService';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const CreateChoreScreen = () => {
  const navigation = useNavigation();
  const [isLoading, setIsLoading] = useState(false);
  const [children, setChildren] = useState([]);
  const [showChildPicker, setShowChildPicker] = useState(false);
  
  // Form fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assigneeId, setAssigneeId] = useState('');
  const [recurrence, setRecurrence] = useState('once');
  const [rewardType, setRewardType] = useState('fixed');
  const [rewardAmount, setRewardAmount] = useState('');
  const [maxRewardAmount, setMaxRewardAmount] = useState('');

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    const result = await userService.getChildren();
    console.log('Loading children:', result);
    if (result.success) {
      setChildren(result.data);
      // Don't auto-select, let user choose
      // if (result.data.length > 0) {
      //   setAssigneeId(result.data[0].id.toString());
      // }
    }
  };

  const validateForm = () => {
    if (!title.trim()) {
      Alert.alert('Error', 'Please enter a chore title');
      return false;
    }
    if (!description.trim()) {
      Alert.alert('Error', 'Please enter a description');
      return false;
    }
    if (!assigneeId) {
      Alert.alert('Error', 'Please select who will do this chore');
      return false;
    }
    
    const amount = parseFloat(rewardAmount);
    if (isNaN(amount) || amount < 0) {
      Alert.alert('Error', 'Please enter a valid reward amount');
      return false;
    }
    
    if (rewardType === 'range') {
      const maxAmount = parseFloat(maxRewardAmount);
      if (isNaN(maxAmount) || maxAmount <= amount) {
        Alert.alert('Error', 'Maximum reward must be greater than minimum reward');
        return false;
      }
    }
    
    return true;
  };

  const handleCreate = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    
    const choreData = {
      title: title.trim(),
      description: description.trim(),
      assignee_id: parseInt(assigneeId),
      is_recurring: recurrence === 'recurring',
      is_range_reward: rewardType === 'range',
    };

    if (rewardType === 'range') {
      choreData.min_reward = parseFloat(rewardAmount);
      choreData.max_reward = parseFloat(maxRewardAmount);
    } else {
      choreData.reward = parseFloat(rewardAmount);
    }

    try {
      const result = await choreService.createChore(choreData);
      
      if (result.success) {
        Alert.alert(
          'Success',
          'Chore created successfully!',
          [
            {
              text: 'OK',
              onPress: () => {
                navigation.goBack();
                // TODO: Refresh parent home screen
              },
            },
          ]
        );
      } else {
        Alert.alert('Error', result.error);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to create chore');
    } finally {
      setIsLoading(false);
    }
  };

  const renderRewardInputs = () => {
    return (
      <View>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Reward Type</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[styles.toggleButton, rewardType === 'fixed' && styles.toggleActive]}
              onPress={() => setRewardType('fixed')}
            >
              <Text style={[styles.toggleText, rewardType === 'fixed' && styles.toggleTextActive]}>
                Fixed Amount
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleButton, rewardType === 'range' && styles.toggleActive]}
              onPress={() => setRewardType('range')}
            >
              <Text style={[styles.toggleText, rewardType === 'range' && styles.toggleTextActive]}>
                Range
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>
            {rewardType === 'fixed' ? 'Reward Amount' : 'Minimum Reward'}
          </Text>
          <View style={styles.currencyInput}>
            <Text style={styles.currencySymbol}>$</Text>
            <TextInput
              style={styles.currencyField}
              value={rewardAmount}
              onChangeText={setRewardAmount}
              placeholder="0.00"
              keyboardType="decimal-pad"
              placeholderTextColor={colors.textSecondary}
            />
          </View>
        </View>

        {rewardType === 'range' && (
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Maximum Reward</Text>
            <View style={styles.currencyInput}>
              <Text style={styles.currencySymbol}>$</Text>
              <TextInput
                style={styles.currencyField}
                value={maxRewardAmount}
                onChangeText={setMaxRewardAmount}
                placeholder="0.00"
                keyboardType="decimal-pad"
                placeholderTextColor={colors.textSecondary}
              />
            </View>
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.form}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Chore Title</Text>
              <TextInput
                style={styles.input}
                value={title}
                onChangeText={setTitle}
                placeholder="e.g., Take out the trash"
                placeholderTextColor={colors.textSecondary}
                maxLength={100}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Description</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={description}
                onChangeText={setDescription}
                placeholder="Describe what needs to be done..."
                placeholderTextColor={colors.textSecondary}
                multiline
                numberOfLines={3}
                maxLength={500}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Assign To</Text>
              {children.length === 0 ? (
                <Text style={styles.noChildrenText}>
                  No children added yet. Go to Family tab to add children.
                </Text>
              ) : Platform.OS === 'ios' ? (
                <>
                  <TouchableOpacity 
                    style={styles.pickerContainer}
                    onPress={() => setShowChildPicker(true)}
                  >
                    <View style={styles.pickerContent}>
                      <Text style={[styles.pickerText, !assigneeId && styles.pickerPlaceholder]}>
                        {assigneeId 
                          ? children.find(c => c.id.toString() === assigneeId)?.username || 'Select a child...'
                          : 'Select a child...'}
                      </Text>
                      <Icon name="arrow-drop-down" size={24} color={colors.textSecondary} />
                    </View>
                  </TouchableOpacity>
                  
                  <Modal
                    visible={showChildPicker}
                    transparent
                    animationType="slide"
                  >
                    <TouchableOpacity 
                      style={styles.modalOverlay}
                      onPress={() => setShowChildPicker(false)}
                    >
                      <View style={styles.pickerModal}>
                        <View style={styles.pickerHeader}>
                          <TouchableOpacity onPress={() => setShowChildPicker(false)}>
                            <Text style={styles.pickerDone}>Done</Text>
                          </TouchableOpacity>
                        </View>
                        <Picker
                          selectedValue={assigneeId}
                          onValueChange={(value) => {
                            setAssigneeId(value);
                          }}
                          style={styles.modalPicker}
                        >
                          <Picker.Item label="Select a child..." value="" />
                          {children.map((child) => (
                            <Picker.Item
                              key={child.id}
                              label={child.username}
                              value={child.id.toString()}
                            />
                          ))}
                        </Picker>
                      </View>
                    </TouchableOpacity>
                  </Modal>
                </>
              ) : (
                // Android picker
                <View style={styles.pickerContainer}>
                  <Picker
                    selectedValue={assigneeId}
                    onValueChange={setAssigneeId}
                    style={styles.androidPicker}
                  >
                    <Picker.Item label="Select a child..." value="" />
                    {children.map((child) => (
                      <Picker.Item
                        key={child.id}
                        label={child.username}
                        value={child.id.toString()}
                      />
                    ))}
                  </Picker>
                </View>
              )}
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>How Often?</Text>
              <View style={styles.recurrenceContainer}>
                {['once', 'daily', 'weekly', 'monthly'].map((option) => (
                  <TouchableOpacity
                    key={option}
                    style={[
                      styles.recurrenceButton,
                      recurrence === option && styles.recurrenceActive,
                    ]}
                    onPress={() => setRecurrence(option)}
                  >
                    <Text
                      style={[
                        styles.recurrenceText,
                        recurrence === option && styles.recurrenceTextActive,
                      ]}
                    >
                      {option.charAt(0).toUpperCase() + option.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {renderRewardInputs()}

            <TouchableOpacity
              style={[styles.createButton, isLoading && styles.buttonDisabled]}
              onPress={handleCreate}
              disabled={isLoading || children.length === 0}
            >
              {isLoading ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <Icon name="add-circle" size={24} color="white" />
                  <Text style={styles.createButtonText}>Create Chore</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  form: {
    padding: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    ...typography.label,
    color: colors.text,
    marginBottom: 8,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  pickerContainer: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    overflow: 'hidden',
  },
  picker: {
    height: 50,
  },
  noChildrenText: {
    ...typography.body,
    color: colors.textSecondary,
    fontStyle: 'italic',
    padding: 12,
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  recurrenceContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  recurrenceButton: {
    flex: 1,
    paddingVertical: 12,
    marginHorizontal: 4,
    backgroundColor: colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  recurrenceActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  recurrenceText: {
    ...typography.label,
    color: colors.text,
  },
  recurrenceTextActive: {
    color: 'white',
  },
  toggleContainer: {
    flexDirection: 'row',
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: colors.surface,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  toggleActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  toggleText: {
    ...typography.label,
    color: colors.text,
  },
  toggleTextActive: {
    color: 'white',
  },
  currencyInput: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingHorizontal: 16,
  },
  currencySymbol: {
    ...typography.body,
    color: colors.textSecondary,
    marginRight: 8,
  },
  currencyField: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  createButton: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
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
  buttonDisabled: {
    opacity: 0.6,
  },
  createButtonText: {
    ...typography.button,
    color: 'white',
    marginLeft: 8,
  },
  pickerContainer: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    overflow: 'hidden',
    position: 'relative',
  },
  pickerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    minHeight: 50,
  },
  pickerText: {
    ...typography.body,
    color: colors.text,
    flex: 1,
  },
  pickerPlaceholder: {
    color: colors.textSecondary,
  },
  picker: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    opacity: 0, // Make picker invisible but still tappable
  },
  pickerItem: {
    fontSize: 18,
  },
  noChildrenText: {
    ...typography.body,
    color: colors.textSecondary,
    fontStyle: 'italic',
    paddingVertical: 12,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  pickerModal: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 20,
  },
  pickerHeader: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  pickerDone: {
    ...typography.button,
    color: colors.primary,
  },
  modalPicker: {
    height: 200,
  },
  androidPicker: {
    height: 50,
    color: colors.text,
  },
});

export default CreateChoreScreen;