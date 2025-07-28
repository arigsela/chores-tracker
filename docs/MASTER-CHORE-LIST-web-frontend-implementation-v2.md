# Master Chore List - Web Frontend Implementation Plan v2

## Overview

This document outlines the web frontend implementation plan for the Master Chore List feature with two key enhancements:
1. **Selective Visibility**: Parents can hide specific chores from certain children
2. **Grayed Out Completed Chores**: Show completed chores as unavailable until reset based on recurrence

## Phased Implementation Plan

### Phase 1: Core UI/Template Updates (1.5 days)

#### Subphase 1.1: Parent Chore Creation Form (0.5 day)
**Tasks:**
- [ ] Update chore creation template with recurrence section
- [ ] Add visibility settings checkboxes
- [ ] Implement Alpine.js data bindings
- [ ] Style form with Tailwind CSS

**Testing:**
- [ ] Test form submission with all fields
- [ ] Verify Alpine.js reactivity
- [ ] Test validation messages
- [ ] Cross-browser form testing

**Deliverables:**
- Updated `chores-form.html` template
- Form validation logic
- Responsive design implementation

#### Subphase 1.2: Child Dashboard Layout (0.5 day)
**Tasks:**
- [ ] Create two-section layout (available/completed)
- [ ] Design chore card components
- [ ] Implement grayed-out styling
- [ ] Add progress bar component

**Testing:**
- [ ] Test responsive grid layout
- [ ] Verify card hover states
- [ ] Test progress bar rendering
- [ ] Mobile layout testing

**Template Code:**
```html
<!-- Test file: tests/templates/test_child_dashboard.html -->
<div class="test-scenarios">
  <!-- Scenario 1: Mixed available and completed chores -->
  <!-- Scenario 2: Only completed chores -->
  <!-- Scenario 3: Empty states -->
</div>
```

#### Subphase 1.3: Component Templates (0.5 day)
**Tasks:**
- [ ] Create available-chore-card component
- [ ] Create completed-chore-card component
- [ ] Build visibility-settings-modal
- [ ] Design parent management cards

**Testing:**
- [ ] Component isolation tests
- [ ] HTMX integration tests
- [ ] Modal behavior tests
- [ ] Accessibility testing

### Phase 2: JavaScript/Alpine.js Implementation (2 days)

#### Subphase 2.1: Visibility Settings Component (0.5 day)
**Tasks:**
- [ ] Implement visibility settings Alpine component
- [ ] Add API integration for loading/saving
- [ ] Handle error states
- [ ] Add loading indicators

**Testing:**
- [ ] Test API calls with mock data
- [ ] Verify checkbox state management
- [ ] Test error handling
- [ ] Test save confirmation

**JavaScript Tests:**
```javascript
// tests/js/test_visibility_settings.js
describe('Visibility Settings', () => {
  it('should load current visibility settings')
  it('should update hiddenFromUsers array')
  it('should save settings via API')
  it('should handle API errors gracefully')
});
```

#### Subphase 2.2: Timer and Progress Components (0.75 day)
**Tasks:**
- [ ] Create choreTimer Alpine component
- [ ] Implement countdown logic
- [ ] Calculate progress percentage
- [ ] Add auto-refresh triggers

**Testing:**
- [ ] Test time calculations
- [ ] Verify progress accuracy
- [ ] Test auto-refresh timing
- [ ] Test timezone handling

**Test Cases:**
```javascript
// tests/js/test_chore_timer.js
describe('Chore Timer', () => {
  it('should calculate time remaining correctly')
  it('should update progress bar smoothly')
  it('should trigger refresh when timer expires')
  it('should handle different time zones')
});
```

#### Subphase 2.3: HTMX Integration (0.75 day)
**Tasks:**
- [ ] Setup HTMX polling for chore lists
- [ ] Implement claim chore functionality
- [ ] Add event listeners for updates
- [ ] Configure smart polling intervals

