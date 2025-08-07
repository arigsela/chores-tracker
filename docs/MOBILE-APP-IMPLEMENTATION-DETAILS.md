# Mobile App Implementation Details

**Companion to**: MOBILE-APP-UPDATE-PLAN.md  
**Date**: January 2, 2025

## Component Architecture

### Component Hierarchy

```
App
├── AuthProvider (enhanced with balance)
│   ├── AppNavigator
│   │   ├── MainNavigator
│   │   │   ├── ChildHomeScreen
│   │   │   │   ├── BalanceCard (NEW)
│   │   │   │   └── ChoreList
│   │   │   ├── ParentHomeScreen
│   │   │   │   ├── ChildManagementScreen
│   │   │   │   │   ├── ChildRow (enhanced)
│   │   │   │   │   └── AdjustmentModal (NEW)
│   │   │   │   └── AdjustmentHistoryScreen (NEW)
│   │   │   └── RewardsScreen
│   │   │       └── BalanceCard (reused)
```

## Detailed Implementation Guide

### Phase 1: Core Balance Integration

#### 1.1 Update User Type Definition

**File**: `src/types/user.ts` (create if doesn't exist)
```typescript
export interface User {
  id: number;
  username: string;
  role: 'parent' | 'child';
  is_parent: boolean;
  balance?: number; // NEW - optional for backward compatibility
  created_at: string;
  updated_at: string;
}
```

#### 1.2 Update Auth Service

**File**: `src/services/authService.js`
```javascript
// Update the login method to include balance
async login(username, password) {
  try {
    // ... existing code ...
    
    // Get user profile (now includes balance)
    const userResponse = await apiClient.get(API_ENDPOINTS.USERS.ME);
    const userData = userResponse.data;
    
    // Store complete user data including balance
    await storageService.setUserData(userData);
    
    return {
      success: true,
      user: userData, // Now includes balance field
    };
  } catch (error) {
    // ... existing error handling ...
  }
},

// Add new method to refresh just the balance
async refreshUserBalance() {
  try {
    const token = await storageService.getAuthToken();
    if (!token) return null;
    
    const response = await apiClient.get(API_ENDPOINTS.USERS.ME);
    const userData = response.data;
    
    // Update stored user data
    await storageService.setUserData(userData);
    
    return userData.balance;
  } catch (error) {
    console.error('Failed to refresh balance:', error);
    return null;
  }
},
```

#### 1.3 Enhance Auth Context

**File**: `src/store/authContext.js`
```javascript
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [lastBalanceUpdate, setLastBalanceUpdate] = useState(null); // NEW

  // ... existing code ...

  // NEW: Refresh balance method
  const refreshBalance = async () => {
    if (!user || user.role !== 'child') return;
    
    // Debounce: Don't refresh if updated in last 5 seconds
    const now = Date.now();
    if (lastBalanceUpdate && now - lastBalanceUpdate < 5000) {
      return;
    }
    
    const newBalance = await authService.refreshUserBalance();
    if (newBalance !== null) {
      setUser(prev => ({ ...prev, balance: newBalance }));
      setLastBalanceUpdate(now);
    }
  };

  // NEW: Update balance directly (for optimistic updates)
  const updateBalance = (newBalance) => {
    setUser(prev => ({ ...prev, balance: newBalance }));
    setLastBalanceUpdate(Date.now());
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    isParent: user?.role === 'parent',
    isChild: user?.role === 'child',
    login,
    logout,
    checkAuthState,
    refreshBalance, // NEW
    updateBalance, // NEW
    userBalance: user?.balance || 0, // NEW - convenient accessor
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

#### 1.4 Create Balance Card Component

**File**: `src/components/common/BalanceCard.js`
```javascript
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';
import { useAuth } from '../../store/authContext';

const BalanceCard = ({ onRefresh, showDetails = true }) => {
  const { userBalance, refreshBalance } = useAuth();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Animations
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const expandAnim = useRef(new Animated.Value(0)).current;
  
  // Animate on balance change
  useEffect(() => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 1.05,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, [userBalance]);
  
  const handleRefresh = async () => {
    if (isRefreshing) return;
    
    setIsRefreshing(true);
    
    // Rotate refresh icon
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      })
    ).start();
    
    await refreshBalance();
    if (onRefresh) await onRefresh();
    
    setIsRefreshing(false);
    rotateAnim.stopAnimation();
    rotateAnim.setValue(0);
  };
  
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
    Animated.timing(expandAnim, {
      toValue: isExpanded ? 0 : 1,
      duration: 300,
      useNativeDriver: false,
    }).start();
  };
  
  const rotateInterpolate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });
  
  return (
    <Animated.View style={[styles.container, { transform: [{ scale: scaleAnim }] }]}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Icon name="account-balance-wallet" size={24} color={colors.primary} />
          <Text style={styles.title}>My Balance</Text>
          <TouchableOpacity onPress={handleRefresh} disabled={isRefreshing}>
            <Animated.View style={{ transform: [{ rotate: rotateInterpolate }] }}>
              <Icon 
                name="refresh" 
                size={20} 
                color={isRefreshing ? colors.textSecondary : colors.primary} 
              />
            </Animated.View>
          </TouchableOpacity>
        </View>
        
        <Text style={styles.balance}>
          ${(userBalance || 0).toFixed(2)}
        </Text>
        
        {showDetails && (
          <TouchableOpacity onPress={toggleExpanded} style={styles.expandButton}>
            <Text style={styles.expandText}>
              {isExpanded ? 'Hide' : 'Show'} Details
            </Text>
            <Icon 
              name={isExpanded ? 'expand-less' : 'expand-more'} 
              size={20} 
              color={colors.primary} 
            />
          </TouchableOpacity>
        )}
      </View>
      
      {showDetails && (
        <Animated.View 
          style={[
            styles.details,
            {
              maxHeight: expandAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0, 200],
              }),
              opacity: expandAnim,
            },
          ]}
        >
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Earned from chores:</Text>
            <Text style={styles.detailValue}>$0.00</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Adjustments:</Text>
            <Text style={styles.detailValue}>$0.00</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Paid out:</Text>
            <Text style={[styles.detailValue, styles.negative]}>$0.00</Text>
          </View>
          <View style={[styles.detailRow, styles.totalRow]}>
            <Text style={styles.detailLabel}>Current balance:</Text>
            <Text style={styles.totalValue}>${(userBalance || 0).toFixed(2)}</Text>
          </View>
        </Animated.View>
      )}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    alignItems: 'center',
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    ...typography.body1,
    color: colors.text,
    marginHorizontal: 8,
    flex: 1,
  },
  balance: {
    ...typography.h1,
    color: colors.primary,
    fontSize: 36,
    fontWeight: 'bold',
    marginVertical: 8,
  },
  expandButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  expandText: {
    ...typography.caption,
    color: colors.primary,
    marginRight: 4,
  },
  details: {
    overflow: 'hidden',
    marginTop: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  detailLabel: {
    ...typography.body2,
    color: colors.textSecondary,
  },
  detailValue: {
    ...typography.body2,
    color: colors.text,
    fontWeight: '500',
  },
  negative: {
    color: colors.error,
  },
  totalRow: {
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    marginTop: 8,
    paddingTop: 12,
  },
  totalValue: {
    ...typography.body1,
    color: colors.primary,
    fontWeight: 'bold',
  },
});

