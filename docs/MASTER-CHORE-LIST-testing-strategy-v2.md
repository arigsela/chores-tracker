# Master Chore List Testing Strategy v2

## Overview

This document outlines the comprehensive testing strategy for the Master Chore List feature with the two new enhancements:
1. **Selective Visibility**: Hide specific chores from certain children
2. **Grayed Out Completed Chores**: Show completed chores as unavailable until reset based on recurrence

## Phased Testing Implementation Plan

### Phase 1: Unit Testing Foundation (1.5 days)

#### Subphase 1.1: Backend Unit Tests (0.5 day)
**Tasks:**
- [ ] Write tests for ChoreVisibility model
- [ ] Test recurrence calculation methods
- [ ] Test visibility filtering logic
- [ ] Test service layer methods

**Testing:**
- [ ] Model validation tests
- [ ] Business logic tests
- [ ] Edge case coverage
- [ ] Error handling tests

**Test Structure:**
```python
# tests/unit/test_visibility_service.py
class TestVisibilityService:
    def test_hide_chore_from_single_user()
    def test_hide_chore_from_multiple_users()
    def test_visibility_cascade_delete()
    def test_concurrent_visibility_updates()
```

#### Subphase 1.2: Frontend Unit Tests (0.5 day)
**Tasks:**
- [ ] Test visibility components
- [ ] Test timer calculations
- [ ] Test progress bar logic
- [ ] Test form validations

**Testing:**
- [ ] Component isolation tests
- [ ] State management tests
- [ ] Utility function tests
- [ ] Event handler tests

**JavaScript Tests:**
```javascript
// tests/unit/frontend/test_timer_logic.js
describe('Timer Calculations', () => {
  test('calculates daily reset correctly')
  test('handles timezone changes')
  test('shows correct progress percentage')
  test('triggers refresh at right time')
});
```

#### Subphase 1.3: Mobile Unit Tests (0.5 day)
**Tasks:**
- [ ] Test React Native components
- [ ] Test state management
- [ ] Test offline queue logic
- [ ] Test platform-specific code

**Testing:**
- [ ] Component rendering tests
- [ ] Hook behavior tests
- [ ] Service method tests
- [ ] Navigation tests

### Phase 2: Integration Testing (2 days)

#### Subphase 2.1: API Integration Tests (0.75 day)
**Tasks:**
- [ ] Test visibility endpoints
- [ ] Test chore claiming flow
- [ ] Test recurrence updates
- [ ] Test authorization

**Testing:**
- [ ] Request/response validation
- [ ] Error response handling
- [ ] Rate limiting tests
- [ ] Concurrent request tests

**API Test Suite:**
```python
# tests/integration/test_visibility_api.py
async def test_visibility_api_flow():
    # Create chore with visibility
    # Verify child cannot access
    # Update visibility
    # Verify access granted
```

#### Subphase 2.2: Database Integration Tests (0.75 day)
**Tasks:**
- [ ] Test visibility queries
- [ ] Test recurrence calculations
- [ ] Test transaction integrity
- [ ] Test migration scripts

**Testing:**
- [ ] Query performance tests
- [ ] Data integrity tests
- [ ] Cascade operation tests
- [ ] Index effectiveness tests

#### Subphase 2.3: Frontend Integration Tests (0.5 day)
**Tasks:**
- [ ] Test HTMX interactions
- [ ] Test visibility UI flow
- [ ] Test timer updates
- [ ] Test form submissions

**Testing:**
- [ ] Component interaction tests
- [ ] API call integration
- [ ] State synchronization
- [ ] Event propagation tests

### Phase 3: End-to-End Testing (2 days)

#### Subphase 3.1: Core Feature E2E Tests (1 day)
**Tasks:**
- [ ] Test complete visibility workflow
- [ ] Test recurrence lifecycle
- [ ] Test claiming conflicts
- [ ] Test multi-user scenarios

