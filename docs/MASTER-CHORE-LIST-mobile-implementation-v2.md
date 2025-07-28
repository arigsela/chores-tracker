# Master Chore List - Mobile Implementation Plan v2

## Overview

This document outlines the React Native mobile implementation for the Master Chore List feature with two key enhancements:
1. **Selective Visibility**: Hide specific chores from certain children
2. **Grayed Out Completed Chores**: Show completed chores as unavailable until reset based on recurrence

## Phased Implementation Plan

### Phase 1: API Service and Data Layer (1.5 days)

#### Subphase 1.1: API Service Updates (0.5 day)
**Tasks:**
- [ ] Extend ChoreService with V2 endpoints
- [ ] Add visibility management methods
- [ ] Update TypeScript interfaces
- [ ] Implement error handling

**Testing:**
- [ ] Unit test new API methods
- [ ] Test error scenarios
- [ ] Mock API responses
- [ ] Test type safety

**Deliverables:**
- Updated `choreService.ts`
- New TypeScript types
- API integration tests

#### Subphase 1.2: State Management Updates (0.5 day)
**Tasks:**
- [ ] Update Redux/Context state structure
- [ ] Add visibility filtering logic
- [ ] Implement chore availability calculations
- [ ] Add progress tracking state

**Testing:**
- [ ] Test state updates
- [ ] Verify filtering logic
- [ ] Test availability calculations
- [ ] Test state persistence

**Code Structure:**
```typescript
// tests/state/test_chore_state.ts
describe('Chore State Management', () => {
  it('should filter chores by visibility')
  it('should calculate availability correctly')
  it('should update progress in real-time')
});
```

#### Subphase 1.3: Data Models and Types (0.5 day)
**Tasks:**
- [ ] Create ChoreWithAvailability type
- [ ] Add RecurrenceType enum
- [ ] Update CreateChoreData interface
- [ ] Add visibility types

**Testing:**
- [ ] Type validation tests
- [ ] Interface compatibility tests
- [ ] Enum usage tests
- [ ] Migration tests

### Phase 2: Core UI Components (2 days)

#### Subphase 2.1: Child Chores Screen Redesign (0.75 day)
**Tasks:**
- [ ] Implement two-section layout
- [ ] Add auto-refresh logic
- [ ] Create claiming flow
- [ ] Handle empty states

**Testing:**
- [ ] Component rendering tests
- [ ] User interaction tests
- [ ] Auto-refresh timing tests
- [ ] Error state tests

**Component Tests:**
```tsx
// tests/screens/test_child_chores.tsx
describe('Child Chores Screen', () => {
  it('should display available and completed sections')
  it('should auto-refresh when chores become available')
  it('should handle claim conflicts gracefully')
  it('should show proper empty states')
});
```

#### Subphase 2.2: Chore Card Components (0.75 day)
**Tasks:**
- [ ] Create AvailableChoreCard component
- [ ] Create CompletedChoreCard component
- [ ] Implement countdown timer
- [ ] Add progress bar animation

**Testing:**
- [ ] Visual regression tests
- [ ] Timer accuracy tests
- [ ] Animation performance tests
- [ ] Accessibility tests

**Timer Testing:**
```tsx
// tests/components/test_chore_timer.tsx
describe('Chore Timer Component', () => {
  it('should update every minute')
  it('should handle timezone changes')
  it('should trigger refresh on expiry')
  it('should calculate progress accurately')
});
```

#### Subphase 2.3: Create/Edit Chore Updates (0.5 day)
**Tasks:**
- [ ] Add recurrence settings UI
- [ ] Implement visibility checkboxes
- [ ] Update form validation
- [ ] Add helper text

**Testing:**
- [ ] Form submission tests
- [ ] Validation tests
- [ ] UI state tests
- [ ] Accessibility tests

### Phase 3: Parent Management Features (2 days)

#### Subphase 3.1: Visibility Management Screen (1 day)
**Tasks:**
- [ ] Create ChoreVisibilityScreen component
- [ ] Implement child selection UI
- [ ] Add save/cancel functionality
- [ ] Create loading states

