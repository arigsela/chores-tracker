# Manual Testing Checklist & Bug Tracker

## Overview
This document serves as a comprehensive manual testing guide for the Chores Tracker application. Use this checklist to verify functionality and track any bugs discovered during testing.

**Application URLs:**
- Backend API: http://localhost:8000
- Frontend Web: http://localhost:8081
- API Documentation: http://localhost:8000/docs

**Test Date:** 2025-08-17
**Tester:** Ari Sela
**Version:** 2.0
**Phase 1 Status:** ✅ COMPLETE - All authentication and user management features tested and working
**Phase 2 Status:** ✅ COMPLETE - All chore management (parent) features tested and working

---

## 1. User Registration & Authentication

### 1.1 Parent Registration
- [X] Navigate to registration page
- [X] Fill in parent registration form
  - Username: asela
  - Password: password123
  - Email: (provided)
- [X] Submit registration
- [X] Verify success message
- [X] Verify automatic login after registration

**Issues Found:**
```
Date: 2025-08-12
Issue: No registration button/link on login page
Steps to Reproduce: 
  1. Navigate to http://localhost:8081
  2. View login page
Expected: Should see a "Sign Up" or "Register" link/button
Actual: Only login form visible with no way to register
Status: [X] Fixed - Added RegisterScreen and link from LoginScreen
```

**Test Notes:**
- Successfully created parent account "asela" with password "password123"
- Registration flow working correctly after fix
- Able to log in immediately after registration

### 1.2 Parent Login
- [X] Navigate to login page
- [X] Enter parent credentials
- [X] Submit login
- [X] Verify redirect to dashboard
- [X] Verify parent-specific UI elements visible

**Issues Found:**
```
No issues found - Working as expected
```

**Test Notes:**
- Logged in successfully with username "asela" and password "password123"
- Dashboard loaded correctly with parent-specific UI
- Parent tabs visible: Home, Chores, Children, Approvals, Profile

### 1.3 Child Account Creation (by Parent)
- [X] Login as parent
- [X] Navigate to user management
- [X] Create child account
  - Username: test_child1
  - Password: child123
- [X] Verify child appears in children list
- [X] Verify child can be selected in dropdowns

**Issues Found:**
```
Date: 2025-08-12
Issue: Create Account button does not work when creating child
Steps to Reproduce: 
  1. Login as parent (asela)
  2. Navigate to Children tab
  3. Click "+ Add Child" button
  4. Fill in child details
  5. Click "Create Account"
Expected: Child account should be created
Actual: Button clicks but nothing happens
Status: [ ] Open [X] Fixed - API endpoint corrected, form now working
```

**Test Notes:**
- Successfully created child account "test_child1" with password "child123"
- Child appears in children list immediately after creation
- Child details card shows correctly with chore statistics

### 1.4 Child Login
- [X] Logout from parent account
- [X] Login with child credentials
- [X] Verify redirect to child dashboard
- [X] Verify child-specific UI (no admin features)
- [X] Verify balance display is visible

**Issues Found:**
```
No issues found - Working as expected
```

**Test Notes:**
- Child login successful with "test_child1" account
- Child dashboard shows limited tabs: Home, Chores, Balance, Profile
- No admin features visible (no Children/Approvals tabs)
- Balance displayed prominently on home screen

### 1.5 Password Reset
- [X] Login as parent
- [X] Navigate to children management
- [X] Select "Reset Password" for a child
- [X] Enter new password
- [X] Verify success message
- [X] Logout and verify child can login with new password

**Issues Found:**
```
Date: 2025-08-12
Issue: Password reset used popup dialogs instead of proper form
Steps to Reproduce: 
  1. Login as parent
  2. Navigate to Children tab
  3. Click "Reset Password" on child card
Expected: Form should appear to enter new password
Actual: Browser confirm/alert popups appeared, then failed
Status: [ ] Open [X] Fixed - Replaced with modal form
Fix Details:
  - Removed all window.confirm() and window.alert() calls
  - Implemented clean modal with password input field
  - Added validation (minimum 3 characters)
  - Fixed API call to send password string directly
  - Modal auto-closes on success with feedback
```