**Testing:**
- [ ] User journey tests
- [ ] Cross-role interactions
- [ ] Data consistency tests
- [ ] Real-time update tests

**E2E Scenarios:**
```gherkin
# tests/e2e/visibility_workflow.feature
Feature: Chore Visibility Management
  Scenario: Parent hides chore from specific child
    Given parent creates chore "Clean garage"
    When parent hides it from "Child A"
    Then "Child A" cannot see the chore
    And "Child B" can see and claim it
```

#### Subphase 3.2: Edge Case E2E Tests (0.5 day)
**Tasks:**
- [ ] Test timezone edge cases
- [ ] Test concurrent operations
- [ ] Test offline scenarios
- [ ] Test migration paths

**Testing:**
- [ ] Boundary condition tests
- [ ] Race condition tests
- [ ] Recovery scenario tests
- [ ] Backward compatibility tests

#### Subphase 3.3: Cross-Platform E2E Tests (0.5 day)
**Tasks:**
- [ ] Test web-mobile sync
- [ ] Test visibility across platforms
- [ ] Test timer consistency
- [ ] Test offline sync

**Testing:**
- [ ] Platform parity tests
- [ ] Sync accuracy tests
- [ ] UI consistency tests
- [ ] Performance comparison

### Phase 4: Performance and Load Testing (1.5 days)

#### Subphase 4.1: Backend Performance Tests (0.75 day)
**Tasks:**
- [ ] Test visibility query performance
- [ ] Test recurrence calculations under load
- [ ] Test concurrent user operations
- [ ] Test database query optimization

**Testing:**
- [ ] Response time benchmarks
- [ ] Throughput testing
- [ ] Resource utilization
- [ ] Scalability testing

**Performance Benchmarks:**
```javascript
// tests/performance/visibility_load.js
export default function() {
  // Create 1000 chores with visibility
  // Measure query performance
  // Target: <50ms for filtered list
  // Target: <100ms for bulk updates
}
```

#### Subphase 4.2: Frontend Performance Tests (0.75 day)
**Tasks:**
- [ ] Test rendering performance
- [ ] Test timer update efficiency
- [ ] Test memory usage
- [ ] Test animation smoothness

**Testing:**
- [ ] FPS measurements
- [ ] Memory profiling
- [ ] CPU usage monitoring
- [ ] Network efficiency tests

### Phase 5: Security and Accessibility Testing (1 day)

#### Subphase 5.1: Security Testing (0.5 day)
**Tasks:**
- [ ] Test visibility bypass attempts
- [ ] Test authorization checks
- [ ] Test data leakage prevention
- [ ] Test injection vulnerabilities

**Testing:**
- [ ] Penetration testing
- [ ] Authorization testing
- [ ] Input validation testing
- [ ] Session security testing

**Security Test Cases:**
```python
# tests/security/test_visibility_security.py
def test_cannot_view_hidden_chore_directly():
    """Ensure hidden chores cannot be accessed via direct API calls"""
    
def test_no_visibility_metadata_leak():
    """Ensure children don't see visibility settings"""
```

#### Subphase 5.2: Accessibility Testing (0.5 day)
**Tasks:**
- [ ] Test screen reader compatibility
- [ ] Test keyboard navigation
- [ ] Test color contrast
- [ ] Test focus management

**Testing:**
- [ ] WCAG compliance tests
- [ ] Screen reader tests
- [ ] Keyboard-only navigation
- [ ] Visual impairment tests

### Phase 6: User Acceptance Testing (1 day)

#### Subphase 6.1: Alpha Testing (0.5 day)
**Tasks:**
- [ ] Internal team testing
- [ ] Feature walkthrough
- [ ] Bug identification
- [ ] Feedback collection

**Testing:**
- [ ] Functionality verification
- [ ] Usability assessment
- [ ] Performance validation
- [ ] Edge case discovery