**Testing:**
- [ ] Screen navigation tests
- [ ] Data loading tests
- [ ] Save operation tests
- [ ] UI consistency tests

**Screen Tests:**
```tsx
// tests/screens/test_visibility_management.tsx
describe('Visibility Management', () => {
  it('should load current visibility settings')
  it('should update visibility selections')
  it('should save changes successfully')
  it('should handle concurrent updates')
});
```

#### Subphase 3.2: Parent Dashboard Updates (1 day)
**Tasks:**
- [ ] Add visibility indicators to chore cards
- [ ] Create management shortcuts
- [ ] Implement bulk operations
- [ ] Add activity monitoring

**Testing:**
- [ ] Dashboard data accuracy
- [ ] Indicator visibility tests
- [ ] Bulk operation tests
- [ ] Performance tests

### Phase 4: Platform-Specific Enhancements (1.5 days)

#### Subphase 4.1: iOS Optimizations (0.75 day)
**Tasks:**
- [ ] Add haptic feedback
- [ ] Implement iOS-specific animations
- [ ] Optimize for different screen sizes
- [ ] Add 3D touch shortcuts

**Testing:**
- [ ] Haptic feedback tests
- [ ] Animation smoothness tests
- [ ] Device compatibility tests
- [ ] Performance profiling

**iOS Tests:**
```swift
// tests/ios/test_platform_features.swift
func testHapticFeedback()
func testAnimationPerformance()
func test3DTouchActions()
```

#### Subphase 4.2: Android Optimizations (0.75 day)
**Tasks:**
- [ ] Implement native toasts
- [ ] Add material design transitions
- [ ] Optimize for various densities
- [ ] Handle back button properly

**Testing:**
- [ ] Toast display tests
- [ ] Transition tests
- [ ] Multi-device tests
- [ ] Navigation tests

### Phase 5: Offline Support and Performance (1.5 days)

#### Subphase 5.1: Offline Capabilities (0.75 day)
**Tasks:**
- [ ] Cache chore data locally
- [ ] Queue claim operations
- [ ] Sync visibility changes
- [ ] Handle conflicts

**Testing:**
- [ ] Offline mode tests
- [ ] Sync accuracy tests
- [ ] Conflict resolution tests
- [ ] Data integrity tests

**Offline Tests:**
```typescript
// tests/offline/test_offline_sync.ts
describe('Offline Synchronization', () => {
  it('should cache chores when online')
  it('should queue claims when offline')
  it('should sync on reconnection')
  it('should resolve conflicts properly')
});
```

#### Subphase 5.2: Performance Optimization (0.75 day)
**Tasks:**
- [ ] Optimize list rendering
- [ ] Implement lazy loading
- [ ] Reduce re-renders
- [ ] Profile memory usage

**Testing:**
- [ ] Scroll performance tests
- [ ] Memory leak tests
- [ ] Battery usage tests
- [ ] Load time tests

### Phase 6: Integration and Final Testing (1 day)

#### Subphase 6.1: End-to-End Testing (0.5 day)
**Tasks:**
- [ ] Complete user flow tests
- [ ] Cross-platform testing
- [ ] Integration with backend
- [ ] Edge case testing

**E2E Scenarios:**
```typescript
// tests/e2e/test_complete_flow.ts
describe('Complete User Flow', () => {
  it('parent creates hidden recurring chore')
  it('child cannot see hidden chore')
  it('child completes visible chore')
  it('chore grays out with timer')
  it('chore becomes available after reset')
});
```

#### Subphase 6.2: Release Preparation (0.5 day)
**Tasks:**
- [ ] Final bug fixes
- [ ] Performance profiling
- [ ] Update app store descriptions
- [ ] Prepare release notes

**Release Tests:**
- [ ] Build verification
- [ ] Store compliance
- [ ] Crash reporting setup
- [ ] Analytics verification

