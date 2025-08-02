# Dashboard Bug Fixes Implementation Plan

## Overview
This document outlines the implementation plan for fixing 4 identified bugs in the Chores Tracker dashboard.

## Bug Fixes

### Bug 1: Duplicate Chores Sections for Children
**Issue**: Children see both "Active Chores" and "Available Chores" sections with duplicate content.

**Root Cause**: 
- The "Active Chores" section (line 75 in dashboard.html) is always visible
- Children also see "Available Chores" section, creating duplication
- Both sections show similar content

**Implementation**:
1. In dashboard.html, modify the "Active Chores" section to be hidden by default:
   ```html
   <!-- Active Chores -->
   <div class="bg-white p-4 rounded-lg shadow" id="active-chores-section" style="display: none;">
   ```

2. Update JavaScript (around line 188) to show "Active Chores" only for parents:
   ```javascript
   if (user.is_parent) {
       // ... existing parent code ...
       document.getElementById('active-chores-section').style.display = 'block';
   }
   ```

3. Limit the number of chores displayed to prevent scrolling:
   - Modify the endpoint or add client-side limiting to show max 10 chores
   - Add a "View All" link if there are more chores

### Bug 2: Allowance Summary Shows "Not Authorized" for Children
**Issue**: The allowance summary section is visible to children but shows "Not authorized".

**Root Cause**: 
- The allowance summary section (line 117) doesn't have conditional display
- The endpoint returns "Not authorized" for non-parent users

**Implementation**:
1. Add an ID to the allowance summary section:
   ```html
   <div class="mt-8 bg-white p-4 rounded-lg shadow" id="allowance-summary-section">
   ```

2. Hide it by default in the HTML:
   ```html
   <div class="mt-8 bg-white p-4 rounded-lg shadow" id="allowance-summary-section" style="display: none;">
   ```

3. Show it only for parents in JavaScript:
   ```javascript
   if (user.is_parent) {
       // ... existing parent code ...
       document.getElementById('allowance-summary-section').style.display = 'block';
   }
   ```

### Bug 3: Remove Active Chores from Parent Dashboard
**Issue**: Parents see "Active Chores" which is not relevant for their workflow.

**Root Cause**: The active chores section is shown for all users by default.

**Implementation**:
- This will be fixed by Bug 1's implementation
- The "Active Chores" section will be hidden by default and not shown for parents

### Bug 4: Child Selection Not Interactive for Parents
**Issue**: Parent dashboard shows child names as plain text instead of interactive elements.

**Root Cause**: 
- The endpoint `/api/v1/users/children` returns dropdown options HTML
- No click handlers are attached to make children selectable

**Implementation Options**:

**Option A (Recommended - Minimal Changes):**
1. Create a new template `children_cards.html` that returns clickable child cards
2. Update the children-list div to add click handlers:
   ```javascript
   // After children load, add click handlers
   document.querySelectorAll('#children-list .child-card').forEach(card => {
       card.addEventListener('click', function() {
           const childId = this.dataset.childId;
           viewChildChores(childId);
       });
   });
   ```

**Option B (Alternative):**
1. Change the endpoint in dashboard.html from:
   ```html
   hx-get="/api/v1/users/children"
   ```
   To:
   ```html
   hx-get="/api/v1/html/users/children"
   ```

## Implementation Order
1. Fix Bug 2 first (easiest - just add ID and hide/show logic)
2. Fix Bugs 1 & 3 together (related - hiding active chores)
3. Fix Bug 4 last (requires template creation or endpoint change)

## Testing Plan
1. Login as child user:
   - Verify only "Available Chores" section is visible
   - Verify no "Allowance Summary" section
   - Verify limited number of chores shown

2. Login as parent user:
   - Verify children are shown as clickable elements
   - Verify "Allowance Summary" is visible
   - Verify no "Active Chores" section
   - Test clicking on a child loads their chores

## Files to Modify
1. `/backend/app/templates/pages/dashboard.html`
2. Potentially create `/backend/app/templates/components/children_cards.html`

## Estimated Time
- Total implementation: 30-45 minutes
- Testing: 15-20 minutes