#### Subphase 6.2: Beta Testing (0.5 day)
**Tasks:**
- [ ] Select user testing
- [ ] Real-world scenarios
- [ ] Feedback analysis
- [ ] Final adjustments

**Testing:**
- [ ] User satisfaction surveys
- [ ] Task completion rates
- [ ] Error frequency tracking
- [ ] Performance metrics

## New Test Scenarios

### 1. Selective Visibility Testing

#### Backend Tests

```python
# backend/tests/test_chore_visibility.py

class TestChoreVisibility:
    async def test_create_chore_with_hidden_users(self):
        """Test creating a chore hidden from specific children"""
        # Create chore hidden from child1
        chore_data = {
            "title": "Clean bathroom",
            "hidden_from_users": [child1.id]
        }
        # Verify child1 cannot see the chore
        # Verify child2 can see the chore
    
    async def test_update_visibility_settings(self):
        """Test updating visibility after chore creation"""
        # Create normal chore
        # Update to hide from child1
        # Verify visibility change takes effect
    
    async def test_visibility_filtering_in_list(self):
        """Test chore list respects visibility settings"""
        # Create multiple chores with different visibility
        # Get list as child1 - verify hidden chores excluded
        # Get list as child2 - verify all visible
    
    async def test_parent_sees_all_chores(self):
        """Test parents always see all chores regardless of visibility"""
        # Create hidden chores
        # Get list as parent - verify all visible
    
    async def test_bulk_visibility_update(self):
        """Test updating visibility for multiple children at once"""
        # Update chore to hide from [child1, child2]
        # Verify both children cannot see it
```

#### Frontend Tests

```javascript
// frontend/tests/visibility.test.js

describe('Chore Visibility UI', () => {
  test('visibility checkboxes in create form', () => {
    // Render create form
    // Verify all children listed with checkboxes
    // Check some boxes
    // Submit and verify API call includes hidden_from_users
  });

  test('visibility indicator on parent dashboard', () => {
    // Render chore with visibility restrictions
    // Verify "Hidden from X" badge appears
    // Click to open visibility modal
  });

  test('child cannot see hidden chores', () => {
    // Login as child with hidden chores
    // Verify hidden chores not in available list
    // Verify no way to access hidden chores
  });
});
```

#### Mobile Tests

```typescript
// mobile/tests/visibility.test.tsx

describe('Mobile Visibility Features', () => {
  it('should filter chores based on visibility', async () => {
    // Mock API to return chores with visibility data
    // Render chores screen as child
    // Verify hidden chores not displayed
  });

  it('should allow parent to manage visibility', async () => {
    // Render visibility management screen
    // Toggle child visibility
    // Save and verify API call
  });
});
```

### 2. Grayed Out Completed Chores Testing

#### Backend Tests

```python
# backend/tests/test_chore_recurrence.py

class TestChoreRecurrence:
    async def test_daily_recurrence_calculation(self):
        """Test daily chore reset time calculation"""
        # Complete chore at 3pm
        # Verify next_available_time is tomorrow midnight
        # Verify chore not available until then
    
    async def test_weekly_recurrence_calculation(self):
        """Test weekly chore reset on specific day"""
        # Complete Monday chore on Monday
        # Verify next_available_time is next Monday
        # Test edge cases (complete on Sunday, etc)
    
    async def test_monthly_recurrence_edge_cases(self):
        """Test monthly recurrence with edge cases"""
        # Test 31st of month (February, April, etc)
        # Test leap years
        # Verify proper date handling
    
    async def test_chore_availability_check(self):
        """Test chore availability based on reset time"""
        # Complete chore with daily recurrence
        # Try to complete again - should fail
        # Advance time past reset
        # Verify now available
    
    async def test_timezone_handling(self):
        """Test reset times across timezones"""
        # Create chore in one timezone
        # Complete in another timezone
        # Verify correct reset calculation
```

#### Frontend Tests