## API Service Updates

### 1. Extended Chore Service
```typescript
// src/services/choreService.ts

interface ChoreVisibilityUpdate {
  choreId: number;
  hiddenFromUsers: number[];
  visibleToUsers: number[];
}

interface ChoreWithAvailability extends Chore {
  isAvailable: boolean;
  nextAvailableTime?: Date;
  lastCompletionTime?: Date;
  isHiddenFromCurrentUser: boolean;
  availabilityProgress: number;
}

interface ChoreListResponse {
  availableChores: ChoreWithAvailability[];
  completedChores: ChoreWithAvailability[];
}

class ChoreServiceV2 extends ChoreService {
  async getMyChores(): Promise<ChoreListResponse> {
    const response = await apiClient.get('/api/v2/chores/my-chores');
    return response.data;
  }

  async updateChoreVisibility(
    choreId: number, 
    visibility: ChoreVisibilityUpdate
  ): Promise<void> {
    await apiClient.put(`/api/v2/chores/${choreId}/visibility`, visibility);
  }

  async getChoreVisibility(choreId: number): Promise<ChoreVisibilityUpdate> {
    const response = await apiClient.get(`/api/v2/chores/${choreId}/visibility`);
    return response.data;
  }
}
```

### 2. Type Updates
```typescript
// src/types/chore.ts

export enum RecurrenceType {
  NONE = 'none',
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly'
}

export interface Chore {
  // ... existing fields ...
  recurrenceType: RecurrenceType;
  recurrenceValue?: number;
  lastCompletionTime?: string;
  nextAvailableTime?: string;
}

export interface CreateChoreData {
  // ... existing fields ...
  recurrenceType: RecurrenceType;
  recurrenceValue?: number;
  hiddenFromUsers?: number[];
}
```

## Navigation Updates

### 1. Parent Navigation Enhancement
```tsx
// src/navigation/ParentNavigator.tsx

// Add visibility management to stack
<Stack.Screen 
  name="ChoreVisibility" 
  component={ChoreVisibilityScreen}
  options={{ 
    title: 'Manage Visibility',
    presentation: 'modal' 
  }}
/>
```

### 2. Child Navigation - No Changes Needed
The existing tab structure works well, just need to update the screens to show available/completed sections.

## Screen Updates

### 1. Updated Child Chores Screen
```tsx
// src/screens/child/ChoresScreen.tsx

interface ChoresScreenProps {
  navigation: NavigationProp<any>;
}

export const ChoresScreen: React.FC<ChoresScreenProps> = ({ navigation }) => {
  const [choreData, setChoreData] = useState<ChoreListResponse | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [claimingChoreId, setClaimingChoreId] = useState<number | null>(null);

  // Auto-refresh logic
  useEffect(() => {
    const interval = setInterval(() => {
      checkChoreAvailability();
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [choreData]);

  const checkChoreAvailability = () => {
    if (!choreData) return;

    const now = new Date();
    const hasNewlyAvailable = choreData.completedChores.some(chore => {
      if (!chore.nextAvailableTime) return false;
      return new Date(chore.nextAvailableTime) <= now;
    });

    if (hasNewlyAvailable) {
      fetchChores();
    }
  };

  const fetchChores = async () => {
    try {
      const data = await choreService.getMyChores();
      setChoreData(data);
    } catch (error) {
      console.error('Error fetching chores:', error);
    }
  };

  const handleClaim = async (choreId: number) => {
    setClaimingChoreId(choreId);
    
    try {
      await choreService.claimChore(choreId);
      await fetchChores();
      showSuccessToast('Chore claimed successfully!');
    } catch (error) {
      if (error.response?.status === 409) {
        Alert.alert('Already Claimed', 'This chore was already claimed by someone else.');
      } else {
        Alert.alert('Error', 'Failed to claim chore. Please try again.');
      }
    } finally {
      setClaimingChoreId(null);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={onRefresh}
          />
        }
      >
        {/* Available Chores Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Available Chores</Text>
          {choreData?.availableChores.length === 0 ? (
            <EmptyState message="No chores available right now" />
          ) : (
            <View style={styles.choreGrid}>
              {choreData?.availableChores.map(chore => (
                <AvailableChoreCard
                  key={chore.id}
                  chore={chore}
                  onClaim={handleClaim}
                  isClaiming={claimingChoreId === chore.id}
                />
              ))}
            </View>
          )}
        </View>

        {/* Completed Chores Section */}
        {choreData?.completedChores.length > 0 && (
          <View style={[styles.section, styles.completedSection]}>
            <Text style={[styles.sectionTitle, styles.completedTitle]}>
              Completed (Waiting for Reset)
            </Text>
            <View style={styles.choreGrid}>
              {choreData.completedChores.map(chore => (
                <CompletedChoreCard
                  key={chore.id}
                  chore={chore}
                />
              ))}
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  section: {
    padding: spacing.md,
  },
  sectionTitle: {
    ...typography.h2,
    marginBottom: spacing.md,
  },
  completedSection: {
    backgroundColor: colors.gray[50],
    marginTop: spacing.lg,
  },
  completedTitle: {
    color: colors.gray[600],
  },
  choreGrid: {
    gap: spacing.sm,
  },
});
```