**Test Notes:**
- Password reset now uses clean modal form interface
- Successfully reset password for "test_child1" to "newpass123"
- Verified child can login with new password
- No popups - much better user experience

---

## 2. Chore Management (Parent)

### 2.1 Create Fixed Reward Chore
- [X] Login as parent
- [X] Navigate to chore creation
- [X] Fill in chore details:
  - Title: Test Fixed Chore
  - Description: A basic fixed reward chore
  - Reward Type: Fixed
  - Amount: $5.00
  - Assignee: test_child1
- [X] Submit chore
- [X] Verify chore appears in list
- [X] Verify chore shows correct details

**Issues Found:**
```
Date: 2025-08-17
Issue: Success popup was showing after chore creation
Steps to Reproduce: 
  1. Create a new chore
  2. Click "Create Chore" 
Expected: Should create chore and return to list without popup
Actual: Showed "Chore created successfully" popup
Status: [ ] Open [X] Fixed - Removed success alert from ChoreFormScreen
```

### 2.2 Create Range Reward Chore
- [X] Create chore with range reward
  - Title: Test Range Chore
  - Min Reward: $3.00
  - Max Reward: $8.00
- [X] Verify range displayed correctly
- [X] Verify chore can be assigned to child

**Issues Found:**
```
Date: 2025-08-17
Issue: Range reward chores previously had input field issues
Steps to Reproduce: 
  1. Toggle range reward on
  2. Enter min/max values
Expected: Should accept numeric inputs and create chore
Actual: Previously had validation/input handling issues
Status: [ ] Open [X] Fixed - Range reward creation working properly
```

### 2.3 Create Recurring Chore
- [X] Create recurring chore
  - Cooldown period: 7 days
- [X] Verify recurring indicator shown
- [X] After completion, verify cooldown period enforced

**Issues Found:**
```
Date: 2025-08-17
Issue: Success popup was showing after recurring chore creation
Steps to Reproduce: 
  1. Create recurring chore
  2. Set cooldown days
  3. Submit form
Expected: Should create chore without popup
Actual: Previously showed success popup
Status: [ ] Open [X] Fixed - Success alert removed from creation flow
```

### 2.4 Edit Chore
- [X] Select existing chore
- [X] Click edit button
- [X] Modify chore details
- [X] Save changes
- [X] Verify changes reflected in list

**Issues Found:**
```
Date: 2025-08-17
Issue: Child names showed as "Child #ID" instead of actual names
Steps to Reproduce: 
  1. View chore list after creation/editing
  2. Check assignee field
Expected: Should show actual child usernames
Actual: Showed "Child #37", "Child #39" etc.
Status: [ ] Open [X] Fixed - Added child name lookup in ChoresManagementScreen
```

### 2.5 Delete/Disable Chore
- [X] Select chore to disable
- [X] Click disable/delete
- [X] Confirm action
- [X] Verify chore removed/disabled

**Issues Found:**
```
Date: 2025-08-17
Issue: Delete button was not working, showing console error
Steps to Reproduce: 
  1. Click delete button on a chore
  2. Check console
Expected: Should show confirmation dialog
Actual: Error "Unexpected text node: . A text node cannot be a child of a <View>"
Status: [ ] Open [X] Fixed - Removed CSS gap property, implemented cross-platform Alert utility
Fix Details:
  - Removed gap property causing React Native Web text node error
  - Created custom Alert utility for web compatibility
  - Delete confirmation now works properly
  - Removed redundant success alert after deletion
```

---

## 3. Chore Completion (Child)

### 3.1 View Assigned Chores
- [X] Login as child
- [X] Verify assigned chores visible
- [X] Verify chore details displayed
- [X] Verify reward amounts shown

**Issues Found:**
```
Date: 2025-08-17
Issue: No issues found - Working as expected
Steps to Reproduce: 
  1. Login as child (test_child1)
  2. Navigate to Chores tab
  3. View assigned chores list
Expected: Should show chores assigned to this child with details
Actual: Chores displayed correctly with titles, descriptions, and reward amounts
Status: [ ] Open [X] Working - All chore viewing functionality operational
```

