# Mobile App File Changes Checklist

**Quick Reference**: Files to modify/create for balance and adjustment features

## Phase 1: Core Balance Integration

### Modified Files
- [ ] `src/api/endpoints.js` - Add ADJUSTMENTS endpoints
- [ ] `src/services/authService.js` - Add refreshUserBalance method
- [ ] `src/store/authContext.js` - Add balance state and methods
- [ ] `src/screens/child/ChildHomeScreen.js` - Replace potential rewards with balance
- [ ] `src/screens/child/RewardsScreen.js` - Add balance display

### New Files
- [ ] `src/types/user.ts` - User type definition with balance
- [ ] `src/components/common/BalanceCard.js` - Balance display component

## Phase 2: Parent Adjustment Features

### Modified Files
- [ ] `src/screens/parent/ChildManagementScreen.js` - Add adjust button and modal
- [ ] `src/navigation/MainNavigator.js` - Add AdjustmentHistoryScreen route

### New Files
- [ ] `src/services/adjustmentService.js` - Adjustment API service
- [ ] `src/components/adjustments/AdjustmentModal.js` - Adjustment creation modal
- [ ] `src/screens/parent/AdjustmentHistoryScreen.js` - View adjustment history

## Phase 3: Enhanced Features

### Modified Files
- [ ] `src/services/choreService.js` - Trigger balance refresh on completion
- [ ] `src/services/storageService.js` - Add balance caching methods
- [ ] `src/components/common/NetworkStatusBar.js` - Show sync status

### New Files
- [ ] `src/hooks/useBalanceSync.js` - Balance synchronization hook
- [ ] `src/utils/balanceCache.js` - Offline balance caching

## Phase 4: Testing

### New Files
- [ ] `__tests__/services/adjustmentService.test.js`
- [ ] `__tests__/components/BalanceCard.test.js`
- [ ] `__tests__/components/AdjustmentModal.test.js`
- [ ] `__tests__/integration/balanceFlow.test.js`

## File Modification Details

### 1. `src/api/endpoints.js`
```javascript
// Add after CHORES object
ADJUSTMENTS: {
  CREATE: '/adjustments/',
  LIST_BY_CHILD: (childId) => `/adjustments/child/${childId}`,
},
```

### 2. `src/services/authService.js`
```javascript
// Add new method after logout()
async refreshUserBalance() {
  // Implementation from detailed guide
}
```

### 3. `src/store/authContext.js`
```javascript
// Add state
const [lastBalanceUpdate, setLastBalanceUpdate] = useState(null);

// Add methods
const refreshBalance = async () => { /* ... */ };
const updateBalance = (newBalance) => { /* ... */ };

// Add to context value
refreshBalance,
updateBalance,
userBalance: user?.balance || 0,
```

### 4. `src/screens/child/ChildHomeScreen.js`
```javascript
// Add import
import BalanceCard from '../../components/common/BalanceCard';

// Remove reward box code (lines 152-162)
// Add <BalanceCard /> before <ChoreList>
// Update handleComplete to call refreshBalance
```

### 5. `src/screens/parent/ChildManagementScreen.js`
```javascript
// Add imports
import AdjustmentModal from '../../components/adjustments/AdjustmentModal';
import { adjustmentService } from '../../services/adjustmentService';

// Add state
const [adjustmentModal, setAdjustmentModal] = useState({ visible: false, child: null });

// Add adjust button to each child row
// Add <AdjustmentModal /> at end of component
```

## Component Tree Changes

```
Before:
ChildHomeScreen
├── Header (greeting)
├── RewardBox (potential rewards)
└── ChoreList

After:
ChildHomeScreen
├── BalanceCard (NEW - actual balance)
├── Header (greeting)
└── ChoreList
```

```
Before:
ChildManagementScreen
└── ChildList
    └── ChildRow (name only)

After:
ChildManagementScreen
├── ChildList
│   └── ChildRow (name + balance + adjust button)
└── AdjustmentModal (NEW)
```

## API Call Flow

### Balance Refresh Flow
1. User opens app → `authService.getCurrentUser()`
2. User data includes balance → Store in context
3. Pull to refresh → `authService.refreshUserBalance()`
4. Complete chore → `choreService.completeChore()` → `refreshBalance()`

### Adjustment Creation Flow
1. Parent taps adjust → Open modal
2. Enter amount/reason → Validate
3. Submit → `adjustmentService.createAdjustment()`
4. Success → Refresh child list with new balances

## State Management Changes

### AuthContext State
```javascript
// Before
{
  user: { id, username, role },
  isAuthenticated: boolean,
  isLoading: boolean,
}

// After
{
  user: { id, username, role, balance }, // balance added
  isAuthenticated: boolean,
  isLoading: boolean,
  lastBalanceUpdate: Date, // NEW
  userBalance: number, // NEW computed property
}
```

## Testing Checklist

### Manual Testing
- [ ] Child sees balance on home screen
- [ ] Balance updates after chore completion
- [ ] Parent can adjust child balance
- [ ] Adjustments show correct amount/reason
- [ ] Error messages display properly
- [ ] Offline mode works correctly

### Automated Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] No console errors
- [ ] No memory leaks
- [ ] Performance benchmarks met

## Common Gotchas

1. **Balance not showing**: Check if user object has balance field
2. **Adjustment fails**: Verify parent-child relationship in backend
3. **Animation jank**: Use `useNativeDriver: true` where possible
4. **State not updating**: Ensure proper state immutability

## Rollback Plan

If issues arise:
1. Revert to previous app version
2. Backend API remains compatible
3. No data migration needed
4. Users can continue using web app

---

**Tip**: Check off items as you complete them. This checklist can be used for PR reviews.