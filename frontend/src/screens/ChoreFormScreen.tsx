import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Switch,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Chore, choreAPI } from '../api/chores';
import { usersAPI, ChildWithChores } from '../api/users';

interface ChoreFormScreenProps {
  chore?: Chore; // If provided, we're editing; otherwise creating
  onSave: (chore: Chore) => void;
  onCancel: () => void;
}

const ChoreFormScreen: React.FC<ChoreFormScreenProps> = ({ chore, onSave, onCancel }) => {
  const isEditing = !!chore;
  
  // Form state
  const [title, setTitle] = useState(chore?.title || '');
  const [description, setDescription] = useState(chore?.description || '');
  const [isRangeReward, setIsRangeReward] = useState(chore?.is_range_reward || false);
  const [fixedReward, setFixedReward] = useState(chore?.reward?.toString() || '');
  const [minReward, setMinReward] = useState(chore?.min_reward?.toString() || '');
  const [maxReward, setMaxReward] = useState(chore?.max_reward?.toString() || '');
  const [isRecurring, setIsRecurring] = useState(chore?.is_recurring || false);
  const [cooldownDays, setCooldownDays] = useState(chore?.cooldown_days?.toString() || '');
  const [assignedToId, setAssignedToId] = useState<number | null>(
    chore?.assignee_id || chore?.assigned_to_id || null
  );
  
  // UI state
  const [children, setChildren] = useState<ChildWithChores[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingChildren, setLoadingChildren] = useState(true);

  useEffect(() => {
    fetchChildren();
  }, []);

  const fetchChildren = async () => {
    try {
      const childrenData = await usersAPI.getMyChildren();
      setChildren(childrenData);
    } catch (error) {
      console.error('Failed to fetch children:', error);
      Alert.alert('Error', 'Failed to load children list');
    } finally {
      setLoadingChildren(false);
    }
  };

  const validateForm = (): boolean => {
    if (!title.trim()) {
      Alert.alert('Validation Error', 'Title is required');
      return false;
    }

    if (isRangeReward) {
      const min = parseFloat(minReward);
      const max = parseFloat(maxReward);
      
      if (isNaN(min) || isNaN(max)) {
        Alert.alert('Validation Error', 'Please enter valid reward amounts');
        return false;
      }
      
      if (min >= max) {
        Alert.alert('Validation Error', 'Minimum reward must be less than maximum');
        return false;
      }
      
      if (min < 0 || max < 0) {
        Alert.alert('Validation Error', 'Reward amounts must be positive');
        return false;
      }
    } else {
      const reward = parseFloat(fixedReward);
      if (isNaN(reward) || reward < 0) {
        Alert.alert('Validation Error', 'Please enter a valid reward amount');
        return false;
      }
    }

    if (isRecurring) {
      const cooldown = parseInt(cooldownDays);
      if (isNaN(cooldown) || cooldown < 1) {
        Alert.alert('Validation Error', 'Cooldown days must be at least 1');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    const choreData: any = {
      title: title.trim(),
      description: description.trim() || undefined,
      is_range_reward: isRangeReward,
      is_recurring: isRecurring,
    };

    if (isRangeReward) {
      choreData.min_reward = parseFloat(minReward);
      choreData.max_reward = parseFloat(maxReward);
      choreData.reward = 0; // Backend expects this
    } else {
      choreData.reward = parseFloat(fixedReward);
    }

    if (isRecurring) {
      choreData.cooldown_days = parseInt(cooldownDays);
    }

    // assignee_id is required by backend, use first child if none selected
    if (assignedToId) {
      choreData.assignee_id = assignedToId;
    } else if (children.length > 0) {
      choreData.assignee_id = children[0].id;
    } else {
      Alert.alert('Error', 'No children available to assign chore to');
      setLoading(false);
      return;
    }

    try {
      let savedChore: Chore;
      
      if (isEditing && chore) {
        savedChore = await choreAPI.updateChore(chore.id, choreData);
        Alert.alert('Success', 'Chore updated successfully');
      } else {
        savedChore = await choreAPI.createChore(choreData);
        Alert.alert('Success', 'Chore created successfully');
      }
      
      onSave(savedChore);
    } catch (error: any) {
      console.error('Failed to save chore:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save chore';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const renderRewardInput = () => {
    if (isRangeReward) {
      return (
        <View style={styles.rangeContainer}>
          <View style={styles.rangeInputContainer}>
            <Text style={styles.rangeLabel}>Min $</Text>
            <TextInput
              style={[styles.input, styles.rangeInput]}
              value={minReward}
              onChangeText={setMinReward}
              placeholder="0.00"
              keyboardType="decimal-pad"
            />
          </View>
          <Text style={styles.rangeSeparator}>to</Text>
          <View style={styles.rangeInputContainer}>
            <Text style={styles.rangeLabel}>Max $</Text>
            <TextInput
              style={[styles.input, styles.rangeInput]}
              value={maxReward}
              onChangeText={setMaxReward}
              placeholder="0.00"
              keyboardType="decimal-pad"
            />
          </View>
        </View>
      );
    }

    return (
      <View>
        <Text style={styles.label}>Reward Amount ($)</Text>
        <TextInput
          style={styles.input}
          value={fixedReward}
          onChangeText={setFixedReward}
          placeholder="0.00"
          keyboardType="decimal-pad"
        />
      </View>
    );
  };

  if (loadingChildren) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196f3" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{isEditing ? 'Edit Chore' : 'Create New Chore'}</Text>
      </View>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Title *</Text>
          <TextInput
            style={styles.input}
            value={title}
            onChangeText={setTitle}
            placeholder="Enter chore title"
            maxLength={100}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Description</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={description}
            onChangeText={setDescription}
            placeholder="Enter chore description (optional)"
            multiline
            numberOfLines={3}
            maxLength={500}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Assign To</Text>
          <View style={styles.childrenList}>
            <TouchableOpacity
              style={[
                styles.childOption,
                !assignedToId && styles.childOptionSelected,
              ]}
              onPress={() => setAssignedToId(null)}
            >
              <Text style={[
                styles.childOptionText,
                !assignedToId && styles.childOptionTextSelected,
              ]}>
                Unassigned (Any child can claim)
              </Text>
            </TouchableOpacity>
            {children.map((child) => (
              <TouchableOpacity
                key={child.id}
                style={[
                  styles.childOption,
                  assignedToId === child.id && styles.childOptionSelected,
                ]}
                onPress={() => setAssignedToId(child.id)}
              >
                <Text style={[
                  styles.childOptionText,
                  assignedToId === child.id && styles.childOptionTextSelected,
                ]}>
                  {child.username}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.switchGroup}>
          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Range Reward</Text>
            <Switch
              value={isRangeReward}
              onValueChange={setIsRangeReward}
              trackColor={{ false: '#ccc', true: '#2196f3' }}
              thumbColor={isRangeReward ? '#1976d2' : '#f4f3f4'}
            />
          </View>
          <Text style={styles.switchDescription}>
            {isRangeReward 
              ? 'Set min/max amounts - you choose exact reward when approving'
              : 'Set a fixed reward amount'}
          </Text>
        </View>

        <View style={styles.inputGroup}>
          {renderRewardInput()}
        </View>

        <View style={styles.switchGroup}>
          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Recurring Chore</Text>
            <Switch
              value={isRecurring}
              onValueChange={setIsRecurring}
              trackColor={{ false: '#ccc', true: '#2196f3' }}
              thumbColor={isRecurring ? '#1976d2' : '#f4f3f4'}
            />
          </View>
          <Text style={styles.switchDescription}>
            {isRecurring 
              ? 'Chore can be completed multiple times with cooldown'
              : 'One-time chore that disappears after completion'}
          </Text>
        </View>

        {isRecurring && (
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Cooldown Days</Text>
            <TextInput
              style={styles.input}
              value={cooldownDays}
              onChangeText={setCooldownDays}
              placeholder="Days before chore can be done again"
              keyboardType="number-pad"
            />
            <Text style={styles.helperText}>
              Examples: 1 = daily, 7 = weekly, 30 = monthly
            </Text>
          </View>
        )}

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.button, styles.cancelButton]}
            onPress={onCancel}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.submitButton, loading && styles.buttonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.submitButtonText}>
                {isEditing ? 'Update Chore' : 'Create Chore'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
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
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
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
  form: {
    padding: 16,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  childrenList: {
    gap: 8,
  },
  childOption: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
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
    color: '#2196f3',
    fontWeight: '600',
  },
  switchGroup: {
    marginBottom: 20,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  switchLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  switchDescription: {
    marginTop: 4,
    fontSize: 14,
    color: '#666',
    paddingHorizontal: 4,
  },
  rangeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  rangeInputContainer: {
    flex: 1,
  },
  rangeLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  rangeInput: {
    flex: 1,
  },
  rangeSeparator: {
    fontSize: 16,
    color: '#666',
    paddingTop: 20,
  },
  helperText: {
    marginTop: 4,
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
    marginBottom: 40,
  },
  button: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  submitButton: {
    backgroundColor: '#2196f3',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  cancelButtonText: {
    fontSize: 16,
    color: '#666',
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
});

export default ChoreFormScreen;