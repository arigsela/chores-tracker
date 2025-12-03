# BUG-001: Parent Chore Management - Assignee Display Shows "Unassigned"

## Status: Open
## Priority: Medium
## Created: 2025-12-03
## Component: Frontend - ChoresManagementScreen

---

## Summary

In the parent's "Manage Chores" view, all chores display "Assigned to: Unassigned" even when chores have valid assignments. This is a frontend display bug caused by using legacy data fields instead of the new multi-assignment data structure.

## Steps to Reproduce

1. Log in as a parent user (e.g., `testparent`)
2. Navigate to the **Chores** tab
3. Observe the chore cards - all show "Assigned to: Unassigned"
4. Compare with child view - the child (e.g., `makoto`) correctly sees "Assigned to You"

## Expected Behavior

Chores should display the correct assignee name(s):
- **Single assignment**: "Assigned to: makoto"
- **Multi-independent**: "Assigned to: alice, bob, charlie"
- **Unassigned pool**: "Assigned to: Unassigned (Pool)"

## Actual Behavior

All chores show "Assigned to: Unassigned" regardless of actual assignment status.

## Root Cause Analysis

**File**: `frontend/src/screens/ChoresManagementScreen.tsx`
**Line**: 216

### Current Code (Broken)
```typescript
<View style={styles.detailRow}>
  <Text style={styles.detailLabel}>Assigned to:</Text>
  <Text style={[styles.detailValue, isDisabled && styles.disabledText]}>
    {getChildName(chore.assignee_id || chore.assigned_to_id)}
  </Text>
</View>
```

### Problem
The code reads from legacy fields (`chore.assignee_id`, `chore.assigned_to_id`) which are **deprecated** and return `null` in the new multi-assignment system.

### API Response Structure (New)
```json
{
  "id": 2,
  "title": "test chore 2",
  "assignment_mode": "single",
  "assignee_id": null,           // Legacy - always null now
  "assigned_to_id": null,        // Legacy - always null now
  "assignments": [               // NEW - use this instead
    {
      "id": 1,
      "chore_id": 2,
      "assignee_id": 2,
      "is_completed": false,
      "is_approved": false
    }
  ]
}
```

## Proposed Fix

### Option 1: Simple Fix (Single Assignment Display)
Update `getChildName` call to read from assignments array:

```typescript
const getAssigneeDisplay = (chore: Chore): string => {
  // Check new multi-assignment structure first
  if (chore.assignments && chore.assignments.length > 0) {
    if (chore.assignment_mode === 'unassigned') {
      return 'Unassigned (Pool)';
    }
    const names = chore.assignments.map(a => {
      const child = children.find(c => c.id === a.assignee_id);
      return child ? child.username : `Child #${a.assignee_id}`;
    });
    return names.join(', ');
  }

  // Fallback to legacy fields for backward compatibility
  if (chore.assignee_id || chore.assigned_to_id) {
    return getChildName(chore.assignee_id || chore.assigned_to_id);
  }

  return 'Unassigned';
};
```

### Option 2: Enhanced Display with Assignment Mode
Show assignment mode context:

```typescript
// Display examples:
// - "makoto (Single)"
// - "alice, bob (Independent)"
// - "Available Pool"
```

## Files to Modify

1. `frontend/src/screens/ChoresManagementScreen.tsx`
   - Update `getChildName` or create `getAssigneeDisplay` function
   - Update line 216 to use new function

## Testing Checklist

- [ ] Single assignment chore shows correct child name
- [ ] Multi-independent chore shows all assigned children
- [ ] Unassigned pool chore shows "Unassigned (Pool)" or similar
- [ ] Legacy chores (if any) still display correctly
- [ ] Disabled chores display assignee with disabled styling

## Related Components

The child view (`ChoresScreen.tsx`) correctly handles multi-assignment because it uses the `/chores/available` endpoint which returns properly structured data with `assigned` and `pool` arrays.

## Screenshots

### Current (Bug)
![Parent view showing Unassigned](/.playwright-mcp/parent-chores-view.png)

### Expected
Chore cards should show actual assignee names like "makoto" instead of "Unassigned".

---

## Notes

- This bug was discovered during PostgreSQL migration testing
- The PostgreSQL migration itself is working correctly - this is a pre-existing frontend bug
- The child view works correctly because it uses a different API endpoint structure