### 3.2 Mark Chore as Complete
- [X] Select pending chore
- [X] Click "Mark as Complete"
- [X] Verify chore status changes to "Pending Approval"
- [X] Verify chore moves from available list
- [X] Verify API call succeeds

**Issues Found:**
```
Date: 2025-08-17
Issue: Multiple critical issues preventing chore completion
Steps to Reproduce: 
  1. Login as child (makoto/makoto123)
  2. Navigate to Chores tab, Available section
  3. Click "Mark as Complete" on any chore
Expected: Should complete chore and update UI
Actual: Multiple issues found and resolved:
  1. React Native Alert not working on web (clicking did nothing)
  2. CSS gap properties causing "Unexpected text node" errors
  3. Multiple confirmation popups creating poor UX
Status: [ ] Open [X] Fixed - Comprehensive fixes implemented
Fix Details:
  - Replaced React Native Alert with cross-platform Alert utility
  - Removed all CSS gap properties for React Native Web compatibility
  - Streamlined UX by removing confirmation and success popups
  - Chore completion now works seamlessly with immediate visual feedback
```

### 3.3 View Balance
- [X] Check balance display on dashboard
- [X] Verify balance card shows current amount
- [X] Complete a chore and verify balance doesn't change (pending approval)

**Issues Found:**
```
Date: 2025-08-18
Issue: Balance calculation was showing $6 instead of expected $9
Steps to Reproduce: 
  1. Complete 4 test chores totaling $9 ($1+$2+$3+$3 range reward)
  2. Have parent approve all chores
  3. Check balance in both child and parent views
Expected: Should show $9.00 total balance
Actual: Showed $6.00 instead
Status: [ ] Open [X] Fixed - Backend balance calculation now uses approval_reward field correctly
Fix Details:
  - Updated backend balance calculation to prioritize approval_reward field
  - Fixed both child balance endpoint and parent allowance summary
  - Added helper function matching frontend ChoreCard logic
  - Verified end-to-end with fresh test data showing correct $9.00 balance
```

### 3.4 Completed Chores Display
- [X] Navigate to Completed tab as child
- [X] Verify completed chores show correct status
- [X] Verify approved chores display actual reward amount (not range)
- [X] Verify completed chores count matches balance calculation

**Issues Found:**
```
Date: 2025-08-18
Issue: Multiple display issues with completed chores
Steps to Reproduce: 
  1. Complete and approve chores
  2. Check Completed tab filtering and status display
  3. Verify range reward chores show final approved amount
Expected: Should show all completed chores with correct status and final reward amounts
Actual: Several issues found and resolved:
  1. Completed tab was empty - filtering logic incorrect
  2. Approved chores still showed "Pending Approval" status
  3. Range reward chores showed range instead of final approved amount
Status: [ ] Open [X] Fixed - Comprehensive completed chore display improvements
Fix Details:
  - Fixed completed tab filtering to use both assignee_id and assigned_to_id fields
  - Updated ChoreCard status logic to check both approved_at and is_approved fields
  - Implemented proper reward display prioritizing approval_reward for final amounts
  - Added comprehensive status checking for accurate chore state display
```

---

## 4. Chore Approval (Parent)

### 4.1 View Pending Approvals
- [X] Login as parent
- [X] Navigate to pending approvals
- [X] Verify list shows completed chores awaiting approval
- [X] Verify child name and completion time shown

**Issues Found:**
```
Date: 2025-08-18
Issue: Parent not seeing pending approval counts when children completed chores
Steps to Reproduce: 
  1. Have child (makoto) complete chores
  2. Login as parent (asela)
  3. Check Children tab for pending approval counts
Expected: Should show pending counts for each child with completed chores
Actual: Pending counts showed 0 even when chores were completed
Status: [ ] Open [X] Fixed - Updated ChildrenScreen to use consistent API endpoints
Fix Details:
  - Updated pending chores fetching to use choreAPI.getPendingApprovalChores()
  - Fixed API endpoint consistency between parent and child views
  - Parent now correctly sees when children complete chores requiring approval
```

