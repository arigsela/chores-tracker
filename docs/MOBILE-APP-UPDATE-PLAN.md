# Mobile App Update Implementation Plan

**Date**: January 2, 2025  
**Feature**: Sync mobile app with recent backend updates (balance display & adjustments)  
**Estimated Implementation Time**: 3-4 weeks  
**Code Reuse Target**: 80%+ (following LEVER framework)

## Executive Summary

This plan updates the React Native mobile application to match recent backend enhancements:
1. Child balance display with real-time updates
2. Parent adjustment capabilities (add/deduct from balances)
3. Improved data synchronization and error handling

## Current State Analysis

### Backend Changes (Completed)
- ✅ User model includes `balance` field
- ✅ New endpoint: `GET /api/v1/users/me/balance` (children only)
- ✅ New endpoints for adjustments: `POST /api/v1/adjustments/`, `GET /api/v1/adjustments/child/{id}`
- ✅ Balance calculation includes: earnings + adjustments - paid_out

### Mobile App Gaps
- ❌ No balance display (only shows "potential rewards")
- ❌ User object doesn't include balance field
- ❌ No adjustment creation for parents
- ❌ No adjustment history viewing
- ❌ Missing real-time balance synchronization

## Solution Architecture

### Design Principles (LEVER Framework)

**Leverage (80% reuse)**:
- Existing API client and authentication
- Current component patterns (cards, lists, modals)
- Error handling and toast notifications
- Animation utilities

**Extend**:
- Add balance to existing user context
- Enhance current reward displays
- Build on existing parent management screens

**Verify**:
- Role-based access (parent-only adjustments)
- Parent-child relationship validation
- Real-time data consistency

**Eliminate**:
- Remove duplicate reward calculations
- Consolidate balance display logic

**Reduce**:
- Minimal new components (2-3 total)
- Reuse existing UI patterns

## Implementation Phases

### Phase 1: Core Balance Integration (Week 1)
Enable children to see their current balance with proper data flow.

#### Subphase 1.1: Data Model Updates (Day 1-2)
**Estimated Time**: 8 hours

**Tasks**:
- [ ] Update user type definition to include balance field
- [ ] Modify authService to fetch and store balance
- [ ] Update AuthContext to expose balance data
- [ ] Add balance refresh method to auth context

**Code Changes**:
```javascript
// src/store/authContext.js - Add to user state
const [userBalance, setUserBalance] = useState(null);

// src/services/authService.js - Update getCurrentUser
const userResponse = await apiClient.get(API_ENDPOINTS.USERS.ME);
// User object now includes balance field
```

#### Subphase 1.2: Balance Display Component (Day 2-3)
**Estimated Time**: 6 hours

**Tasks**:
- [ ] Create BalanceCard component with animations
- [ ] Implement expandable details (earnings, adjustments, paid out)
- [ ] Add pull-to-refresh capability
- [ ] Style with existing color scheme

**Component Structure**:
```javascript
// src/components/common/BalanceCard.js
- Main balance display (large, prominent)
- Expand/collapse for details
- Loading skeleton during refresh
- Error state handling
```

#### Subphase 1.3: Screen Integration (Day 3-4)
**Estimated Time**: 8 hours

**Tasks**:
- [ ] Replace "Potential Rewards" with BalanceCard in ChildHomeScreen
- [ ] Add balance to RewardsScreen header
- [ ] Implement balance refresh on chore completion
- [ ] Add balance refresh to pull-to-refresh

**Key Integration Points**:
- ChildHomeScreen: Top of screen, before chore list
- RewardsScreen: Replace/enhance current summary card
- Trigger refresh after chore state changes

#### Subphase 1.4: Testing & Polish (Day 4-5)
**Estimated Time**: 6 hours

**Tasks**:
- [ ] Test balance updates after chore completion
- [ ] Verify animation smoothness
- [ ] Test error scenarios (network issues)
- [ ] Ensure proper number formatting

### Phase 2: Parent Adjustment Features (Week 2)
Enable parents to make balance adjustments with proper validation.

#### Subphase 2.1: Adjustment Service (Day 6-7)
**Estimated Time**: 6 hours

**Tasks**:
- [ ] Create adjustmentService.js
- [ ] Implement createAdjustment method
- [ ] Implement getChildAdjustments method
- [ ] Add proper error handling

**Service Methods**:
```javascript
// src/services/adjustmentService.js
- createAdjustment(childId, amount, reason)
- getChildAdjustments(childId, limit, skip)
- Error handling with specific messages
```

#### Subphase 2.2: Adjustment UI Components (Day 7-9)
**Estimated Time**: 12 hours

**Tasks**:
- [ ] Create AdjustmentModal component
- [ ] Add amount input with +/- controls
- [ ] Implement reason input with character count
- [ ] Add quick amount buttons ($5, $10, $20, -$5, -$10)
- [ ] Implement form validation

**Component Features**:
- Animated modal presentation
- Real-time validation feedback
- Loading state during submission
- Success animation on completion

#### Subphase 2.3: Parent Screen Integration (Day 9-10)
**Estimated Time**: 8 hours