### 2. Updated Create Chore Screen
```tsx
// src/screens/parent/CreateChoreScreen.tsx

export const CreateChoreScreen: React.FC = ({ navigation }) => {
  const [formData, setFormData] = useState<CreateChoreData>({
    title: '',
    description: '',
    rewardType: 'fixed',
    rewardAmount: 0,
    recurrenceType: RecurrenceType.NONE,
    hiddenFromUsers: [],
  });
  const [showRecurrence, setShowRecurrence] = useState(false);
  const [showVisibility, setShowVisibility] = useState(false);
  const [children, setChildren] = useState<User[]>([]);

  return (
    <ScrollView style={styles.container}>
      {/* Basic fields... */}

      {/* Recurrence Settings */}
      <View style={styles.section}>
        <TouchableOpacity
          style={styles.toggleRow}
          onPress={() => setShowRecurrence(!showRecurrence)}
        >
          <Text style={styles.label}>Recurring Chore</Text>
          <Switch
            value={showRecurrence}
            onValueChange={setShowRecurrence}
          />
        </TouchableOpacity>

        {showRecurrence && (
          <Animated.View style={styles.expandedSection}>
            <View style={styles.field}>
              <Text style={styles.label}>Recurrence Type</Text>
              <Picker
                selectedValue={formData.recurrenceType}
                onValueChange={(value) => setFormData({
                  ...formData,
                  recurrenceType: value
                })}
                style={styles.picker}
              >
                <Picker.Item label="Daily" value={RecurrenceType.DAILY} />
                <Picker.Item label="Weekly" value={RecurrenceType.WEEKLY} />
                <Picker.Item label="Monthly" value={RecurrenceType.MONTHLY} />
              </Picker>
            </View>

            {formData.recurrenceType === RecurrenceType.DAILY && (
              <View style={styles.field}>
                <Text style={styles.label}>Every X days</Text>
                <TextInput
                  style={styles.input}
                  keyboardType="numeric"
                  value={formData.recurrenceValue?.toString() || '1'}
                  onChangeText={(text) => setFormData({
                    ...formData,
                    recurrenceValue: parseInt(text) || 1
                  })}
                />
              </View>
            )}

            {formData.recurrenceType === RecurrenceType.WEEKLY && (
              <View style={styles.field}>
                <Text style={styles.label}>Day of Week</Text>
                <Picker
                  selectedValue={formData.recurrenceValue || 0}
                  onValueChange={(value) => setFormData({
                    ...formData,
                    recurrenceValue: value
                  })}
                  style={styles.picker}
                >
                  <Picker.Item label="Monday" value={0} />
                  <Picker.Item label="Tuesday" value={1} />
                  <Picker.Item label="Wednesday" value={2} />
                  <Picker.Item label="Thursday" value={3} />
                  <Picker.Item label="Friday" value={4} />
                  <Picker.Item label="Saturday" value={5} />
                  <Picker.Item label="Sunday" value={6} />
                </Picker>
              </View>
            )}
          </Animated.View>
        )}
      </View>

      {/* Visibility Settings */}
      <View style={styles.section}>
        <TouchableOpacity
          style={styles.toggleRow}
          onPress={() => setShowVisibility(!showVisibility)}
        >
          <Text style={styles.label}>Hide from Specific Children</Text>
          <Icon
            name={showVisibility ? 'chevron-up' : 'chevron-down'}
            size={20}
            color={colors.gray[600]}
          />
        </TouchableOpacity>

        {showVisibility && (
          <Animated.View style={styles.expandedSection}>
            <Text style={styles.helperText}>
              Select children who should NOT see this chore:
            </Text>
            {children.map(child => (
              <TouchableOpacity
                key={child.id}
                style={styles.checkboxRow}
                onPress={() => toggleChildVisibility(child.id)}
              >
                <Checkbox
                  value={formData.hiddenFromUsers?.includes(child.id)}
                  onValueChange={() => toggleChildVisibility(child.id)}
                />
                <Text style={styles.checkboxLabel}>{child.username}</Text>
              </TouchableOpacity>
            ))}
          </Animated.View>
        )}
      </View>

      <Button
        title="Create Chore"
        onPress={handleSubmit}
        style={styles.submitButton}
      />
    </ScrollView>
  );
};
```

