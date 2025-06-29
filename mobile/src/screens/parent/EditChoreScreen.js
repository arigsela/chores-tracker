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
import { useNavigation, useRoute } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Picker } from '@react-native-picker/picker';
import { choreService } from '../../services/choreService';
import { userService } from '../../services/userService';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';

const EditChoreScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { chore } = route.params;
  
  const [isLoading, setIsLoading] = useState(false);
  const [children, setChildren] = useState([]);
  const [showChildPicker, setShowChildPicker] = useState(false);
  
  // Form fields - initialize with chore data
  const [title, setTitle] = useState(chore.title);
  const [description, setDescription] = useState(chore.description || '');
  const [assigneeId, setAssigneeId] = useState(chore.assignee_id?.toString() || '');
  const [recurrence, setRecurrence] = useState(chore.recurrence);
  const [rewardType, setRewardType] = useState(chore.reward_type);
  const [rewardAmount, setRewardAmount] = useState(chore.reward_amount?.toString() || '');
  const [maxRewardAmount, setMaxRewardAmount] = useState(chore.max_reward_amount?.toString() || '');
  const [cooldownDays, setCooldownDays] = useState(chore.cooldown_days?.toString() || '7');

  useEffect(() => {
    loadChildren();
  }, []);

  const loadChildren = async () => {
    const result = await userService.getChildren();
    if (result.success) {
      setChildren(result.data);
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

  const handleUpdate = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    
    const choreData = {
      title: title.trim(),
      description: description.trim(),
      assignee_id: parseInt(assigneeId),
      is_recurring: recurrence === 'recurring',
      is_range_reward: rewardType === 'range',
    };

    if (recurrence === 'recurring') {
      choreData.cooldown_days = parseInt(cooldownDays) || 7;
    }

    if (rewardType === 'range') {
      choreData.min_reward = parseFloat(rewardAmount);
      choreData.max_reward = parseFloat(maxRewardAmount);
    } else {
      choreData.reward = parseFloat(rewardAmount);
    }

    try {
      const result = await choreService.updateChore(chore.id, choreData);
      
      if (result.success) {
        Alert.alert(
          'Success',
          'Chore updated successfully!',
          [
            {
              text: 'OK',
              onPress: () => navigation.goBack(),
            },
          ]
        );
      } else {
        Alert.alert('Error', result.error || 'Failed to update chore');
      }
    } catch (error) {
      Alert.alert('Error', 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisable = async () => {
    Alert.alert(
      'Disable Chore',
      'Are you sure you want to disable this chore? It will no longer be visible to children.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Disable',
          style: 'destructive',
          onPress: async () => {
            setIsLoading(true);
            try {
              const result = await choreService.disableChore(chore.id);
              if (result.success) {
                Alert.alert(
                  'Success',
                  'Chore disabled successfully!',
                  [
                    {
                      text: 'OK',
                      onPress: () => navigation.goBack(),
                    },
                  ]
                );
              } else {
                Alert.alert('Error', result.error || 'Failed to disable chore');
              }
            } catch (error) {
              Alert.alert('Error', 'An unexpected error occurred');
            } finally {
              setIsLoading(false);
            }
          },
        },
      ]
    );
  };

  const renderRecurrenceToggle = () => (
    <View style={styles.toggleContainer}>
      <TouchableOpacity
        style={[
          styles.toggleButton,
          { borderTopLeftRadius: 8, borderBottomLeftRadius: 8 },
          recurrence === 'once' && styles.toggleActive,
        ]}
        onPress={() => setRecurrence('once')}
      >
        <Text style={[styles.toggleText, recurrence === 'once' && styles.toggleTextActive]}>
          One Time
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[
          styles.toggleButton,
          { borderTopRightRadius: 8, borderBottomRightRadius: 8 },
          recurrence === 'recurring' && styles.toggleActive,
        ]}
        onPress={() => setRecurrence('recurring')}
      >
        <Text style={[styles.toggleText, recurrence === 'recurring' && styles.toggleTextActive]}>
          Recurring
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderRewardSection = () => {
    return (
      <View>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Reward Type</Text>
          <View style={styles.toggleContainer}>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                { borderTopLeftRadius: 8, borderBottomLeftRadius: 8 },
                rewardType === 'fixed' && styles.toggleActive,
              ]}
              onPress={() => setRewardType('fixed')}
            >
              <Text style={[styles.toggleText, rewardType === 'fixed' && styles.toggleTextActive]}>
                Fixed Amount
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.toggleButton,
                { borderTopRightRadius: 8, borderBottomRightRadius: 8 },
                rewardType === 'range' && styles.toggleActive,
              ]}
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
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Edit Chore</Text>
        <View style={{ width: 24 }} />
      </View>

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
              {renderRecurrenceToggle()}
            </View>

            {recurrence === 'recurring' && (
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Cooldown Period</Text>
                <View style={styles.cooldownContainer}>
                  <TouchableOpacity
                    style={[styles.cooldownOption, cooldownDays === '1' && styles.cooldownActive]}
                    onPress={() => setCooldownDays('1')}
                  >
                    <Text style={[styles.cooldownText, cooldownDays === '1' && styles.cooldownTextActive]}>
                      Daily
                    </Text>
                    <Text style={[styles.cooldownSubtext, cooldownDays === '1' && styles.cooldownTextActive]}>
                      1 day
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.cooldownOption, cooldownDays === '7' && styles.cooldownActive]}
                    onPress={() => setCooldownDays('7')}
                  >
                    <Text style={[styles.cooldownText, cooldownDays === '7' && styles.cooldownTextActive]}>
                      Weekly
                    </Text>
                    <Text style={[styles.cooldownSubtext, cooldownDays === '7' && styles.cooldownTextActive]}>
                      7 days
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.cooldownOption, cooldownDays === '30' && styles.cooldownActive]}
                    onPress={() => setCooldownDays('30')}
                  >
                    <Text style={[styles.cooldownText, cooldownDays === '30' && styles.cooldownTextActive]}>
                      Monthly
                    </Text>
                    <Text style={[styles.cooldownSubtext, cooldownDays === '30' && styles.cooldownTextActive]}>
                      30 days
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}

            {renderRewardSection()}

            <TouchableOpacity
              style={[styles.updateButton, isLoading && styles.buttonDisabled]}
              onPress={handleUpdate}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="white" />
              ) : (
                <>
                  <Icon name="save" size={20} color="white" />
                  <Text style={styles.updateButtonText}>Update Chore</Text>
                </>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.disableButton, isLoading && styles.buttonDisabled]}
              onPress={handleDisable}
              disabled={isLoading || chore.status === 'disabled'}
            >
              <Icon name="block" size={20} color="white" />
              <Text style={styles.disableButtonText}>Disable Chore</Text>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.text,
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
    height: 80,
    textAlignVertical: 'top',
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
  updateButton: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    borderRadius: 8,
    paddingVertical: 16,
    marginTop: 20,
    alignItems: 'center',
    justifyContent: 'center',
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
  updateButtonText: {
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
    opacity: 0,
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
  cooldownContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  cooldownOption: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    backgroundColor: colors.surface,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    marginHorizontal: 4,
    borderRadius: 8,
  },
  cooldownActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  cooldownText: {
    ...typography.label,
    color: colors.text,
    fontWeight: '600',
  },
  cooldownTextActive: {
    color: 'white',
  },
  cooldownSubtext: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: 2,
  },
  disableButton: {
    flexDirection: 'row',
    backgroundColor: colors.error,
    borderRadius: 8,
    paddingVertical: 16,
    marginTop: 12,
    alignItems: 'center',
    justifyContent: 'center',
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
  disableButtonText: {
    ...typography.button,
    color: 'white',
    marginLeft: 8,
  },
});

export default EditChoreScreen;