**Testing:**
- [ ] Test HTMX request/response cycle
- [ ] Verify event propagation
- [ ] Test polling intervals
- [ ] Load test with multiple users

### Phase 3: Parent Management Features (1.5 days)

#### Subphase 3.1: Visibility Management Interface (0.75 day)
**Tasks:**
- [ ] Build bulk visibility management UI
- [ ] Create child-specific visibility view
- [ ] Add quick toggle buttons
- [ ] Implement search/filter

**Testing:**
- [ ] Test bulk operations
- [ ] Verify UI state consistency
- [ ] Test search functionality
- [ ] Performance with many chores

**UI Tests:**
```javascript
// tests/ui/test_visibility_management.js
describe('Visibility Management', () => {
  it('should display hidden chores by child')
  it('should allow bulk visibility changes')
  it('should update UI immediately')
  it('should handle concurrent updates')
});
```

#### Subphase 3.2: Chore Management Dashboard (0.75 day)
**Tasks:**
- [ ] Update parent dashboard layout
- [ ] Add visibility indicators to chore cards
- [ ] Implement edit visibility shortcuts
- [ ] Create activity monitoring view

**Testing:**
- [ ] Test dashboard data accuracy
- [ ] Verify indicator visibility
- [ ] Test real-time updates
- [ ] Load test with many chores

### Phase 4: Styling and Responsive Design (1 day)

#### Subphase 4.1: CSS Implementation (0.5 day)
**Tasks:**
- [ ] Create chore card state styles
- [ ] Implement progress bar animations
- [ ] Design recurrence badges
- [ ] Style visibility indicators

**Testing:**
- [ ] Visual regression testing
- [ ] Animation performance
- [ ] Cross-browser CSS
- [ ] Dark mode compatibility

**CSS Test File:**
```css
/* tests/css/test_chore_states.css */
.test-available-state { }
.test-completed-state { }
.test-progress-animation { }
.test-responsive-grid { }
```

#### Subphase 4.2: Mobile Optimization (0.5 day)
**Tasks:**
- [ ] Optimize touch targets
- [ ] Implement responsive grid
- [ ] Adjust modal sizes
- [ ] Optimize performance

**Testing:**
- [ ] Test on various devices
- [ ] Touch interaction testing
- [ ] Performance profiling
- [ ] Orientation changes

### Phase 5: Integration and Polish (1 day)

#### Subphase 5.1: End-to-End Testing (0.5 day)
**Tasks:**
- [ ] Write complete user flow tests
- [ ] Test parent → child workflows
- [ ] Verify data synchronization
- [ ] Test edge cases

**E2E Test Scenarios:**
```javascript
// tests/e2e/test_visibility_flow.js
describe('Complete Visibility Flow', () => {
  it('parent creates hidden chore')
  it('child cannot see hidden chore')
  it('parent updates visibility')
  it('child sees newly visible chore')
});
```

#### Subphase 5.2: Performance and Polish (0.5 day)
**Tasks:**
- [ ] Optimize polling intervals
- [ ] Implement lazy loading
- [ ] Add loading skeletons
- [ ] Final UI polish

**Performance Tests:**
```javascript
// tests/performance/test_frontend_load.js
describe('Frontend Performance', () => {
  it('should load dashboard < 2s')
  it('should handle 100+ chores smoothly')
  it('should minimize API calls')
  it('should cache appropriately')
});
```

## Key UI/UX Changes

### 1. Parent Views