### 3. New Visibility Management Screen
```tsx
// src/screens/parent/ChoreVisibilityScreen.tsx

export const ChoreVisibilityScreen: React.FC = ({ route, navigation }) => {
  const { choreId, choreTitle } = route.params;
  const [visibility, setVisibility] = useState<ChoreVisibilityUpdate | null>(null);
  const [children, setChildren] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [visibilityData, childrenData] = await Promise.all([
        choreService.getChoreVisibility(choreId),
        userService.getMyChildren()
      ]);
      setVisibility(visibilityData);
      setChildren(childrenData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load visibility settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!visibility) return;

    try {
      await choreService.updateChoreVisibility(choreId, visibility);
      Alert.alert('Success', 'Visibility settings updated', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (error) {
      Alert.alert('Error', 'Failed to update visibility settings');
    }
  };

  const toggleChildVisibility = (childId: number) => {
    if (!visibility) return;

    const hidden = new Set(visibility.hiddenFromUsers);
    if (hidden.has(childId)) {
      hidden.delete(childId);
    } else {
      hidden.add(childId);
    }

    setVisibility({
      ...visibility,
      hiddenFromUsers: Array.from(hidden)
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Visibility Settings</Text>
        <Text style={styles.choreTitle}>{choreTitle}</Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" style={styles.loader} />
      ) : (
        <ScrollView style={styles.content}>
          <Text style={styles.instruction}>
            Select children who should NOT see this chore:
          </Text>

          {children.map(child => (
            <TouchableOpacity
              key={child.id}
              style={styles.childRow}
              onPress={() => toggleChildVisibility(child.id)}
            >
              <Checkbox
                value={visibility?.hiddenFromUsers.includes(child.id)}
                onValueChange={() => toggleChildVisibility(child.id)}
              />
              <Text style={styles.childName}>{child.username}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      <View style={styles.footer}>
        <Button
          title="Cancel"
          onPress={() => navigation.goBack()}
          variant="secondary"
          style={styles.button}
        />
        <Button
          title="Save"
          onPress={handleSave}
          style={styles.button}
        />
      </View>
    </SafeAreaView>
  );
};
```

## Component Updates

