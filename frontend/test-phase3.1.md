# Phase 3.1 Testing Checklist

## Test Setup
1. Backend API running: `docker-compose up`
2. Frontend dev server running: `npm run web` 
3. Test users created:
   - Parent: `demoparent` / `demo123`
   - Child: `demochild` / `child123`
4. Test chores created for demochild

## Test Scenarios

### 1. Child Login
- [x] Navigate to http://localhost:8081
- [x] Login with `demochild` / `child123`
- [x] Verify successful login
- [x] Verify user info shows "demochild" and role "child"

### 2. Chores List Display (Child View)
- [x] Navigate to Chores tab
- [x] Verify Available tab is visible and selected by default
- [x] Verify chores are displayed in Available tab (5 chores created)
- [x] Each chore card should show:
  - Title
  - Description
  - Reward amount (fixed or range)
  - "Mark as Complete" button
  - Recurring indicator if applicable

### 3. Tab Navigation
- [x] Click on Active tab
  - Should show no chores (none are active yet)
- [x] Click on Completed tab  
  - Should show no chores (none completed yet)
- [x] Click back on Available tab
  - Should show the 5 available chores

### 4. Complete Chore Action
- [x] Click "Mark as Complete" on any chore
- [x] Confirm in the alert dialog
- [x] Verify success message
- [x] Chore should disappear from Available tab
- [x] Navigate to Active tab - chore should appear here as pending approval

### 5. Refresh Functionality
- [x] Pull down to refresh on any tab
- [x] Verify loading indicator appears
- [x] Verify chores reload

## API Verification
```bash
# Get available chores for child
curl -X GET "http://localhost:8000/api/v1/chores/available" \
  -H "Authorization: Bearer [CHILD_TOKEN]"

# Complete a chore
curl -X POST "http://localhost:8000/api/v1/chores/{CHORE_ID}/complete" \
  -H "Authorization: Bearer [CHILD_TOKEN]"
```

## Known Issues Fixed
1. ✅ Conflicting HTML endpoint at `/api/v1/chores` - renamed to `/api/v1/html/chores`
2. ✅ ChoreResponse schema had lazy loading issues - removed `assignee` and `creator` fields
3. ✅ CORS not configured for localhost:8081 - added to allowed origins

## Phase 3.1 Status: COMPLETED ✅

All core functionality for child chores listing has been implemented and tested:
- Available chores screen shows assigned chores
- Active chores screen shows in-progress chores
- Completed chores screen shows finished chores
- Chore cards display all relevant information
- Tab navigation works correctly
- Pull-to-refresh functionality implemented
- Test data successfully created