#### Chore Creation/Edit Form Updates
```html
<!-- templates/pages/chores-form.html -->
<form hx-post="/api/v1/html/chores" class="space-y-4">
    <!-- Existing fields... -->
    
    <!-- New: Recurrence Settings -->
    <div class="mb-4" x-data="{ isRecurring: false, recurrenceType: 'daily' }">
        <label class="flex items-center">
            <input type="checkbox" x-model="isRecurring" name="is_recurring" class="mr-2">
            <span class="text-gray-700 font-medium">Recurring Chore</span>
        </label>
        
        <div x-show="isRecurring" x-transition class="mt-3 ml-6 space-y-3">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Recurrence Type</label>
                <select x-model="recurrenceType" name="recurrence_type" class="form-select">
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                </select>
            </div>
            
            <!-- Dynamic recurrence value based on type -->
            <div x-show="recurrenceType === 'daily'">
                <label class="block text-sm font-medium text-gray-700 mb-1">Every X days</label>
                <input type="number" name="recurrence_value" value="1" min="1" max="30" class="form-input w-20">
            </div>
            
            <div x-show="recurrenceType === 'weekly'">
                <label class="block text-sm font-medium text-gray-700 mb-1">On day of week</label>
                <select name="recurrence_value" class="form-select">
                    <option value="0">Monday</option>
                    <option value="1">Tuesday</option>
                    <option value="2">Wednesday</option>
                    <option value="3">Thursday</option>
                    <option value="4">Friday</option>
                    <option value="5">Saturday</option>
                    <option value="6">Sunday</option>
                </select>
            </div>
            
            <div x-show="recurrenceType === 'monthly'">
                <label class="block text-sm font-medium text-gray-700 mb-1">On day of month</label>
                <input type="number" name="recurrence_value" value="1" min="1" max="31" class="form-input w-20">
            </div>
        </div>
    </div>
    
    <!-- New: Visibility Settings -->
    <div class="mb-4">
        <label class="block text-gray-700 font-medium mb-2">Visibility Settings</label>
        <p class="text-sm text-gray-600 mb-3">Hide this chore from specific children (optional)</p>
        
        <div id="visibility-settings" class="space-y-2">
            {% for child in children %}
            <label class="flex items-center">
                <input type="checkbox" 
                       name="hidden_from_users[]" 
                       value="{{ child.id }}"
                       class="mr-2">
                <span class="text-gray-700">Hide from {{ child.username }}</span>
            </label>
            {% endfor %}
        </div>
    </div>
    
    <button type="submit" class="btn btn-primary">
        Create Chore
    </button>
</form>
```

#### Parent Dashboard - Chore Management
```html
<!-- templates/parent/chore-management.html -->
<div class="grid gap-6 lg:grid-cols-2">
    <!-- Chore Pool Section -->
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Chore Pool</h2>
        
        <div id="chore-pool" 
             hx-get="/api/v1/html/chores/pool"
             hx-trigger="load, every 30s"
             class="space-y-3">
            <!-- Chore cards with visibility indicators -->
        </div>
    </div>
    
    <!-- Active Chores by Child -->
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Active Chores by Child</h2>
        
        <div id="active-chores" 
             hx-get="/api/v1/html/chores/active-by-child"
             hx-trigger="load, chore-completed from:body"
             class="space-y-4">
            <!-- Grouped by child with completion status -->
        </div>
    </div>
</div>
```

### 2. Child Views

#### Updated Child Dashboard
```html
<!-- templates/child/dashboard.html -->
<div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">My Chores</h1>
    
    <!-- Available Chores Section -->
    <div class="mb-8">
        <h2 class="text-2xl font-semibold mb-4 flex items-center">
            <svg class="w-6 h-6 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <!-- Check circle icon -->
            </svg>
            Available Chores
        </h2>
        
        <div id="available-chores"
             hx-get="/api/v1/html/chores/my-available"
             hx-trigger="load, every 10s"
             class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <!-- Available chore cards -->
        </div>
    </div>
    
    <!-- Completed/Waiting Chores Section -->
    <div>
        <h2 class="text-2xl font-semibold mb-4 flex items-center">
            <svg class="w-6 h-6 mr-2 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <!-- Clock icon -->
            </svg>
            Completed Chores (Waiting for Reset)
        </h2>
        
        <div id="completed-chores"
             hx-get="/api/v1/html/chores/my-completed"
             hx-trigger="load, chore-completed from:body"
             class="grid gap-4 md:grid-cols-2 lg:grid-cols-3 opacity-60">
            <!-- Grayed out completed chore cards -->
        </div>
    </div>
</div>
```