```javascript
// frontend/tests/recurrence.test.js

describe('Recurrence UI Tests', () => {
  test('completed chores show as grayed out', () => {
    // Render chore list with completed chores
    // Verify grayed out styling applied
    // Verify "Available in X hours" displayed
    // Verify claim button disabled
  });

  test('progress bar updates correctly', () => {
    // Render completed chore with progress
    // Verify progress bar width matches time elapsed
    // Mock time passing
    // Verify progress updates
  });

  test('auto-refresh when chore becomes available', async () => {
    // Render with completed chore near reset time
    // Fast-forward time past reset
    // Verify chore moves to available section
  });

  test('recurrence settings in create form', () => {
    // Toggle recurrence checkbox
    // Verify recurrence options appear
    // Select weekly, pick day
    // Submit and verify data
  });
});
```

#### Mobile Tests

```typescript
// mobile/tests/recurrence.test.tsx

describe('Mobile Recurrence Features', () => {
  it('should display countdown timer accurately', () => {
    // Render completed chore card
    // Verify timer shows correct time
    // Advance time by 1 hour
    // Verify timer updates
  });

  it('should handle app background/foreground', async () => {
    // Complete chore
    // Background app
    // Advance time past reset
    // Foreground app
    // Verify chore now available
  });
});
```

## Integration Test Scenarios

### Scenario 1: Complete Visibility Flow
```gherkin
Feature: Chore Visibility Management
  Scenario: Parent hides chore from specific child
    Given a parent with two children
    When parent creates chore "Clean garage" hidden from Child A
    Then Child A should not see "Clean garage" in available chores
    And Child B should see "Clean garage" in available chores
    And parent should see "Hidden from 1" indicator on chore
```

### Scenario 2: Recurrence and Reset Flow
```gherkin
Feature: Recurring Chore Management
  Scenario: Daily chore reset cycle
    Given a daily recurring chore "Make bed"
    When Child A completes the chore at 8:00 AM
    Then chore should appear in completed section
    And chore should show "Available tomorrow at 12:00 AM"
    When time advances to next day 12:01 AM
    Then chore should appear in available section
    And Child A can claim and complete it again
```

### Scenario 3: Combined Features
```gherkin
Feature: Hidden Recurring Chores
  Scenario: Recurring chore with visibility restrictions
    Given a weekly chore "Mow lawn" that recurs on Saturdays
    And chore is hidden from younger children
    When older child completes it on Saturday
    Then younger children never see it
    And older child sees it grayed out until next Saturday
```

## Performance Testing Updates

### 1. Visibility Query Performance
```javascript
// performance/visibility-load-test.js
export default function() {
  // Create 100 chores with various visibility settings
  // Query as different children
  // Measure query time with visibility filtering
  // Target: <50ms additional overhead
}
```

### 2. Recurrence Calculation Load
```javascript
// performance/recurrence-stress-test.js
export default function() {
  // Create 1000 recurring chores
  // Complete them all simultaneously
  // Measure reset time calculation performance
  // Target: <100ms per chore
}
```

## Edge Case Testing

### 1. Visibility Edge Cases
- **All chores hidden**: Child with no visible chores
- **Visibility change during claim**: Hide chore while child is claiming
- **Deleted child**: Chore hidden from deleted user
- **New child added**: Existing visibility settings with new family member

### 2. Recurrence Edge Cases
- **Daylight Saving Time**: Reset times during DST transitions
- **Leap Years**: Monthly recurrence on Feb 29
- **Month Boundaries**: 31st day monthly recurrence in 30-day months
- **Concurrent Completions**: Multiple children try to complete after reset

### 3. Combined Edge Cases
- **Hidden chore becomes available**: Notification handling
- **Visibility + Recurrence changes**: Update both simultaneously
- **Migration scenarios**: Existing chores getting new features

## Security Testing