### 1. Available Chore Card
```tsx
// src/components/chores/AvailableChoreCard.tsx

interface AvailableChoreCardProps {
  chore: ChoreWithAvailability;
  onClaim: (choreId: number) => void;
  isClaiming: boolean;
}

export const AvailableChoreCard: React.FC<AvailableChoreCardProps> = ({
  chore,
  onClaim,
  isClaiming
}) => {
  return (
    <Pressable style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>{chore.title}</Text>
        {chore.recurrenceType !== RecurrenceType.NONE && (
          <View style={styles.recurrenceBadge}>
            <Text style={styles.recurrenceText}>
              {chore.recurrenceType}
            </Text>
          </View>
        )}
      </View>

      {chore.description && (
        <Text style={styles.description}>{chore.description}</Text>
      )}

      <View style={styles.footer}>
        <RewardDisplay
          type={chore.rewardType}
          amount={chore.rewardAmount}
          min={chore.rewardMin}
          max={chore.rewardMax}
        />

        <TouchableOpacity
          style={[styles.claimButton, isClaiming && styles.claimingButton]}
          onPress={() => onClaim(chore.id)}
          disabled={isClaiming}
        >
          {isClaiming ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.claimButtonText}>Claim</Text>
          )}
        </TouchableOpacity>
      </View>
    </Pressable>
  );
};
```

### 2. Completed Chore Card (Grayed Out)
```tsx
// src/components/chores/CompletedChoreCard.tsx

interface CompletedChoreCardProps {
  chore: ChoreWithAvailability;
}

export const CompletedChoreCard: React.FC<CompletedChoreCardProps> = ({ chore }) => {
  const [timeRemaining, setTimeRemaining] = useState('');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const updateTimer = () => {
      if (!chore.nextAvailableTime) return;

      const now = new Date();
      const available = new Date(chore.nextAvailableTime);
      const diff = available.getTime() - now.getTime();

      if (diff <= 0) {
        // Chore is now available
        return;
      }

      // Calculate time remaining
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 24) {
        const days = Math.floor(hours / 24);
        setTimeRemaining(`${days}d ${hours % 24}h`);
      } else {
        setTimeRemaining(`${hours}h ${minutes}m`);
      }

      // Calculate progress
      if (chore.lastCompletionTime) {
        const total = available.getTime() - new Date(chore.lastCompletionTime).getTime();
        const elapsed = now.getTime() - new Date(chore.lastCompletionTime).getTime();
        setProgress(Math.min(100, (elapsed / total) * 100));
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [chore]);

  return (
    <View style={[styles.card, styles.completedCard]}>
      <View style={styles.overlay} />
      
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={[styles.title, styles.completedTitle]}>{chore.title}</Text>
          <View style={styles.completedBadge}>
            <Icon name="check-circle" size={16} color={colors.gray[500]} />
            <Text style={styles.completedText}>Completed</Text>
          </View>
        </View>

        {chore.description && (
          <Text style={[styles.description, styles.completedDescription]}>
            {chore.description}
          </Text>
        )}

        <View style={styles.footer}>
          <Text style={styles.rewardText}>
            ${chore.rewardAmount || `${chore.rewardMin}-${chore.rewardMax}`}
          </Text>
          
          <View style={styles.timerContainer}>
            <Icon name="clock" size={14} color={colors.gray[500]} />
            <Text style={styles.timerText}>Available in {timeRemaining}</Text>
          </View>
        </View>

        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <Animated.View
              style={[
                styles.progressFill,
                { width: `${progress}%` }
              ]}
            />
          </View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    ...shadows.sm,
  },
  completedCard: {
    position: 'relative',
    backgroundColor: colors.gray[100],
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: colors.gray[200],
    opacity: 0.3,
    borderRadius: radius.md,
  },
  content: {
    position: 'relative',
    zIndex: 1,
  },
  completedTitle: {
    color: colors.gray[600],
  },
  completedDescription: {
    color: colors.gray[500],
  },
  progressContainer: {
    marginTop: spacing.sm,
  },
  progressBar: {
    height: 6,
    backgroundColor: colors.gray[300],
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.blue[400],
    borderRadius: 3,
  },
});
```