### 3. Component Templates

#### Available Chore Card
```html
<!-- templates/components/available-chore-card.html -->
<div class="chore-card bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
     x-data="{ claiming: false }">
    
    <div class="flex justify-between items-start mb-4">
        <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-900">{{ chore.title }}</h3>
            {% if chore.description %}
            <p class="text-sm text-gray-600 mt-1">{{ chore.description }}</p>
            {% endif %}
        </div>
        
        {% if chore.is_recurring %}
        <span class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {{ chore.recurrence_type|title }}
        </span>
        {% endif %}
    </div>
    
    <div class="flex items-center justify-between">
        <div class="text-green-600 font-semibold">
            {% if chore.reward_type == 'fixed' %}
                ${{ chore.reward_amount }}
            {% else %}
                ${{ chore.reward_min }} - ${{ chore.reward_max }}
            {% endif %}
        </div>
        
        <button @click="claiming = true"
                x-show="!claiming"
                hx-post="/api/v1/html/chores/{{ chore.id }}/claim"
                hx-target="closest .chore-card"
                hx-swap="outerHTML"
                class="btn btn-primary btn-sm">
            Claim Chore
        </button>
        
        <div x-show="claiming" class="flex items-center">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span class="ml-2 text-sm text-gray-600">Claiming...</span>
        </div>
    </div>
</div>
```

#### Completed Chore Card (Grayed Out)
```html
<!-- templates/components/completed-chore-card.html -->
<div class="chore-card bg-gray-100 rounded-lg shadow p-6 relative">
    <!-- Overlay to show it's unavailable -->
    <div class="absolute inset-0 bg-gray-200 bg-opacity-50 rounded-lg"></div>
    
    <div class="relative z-10">
        <div class="flex justify-between items-start mb-4">
            <div class="flex-1">
                <h3 class="text-lg font-semibold text-gray-600">{{ chore.title }}</h3>
                {% if chore.description %}
                <p class="text-sm text-gray-500 mt-1">{{ chore.description }}</p>
                {% endif %}
            </div>
            
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                Completed
            </span>
        </div>
        
        <div class="flex items-center justify-between">
            <div class="text-gray-500">
                {% if chore.reward_type == 'fixed' %}
                    ${{ chore.reward_amount }}
                {% else %}
                    ${{ chore.reward_min }} - ${{ chore.reward_max }}
                {% endif %}
            </div>
            
            <div class="text-sm text-gray-600">
                <svg class="inline w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <!-- Clock icon -->
                </svg>
                Available {{ chore.next_available_time|timeuntil }}
            </div>
        </div>
        
        <!-- Progress bar showing time until available -->
        <div class="mt-4">
            <div class="bg-gray-300 rounded-full h-2">
                <div class="bg-blue-400 h-2 rounded-full transition-all duration-300"
                     style="width: {{ chore.availability_progress }}%"></div>
            </div>
        </div>
    </div>
</div>
```

#### Visibility Settings Modal
```html
<!-- templates/components/visibility-settings-modal.html -->
<div x-data="visibilitySettings({{ chore.id }})" 
     x-show="showModal"
     class="fixed inset-0 z-50 overflow-y-auto">
    
    <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
        
        <div class="relative bg-white rounded-lg max-w-md w-full p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">
                Visibility Settings for "{{ chore.title }}"
            </h3>
            
            <form @submit.prevent="saveVisibility">
                <div class="space-y-3 mb-6">
                    <p class="text-sm text-gray-600">Select children who should NOT see this chore:</p>
                    
                    {% for child in children %}
                    <label class="flex items-center">
                        <input type="checkbox" 
                               x-model="hiddenFromUsers"
                               value="{{ child.id }}"
                               class="mr-3">
                        <span>{{ child.username }}</span>
                    </label>
                    {% endfor %}
                </div>
                
                <div class="flex justify-end space-x-3">
                    <button type="button" 
                            @click="showModal = false"
                            class="btn btn-secondary">
                        Cancel
                    </button>
                    <button type="submit" 
                            class="btn btn-primary"
                            :disabled="saving">
                        <span x-show="!saving">Save Settings</span>
                        <span x-show="saving">Saving...</span>
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
```