### 1. Visibility Authorization
```python
async def test_cannot_bypass_visibility():
    """Ensure hidden chores cannot be accessed directly"""
    # Try to complete hidden chore via direct API call
    # Try to view hidden chore details
    # Verify all access denied
```

### 2. Data Leakage Prevention
```python
async def test_no_visibility_data_leakage():
    """Ensure visibility settings don't leak to children"""
    # Get chore list as child
    # Verify no visibility metadata included
    # Check API responses for any hints about hidden chores
```

## UI/UX Testing

### 1. Visual Regression Tests
- Grayed out chore styling consistency
- Progress bar rendering across devices
- Visibility badges on parent dashboard
- Countdown timer formatting

### 2. Accessibility Testing
- Screen reader announces chore availability
- Keyboard navigation for visibility settings
- Color contrast for grayed out chores
- ARIA labels for progress indicators

### 3. Usability Testing
- Time to understand grayed out state
- Clarity of countdown timers
- Intuitiveness of visibility settings
- Parent workflow efficiency

## Mobile-Specific Testing

### 1. Offline Scenarios
- View cached completed chores offline
- Sync visibility changes when online
- Handle reset times while offline
- Queue claims for hidden chores

### 2. Performance Testing
- Scroll performance with many grayed chores
- Timer update CPU usage
- Memory usage with progress animations
- Battery impact of countdown timers

## Regression Testing

### 1. Existing Features
- Verify direct assignment still works
- Check non-recurring chores unaffected
- Confirm reward calculations unchanged
- Test approval workflow compatibility

### 2. API Compatibility
- V1 endpoints continue working
- Existing mobile apps function
- No breaking changes for web UI
- Database migrations reversible

## Test Data Requirements

### 1. Visibility Test Data
```yaml
visibility_test_data:
  families:
    - parent_id: 1
      children: [2, 3, 4]
  chores:
    - title: "Visible to all"
      hidden_from_users: []
    - title: "Hidden from child 2"
      hidden_from_users: [2]
    - title: "Hidden from children 2 and 3"
      hidden_from_users: [2, 3]
```

### 2. Recurrence Test Data
```yaml
recurrence_test_data:
  chores:
    - title: "Daily chore"
      recurrence_type: "daily"
      recurrence_value: 1
    - title: "Weekly Monday chore"
      recurrence_type: "weekly"
      recurrence_value: 0
    - title: "Monthly 31st chore"
      recurrence_type: "monthly"
      recurrence_value: 31
```

## Monitoring & Metrics

### 1. Feature Adoption Metrics
- % of chores with visibility restrictions
- % of chores set as recurring
- Average hidden children per chore
- Most common recurrence patterns

### 2. Performance Metrics
- Visibility filtering query time
- Reset calculation duration
- Timer update frequency impact
- API response time with new features

### 3. Error Monitoring
- Failed visibility updates
- Invalid recurrence calculations
- Timer synchronization issues
- Timezone-related errors

## Test Automation Updates

### CI/CD Pipeline
```yaml
# .github/workflows/test-v2-features.yml
name: V2 Feature Tests

on: [push, pull_request]

jobs:
  visibility-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run visibility test suite
        run: pytest tests/test_visibility.py -v
      
  recurrence-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run recurrence test suite
        run: pytest tests/test_recurrence.py -v
      
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run combined feature tests
        run: pytest tests/test_v2_integration.py -v
```

## Test Timeline Summary

### Phase-by-Phase Breakdown
- **Phase 1**: Unit Testing Foundation (1.5 days)
  - Subphase 1.1: Backend Unit Tests (0.5 day)
  - Subphase 1.2: Frontend Unit Tests (0.5 day)
  - Subphase 1.3: Mobile Unit Tests (0.5 day)

- **Phase 2**: Integration Testing (2 days)
  - Subphase 2.1: API Integration Tests (0.75 day)
  - Subphase 2.2: Database Integration Tests (0.75 day)
  - Subphase 2.3: Frontend Integration Tests (0.5 day)