### 3. Parent Chore Management Card
```tsx
// src/components/parent/ChoreManagementCard.tsx

interface ChoreManagementCardProps {
  chore: Chore;
  onEditVisibility: () => void;
  hiddenFromCount: number;
}

export const ChoreManagementCard: React.FC<ChoreManagementCardProps> = ({
  chore,
  onEditVisibility,
  hiddenFromCount
}) => {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>{chore.title}</Text>
        <View style={styles.badges}>
          {chore.recurrenceType !== RecurrenceType.NONE && (
            <Badge text={chore.recurrenceType} variant="info" />
          )}
          {hiddenFromCount > 0 && (
            <Badge 
              text={`Hidden from ${hiddenFromCount}`} 
              variant="warning" 
            />
          )}
        </View>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={onEditVisibility}
        >
          <Icon name="eye-off" size={18} color={colors.gray[600]} />
          <Text style={styles.actionText}>Visibility</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton}>
          <Icon name="edit" size={18} color={colors.gray[600]} />
          <Text style={styles.actionText}>Edit</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};
```

## State Management Updates

### 1. Chores Context Enhancement
```tsx
// src/contexts/ChoresContext.tsx

interface ChoresContextValue {
  availableChores: ChoreWithAvailability[];
  completedChores: ChoreWithAvailability[];
  isLoading: boolean;
  refreshChores: () => Promise<void>;
  claimChore: (choreId: number) => Promise<void>;
  updateVisibility: (choreId: number, visibility: ChoreVisibilityUpdate) => Promise<void>;
}

export const ChoresProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [choreData, setChoreData] = useState<ChoreListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Check for chores becoming available
  useEffect(() => {
    const checkAvailability = () => {
      if (!choreData) return;

      const now = new Date();
      const hasNewlyAvailable = choreData.completedChores.some(chore => {
        if (!chore.nextAvailableTime) return false;
        return new Date(chore.nextAvailableTime) <= now;
      });

      if (hasNewlyAvailable) {
        refreshChores();
      }
    };

    const interval = setInterval(checkAvailability, 60000);
    return () => clearInterval(interval);
  }, [choreData]);

  // ... rest of implementation
};
```

## Performance Optimizations

### 1. Memoized Chore Lists
```tsx
// Use React.memo for chore cards
export const AvailableChoreCard = React.memo(
  AvailableChoreCardComponent,
  (prevProps, nextProps) => {
    return (
      prevProps.chore.id === nextProps.chore.id &&
      prevProps.isClaiming === nextProps.isClaiming
    );
  }
);
```

### 2. Lazy Progress Updates
```tsx
// Only update progress bars when visible
const useVisibilityTimer = (callback: () => void, interval: number) => {
  const appState = useRef(AppState.currentState);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', nextAppState => {
      appState.current = nextAppState;
    });

    const timer = setInterval(() => {
      if (appState.current === 'active') {
        callback();
      }
    }, interval);

    return () => {
      clearInterval(timer);
      subscription.remove();
    };
  }, [callback, interval]);
};
```

## Platform-Specific Features

### iOS
```tsx
// Add haptic feedback for claim success
import { HapticFeedback } from 'react-native-haptic-feedback';

const handleClaimSuccess = () => {
  if (Platform.OS === 'ios') {
    HapticFeedback.trigger('notificationSuccess');
  }
};
```

### Android
```tsx
// Use native toast for quick feedback
import { ToastAndroid } from 'react-native';

const showClaimSuccess = () => {
  if (Platform.OS === 'android') {
    ToastAndroid.show('Chore claimed!', ToastAndroid.SHORT);
  }
};
```

## Testing Considerations

### 1. New Test Cases
- Test visibility filtering logic
- Test recurrence calculations
- Test timer updates for completed chores
- Test progress bar calculations
- Test auto-refresh when chores become available

### 2. Edge Cases
- Test with all chores hidden from a child
- Test timezone handling for reset times
- Test app background/foreground transitions
- Test offline claim attempts

## Implementation Timeline Summary