## JavaScript/Alpine.js Components

### 1. Visibility Settings Component
```javascript
// static/js/components/visibility-settings.js
function visibilitySettings(choreId) {
    return {
        showModal: false,
        hiddenFromUsers: [],
        saving: false,
        
        async loadSettings() {
            try {
                const response = await fetch(`/api/v1/chores/${choreId}/visibility`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                const data = await response.json();
                this.hiddenFromUsers = data.hidden_from_users || [];
            } catch (error) {
                console.error('Error loading visibility settings:', error);
            }
        },
        
        async saveVisibility() {
            this.saving = true;
            
            try {
                const response = await fetch(`/api/v1/chores/${choreId}/visibility`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        chore_id: choreId,
                        hidden_from_users: this.hiddenFromUsers.map(id => parseInt(id)),
                        visible_to_users: []
                    })
                });
                
                if (response.ok) {
                    this.showModal = false;
                    // Trigger refresh
                    htmx.trigger('#chore-pool', 'refresh');
                    showNotification('Visibility settings updated');
                }
            } catch (error) {
                showNotification('Error saving settings', 'error');
            } finally {
                this.saving = false;
            }
        }
    };
}
```

### 2. Chore Timer Component
```javascript
// static/js/components/chore-timer.js
Alpine.data('choreTimer', (nextAvailableTime) => ({
    timeRemaining: '',
    progress: 0,
    
    init() {
        this.updateTimer();
        setInterval(() => this.updateTimer(), 60000); // Update every minute
    },
    
    updateTimer() {
        const now = new Date();
        const available = new Date(nextAvailableTime);
        const diff = available - now;
        
        if (diff <= 0) {
            // Chore is now available, trigger refresh
            htmx.trigger('#available-chores', 'refresh');
            htmx.trigger('#completed-chores', 'refresh');
            return;
        }
        
        // Calculate time remaining
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        
        if (hours > 24) {
            const days = Math.floor(hours / 24);
            this.timeRemaining = `${days} day${days > 1 ? 's' : ''}`;
        } else if (hours > 0) {
            this.timeRemaining = `${hours}h ${minutes}m`;
        } else {
            this.timeRemaining = `${minutes} minutes`;
        }
        
        // Calculate progress (for daily chores, show % of day completed)
        const totalTime = available - new Date(available.getTime() - 24 * 60 * 60 * 1000);
        this.progress = Math.min(100, Math.max(0, ((totalTime - diff) / totalTime) * 100));
    }
}));
```

## CSS Updates

### 1. Chore Card States
```css
/* static/css/chores.css */

/* Available chore cards */
.chore-card {
    @apply transition-all duration-200;
}

.chore-card:hover {
    @apply transform -translate-y-0.5;
}

/* Completed/unavailable chore cards */
.chore-card.completed {
    @apply relative overflow-hidden;
}

.chore-card.completed::before {
    content: '';
    @apply absolute inset-0 bg-gray-200 bg-opacity-60 z-10;
}

.chore-card.completed .chore-content {
    @apply relative z-20;
}

/* Progress bar animation */
.availability-progress {
    @apply transition-all duration-300 ease-linear;
}

/* Visibility indicator */
.visibility-indicator {
    @apply inline-flex items-center px-2 py-1 text-xs rounded-full;
}

.visibility-indicator.hidden-from-some {
    @apply bg-yellow-100 text-yellow-800;
}

/* Recurrence badges */
.recurrence-badge {
    @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}

.recurrence-badge.daily {
    @apply bg-blue-100 text-blue-800;
}

.recurrence-badge.weekly {
    @apply bg-purple-100 text-purple-800;
}

.recurrence-badge.monthly {
    @apply bg-green-100 text-green-800;
}
```