### 4.2 Approve Fixed Reward Chore
- [X] Select pending fixed reward chore
- [X] Click approve
- [X] Verify approval confirmation
- [X] Verify chore moves to approved list
- [X] Verify reward amount applied

**Issues Found:**
```
Date: 2025-08-18
Issue: Component import/export errors preventing chore approval
Steps to Reproduce: 
  1. Navigate to ChildDetailScreen via Children > View Details > Pending tab
  2. Try to approve a pending chore
Expected: Should show approval interface and process approval
Actual: Multiple component errors prevented functionality:
  1. "Element type is invalid" error - ChoreCard default import issue
  2. "Alert.prompt is not a function" - Missing prompt method in Alert utility
Status: [ ] Open [X] Fixed - Fixed component imports and Alert utility
Fix Details:
  - Changed ChoreCard from default import to named import in ChildDetailScreen
  - Implemented prompt method in custom Alert utility for range reward approvals
  - Fixed cross-platform Alert compatibility for React Native Web
  - Fixed reward chore approval now works seamlessly
```

### 4.3 Approve Range Reward Chore
- [X] Select pending range reward chore
- [X] Enter specific reward amount (within range)
- [X] Submit approval
- [X] Verify amount applied correctly
- [X] Verify cannot exceed max amount

**Issues Found:**
```
Date: 2025-08-18
Issue: Range reward approvals integrated with same fixes as fixed rewards
Steps to Reproduce: 
  1. Complete range reward chore ($1-$5 range)
  2. Parent approves and sets specific amount ($3)
  3. Verify amount validation and storage
Expected: Should prompt for amount within range and store in approval_reward field
Actual: Working correctly after component and Alert utility fixes
Status: [ ] Open [X] Fixed - Range reward approval works with custom Alert.prompt
Fix Details:
  - Alert.prompt method implemented for range reward amount entry
  - Range validation ensures amount is within min/max bounds
  - Approval_reward field correctly stores final approved amount
  - Both frontend and backend properly handle range reward approvals
  - End-to-end testing confirmed $3 approval for $1-$5 range chore
```

### 4.4 Reject Chore
- [X] Select pending chore
- [X] Click reject/return
- [ ] Add rejection reason
- [ ] Verify chore returned to pending
- [ ] Verify child can see rejection reason

**Issues Found:**
```
Date: 2025-08-18
Issue: Reject functionality partially implemented but non-functional
Steps to Reproduce: 
  1. Create chore as parent (asela) and assign to child (makoto)
  2. Complete chore as child (makoto)
  3. Login as parent (asela) and navigate to pending approvals
  4. Click the "Reject" button on the pending chore
Expected: Should show rejection reason modal, allow reason input, and return chore to available status
Actual: Reject button is visible and clickable but nothing happens when clicked
Status: [X] Open [ ] Fixed - Reject feature requires implementation completion
Test Results:
  ✅ UI elements exist (reject button present in approvals interface)
  ✅ Pending approvals workflow functions correctly
  ✅ Approval functionality works perfectly as baseline comparison
  ❌ Reject button click produces no visible response or state change
  ❌ No rejection reason modal or form appears
  ❌ No state transition from pending back to available
  ❌ No rejection reason storage or display system
Implementation Needed:
  - Rejection reason input modal/form
  - Reject button click handler
  - State transition logic for rejected chores
  - Rejection reason display in child's view
  - Backend API endpoint for rejection workflow
```

---

## 5. Reward Adjustments

### 5.1 Add Bonus
- [X] Login as parent
- [X] Navigate to child's profile
- [X] Add positive adjustment
  - Amount: $5.00
  - Reason: "Good behavior bonus"
- [X] Verify balance increases
- [X] Verify adjustment in history