export default BalanceCard;
```

#### 1.5 Update Child Home Screen

**File**: `src/screens/child/ChildHomeScreen.js` (modifications)
```javascript
// Add to imports
import BalanceCard from '../../components/common/BalanceCard';

// Remove the rewardScale animation and reward box code

// Replace renderHeader method
const renderHeader = () => (
  <Animated.View style={[styles.header, { opacity: headerOpacity }]}>
    <Text style={styles.greeting}>Hi {user?.username}! 👋</Text>
    <Text style={styles.subtitle}>Ready to complete some chores?</Text>
  </Animated.View>
);

// Update handleComplete to refresh balance
const handleComplete = async (choreId) => {
  try {
    const result = await choreService.completeChore(choreId);
    if (result.success) {
      showSuccess('Great job! Your chore has been submitted for approval.');
      
      // Refresh chores and balance
      setTimeout(() => {
        loadChores(true);
        refreshBalance(); // Add this
      }, 500);
    } else {
      showToastError(result.error || 'Failed to complete chore');
    }
  } catch (error) {
    showToastError('Failed to complete chore');
  }
};

// Update the return statement
return (
  <SafeAreaView style={styles.container}>
    <BalanceCard /> {/* Add this before ChoreList */}
    <ChoreList
      chores={chores}
      isLoading={isLoading}
      isRefreshing={isRefreshing}
      onRefresh={() => loadChores(true)}
      onChorePress={handleChorePress}
      showActions={true}
      onComplete={handleComplete}
      emptyMessage="No chores assigned yet. Check back later!"
      ListHeaderComponent={renderHeader}
    />
  </SafeAreaView>
);

// Remove reward-related styles
```

### Phase 2: Parent Adjustment Features

#### 2.1 Create Adjustment Service

**File**: `src/services/adjustmentService.js`
```javascript
import apiClient from '../api/client';
import { API_ENDPOINTS } from '../api/endpoints';