### 2. Responsive Grid Layout
```css
/* Responsive chore grid */
@media (min-width: 640px) {
    .chore-grid {
        @apply grid-cols-2;
    }
}

@media (min-width: 1024px) {
    .chore-grid {
        @apply grid-cols-3;
    }
}

/* Completed chores section styling */
.completed-section {
    @apply relative;
}

.completed-section::before {
    content: '';
    @apply absolute left-0 right-0 top-0 h-px bg-gray-300;
}
```

## HTMX Enhancements

### 1. Real-time Updates
```javascript
// static/js/chore-updates.js

// Listen for chore completion events
document.body.addEventListener('chore-completed', (event) => {
    // Refresh both available and completed sections
    htmx.trigger('#available-chores', 'refresh');
    htmx.trigger('#completed-chores', 'refresh');
    
    // Show notification
    showNotification('Chore marked as complete!');
});

// Auto-refresh completed chores when they become available
document.addEventListener('DOMContentLoaded', () => {
    // Check every minute if any completed chores are now available
    setInterval(() => {
        const completedChores = document.querySelectorAll('[data-next-available]');
        completedChores.forEach(chore => {
            const nextAvailable = new Date(chore.dataset.nextAvailable);
            if (nextAvailable <= new Date()) {
                htmx.trigger('#available-chores', 'refresh');
                htmx.trigger('#completed-chores', 'refresh');
            }
        });
    }, 60000);
});
```

### 2. Visibility Settings Integration
```html
<!-- HTMX endpoint for visibility settings -->
<div hx-get="/api/v1/html/chores/{{ chore.id }}/visibility-form"
     hx-target="#visibility-modal"
     hx-trigger="click"
     class="cursor-pointer">
    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <!-- Eye icon -->
    </svg>
</div>
```

## Parent Management Features

### 1. Bulk Visibility Management
```html
<!-- templates/parent/bulk-visibility.html -->
<div x-data="bulkVisibility()" class="bg-white rounded-lg shadow p-6">
    <h3 class="text-lg font-semibold mb-4">Manage Chore Visibility</h3>
    
    <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
            Select Child
        </label>
        <select x-model="selectedChild" class="form-select">
            <option value="">Choose a child...</option>
            {% for child in children %}
            <option value="{{ child.id }}">{{ child.username }}</option>
            {% endfor %}
        </select>
    </div>
    
    <div x-show="selectedChild" class="space-y-2">
        <h4 class="font-medium text-gray-700">Hidden Chores:</h4>
        <div class="max-h-60 overflow-y-auto space-y-2">
            <template x-for="chore in hiddenChores" :key="chore.id">
                <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span x-text="chore.title"></span>
                    <button @click="makeVisible(chore.id)" 
                            class="text-sm text-blue-600 hover:text-blue-800">
                        Make Visible
                    </button>
                </div>
            </template>
        </div>
    </div>
</div>
```

## Mobile Responsive Considerations

### 1. Touch-Friendly Interactions
```css
/* Larger touch targets for mobile */
@media (max-width: 640px) {
    .btn {
        @apply min-h-[44px] px-4;
    }
    
    .chore-card {
        @apply p-4;
    }
    
    .checkbox-label {
        @apply py-2;
    }
}
```

### 2. Stacked Layout for Small Screens
```html
<!-- Responsive grid that stacks on mobile -->
<div class="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
    <!-- Chore cards -->
</div>
```

## Performance Optimizations

### 1. Debounced Polling
```javascript
// Reduce server load with smart polling
let pollInterval = 10000; // Start with 10 seconds
let lastActivityTime = Date.now();

// Increase interval when inactive
setInterval(() => {
    const timeSinceActivity = Date.now() - lastActivityTime;
    if (timeSinceActivity > 300000) { // 5 minutes
        pollInterval = 60000; // Poll every minute when inactive
    } else {
        pollInterval = 10000; // Poll every 10 seconds when active
    }
}, 60000);

// Reset on user activity
document.addEventListener('click', () => {
    lastActivityTime = Date.now();
    pollInterval = 10000;
});
```

