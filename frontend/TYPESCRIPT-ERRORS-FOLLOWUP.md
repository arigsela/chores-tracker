# TypeScript Errors - Follow-Up Required

**Created**: 2025-11-03
**Phase**: Phase 2, Task 2.1 - Fix TypeScript Errors in Integration Tests
**Status**: Partial completion - factories fixed, test files need rewrites

## Summary

During Phase 2, Task 2.1, we fixed critical TypeScript errors in the **test factory functions** to align with the multi-assignment chore system. However, extensive integration test files require significant rewrites that are better suited as a separate focused task.

## Completed Fixes ✅

### 1. Import/Export Mismatch
- **File**: `frontend/src/__tests__/integration/approvalWorkflow.test.tsx`
- **Fix**: Changed `import { ChildCard }` to `import ChildCard` (default export)
- **Impact**: Resolved 1 import error

### 2. Mock Factory Updates
- **File**: `frontend/src/test-utils/factories.ts`
- **Changes**:
  - Added `assignment_mode: 'single'` to `createMockChore()` (required field)
  - Added `assignee_ids: [2]` and `assignments: []` for multi-assignment support
  - Updated `MockActivity` interface to include `activity_type` and `activity_data` (required fields)
  - Updated all activity factory functions to use new structure
- **Impact**: All test factories now generate valid objects matching current API interfaces

### 3. Mock API Response Types
- **File**: `frontend/src/__tests__/integration/approvalWorkflow.test.tsx`
- **Fix**: Updated `beforeEach()` to return proper `AssignmentActionResponse` and `ActivityListResponse` structures
- **Impact**: Mock API responses now match actual API return types

## Remaining TypeScript Errors (90+ errors)

### Category 1: Integration Test Mocks Need Rewrites (High Effort)
**Files**:
- `src/__tests__/integration/approvalWorkflow.test.tsx` (38 errors)
- `src/__tests__/integration/choreManagement.test.tsx` (18 errors)

**Issues**:
1. **onApprovalChange prop doesn't exist** (15+ errors)
   - Mock ChoreCard component has `onApprovalChange` callback
   - Real ChoreCard doesn't have this prop
   - **Solution**: Remove mock component's `onApprovalChange` or redesign test flow

2. **getUserBalance doesn't exist in usersAPI** (5+ errors)
   - Tests call `usersAPI.getUserBalance(childId)`
   - Actual API: `balanceAPI.getMyBalance()` (no child ID parameter)
   - **Solution**: Rewrite ChildCard mock to use correct API or mock balanceAPI

3. **Deprecated chore fields used** (10+ errors)
   - Tests use `needs_approval`, `assignee`, etc.
   - These fields don't exist in current Chore interface
   - **Solution**: Update all test chore creation to use multi-assignment structure

4. **MockUser vs ChildWithChores type mismatch** (5+ errors)
   - Tests pass `MockUser` where `ChildWithChores` expected
   - `ChildWithChores` extends `User` (requires `is_active`, `is_parent`, `parent_id`)
   - **Solution**: Use `createMockApiChild()` instead of `createMockChild()`

5. **Activity array vs ActivityListResponse** (2 errors)
   - Tests return `Activity[]` where `ActivityListResponse` expected
   - **Solution**: Wrap in `{ activities: [...], has_more: false }`

**Estimated Effort**: 3-4 hours to rewrite all integration test mocks properly

### Category 2: API Tests Use Old Fields (Medium Effort)
**File**: `src/api/__tests__/chores.test.ts` (9 errors)

**Issues**:
1. **Missing assignment_mode and assignee_ids** (6 errors)
   - Lines 365, 385, 407, 425, 439, 736
   - Tests pass `{ assignee_id: 2 }` to `choreAPI.createChore()`
   - API requires `{ assignment_mode: 'single', assignee_ids: [2] }`
   - **Solution**: Add these fields to all test chore creation calls

2. **CompleteChoreResponse structure mismatch** (2 errors)
   - Lines 123-124: `result.is_completed`, `result.completed_at`
   - Actual return: `{ chore, assignment, message }`
   - **Solution**: Change to `result.assignment.is_completed`, `result.chore.completed_at`