export const adjustmentService = {
  async createAdjustment(childId, amount, reason) {
    try {
      const response = await apiClient.post(API_ENDPOINTS.ADJUSTMENTS.CREATE, {
        child_id: childId,
        amount: parseFloat(amount),
        reason: reason.trim(),
      });
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorDetail = error.response?.data?.detail;
      
      // Handle specific error cases
      if (error.response?.status === 400 && errorDetail?.includes('negative balance')) {
        return {
          success: false,
          error: 'This adjustment would result in a negative balance',
        };
      }
      
      return {
        success: false,
        error: errorDetail || 'Failed to create adjustment',
      };
    }
  },
  
  async getChildAdjustments(childId, limit = 20, skip = 0) {
    try {
      const response = await apiClient.get(
        API_ENDPOINTS.ADJUSTMENTS.LIST_BY_CHILD(childId),
        {
          params: { limit, skip },
        }
      );
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch adjustments',
        data: [],
      };
    }
  },
  
  // Helper to format adjustment display
  formatAdjustment(adjustment) {
    const sign = adjustment.amount >= 0 ? '+' : '';
    const color = adjustment.amount >= 0 ? colors.success : colors.error;
    
    return {
      displayAmount: `${sign}$${Math.abs(adjustment.amount).toFixed(2)}`,
      color,
      date: new Date(adjustment.created_at).toLocaleDateString(),
      time: new Date(adjustment.created_at).toLocaleTimeString(),
    };
  },
};
```

#### 2.2 Update API Endpoints

**File**: `src/api/endpoints.js`
```javascript
export const API_ENDPOINTS = {
  // ... existing endpoints ...
  
  // Add new endpoints
  ADJUSTMENTS: {
    CREATE: '/adjustments/',
    LIST_BY_CHILD: (childId) => `/adjustments/child/${childId}`,
  },
};
```

#### 2.3 Create Adjustment Modal

**File**: `src/components/adjustments/AdjustmentModal.js`
```javascript
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
```

## Testing Strategy

### Unit Tests

**File**: `__tests__/services/adjustmentService.test.js`
```javascript
import { adjustmentService } from '../../src/services/adjustmentService';
import apiClient from '../../src/api/client';

jest.mock('../../src/api/client');

describe('AdjustmentService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  describe('createAdjustment', () => {
    it('should create adjustment successfully', async () => {
      apiClient.post.mockResolvedValueOnce({
        data: { id: 1, amount: 10, reason: 'Good behavior' },
      });
      
      const result = await adjustmentService.createAdjustment(
        1,
        10,
        'Good behavior'
      );
      
      expect(result.success).toBe(true);
      expect(result.data.amount).toBe(10);
    });
    
    it('should handle negative balance error', async () => {
      apiClient.post.mockRejectedValueOnce({
        response: {
          status: 400,
          data: { detail: 'Adjustment would result in negative balance' },
        },
      });
      
      const result = await adjustmentService.createAdjustment(1, -50, 'Test');
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('negative balance');
    });
  });
});
```

### Integration Test Checklist

1. **Balance Display**
   - [ ] Balance shows on child home screen
   - [ ] Balance updates after chore completion
   - [ ] Balance refreshes on pull-to-refresh
   - [ ] Balance animation works smoothly

2. **Adjustment Flow**
   - [ ] Parent can open adjustment modal
   - [ ] Preset amounts work correctly
   - [ ] Validation prevents invalid amounts
   - [ ] Submission updates child balance
   - [ ] Error messages display properly

3. **Performance**
   - [ ] Balance refresh is debounced
   - [ ] No unnecessary re-renders
   - [ ] Smooth animations on all devices

## Deployment Checklist

- [ ] Update app version in package.json
- [ ] Test on iOS simulator (iPhone 12+)
- [ ] Test on Android emulator (API 21+)
- [ ] Test on physical devices
- [ ] Update release notes
- [ ] Create signed builds
- [ ] Submit to app stores

## Common Issues & Solutions

### Issue: Balance not updating
**Solution**: Check auth token expiry and refresh logic

### Issue: Adjustment fails silently
**Solution**: Ensure error toast is shown, check API response

### Issue: Animation jank on Android
**Solution**: Use native driver where possible, reduce animation complexity

## API Response Examples

### GET /users/me Response
```json
{
  "id": 2,
  "username": "sarah",
  "role": "child",
  "is_parent": false,
  "balance": 25.50,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2025-01-02T10:30:00"
}
```

### POST /adjustments/ Response
```json
{
  "id": 1,
  "child_id": 2,
  "parent_id": 1,
  "amount": 10.00,
  "reason": "Extra help with yard work",
  "created_at": "2025-01-02T15:00:00"
}
```

### Error Response Format
```json
{
  "detail": "Specific error message here"
}
```