### Phase-by-Phase Breakdown
- **Phase 1**: API Service and Data Layer (1.5 days)
  - Subphase 1.1: API Service Updates (0.5 day)
  - Subphase 1.2: State Management Updates (0.5 day)
  - Subphase 1.3: Data Models and Types (0.5 day)

- **Phase 2**: Core UI Components (2 days)
  - Subphase 2.1: Child Chores Screen Redesign (0.75 day)
  - Subphase 2.2: Chore Card Components (0.75 day)
  - Subphase 2.3: Create/Edit Chore Updates (0.5 day)

- **Phase 3**: Parent Management Features (2 days)
  - Subphase 3.1: Visibility Management Screen (1 day)
  - Subphase 3.2: Parent Dashboard Updates (1 day)

- **Phase 4**: Platform-Specific Enhancements (1.5 days)
  - Subphase 4.1: iOS Optimizations (0.75 day)
  - Subphase 4.2: Android Optimizations (0.75 day)

- **Phase 5**: Offline Support and Performance (1.5 days)
  - Subphase 5.1: Offline Capabilities (0.75 day)
  - Subphase 5.2: Performance Optimization (0.75 day)

- **Phase 6**: Integration and Final Testing (1 day)
  - Subphase 6.1: End-to-End Testing (0.5 day)
  - Subphase 6.2: Release Preparation (0.5 day)

**Total: 9.5 days** (increased from 8 due to comprehensive testing and platform optimizations)

## Success Metrics

### Phase 1 Success Criteria
- [ ] All API calls working correctly
- [ ] Type safety maintained
- [ ] State management efficient
- [ ] 100% test coverage for services

### Phase 2 Success Criteria
- [ ] UI components render smoothly
- [ ] Timers accurate to 1 minute
- [ ] Animations at 60fps
- [ ] Accessibility compliant

### Phase 3 Success Criteria
- [ ] Visibility management intuitive
- [ ] Parent workflows streamlined
- [ ] Real-time updates working
- [ ] Bulk operations < 1s

### Phase 4 Success Criteria
- [ ] Platform features working correctly
- [ ] Native feel on both platforms
- [ ] Haptic/toast feedback functional
- [ ] Performance optimized

### Phase 5 Success Criteria
- [ ] Offline mode seamless
- [ ] Sync without data loss
- [ ] Battery usage minimal
- [ ] Memory usage stable

### Phase 6 Success Criteria
- [ ] All E2E tests passing
- [ ] App store ready
- [ ] Crash rate < 0.1%
- [ ] User satisfaction > 95%

## Risk Mitigation

### Technical Risks
1. **Timer Accuracy**: Use background tasks and server reconciliation
2. **State Complexity**: Use normalized state and memoization
3. **Platform Differences**: Abstract platform-specific code

### Performance Risks
1. **List Rendering**: Use FlatList with optimization props
2. **Memory Leaks**: Proper cleanup in useEffect
3. **Battery Drain**: Optimize timer updates and polling

### UX Risks
1. **Complexity**: Progressive disclosure and onboarding
2. **Offline Confusion**: Clear indicators and sync status
3. **Platform Consistency**: Follow platform guidelines

## Testing Strategy Summary

### Unit Testing
- Component tests with React Native Testing Library
- Service tests with Jest
- State management tests
- Utility function tests

### Integration Testing
- API integration tests
- Navigation flow tests
- State persistence tests
- Platform feature tests

### E2E Testing
- Complete user flows with Detox
- Cross-platform scenarios
- Offline/online transitions
- Performance benchmarks

## Documentation Requirements

### For Each Phase
- [ ] Update code documentation
- [ ] Add inline comments
- [ ] Update component storybook
- [ ] Create testing guides

### User Documentation
- [ ] Feature announcement
- [ ] In-app tutorials
- [ ] FAQ updates
- [ ] Video guides

### Developer Documentation
- [ ] API integration guide
- [ ] Component library docs
- [ ] State management guide
- [ ] Platform-specific notes