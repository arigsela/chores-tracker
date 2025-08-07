# Mobile App Testing Plan - Balance & Adjustment Features

## Overview
This document provides a comprehensive manual testing plan for the newly implemented balance display and adjustment features in the React Native mobile app. Test both iOS and Android platforms if possible.

## Test Environment Setup

### Prerequisites
1. Backend server running on `localhost:8000`
2. Mobile app built and running on device/simulator
3. Test data with at least:
   - 1 parent user account
   - 2-3 child user accounts
   - Some completed chores with rewards
   - Initial balance data

### Test Data Setup
Before testing, ensure you have:
- Parent user: `parent1` / `password123`
- Child users: `child1`, `child2` / `password123`
- Some chores created and approved to have initial balance data

---

## Phase 1: Core Balance Integration Tests

### Test 1.1: Balance Display on Child Home Screen
**User:** Child
**Objective:** Verify balance is displayed correctly

**Steps:**
1. Login as a child user
2. Navigate to Home screen
3. Observe the BalanceCard component

**Expected Results:**
- ✅ BalanceCard displays current balance amount
- ✅ Balance shows in currency format ($X.XX)
- ✅ Card has proper styling and animations
- ✅ Tapping card shows expandable details (if implemented)

**Test Cases:**
- [ ] Balance $0.00 (new user)
- [ ] Positive balance (e.g., $25.50)
- [ ] Large balance (e.g., $999.99)

---

### Test 1.2: Balance Updates After Chore Completion
**User:** Child → Parent → Child
**Objective:** Verify balance updates when chores are approved

**Steps:**
1. Login as child, complete a chore
2. Login as parent, approve the chore with reward amount
3. Login as child again, check balance

**Expected Results:**
- ✅ Child balance increases by approved reward amount
- ✅ Balance update is visible immediately upon returning to app
- ✅ BalanceCard reflects new amount correctly

---

### Test 1.3: Balance Refresh Functionality
**User:** Child
**Objective:** Test balance refresh mechanism

**Steps:**
1. Note current balance
2. Use another device/browser to make backend balance changes
3. Pull down to refresh or trigger balance refresh
4. Observe balance update

**Expected Results:**
- ✅ Balance refreshes and shows updated amount
- ✅ Refresh animation works smoothly
- ✅ No duplicate API calls (check network logs)

---

## Phase 2: Parent Adjustment Features Tests

### Test 2.1: Accessing Adjustment Modal
**User:** Parent
**Objective:** Verify adjustment modal opens correctly

**Steps:**
1. Login as parent
2. Navigate to Family/Children management screen
3. Find a child card
4. Tap "Adjust" button

**Expected Results:**
- ✅ AdjustmentModal opens with slide-up animation
- ✅ Modal shows child's name
- ✅ Amount input field is empty
- ✅ Reason input field is empty
- ✅ Preset buttons are visible and functional

---

### Test 2.2: Positive Balance Adjustments
**User:** Parent
**Objective:** Test adding money to child balance

**Steps:**
1. Open adjustment modal for a child
2. Test each preset positive amount (+$5, +$10, +$20)
3. Enter custom positive amount (e.g., $7.50)
4. Enter reason: "Extra chores completed"
5. Submit adjustment

**Expected Results:**
- ✅ Preset buttons populate amount field correctly
- ✅ Custom amounts accept decimal values
- ✅ Success message appears
- ✅ Modal closes after successful submission
- ✅ Child balance updates immediately in parent view
- ✅ Child sees updated balance when they log in

**Test Cases:**
- [ ] $5.00 preset
- [ ] $10.00 preset  
- [ ] $20.00 preset
- [ ] Custom amount: $1.25
- [ ] Custom amount: $99.99

---

### Test 2.3: Negative Balance Adjustments (Deductions)
**User:** Parent
**Objective:** Test removing money from child balance

**Steps:**
1. Open adjustment modal for a child with sufficient balance
2. Test preset negative amounts (-$5, -$10)
3. Enter custom negative amount (e.g., -$3.00)
4. Enter reason: "Allowance advance deduction"
5. Submit adjustment

**Expected Results:**
- ✅ Negative preset buttons work correctly
- ✅ Amount field shows negative values properly
- ✅ Balance decreases by adjustment amount
- ✅ Cannot create adjustment that would result in negative balance (if rule exists)