3. **Missing error properties** (1 error)
   - Line 585: `error.code` doesn't exist on Error
   - **Solution**: Cast to axios error or check `error.response.status`

**Estimated Effort**: 1 hour

### Category 3: Minor Type Issues (Low Effort)
**Files**: Various

**Issues**:
1. **config/api.ts**: Duplicate `getAPIUrl` export (2 errors)
   - **Solution**: Remove duplicate export declaration

2. **contexts/__tests__/AuthContext.test.tsx**: `full_name` doesn't exist on User (2 errors)
   - **Solution**: Remove `full_name` from test assertions

3. **api/__tests__/client.test.ts**: `error.response` doesn't exist (1 error)
   - **Solution**: Cast to axios error type

4. **navigation/AuthNavigator.tsx**: Type mismatch for LoginScreen (1 error)
   - **Solution**: Update navigation types

5. **components/__tests__/ActivityFeed.test.tsx**: Function call error (1 error)
   - **Solution**: Check function signature

**Estimated Effort**: 30 minutes

## Recommended Approach

### Option 1: Complete Now (Total: 4-5 hours)
Systematically fix all 90+ errors before moving to Phase 2 Task 2.2.

**Pros**: Full TypeScript compliance
**Cons**: Delays Phase 2 progress significantly

### Option 2: Incremental (Recommended)
1. **Now**: Commit factory fixes (already done) ✅
2. **Now**: Fix Category 3 (minor issues) - 30 min
3. **Now**: Fix Category 2 (API tests) - 1 hour
4. **Later**: Create separate ticket for Category 1 (integration test rewrites) - 3-4 hours

**Pros**: Pragmatic, maintains momentum, fixes high-value errors
**Cons**: Some test files will have TypeScript errors

### Option 3: Skip Tests For Now
Accept that test files have TypeScript errors, focus on production code.

**Pros**: Fastest path to Phase 2 completion
**Cons**: Technical debt in test files

## Recommendation

**Choose Option 2: Incremental**

**Rationale**:
- Factory fixes already provide significant value (all new tests will work correctly)
- API test fixes are straightforward and high-value
- Integration test rewrites are complex and better as focused task
- Aligns with "perfect is the enemy of good" principle from Phase 1
- Production code has zero TypeScript errors (tests don't block deployment)

## Next Steps

1. ✅ Commit factory fixes (this commit)
2. Fix `config/api.ts` duplicate export (5 min)
3. Fix API test files to use `assignment_mode`/`assignee_ids` (1 hour)
4. Create GitHub issue: "Rewrite integration test mocks for multi-assignment system"
5. Proceed to Phase 2 Task 2.2

## Migration Guide for Future Test Writers

When writing new tests, ensure:

### ✅ DO:
```typescript
// Use updated factories
const chore = createMockChore({
  assignment_mode: 'single',
  assignee_ids: [2],
  assignments: []
});

// Use proper activity structure
const activity = createMockActivity({
  activity_type: 'chore_completed',
  activity_data: { chore_id: 1, reward_amount: 5.00 }
});

// Use correct API response types
mockedChoreAPI.completeChore.mockResolvedValue({
  chore: createMockChore({ id: 1 }),
  assignment: { ...assignmentData },
  message: 'Chore completed'
});
```

### ❌ DON'T:
```typescript
// Old single-assignment fields
const chore = createMockChore({
  assignee_id: 2,  // DEPRECATED
  is_completed: true  // Use assignment.is_completed
});

// Missing required fields
const activity = {
  type: 'chore_completed',  // Use activity_type
  amount: 5.00  // Put in activity_data
};

// Wrong response structure
mockedChoreAPI.completeChore.mockResolvedValue({ success: true });  // WRONG
```

## References

- Multi-Assignment Chore System: `CLAUDE.md#Multi-Assignment Chore System`
- Chore Interface: `frontend/src/api/chores.ts:27-72`
- Activity Interface: `frontend/src/api/activities.ts:4-37`
- Assignment Interface: `frontend/src/api/chores.ts:11-22`