**Issues Found:**
```
Date: 2025-08-18
Issue: Critical UI feedback failure - bonus functionality works but appears broken to users
Steps to Reproduce: 
  1. Login as parent (asela)
  2. Navigate to Children tab, select makoto
  3. Add bonus: $5.00 with reason "Good behavior bonus"
  4. Click "Apply Bonus" button
Expected: Modal should close and refresh the interface
Actual: Modal stays open with form data, no feedback given (though bonus actually applied successfully)
Status: [ ] Open [X] Fixed - Complete UI feedback and popup removal implemented

Test Evidence - FUNCTIONALITY WORKS:
  ✅ API call succeeds (POST /api/v1/adjustments/ → 201 Created)
  ✅ Balance increased correctly ($16.50 → $21.50)
  ✅ Adjustment history updated (1 → 2 adjustments)
  ✅ Database persistence confirmed
  ✅ All bonus calculations accurate

Fixed Issues:
  ✅ Modal closes immediately after successful submission
  ✅ Form resets after successful submission
  ✅ Interface refreshes to show changes
  ✅ Removed unwanted success popup per user request
  ✅ Clean, professional UX without interrupting popups

Fix Details:
  - Replaced React Native Alert with cross-platform Alert utility
  - Implemented immediate onSuccess() callback for modal closure
  - Added form reset and data refresh on successful submission
  - Removed success alert popup for streamlined user experience
```

### 5.2 Add Penalty
- [X] Add negative adjustment
  - Amount: -$2.50
  - Reason: "Deduction for incomplete chores"
- [X] Verify balance decreases
- [X] Verify cannot go below zero

**Issues Found:**
```
Date: 2025-08-18
Issue: Penalty/deduction functionality works identically to bonus system
Steps to Reproduce: 
  1. Login as parent (asela)
  2. Navigate to Children tab, select child
  3. Add deduction: -$2.50 with reason "Deduction for incomplete chores"
  4. Click "Apply Deduction" button
Expected: Should deduct amount from balance and close modal cleanly
Actual: Works perfectly with same fixes applied to bonus system
Status: [ ] Open [X] Fixed - Identical to bonus system, all improvements applied

Test Evidence:
  ✅ Deduction properly applied to balance
  ✅ Modal closes immediately after submission
  ✅ Form resets and interface refreshes
  ✅ Adjustment history updated correctly
  ✅ No unwanted popups or UI feedback issues
  ✅ Cross-platform Alert utility works for validation errors
```

---

## 6. Dashboard & Reports

### 6.1 Parent Dashboard
- [X] View children overview
- [X] Check pending approvals count
- [X] View recent activity
- [X] Check total rewards summary
- [X] Verify all children listed

**Issues Found:**
```
Date: 2025-08-18
Issue: Dashboard missing comprehensive recent activity and total rewards summary features
Steps to Reproduce: 
  1. Login as parent (asela)
  2. View dashboard/home page
  3. Look for recent activity section and total rewards summary
Expected: Should show recent chore completions, approvals, and financial summaries
Actual: Dashboard shows basic stats (pending approvals, active chores) but lacks:
  - Recent activity feed (chore completions, approvals, adjustments)
  - Total rewards summary (total paid out, pending payments)
  - Children overview list with individual balances
Status: [X] Open [ ] Fixed - Features not implemented, dashboard shows minimal stats only

Current Dashboard Features:
  ✅ Welcome message with username
  ✅ Pending approvals count
  ✅ Active chores count
  ✅ Quick action buttons (Create New Chore, Manage Children)
  ✅ Clickable navigation working properly

Missing Features Identified:
  ❌ Recent activity feed showing latest chore completions/approvals
  ❌ Total rewards summary with financial overview
  ❌ Children overview list on dashboard
  ❌ Recent adjustments/bonus activity
  ❌ Weekly/monthly summary statistics

Note: Basic dashboard functionality works well, but comprehensive reporting features would enhance parent oversight
```

### 6.2 Child Dashboard
- [X] View current balance prominently
- [X] Check assigned chores
- [X] View completed chores
- [ ] Check reward history
- [X] Verify no admin features visible