**Test Cases:**
- [ ] -$5.00 preset
- [ ] -$10.00 preset
- [ ] Custom amount: -$2.50
- [ ] Attempt to deduct more than current balance (should fail gracefully)

---

### Test 2.4: Adjustment Validation
**User:** Parent
**Objective:** Test input validation and error handling

**Test Cases:**
1. **Empty amount**
   - Leave amount field empty, try to submit
   - Expected: Error message "Please enter a valid amount"

2. **Zero amount**
   - Enter 0.00, try to submit
   - Expected: Error message about zero amount

3. **Invalid amount format**
   - Enter "abc", "5.555", "-0"
   - Expected: Proper validation and error messages

4. **Missing reason**
   - Enter valid amount, leave reason empty
   - Expected: Error message "Please provide a reason"

5. **Reason too short**
   - Enter valid amount, reason "hi"
   - Expected: Error message about minimum length

6. **Reason too long**
   - Enter valid amount, reason with 600 characters
   - Expected: Character limit enforcement

**Expected Results:**
- ✅ All validation errors display clearly
- ✅ Form doesn't submit with invalid data
- ✅ Error messages are user-friendly
- ✅ Character counter works for reason field

---

### Test 2.5: Adjustment History Navigation
**User:** Parent
**Objective:** Test navigation to adjustment history

**Steps:**
1. From child management screen
2. Find a child with existing adjustments
3. Tap "History" button for that child

**Expected Results:**
- ✅ Navigation to AdjustmentHistoryScreen works
- ✅ Screen title shows "Adjustment History"
- ✅ Child name appears in header
- ✅ Back navigation works correctly

---

### Test 2.6: Adjustment History Display
**User:** Parent
**Objective:** Verify adjustment history shows correctly

**Prerequisites:** Child should have several adjustments in history

**Steps:**
1. Navigate to adjustment history for a child
2. Observe the list of adjustments
3. Check different adjustment types (positive/negative)

**Expected Results:**
- ✅ Adjustments listed in reverse chronological order (newest first)
- ✅ Each adjustment shows: amount, reason, date, time
- ✅ Positive adjustments show with green color/icon
- ✅ Negative adjustments show with red color/icon
- ✅ Amounts formatted correctly (+$X.XX / -$X.XX)
- ✅ Dates and times display in proper format
- ✅ Long reasons display properly (no cutoff)

---

### Test 2.7: Adjustment History Pagination
**User:** Parent
**Objective:** Test pagination with large adjustment lists

**Prerequisites:** Child with 25+ adjustments (create test data if needed)

**Steps:**
1. Navigate to adjustment history
2. Scroll to bottom of list
3. Observe loading behavior
4. Continue scrolling through multiple pages

**Expected Results:**
- ✅ Initial load shows first 20 adjustments
- ✅ Loading indicator appears when fetching more
- ✅ Additional adjustments load smoothly
- ✅ No duplicate entries appear
- ✅ Performance remains smooth with large lists

---

### Test 2.8: Pull-to-Refresh in History
**User:** Parent
**Objective:** Test refresh functionality in adjustment history

**Steps:**
1. Open adjustment history
2. Pull down from top to trigger refresh
3. Create new adjustment in another session
4. Refresh history again

**Expected Results:**
- ✅ Pull-to-refresh animation works
- ✅ List refreshes and shows updated data
- ✅ New adjustments appear at top of list
- ✅ Refresh completes properly

---

## Phase 3: Integration & Cross-Platform Tests

### Test 3.1: Multi-User Balance Synchronization
**Objective:** Test balance consistency across different user sessions

**Steps:**
1. Login as parent, check child's balance
2. Create adjustment for child (+$10)
3. Login as that child on different device/session
4. Check if balance shows updated amount
5. Create another adjustment from parent
6. Switch back to child view

**Expected Results:**
- ✅ Balance updates are consistent across all sessions
- ✅ No data synchronization issues
- ✅ Changes reflect in real-time or upon app focus

---

### Test 3.2: Network Error Handling
**Objective:** Test app behavior during network issues

**Test Cases:**
1. **No Internet Connection**
   - Disconnect internet, try creating adjustment
   - Expected: Clear error message, graceful failure

2. **Slow Network**
   - Use slow network, observe loading states
   - Expected: Loading indicators, timeout handling

3. **Server Error**
   - If possible, test with backend returning 500 errors
   - Expected: User-friendly error messages

---