### 2. Lazy Loading
```html
<!-- Load completed chores only when visible -->
<div id="completed-chores"
     hx-get="/api/v1/html/chores/my-completed"
     hx-trigger="intersect once">
    <!-- Loading skeleton -->
</div>
```

## Testing Considerations

### 1. Feature-Specific Tests
- Test visibility settings persistence
- Test chore filtering based on visibility
- Test recurrence calculations
- Test progress bar accuracy
- Test auto-refresh when chores become available

### 2. Edge Cases
- Child with all chores hidden
- Timezone handling for reset times
- Leap year for monthly recurrence
- Concurrent visibility updates

## Implementation Timeline Summary

### Phase-by-Phase Breakdown
- **Phase 1**: Core UI/Template Updates (1.5 days)
  - Subphase 1.1: Parent Chore Creation Form (0.5 day)
  - Subphase 1.2: Child Dashboard Layout (0.5 day)
  - Subphase 1.3: Component Templates (0.5 day)

- **Phase 2**: JavaScript/Alpine.js Implementation (2 days)
  - Subphase 2.1: Visibility Settings Component (0.5 day)
  - Subphase 2.2: Timer and Progress Components (0.75 day)
  - Subphase 2.3: HTMX Integration (0.75 day)

- **Phase 3**: Parent Management Features (1.5 days)
  - Subphase 3.1: Visibility Management Interface (0.75 day)
  - Subphase 3.2: Chore Management Dashboard (0.75 day)

- **Phase 4**: Styling and Responsive Design (1 day)
  - Subphase 4.1: CSS Implementation (0.5 day)
  - Subphase 4.2: Mobile Optimization (0.5 day)

- **Phase 5**: Integration and Polish (1 day)
  - Subphase 5.1: End-to-End Testing (0.5 day)
  - Subphase 5.2: Performance and Polish (0.5 day)

**Total: 7 days** (increased from 6 due to detailed testing requirements)

## Success Metrics

### Phase 1 Success Criteria
- [ ] All templates render correctly
- [ ] Forms submit with proper data
- [ ] Responsive layout works on all devices
- [ ] 100% accessibility compliance

### Phase 2 Success Criteria
- [ ] All JavaScript components functional
- [ ] API integration working smoothly
- [ ] Timer accuracy within 1 minute
- [ ] No memory leaks

### Phase 3 Success Criteria
- [ ] Visibility management intuitive
- [ ] Bulk operations < 2s
- [ ] Real-time updates working
- [ ] Parent workflow streamlined

### Phase 4 Success Criteria
- [ ] All animations smooth (60fps)
- [ ] Mobile touch targets >= 44px
- [ ] CSS works in all browsers
- [ ] Page weight < 500KB

### Phase 5 Success Criteria
- [ ] All E2E tests passing
- [ ] Page load < 2s
- [ ] 0 console errors
- [ ] User satisfaction > 90%

## Risk Mitigation

### Technical Risks
1. **HTMX Polling Performance**: Use smart intervals and connection pooling
2. **Timer Synchronization**: Server-side source of truth with client reconciliation
3. **Browser Compatibility**: Progressive enhancement approach

### UX Risks
1. **Complexity for Users**: Progressive disclosure and helpful tooltips
2. **Mobile Performance**: Optimize assets and use lazy loading
3. **Visibility Confusion**: Clear visual indicators and onboarding

## Migration Notes

### For Existing Users
1. All existing chores will have default visibility (visible to all)
2. Non-recurring chores remain unchanged
3. UI gracefully handles mixed chore types
4. No breaking changes to existing workflows

## Documentation Requirements

### For Each Phase
- [ ] Update user documentation
- [ ] Add inline code comments
- [ ] Create component documentation
- [ ] Update style guide

### Developer Documentation
- [ ] Alpine.js component reference
- [ ] HTMX endpoint documentation
- [ ] CSS class reference
- [ ] Testing guide