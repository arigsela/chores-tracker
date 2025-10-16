import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { Chore, choreAPI, AssignmentMode } from '../api/chores';
import { usersAPI, ChildWithChores } from '../api/users';
import { familyAPI, FamilyContext } from '../api/families';
import { Alert } from '../utils/Alert';

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

  // NEW: Multi-assignment state
  const [assignmentMode, setAssignmentMode] = useState<AssignmentMode>(
    chore?.assignment_mode || 'single'
  );
  const [selectedChildIds, setSelectedChildIds] = useState<number[]>(
    chore?.assignee_ids || (chore?.assignee_id ? [chore.assignee_id] : [])
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
      // First get family context to understand if user has a family
      const familyCtx = await familyAPI.getFamilyContext();
      
      // Use family children if user has family, otherwise fallback to personal children
      const childrenEndpoint = familyCtx.has_family 
        ? usersAPI.getFamilyChildren() 
        : usersAPI.getMyChildren();
      
      const childrenData = await childrenEndpoint;
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

    // NEW: Assignment mode validation
    if (assignmentMode === 'single' && selectedChildIds.length !== 1) {
      Alert.alert('Validation Error', 'Single mode requires exactly one child to be selected');
      return false;
    }

    if (assignmentMode === 'multi_independent' && selectedChildIds.length === 0) {
      Alert.alert('Validation Error', 'Multi-independent mode requires at least one child to be selected');
      return false;
    }

    if (assignmentMode === 'unassigned' && selectedChildIds.length > 0) {
      Alert.alert('Validation Error', 'Unassigned pool mode cannot have children selected');
      return false;
    }

    if (isRangeReward) {
      if (!minReward || !maxReward) {
        Alert.alert('Validation Error', 'Please enter both minimum and maximum reward amounts');
        console.log('Validation failed: minReward=', minReward, 'maxReward=', maxReward);
        return false;
      }

      const min = parseFloat(minReward);
      const max = parseFloat(maxReward);

      if (isNaN(min) || isNaN(max)) {
        Alert.alert('Validation Error', 'Please enter valid numeric reward amounts');
        console.log('Validation failed: min=', min, 'max=', max);
        return false;
      }

      if (min >= max) {
        Alert.alert('Validation Error', 'Minimum reward must be less than maximum reward');
        console.log('Validation failed: min >= max', min, '>=', max);
        return false;
      }

      if (min < 0 || max < 0) {
        Alert.alert('Validation Error', 'Reward amounts must be positive');
        console.log('Validation failed: negative values', min, max);
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
    console.log('Submit button clicked');
    console.log('Form state:', {
      title,
      description,
      isRangeReward,
      fixedReward,
      minReward,
      maxReward,
      isRecurring,
      cooldownDays,
      assignmentMode,
      selectedChildIds,
      children: children.length
    });

    if (!validateForm()) {
      console.log('Form validation failed');
      return;
    }

    setLoading(true);

    // NEW: Build chore data with multi-assignment fields
    const choreData: any = {
      title: title.trim(),
      description: description.trim() || '',
      is_range_reward: isRangeReward,
      is_recurring: isRecurring,
      assignment_mode: assignmentMode,
      assignee_ids: selectedChildIds,
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

    try {
      console.log('Submitting chore data:', choreData);
      let savedChore: Chore;

      if (isEditing && chore) {
        savedChore = await choreAPI.updateChore(chore.id, choreData);
        Alert.alert('Success', 'Chore updated successfully');
      } else {
        savedChore = await choreAPI.createChore(choreData);
        // Success popup removed - just proceed with navigation
      }

      onSave(savedChore);
    } catch (error: any) {
      console.error('Failed to save chore:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('Sent data:', choreData);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to save chore';
      Alert.alert('Error', `${errorMessage}\n\nCheck console for details`);
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
            <input
              style={{
                flex: 1,
                padding: 8,
                borderWidth: 1,
                borderColor: '#ddd',
                borderRadius: 4,
                fontSize: 16,
              }}
              type="number"
              value={minReward}
              onChange={(e) => {
                const text = e.target.value;
                console.log('Min reward input changed to:', text);
                setMinReward(text);
              }}
              placeholder="0.00"
              step="0.01"
            />
          </View>
          <Text style={styles.rangeSeparator}>to</Text>
          <View style={styles.rangeInputContainer}>
            <Text style={styles.rangeLabel}>Max $</Text>
            <TextInput
              style={[styles.input, styles.rangeInput]}
              value={maxReward}
              onChangeText={(text) => {
                console.log('Max reward changed to:', text);
                setMaxReward(text);
              }}
              onChange={(e) => {
                const text = e.nativeEvent.text;
                console.log('Max reward onChange:', text);
                setMaxReward(text);
              }}
              placeholder="0.00"
              keyboardType="numeric"
              autoComplete="off"
              autoCorrect={false}
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

        {/* NEW: Assignment Mode Selector */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Assignment Mode *</Text>
          <View style={styles.modeSelector}>
            <TouchableOpacity
              style={[
                styles.modeOption,
                assignmentMode === 'single' && styles.modeOptionSelected,
              ]}
              onPress={() => {
                setAssignmentMode('single');
                // When switching to single, keep first selected child only
                if (selectedChildIds.length > 1) {
                  setSelectedChildIds([selectedChildIds[0]]);
                }
              }}
            >
              <Text style={[
                styles.modeOptionTitle,
                assignmentMode === 'single' && styles.modeOptionTitleSelected,
              ]}>
                Single Child
              </Text>
              <Text style={styles.modeOptionDesc}>Assign to one child</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.modeOption,
                assignmentMode === 'multi_independent' && styles.modeOptionSelected,
              ]}
              onPress={() => setAssignmentMode('multi_independent')}
            >
              <Text style={[
                styles.modeOptionTitle,
                assignmentMode === 'multi_independent' && styles.modeOptionTitleSelected,
              ]}>
                Multiple Children
              </Text>
              <Text style={styles.modeOptionDesc}>Each child does their own</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.modeOption,
                assignmentMode === 'unassigned' && styles.modeOptionSelected,
              ]}
              onPress={() => {
                setAssignmentMode('unassigned');
                // When switching to unassigned, clear all selections
                setSelectedChildIds([]);
              }}
            >
              <Text style={[
                styles.modeOptionTitle,
                assignmentMode === 'unassigned' && styles.modeOptionTitleSelected,
              ]}>
                Unassigned Pool
              </Text>
              <Text style={styles.modeOptionDesc}>Any child can claim</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Updated: Child Selection (Multi-select support) */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>
            {assignmentMode === 'unassigned'
              ? 'Assignees (Not needed for pool chores)'
              : assignmentMode === 'single'
              ? 'Assign To *'
              : 'Assign To (Select multiple) *'}
          </Text>
          {assignmentMode === 'multi_independent' && selectedChildIds.length > 0 && (
            <Text style={styles.selectionCount}>
              {selectedChildIds.length} {selectedChildIds.length === 1 ? 'child' : 'children'} selected
            </Text>
          )}
          <View style={styles.childrenList}>
            {children.map((child) => {
              const isSelected = selectedChildIds.includes(child.id);
              const isDisabled = assignmentMode === 'unassigned';

              return (
                <TouchableOpacity
                  key={child.id}
                  style={[
                    styles.childOption,
                    isSelected && styles.childOptionSelected,
                    isDisabled && styles.childOptionDisabled,
                  ]}
                  onPress={() => {
                    if (isDisabled) return;

                    if (assignmentMode === 'single') {
                      // Single mode: replace selection
                      setSelectedChildIds([child.id]);
                    } else {
                      // Multi mode: toggle selection
                      if (isSelected) {
                        setSelectedChildIds(selectedChildIds.filter(id => id !== child.id));
                      } else {
                        setSelectedChildIds([...selectedChildIds, child.id]);
                      }
                    }
                  }}
                  disabled={isDisabled}
                >
                  <View style={styles.childOptionContent}>
                    {assignmentMode === 'multi_independent' && (
                      <View style={[
                        styles.checkbox,
                        isSelected && styles.checkboxSelected,
                      ]}>
                        {isSelected && <Text style={styles.checkmark}>✓</Text>}
                      </View>
                    )}
                    <Text style={[
                      styles.childOptionText,
                      isSelected && styles.childOptionTextSelected,
                      isDisabled && styles.childOptionTextDisabled,
                    ]}>
                      {child.username}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
          {assignmentMode === 'unassigned' && (
            <Text style={styles.helperText}>
              Pool chores can be claimed by any child in the family
            </Text>
          )}
        </View>

        <View style={styles.switchGroup}>
          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>Range Reward</Text>
            <Switch
              value={isRangeReward}
              onValueChange={(value) => {
                console.log('Range reward toggle:', value, 'fixedReward:', fixedReward, 'minReward:', minReward, 'maxReward:', maxReward);
                setIsRangeReward(value);
                // When switching from fixed to range reward, initialize min/max with fixed reward value
                if (value && fixedReward && (!minReward || minReward === '') && (!maxReward || maxReward === '')) {
                  console.log('Initializing min/max rewards with fixed reward value:', fixedReward);
                  setMinReward(fixedReward);
                  setMaxReward(fixedReward);
                } else {
                  console.log('Not initializing because:', 'value:', value, 'fixedReward:', fixedReward, 'minReward check:', (!minReward || minReward === ''), 'maxReward check:', (!maxReward || maxReward === ''));
                }
              }}
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
  // NEW: Assignment mode selector styles
  modeSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  modeOption: {
    flex: 1,
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  modeOptionSelected: {
    borderColor: '#2196f3',
    backgroundColor: '#e3f2fd',
  },
  modeOptionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
    textAlign: 'center',
  },
  modeOptionTitleSelected: {
    color: '#2196f3',
  },
  modeOptionDesc: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  selectionCount: {
    fontSize: 14,
    color: '#2196f3',
    fontWeight: '600',
    marginBottom: 8,
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
  childOptionDisabled: {
    backgroundColor: '#f5f5f5',
    opacity: 0.5,
  },
  childOptionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#ddd',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
  },
  checkboxSelected: {
    backgroundColor: '#2196f3',
    borderColor: '#2196f3',
  },
  checkmark: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  childOptionText: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  childOptionTextSelected: {
    color: '#2196f3',
    fontWeight: '600',
  },
  childOptionTextDisabled: {
    color: '#999',
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