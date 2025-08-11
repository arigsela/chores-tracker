# Phase 3.3 Testing - Balance View

## Prerequisites
- Backend API running: `docker-compose up`
- Frontend dev server running: `npm run web`
- Demo users created (from Phase 3.1)
- Some chores completed (from Phase 3.2)

## Test Scenarios

### 1. Child Balance View
1. **Login as child** (demochild/child123)
2. Navigate to **Balance** tab
3. **Verify main balance card**:
   - Shows "Current Balance" label
   - Displays balance amount in large text
   - Shows formula "Earned + Bonuses - Paid Out"
4. **Verify balance details cards**:
   - Total Earned (green) - from approved chores
   - Adjustments (blue/red) - bonuses or deductions
   - Paid Out (gray) - amount already received
   - Pending Approval (orange) - if any chores pending
5. **Verify summary message**:
   - Different messages based on balance state
   - Mentions pending approval if applicable
   - Encouragement messages

### 2. Balance Calculation Verification
1. Complete a chore (if not already done)
2. Note the pending approval amount
3. Have parent approve the chore (Phase 4.3)
4. Return to balance screen
5. **Verify**:
   - Pending amount moves to Total Earned
   - Current Balance increases accordingly
   - Formula correctly calculates: Earned + Adjustments - Paid

### 3. Pull to Refresh
1. Pull down on balance screen
2. **Verify**:
   - Refresh indicator appears
   - Balance data reloads
   - Any changes are reflected

### 4. Parent View (Placeholder)
1. **Login as parent** (demoparent/demo123)
2. Navigate to **Balance** tab
3. **Verify placeholder**:
   - Shows "Family Balances" title
   - Message about Phase 4 availability
   - No error messages

### 5. Error Handling
1. **Network error** (turn off backend):
   - Should show error alert
   - Loading indicator should stop
2. **Invalid token** (if applicable):
   - Should redirect to login

### 6. Visual Design
- **Color coding**:
  - Green for earnings
  - Blue for positive adjustments
  - Red for negative adjustments
  - Orange for pending
  - Gray for paid out
- **Responsive layout**:
  - Cards adapt to screen size
  - Scrollable if content exceeds viewport
- **Typography hierarchy**:
  - Large balance amount
  - Clear section headers
  - Descriptive helper text

## API Verification

### Get Balance
```bash
# Get child token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demochild&password=child123" 2>/dev/null | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Get balance
curl -X GET "http://localhost:8000/api/v1/users/me/balance" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Expected Response
```json
{
  "balance": 0.0,
  "total_earned": 0.0,
  "adjustments": 0.0,
  "paid_out": 0.0,
  "pending_chores_value": 10.0
}
```

### Parent Access (Should Fail)
```bash
# Get parent token
PARENT_TOKEN=$(curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demoparent&password=demo123" 2>/dev/null | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Try to get balance (should return 403)
curl -X GET "http://localhost:8000/api/v1/users/me/balance" \
  -H "Authorization: Bearer $PARENT_TOKEN"
```

## UI Components Created
1. ✅ Balance API client (`/api/balance.ts`)
2. ✅ Enhanced BalanceScreen with full implementation
3. ✅ Main balance card with prominent display
4. ✅ Detail cards with color coding
5. ✅ Pull-to-refresh functionality
6. ✅ Loading and error states
7. ✅ Responsive summary messages

## Integration Points
- Balance updates after chore completion ✅
- Balance updates after parent approval (Phase 4.3)
- Balance updates after adjustments (Phase 4.4)
- Parent sees children summary (Phase 4.1)

## Test Results
- [x] Balance endpoint returns correct data
- [x] UI displays all balance components
- [x] Calculation formula is accurate
- [x] Parent access correctly denied
- [x] Pull-to-refresh works
- [x] Visual design is clear and informative

## Phase 3.3 Status: COMPLETED ✅

The balance view successfully displays:
- Current balance with clear visual hierarchy
- Breakdown of earnings, adjustments, and payments
- Pending approval amounts
- Contextual messages based on balance state
- Proper role-based access control