**Tasks**:
- [ ] Add "Adjust Balance" button to ChildManagementScreen
- [ ] Display current balance for each child
- [ ] Integrate adjustment modal
- [ ] Implement balance refresh after adjustment
- [ ] Add adjustment history link

**UI Updates**:
- Each child row shows: Name, Balance, Actions
- Adjust button opens modal pre-filled with child data
- Success triggers immediate balance update

#### Subphase 2.4: Adjustment History (Day 10-11)
**Estimated Time**: 6 hours

**Tasks**:
- [ ] Create AdjustmentHistoryScreen
- [ ] Implement paginated list of adjustments
- [ ] Add date formatting and color coding
- [ ] Include reason display
- [ ] Add navigation from parent screens

### Phase 3: Enhanced Features (Week 3)
Polish, optimize, and add advanced capabilities.

#### Subphase 3.1: Real-time Synchronization (Day 12-13)
**Estimated Time**: 8 hours

**Tasks**:
- [ ] Implement background balance refresh
- [ ] Add WebSocket support (if available)
- [ ] Create sync indicator
- [ ] Handle concurrent updates

#### Subphase 3.2: Offline Support (Day 13-14)
**Estimated Time**: 8 hours

**Tasks**:
- [ ] Cache last known balance
- [ ] Queue adjustments for sync
- [ ] Show offline indicator
- [ ] Implement sync on reconnect

#### Subphase 3.3: Animations & Polish (Day 14-15)
**Estimated Time**: 6 hours

**Tasks**:
- [ ] Add balance change animations
- [ ] Implement celebration animation for increases
- [ ] Add haptic feedback
- [ ] Polish all transitions

### Phase 4: Testing & Deployment (Week 4)
Comprehensive testing and production preparation.

#### Subphase 4.1: Unit Testing (Day 16-17)
**Estimated Time**: 8 hours

**Tasks**:
- [ ] Test balance calculations
- [ ] Test adjustment validation
- [ ] Test service methods
- [ ] Test component rendering

#### Subphase 4.2: Integration Testing (Day 17-18)
**Estimated Time**: 8 hours

**Tasks**:
- [ ] Test full adjustment flow
- [ ] Test balance synchronization
- [ ] Test error scenarios
- [ ] Test offline behavior

#### Subphase 4.3: User Acceptance Testing (Day 18-19)
**Estimated Time**: 6 hours

**Tasks**:
- [ ] Parent user journey testing
- [ ] Child user journey testing
- [ ] Cross-device testing
- [ ] Performance testing

#### Subphase 4.4: Release Preparation (Day 19-20)
**Estimated Time**: 6 hours

**Tasks**:
- [ ] Update version numbers
- [ ] Prepare release notes
- [ ] Create app store builds
- [ ] Document any breaking changes

## Technical Specifications

### API Integration

**New Endpoints to Integrate**:
```javascript
// Add to src/api/endpoints.js
USERS: {
  ...existing,
  BALANCE: '/users/me/balance',
},
ADJUSTMENTS: {
  CREATE: '/adjustments/',
  LIST_BY_CHILD: (childId) => `/adjustments/child/${childId}`,
}
```

### State Management

**AuthContext Enhancements**:
```javascript
// Additional state
balance: number | null
lastBalanceUpdate: Date | null

// New methods
refreshBalance: () => Promise<void>
updateBalance: (newBalance: number) => void
```

### Error Handling

**Specific Error Cases**:
- 403: Child attempting parent action
- 400: Invalid adjustment amount
- 404: Child not found
- Network errors: Show cached data

### Performance Optimizations

- Debounce balance refresh (max once per 5 seconds)
- Lazy load adjustment history
- Cache adjustment presets
- Optimize re-renders with React.memo

## Security Considerations

1. **Role Validation**: Double-check user roles client-side
2. **Amount Validation**: Enforce -999.99 to 999.99 range
3. **Parent-Child Validation**: Verify relationships
4. **Token Refresh**: Handle expired tokens gracefully

## Success Metrics

- ✅ Children see current balance within 2 seconds of opening app
- ✅ Balance updates within 1 second of chore approval
- ✅ Parents can make adjustments in under 10 seconds
- ✅ All adjustments sync properly
- ✅ App remains responsive with 100+ adjustments
- ✅ Offline mode works seamlessly

## Risk Mitigation

**Risk**: API changes during development
- **Mitigation**: Version lock API, coordinate with backend team

**Risk**: Performance issues with large adjustment lists
- **Mitigation**: Implement pagination from start

**Risk**: Inconsistent balance calculations
- **Mitigation**: Single source of truth (backend), no client calculations

## Dependencies

- Backend API must remain stable
- Existing auth flow must not change
- React Native 0.80.0 compatibility
- iOS 13+ and Android 5.0+ support

## Post-Launch Enhancements

1. Push notifications for balance changes
2. Monthly balance reports
3. Export adjustment history
4. Bulk adjustment capabilities
5. Adjustment categories/tags

---

**Total Estimated Time**: 120 hours (3 weeks at full-time)
**Code Reuse**: 80%+ (leveraging existing patterns)
**New Components**: 3-4 major components
**Risk Level**: Low (building on stable foundation)