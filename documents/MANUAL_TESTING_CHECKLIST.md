# Manual Testing Checklist & Bug Tracker

## Overview
This document serves as a comprehensive manual testing guide for the Chores Tracker application. Use this checklist to verify functionality and track any bugs discovered during testing.

**Application URLs:**
- Backend API: http://localhost:8000
- Frontend Web: http://localhost:8081
- API Documentation: http://localhost:8000/docs

**Test Date:** ___________
**Tester:** ___________
**Version:** ___________

---

## 1. User Registration & Authentication

### 1.1 Parent Registration
- [ ] Navigate to registration page
- [ ] Fill in parent registration form
  - Username: ___________
  - Password: ___________
  - Email: ___________
- [ ] Submit registration
- [ ] Verify success message
- [ ] Verify automatic login after registration

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 1.2 Parent Login
- [ ] Navigate to login page
- [ ] Enter parent credentials
- [ ] Submit login
- [ ] Verify redirect to dashboard
- [ ] Verify parent-specific UI elements visible

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 1.3 Child Account Creation (by Parent)
- [ ] Login as parent
- [ ] Navigate to user management
- [ ] Create child account
  - Username: ___________
  - Password: ___________
- [ ] Verify child appears in children list
- [ ] Verify child can be selected in dropdowns

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 1.4 Child Login
- [ ] Logout from parent account
- [ ] Login with child credentials
- [ ] Verify redirect to child dashboard
- [ ] Verify child-specific UI (no admin features)
- [ ] Verify balance display is visible

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 1.5 Password Reset
- [ ] Login as parent
- [ ] Navigate to children management
- [ ] Select "Reset Password" for a child
- [ ] Enter new password
- [ ] Verify success message
- [ ] Logout and verify child can login with new password

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 2. Chore Management (Parent)

### 2.1 Create Fixed Reward Chore
- [ ] Login as parent
- [ ] Navigate to chore creation
- [ ] Fill in chore details:
  - Title: ___________
  - Description: ___________
  - Reward Type: Fixed
  - Amount: $___________
  - Assignee: ___________
- [ ] Submit chore
- [ ] Verify chore appears in list
- [ ] Verify chore shows correct details

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 2.2 Create Range Reward Chore
- [ ] Create chore with range reward
  - Title: ___________
  - Min Reward: $___________
  - Max Reward: $___________
- [ ] Verify range displayed correctly
- [ ] Verify chore can be assigned to child

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 2.3 Create Recurring Chore
- [ ] Create recurring chore
  - Cooldown period: ___________ hours
- [ ] Verify recurring indicator shown
- [ ] After completion, verify cooldown period enforced

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 2.4 Edit Chore
- [ ] Select existing chore
- [ ] Click edit button
- [ ] Modify chore details
- [ ] Save changes
- [ ] Verify changes reflected in list

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 2.5 Delete/Disable Chore
- [ ] Select chore to disable
- [ ] Click disable/delete
- [ ] Confirm action
- [ ] Verify chore removed/disabled

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 3. Chore Completion (Child)

### 3.1 View Assigned Chores
- [ ] Login as child
- [ ] Verify assigned chores visible
- [ ] Verify chore details displayed
- [ ] Verify reward amounts shown

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 3.2 Mark Chore as Complete
- [ ] Select pending chore
- [ ] Click "Mark as Complete"
- [ ] Verify confirmation message
- [ ] Verify chore status changes to "Pending Approval"
- [ ] Verify chore moves to completed section

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 3.3 View Balance
- [ ] Check balance display on dashboard
- [ ] Verify balance card shows current amount
- [ ] Complete a chore and verify balance doesn't change (pending approval)

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 4. Chore Approval (Parent)