### Test 3.3: Navigation Flow Testing
**Objective:** Test all navigation paths work correctly

**Navigation Paths to Test:**
1. Parent Home → Family → Child Details → Adjustment Modal
2. Parent Home → Family → Child Details → Adjustment History
3. Adjustment History → Back to Child Details
4. Adjustment Modal → Cancel → Child Details
5. Child Home → Balance Card interactions
6. Deep linking (if implemented)

**Expected Results:**
- ✅ All navigation transitions work smoothly
- ✅ Back button behavior is correct
- ✅ No navigation stack issues
- ✅ Proper state preservation

---

## Phase 4: Performance & Edge Cases

### Test 4.1: Performance with Large Data Sets
**Objective:** Test app performance with large amounts of data

**Test Cases:**
1. Child with 100+ adjustments
2. Parent with 10+ children
3. Large balance amounts ($10,000+)
4. Very long adjustment reasons

**Expected Results:**
- ✅ Lists scroll smoothly
- ✅ No memory leaks or crashes
- ✅ Reasonable load times
- ✅ UI remains responsive

---

### Test 4.2: Edge Case Testing

**Balance Edge Cases:**
- [ ] Balance of exactly $0.00
- [ ] Very large balances ($999,999.99)
- [ ] Many decimal places in backend (should round to 2)

**Adjustment Edge Cases:**
- [ ] Adjustments with exactly same timestamp
- [ ] Special characters in reason field
- [ ] Very long child usernames
- [ ] Maximum and minimum allowed adjustment amounts

**UI Edge Cases:**
- [ ] Device rotation during adjustment creation
- [ ] App backgrounding/foregrounding during API calls
- [ ] Multiple rapid taps on buttons
- [ ] Keyboard covering input fields

---

## Phase 5: Accessibility & Usability

### Test 5.1: Accessibility Testing
**Objective:** Ensure features work with accessibility tools

**Tests:**
- [ ] VoiceOver/TalkBack navigation through adjustment screens
- [ ] Screen reader announces balance amounts correctly
- [ ] High contrast mode compatibility
- [ ] Large text size compatibility
- [ ] Touch target sizes adequate (minimum 44pt)

---

### Test 5.2: User Experience Testing
**Objective:** Validate user experience flows

**Scenarios:**
1. **New Parent User**: First time creating adjustment
2. **Power User**: Parent managing multiple children efficiently
3. **Child User**: Understanding balance changes
4. **Error Recovery**: User recovering from input mistakes

**Success Criteria:**
- ✅ Intuitive navigation flows
- ✅ Clear visual feedback
- ✅ Helpful error messages
- ✅ Efficient task completion

---

## Test Results Documentation

### Test Execution Checklist
For each test case:
- [ ] **Pass**: Works as expected
- [ ] **Fail**: Describe issue and steps to reproduce
- [ ] **Blocked**: Cannot test due to dependencies
- [ ] **Partial**: Works but has minor issues

### Bug Report Template
When reporting issues:

```
**Test Case:** [Test ID and name]
**Platform:** iOS/Android/Both
**Device:** [Device model and OS version]
**Severity:** Critical/High/Medium/Low

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:** [What should happen]
**Actual Result:** [What actually happened]
**Screenshots:** [If applicable]
**Additional Notes:** [Any other relevant information]
```

---

## Post-Testing Actions

### After Testing Completion:
1. **Summarize Results**: Create executive summary of test results
2. **Prioritize Issues**: Categorize bugs by severity and impact
3. **Performance Metrics**: Document load times and responsiveness
4. **User Feedback**: Gather feedback on user experience
5. **Regression Testing**: Plan for testing after bug fixes

### Success Criteria for Release:
- [ ] All critical and high-priority tests pass
- [ ] No data corruption or loss issues
- [ ] Acceptable performance on target devices
- [ ] Positive user experience feedback
- [ ] All accessibility requirements met

---

## Additional Testing Notes

### Test Data Reset
Between test runs, you may need to:
- Reset user balances to known values
- Clear adjustment history
- Create fresh test accounts

### Testing Tools
Recommended tools for thorough testing:
- Network throttling tools
- Device memory monitoring
- Performance profiling tools
- Accessibility scanners

### Automated Testing Opportunities
After manual testing, consider automating:
- API endpoint tests
- Component unit tests
- Integration test suites
- Performance regression tests

Good luck with testing! Please report any issues found during your testing sessions.