# Phase 3.2 Testing - Complete Chore Action

## Prerequisites
- Backend API running: `docker-compose up`
- Frontend dev server running: `npm run web`
- Demo users and chores created (from Phase 3.1)

## Test Scenarios

### 1. Complete Chore - Happy Path
1. **Login as child** (demochild/child123)
2. Navigate to **Chores** tab
3. View **Available** tab (default)
4. Click **"Mark as Complete"** button on any chore
5. **Verify confirmation dialog**:
   - Title: "Complete Chore"
   - Message includes chore name
   - Message mentions parent approval
   - Cancel and Complete buttons present
6. Click **Complete**
7. **Verify success feedback**:
   - Success alert shown
   - Message confirms sent for approval
   - Loading indicator appears during request
8. **Verify UI updates**:
   - Chore disappears from Available tab
   - Available tab count decreases
   - Pull-to-refresh shows updated list

### 2. Verify Chore State After Completion
1. Switch to **Active** tab
   - Completed chore should NOT appear here (it's pending approval, not active)
2. Switch to **Completed** tab
   - Chore should NOT appear here yet (not approved)
3. Refresh the **Available** tab
   - Completed chore should NOT reappear

### 3. Cancel Completion
1. Click **"Mark as Complete"** on another chore
2. Click **Cancel** in confirmation dialog
3. **Verify**:
   - Dialog closes
   - Chore remains in Available tab
   - No API call made

### 4. Error Handling
1. **Network error simulation** (turn off backend):
   - Complete a chore
   - Should show error alert
   - Chore should remain in Available tab
2. **Already completed chore** (if applicable):
   - Should not allow re-completion

### 5. Parent View - Pending Approval
1. **Login as parent** (demoparent/demo123)
2. Navigate to **Chores** tab
3. View **Available** tab (shows "Pending Approval" for parents)
4. **Verify completed chore appears**:
   - Shows "⏳ Pending Approval" status
   - Shows child who completed it
   - Ready for approval action (Phase 4.3)

### 6. Recurring Chore Behavior
1. Complete a recurring chore
2. After approval (Phase 4.3), verify:
   - Chore reappears in Available after cooldown period
   - Cooldown days respected

## API Verification

### Complete Chore Request
```bash
# Get child token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demochild&password=child123" 2>/dev/null | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Complete a chore
curl -X POST "http://localhost:8000/api/v1/chores/{CHORE_ID}/complete" \
  -H "Authorization: Bearer $TOKEN"
```

### Check Chore Status
```bash
# Get all chores to see status
curl -X GET "http://localhost:8000/api/v1/chores" \
  -H "Authorization: Bearer $TOKEN"
```

### Parent Check Pending
```bash
# Login as parent and check pending
PARENT_TOKEN=$(curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demoparent&password=demo123" 2>/dev/null | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X GET "http://localhost:8000/api/v1/chores/pending-approval" \
  -H "Authorization: Bearer $PARENT_TOKEN"
```

## UI/UX Improvements Added
1. ✅ Better confirmation message with chore name
2. ✅ Loading indicator on button during completion
3. ✅ Button disabled while processing
4. ✅ Success message mentions parent approval
5. ✅ Status text shows "Ready to Complete" for available chores
6. ✅ Visual feedback with opacity change during processing

## Test Results
- [x] Complete chore API call works
- [x] Chore removed from available list after completion
- [x] Chore appears in parent's pending approval
- [x] UI provides clear feedback during process
- [x] Error handling in place
- [x] State transitions are correct

## Phase 3.2 Status: COMPLETED ✅