- **Phase 3**: End-to-End Testing (2 days)
  - Subphase 3.1: Core Feature E2E Tests (1 day)
  - Subphase 3.2: Edge Case E2E Tests (0.5 day)
  - Subphase 3.3: Cross-Platform E2E Tests (0.5 day)

- **Phase 4**: Performance and Load Testing (1.5 days)
  - Subphase 4.1: Backend Performance Tests (0.75 day)
  - Subphase 4.2: Frontend Performance Tests (0.75 day)

- **Phase 5**: Security and Accessibility Testing (1 day)
  - Subphase 5.1: Security Testing (0.5 day)
  - Subphase 5.2: Accessibility Testing (0.5 day)

- **Phase 6**: User Acceptance Testing (1 day)
  - Subphase 6.1: Alpha Testing (0.5 day)
  - Subphase 6.2: Beta Testing (0.5 day)

**Total: 9 days** (comprehensive testing across all platforms)

## Success Metrics

### Phase 1 Success Criteria
- [ ] 100% unit test coverage for new code
- [ ] All edge cases identified and tested
- [ ] Zero failing tests
- [ ] Test execution < 5 minutes

### Phase 2 Success Criteria
- [ ] All API endpoints tested
- [ ] Database queries optimized
- [ ] Frontend integration stable
- [ ] No integration failures

### Phase 3 Success Criteria
- [ ] All user journeys validated
- [ ] Cross-platform consistency verified
- [ ] Edge cases handled gracefully
- [ ] Zero critical bugs

### Phase 4 Success Criteria
- [ ] Response times meet targets
- [ ] System handles 100+ concurrent users
- [ ] No memory leaks detected
- [ ] Performance benchmarks achieved

### Phase 5 Success Criteria
- [ ] No security vulnerabilities found
- [ ] WCAG AA compliance achieved
- [ ] All authorization checks pass
- [ ] Accessibility score > 95%

### Phase 6 Success Criteria
- [ ] User satisfaction > 90%
- [ ] Task completion rate > 95%
- [ ] Bug discovery rate < 5%
- [ ] Ready for production

## Test Environment Requirements

### Infrastructure
- Test database with production-like data
- Staging environment matching production
- Load testing infrastructure
- Mobile device lab or cloud service

### Tools
- **Backend**: pytest, pytest-asyncio, coverage
- **Frontend**: Jest, React Testing Library, Cypress
- **Mobile**: Detox, Jest, React Native Testing Library
- **Performance**: K6, Lighthouse, Chrome DevTools
- **Security**: OWASP ZAP, Burp Suite
- **Accessibility**: axe DevTools, NVDA/JAWS

### Test Data
- Families with 2-5 children
- Mix of visibility settings
- Various recurrence patterns
- Edge case scenarios (31st monthly, etc.)

## Risk-Based Testing Priorities

### Critical (Must Test)
1. Visibility filtering accuracy
2. Recurrence calculations
3. Authorization enforcement
4. Data integrity

### High (Should Test)
1. Performance under load
2. Cross-platform sync
3. Offline functionality
4. Timer accuracy

### Medium (Nice to Test)
1. Animation smoothness
2. Extreme edge cases
3. Legacy browser support
4. Advanced accessibility

## Continuous Testing Strategy

### CI/CD Integration
- Unit tests run on every commit
- Integration tests run on PR
- E2E tests run before deployment
- Performance tests run weekly

### Monitoring
- Error rate tracking
- Performance metrics
- User behavior analytics
- A/B testing for UX improvements

## Documentation Requirements

### Test Documentation
- [ ] Test plan for each phase
- [ ] Test case specifications
- [ ] Bug report templates
- [ ] Test execution reports

### Knowledge Transfer
- [ ] Testing best practices guide
- [ ] Common issues and solutions
- [ ] Test data setup instructions
- [ ] Troubleshooting guide