**Issues Found:**
```
Date: 2025-08-18
Issue: Child dashboard missing dedicated reward history feature
Steps to Reproduce: 
  1. Login as child (makoto/makoto123)
  2. Navigate through available tabs and screens
  3. Look for dedicated reward/earnings history view
Expected: Should have access to reward history showing earned amounts and dates
Actual: Most functionality works correctly, but reward history not implemented as standalone feature
Status: [X] Open [ ] Fixed - Reward history not implemented, but related features working

Working Child Dashboard Features:
  ✅ Balance displayed prominently on home screen
  ✅ Assigned chores visible in Chores tab
  ✅ Completed chores viewable with correct filtering
  ✅ No admin features visible (no Children/Approvals tabs)
  ✅ Child-specific navigation (Home, Chores, Balance, Profile only)
  ✅ Proper role-based access control

Missing Feature:
  ❌ Dedicated reward history/earnings report showing:
    - Historical earned amounts by chore
    - Adjustment history (bonuses/deductions)
    - Date-based earnings summary
    - Total earnings over time

Note: Child can view completed chores with reward amounts, and balance is accurate, 
but a comprehensive reward history view would enhance transparency
```

### 6.3 Allowance Summary
- [ ] Login as parent
- [ ] View allowance summary
- [ ] Verify totals per child
- [ ] Check earned vs paid out
- [ ] Verify adjustments included

**Issues Found:**
```
Date: 2025-08-18
Issue: Allowance summary page/feature not implemented
Steps to Reproduce: 
  1. Login as parent (asela)
  2. Navigate through all available tabs and screens
  3. Look for allowance summary, financial reports, or earnings overview
Expected: Should have dedicated allowance summary showing financial overview per child
Actual: No allowance summary page or feature exists in the application
Status: [X] Open [ ] Fixed - Feature not implemented

Missing Allowance Summary Feature:
  ❌ No dedicated allowance/financial summary page
  ❌ No totals per child in consolidated view
  ❌ No earned vs paid out tracking
  ❌ No adjustments summary in financial context
  ❌ No historical financial reporting
  ❌ No export capabilities for financial data

Current Financial Information Available:
  ✅ Individual child balances visible in Children tab
  ✅ Individual adjustment history in child detail screens
  ✅ Individual chore completion/approval tracking
  ✅ Real-time balance calculations working correctly

Note: While individual child financial data is accessible through various screens,
a consolidated allowance summary would provide parents with comprehensive
financial oversight and reporting capabilities.
```

---

## Bug Summary

### Critical Bugs (Blocking)
1. [FIXED] No registration button on login page - Users cannot create accounts
2. [FIXED] Quick Action buttons on parent dashboard not clickable - Changed to TouchableOpacity
3. [FIXED] Child account creation not working - API endpoint corrected
4. [FIXED] Password reset using popups and failing - Replaced with modal form

### Major Bugs (High Priority)
1. ___________
2. ___________
3. ___________

### Minor Bugs (Low Priority)
1. ___________
2. ___________
3. ___________

### Enhancement Requests
1. ___________
2. ___________
3. ___________

---

## Test Environment Details

**Browser:** ___________
**Browser Version:** ___________
**Operating System:** ___________
**Screen Resolution:** ___________
**Network:** [ ] Local [ ] Remote
**Database:** [ ] Empty [ ] Seeded

---

## Sign-off

**Testing Completed By:** ___________
**Date:** ___________
**Signature:** ___________

**Reviewed By:** ___________
**Date:** ___________
**Signature:** ___________

---

## Notes & Observations

```
[Add any additional notes, observations, or recommendations here]




```

---

## Test Data Reference

### Default Test Accounts
```
Parent User:
Username: test_parent
Password: TestPass123!
Email: parent@test.com

Child User:
Username: test_child
Password: ChildPass123!
```

### Sample Chores
```
Fixed Reward:
- Clean Room: $5.00
- Take Out Trash: $2.00

Range Reward:
- Wash Dishes: $3.00 - $8.00
- Mow Lawn: $10.00 - $20.00

Recurring:
- Feed Pet: $1.00 (Daily)
- Water Plants: $2.00 (Every 3 days)
```