### 4.1 View Pending Approvals
- [ ] Login as parent
- [ ] Navigate to pending approvals
- [ ] Verify list shows completed chores awaiting approval
- [ ] Verify child name and completion time shown

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 4.2 Approve Fixed Reward Chore
- [ ] Select pending fixed reward chore
- [ ] Click approve
- [ ] Verify approval confirmation
- [ ] Verify chore moves to approved list
- [ ] Verify reward amount applied

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 4.3 Approve Range Reward Chore
- [ ] Select pending range reward chore
- [ ] Enter specific reward amount (within range)
- [ ] Submit approval
- [ ] Verify amount applied correctly
- [ ] Verify cannot exceed max amount

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 4.4 Reject Chore
- [ ] Select pending chore
- [ ] Click reject/return
- [ ] Add rejection reason
- [ ] Verify chore returned to pending
- [ ] Verify child can see rejection reason

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 5. Reward Adjustments

### 5.1 Add Bonus
- [ ] Login as parent
- [ ] Navigate to child's profile
- [ ] Add positive adjustment
  - Amount: $___________
  - Reason: ___________
- [ ] Verify balance increases
- [ ] Verify adjustment in history

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 5.2 Add Penalty
- [ ] Add negative adjustment
  - Amount: -$___________
  - Reason: ___________
- [ ] Verify balance decreases
- [ ] Verify cannot go below zero

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 6. Dashboard & Reports

### 6.1 Parent Dashboard
- [ ] View children overview
- [ ] Check pending approvals count
- [ ] View recent activity
- [ ] Check total rewards summary
- [ ] Verify all children listed

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 6.2 Child Dashboard
- [ ] View current balance prominently
- [ ] Check assigned chores
- [ ] View completed chores
- [ ] Check reward history
- [ ] Verify no admin features visible

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 6.3 Allowance Summary
- [ ] Login as parent
- [ ] View allowance summary
- [ ] Verify totals per child
- [ ] Check earned vs paid out
- [ ] Verify adjustments included

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 7. Mobile Responsiveness

### 7.1 Phone View (< 640px)
- [ ] Test registration flow
- [ ] Test login flow
- [ ] Test chore creation
- [ ] Test chore completion
- [ ] Verify touch targets adequate size
- [ ] Check text readability

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 7.2 Tablet View (768px - 1024px)
- [ ] Test dashboard layout
- [ ] Verify sidebar/navigation
- [ ] Check form layouts
- [ ] Test modal dialogs

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 8. Performance & Edge Cases

### 8.1 Large Data Sets
- [ ] Create 50+ chores
- [ ] Verify pagination works
- [ ] Check load times
- [ ] Test search/filter performance

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 8.2 Concurrent Users
- [ ] Login with parent in one browser
- [ ] Login with child in another
- [ ] Complete chore as child
- [ ] Verify parent sees update
- [ ] Approve as parent
- [ ] Verify child sees balance update

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 8.3 Session Management
- [ ] Stay logged in for extended period
- [ ] Verify session timeout works
- [ ] Test "Remember Me" functionality
- [ ] Verify logout clears session

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## 9. API Testing

### 9.1 Authentication Endpoints
- [ ] POST /api/v1/users/register
- [ ] POST /api/v1/users/login
- [ ] GET /api/v1/users/me

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 9.2 Chore Endpoints
- [ ] GET /api/v1/chores/
- [ ] POST /api/v1/chores/
- [ ] PUT /api/v1/chores/{id}
- [ ] DELETE /api/v1/chores/{id}
- [ ] POST /api/v1/chores/{id}/complete
- [ ] POST /api/v1/chores/{id}/approve

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

### 9.3 Error Handling
- [ ] Test invalid credentials
- [ ] Test missing required fields
- [ ] Test unauthorized access
- [ ] Verify error messages helpful

**Issues Found:**
```
Date: 
Issue: 
Steps to Reproduce: 
Expected: 
Actual: 
Status: [ ] Open [ ] Fixed
```

---

## Bug Summary

### Critical Bugs (Blocking)
1. ___________
2. ___________
3. ___________

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