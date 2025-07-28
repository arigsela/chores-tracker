# Master Chore List Implementation Overview v2

## Executive Summary

The Master Chore List feature transforms the chores-tracker application from a direct-assignment model to a pool-based system where parents create unassigned chores that children can claim. This version 2 includes two critical enhancements:
1. **Selective Visibility**: Parents can hide specific chores from certain children
2. **Grayed Out Completed Chores**: Completed recurring chores remain visible but unavailable until their reset time

## Feature Overview

### Current State (V1)
- Parents create chores and assign them to specific children
- Children can only see and complete their assigned chores
- Direct 1:1 relationship between chore and child

### Future State (V2) - Enhanced
- Parents create chores without assigning them (master pool)
- **NEW**: Parents can hide specific chores from certain children
- Children see available chores (excluding hidden ones) and can claim them
- First child to claim gets the chore and reward
- **NEW**: Completed recurring chores show as grayed out until reset
- Maintains backward compatibility with V1 assigned chores

## Key Feature Enhancements

### 1. Selective Visibility
- **Use Case**: "Clean older child's room" hidden from younger children
- **Implementation**: New `chore_visibility` table tracks hidden chores per child
- **Parent Control**: Manage visibility during creation or edit later
- **Visual Indicators**: "Hidden from X children" badge on parent dashboard

### 2. Grayed Out Completed Chores
- **Use Case**: Daily/weekly/monthly chores show progress until available again
- **Implementation**: Track `next_available_time` and show countdown
- **Visual Design**: Grayed out cards with progress bars
- **Auto-refresh**: Chores automatically move to available when reset time reached

## Architecture Decisions

### 1. API Versioning Strategy
- **Decision**: Create V2 endpoints alongside V1
- **Rationale**: Ensures zero disruption to existing users
- **Implementation**: `/api/v1/*` remains unchanged, `/api/v2/*` adds new functionality

### 2. Database Schema Approach
- **Decision**: Extend existing schema + new visibility table
- **Fields Added**: 
  - `api_version`, `claimed_at` (original)
  - `recurrence_type`, `recurrence_value`, `next_available_time` (new)
  - `chore_visibility` table for hiding rules (new)
- **Benefit**: Granular control with minimal complexity

### 3. Real-time Updates
- **Web**: HTMX polling with smart intervals
- **Mobile**: Event-driven updates with countdown timers
- **Auto-refresh**: When completed chores become available

### 4. Conflict Resolution
- **Strategy**: First-come-first-served with optimistic UI
- **Implementation**: Database-level constraints prevent double claims
- **User Experience**: Clear error messages and visual feedback

## Implementation Phases - Detailed Breakdown

### Phase 1: Backend Foundation (6.5 days total)
#### Database Foundation (2 days)
- Subphase 1.1: Schema Design & Migration Scripts (0.5 day)
- Subphase 1.2: SQLAlchemy Models (0.5 day)
- Subphase 1.3: Pydantic Schemas (0.5 day)
- Subphase 1.4: Database Migration Execution (0.5 day)

#### Service Layer Implementation (2 days)
- Subphase 2.1: ChoreVisibilityService (0.5 day)
- Subphase 2.2: Recurrence Calculation Engine (0.75 day)
- Subphase 2.3: Enhanced ChoreService (0.75 day)

#### API Layer Implementation (1.5 days)
- Subphase 3.1: Visibility Management Endpoints (0.5 day)
- Subphase 3.2: Enhanced Chore List Endpoints (0.5 day)
- Subphase 3.3: HTMX HTML Endpoints (0.5 day)

#### Integration & Performance (1 day)
- Subphase 4.1: End-to-End Integration Tests (0.5 day)
- Subphase 4.2: Performance Testing & Optimization (0.5 day)

### Phase 2: Web Frontend (7 days total)
#### Core UI/Template Updates (1.5 days)
- Subphase 1.1: Parent Chore Creation Form (0.5 day)
- Subphase 1.2: Child Dashboard Layout (0.5 day)
- Subphase 1.3: Component Templates (0.5 day)

#### JavaScript/Alpine.js Implementation (2 days)
- Subphase 2.1: Visibility Settings Component (0.5 day)
- Subphase 2.2: Timer and Progress Components (0.75 day)
- Subphase 2.3: HTMX Integration (0.75 day)

#### Parent Management Features (1.5 days)
- Subphase 3.1: Visibility Management Interface (0.75 day)
- Subphase 3.2: Chore Management Dashboard (0.75 day)

#### Styling and Responsive Design (1 day)
- Subphase 4.1: CSS Implementation (0.5 day)
- Subphase 4.2: Mobile Optimization (0.5 day)

#### Integration and Polish (1 day)
- Subphase 5.1: End-to-End Testing (0.5 day)
- Subphase 5.2: Performance and Polish (0.5 day)

### Phase 3: Mobile App (9.5 days total)
#### API Service and Data Layer (1.5 days)
- Subphase 1.1: API Service Updates (0.5 day)
- Subphase 1.2: State Management Updates (0.5 day)
- Subphase 1.3: Data Models and Types (0.5 day)

#### Core UI Components (2 days)
- Subphase 2.1: Child Chores Screen Redesign (0.75 day)
- Subphase 2.2: Chore Card Components (0.75 day)
- Subphase 2.3: Create/Edit Chore Updates (0.5 day)

#### Parent Management Features (2 days)
- Subphase 3.1: Visibility Management Screen (1 day)
- Subphase 3.2: Parent Dashboard Updates (1 day)

#### Platform-Specific Enhancements (1.5 days)
- Subphase 4.1: iOS Optimizations (0.75 day)
- Subphase 4.2: Android Optimizations (0.75 day)

#### Offline Support and Performance (1.5 days)
- Subphase 5.1: Offline Capabilities (0.75 day)
- Subphase 5.2: Performance Optimization (0.75 day)

#### Integration and Final Testing (1 day)
- Subphase 6.1: End-to-End Testing (0.5 day)
- Subphase 6.2: Release Preparation (0.5 day)

### Phase 4: Testing & QA (9 days total)
#### Unit Testing Foundation (1.5 days)
- Subphase 1.1: Backend Unit Tests (0.5 day)
- Subphase 1.2: Frontend Unit Tests (0.5 day)
- Subphase 1.3: Mobile Unit Tests (0.5 day)

#### Integration Testing (2 days)
- Subphase 2.1: API Integration Tests (0.75 day)
- Subphase 2.2: Database Integration Tests (0.75 day)
- Subphase 2.3: Frontend Integration Tests (0.5 day)

#### End-to-End Testing (2 days)
- Subphase 3.1: Core Feature E2E Tests (1 day)
- Subphase 3.2: Edge Case E2E Tests (0.5 day)
- Subphase 3.3: Cross-Platform E2E Tests (0.5 day)

#### Performance and Load Testing (1.5 days)
- Subphase 4.1: Backend Performance Tests (0.75 day)
- Subphase 4.2: Frontend Performance Tests (0.75 day)

#### Security and Accessibility Testing (1 day)
- Subphase 5.1: Security Testing (0.5 day)
- Subphase 5.2: Accessibility Testing (0.5 day)

#### User Acceptance Testing (1 day)
- Subphase 6.1: Alpha Testing (0.5 day)
- Subphase 6.2: Beta Testing (0.5 day)

### Phase 5: Deployment (1 day)
- Feature flag configuration
- Production database migration
- Gradual rollout strategy
- Monitoring and alerting setup
- Documentation and training materials

**Total Timeline: 33 days** (with parallel execution of some phases, actual timeline would be 18-20 days)

## Technical Implementation Details

### Backend (FastAPI + SQLAlchemy)
```python
# Key additions:
- ChoreVisibility model and service
- Recurrence calculation logic
- Enhanced filtering in ChoreServiceV2
- New endpoints: 
  - PUT /api/v2/chores/{id}/visibility
  - GET /api/v2/chores/my-chores (returns available + completed)
```

### Web Frontend (Jinja2 + HTMX)
```html
<!-- Key additions: -->
- Visibility checkboxes in create/edit forms
- Two-section layout (available/completed)
- Countdown timers with progress bars
- Auto-refresh when chores become available
- Parent visibility management UI
```

### Mobile App (React Native)
```javascript
// Key additions:
- ChoreVisibilityScreen for parents
- Timer components with background updates
- Progress indicators for completed chores
- Visibility filtering in chore lists
```

## Database Schema Updates

### New Table: chore_visibility
```sql
CREATE TABLE chore_visibility (
    id INT PRIMARY KEY,
    chore_id INT NOT NULL,
    user_id INT NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    UNIQUE(chore_id, user_id),
    FOREIGN KEY (chore_id) REFERENCES chores(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Updated chores table
```sql
ALTER TABLE chores ADD COLUMN recurrence_type ENUM('none','daily','weekly','monthly');
ALTER TABLE chores ADD COLUMN recurrence_value INT;
ALTER TABLE chores ADD COLUMN next_available_time TIMESTAMP;
ALTER TABLE chores ADD COLUMN last_completion_time TIMESTAMP;
```

## Risk Management

### Technical Risks
1. **Visibility Rule Complexity**
   - Mitigation: Simple include/exclude model
   - Testing: Comprehensive filtering tests

2. **Timer Synchronization**
   - Mitigation: Server-side source of truth
   - Testing: Timezone and DST scenarios

3. **Performance with Visibility Filtering**
   - Mitigation: Proper indexes on visibility table
   - Monitoring: Query performance metrics

### Business Risks
1. **Feature Complexity**
   - Mitigation: Progressive disclosure in UI
   - Training: Parent guides for visibility

2. **Child Confusion**
   - Mitigation: Clear visual states
   - Education: In-app tooltips

## Success Metrics

### Technical Metrics
- Visibility query overhead <50ms
- Timer accuracy within 1 minute
- Zero visibility bypass incidents
- <100ms recurrence calculations

### Business Metrics
- 30% of parents use visibility settings
- 80% understand grayed out state
- Reduced support tickets about chore availability
- Increased recurring chore completion rates

### User Experience Metrics
- Time to understand new features <2 minutes
- Visibility setting success rate >90%
- Positive feedback on countdown timers
- Reduced confusion about chore availability

## Migration Strategy

### For Existing Users
1. All existing chores visible to all children (default)
2. Non-recurring chores unaffected
3. Completed chores without recurrence remain completed
4. Graceful feature introduction with tooltips

### Database Migration
```sql
-- Set defaults for existing data
UPDATE chores SET recurrence_type = 'none' WHERE recurrence_type IS NULL;
UPDATE chores SET api_version = 'v1' WHERE api_version IS NULL;
-- No visibility restrictions by default
```

## Testing Focus Areas

### 1. Visibility Testing
- Hidden chores don't appear in child's list
- Parents can always see all chores
- Visibility changes take effect immediately
- Direct API access blocked for hidden chores

### 2. Recurrence Testing
- Daily reset at midnight local time
- Weekly reset on correct day
- Monthly handling of edge cases (31st, Feb)
- Timezone transitions (DST)

### 3. Integration Testing
- Hidden recurring chores
- Visibility changes on completed chores
- Performance with many visibility rules
- Mobile/web synchronization

## User Communication

### For Parents
1. **Feature Announcement**: "New! Control which children see which chores"
2. **Tutorial**: Interactive guide for visibility settings
3. **Use Cases**: Examples like age-appropriate chores
4. **FAQ**: Common questions about hiding chores

### For Children  
1. **Visual Guide**: Understanding grayed out chores
2. **Countdown Explanation**: When chores become available
3. **No Visibility Mention**: Children unaware of hidden chores

## Future Enhancements

### Near Term (1-3 months)
1. **Bulk Visibility Management**: Apply rules to multiple chores
2. **Age-Based Rules**: Auto-hide based on child age
3. **Visibility Templates**: Save common hiding patterns
4. **Notification Options**: Alert when hidden chore completed

### Medium Term (3-6 months)
1. **Smart Visibility**: AI-suggested visibility based on completion history
2. **Chore Categories**: Hide entire categories from children
3. **Temporary Visibility**: Time-based visibility rules
4. **Visibility Analytics**: Insights for parents

### Long Term (6-12 months)
1. **Skill-Based Visibility**: Hide based on skill level
2. **Progressive Disclosure**: Unlock chores as children grow
3. **Family Visibility Policies**: Org-wide rules
4. **Cross-Family Sharing**: With visibility controls

## Conclusion

Version 2 of the Master Chore List feature adds sophisticated parental controls and better visual feedback for chore availability. These enhancements address key user feedback while maintaining the simplicity of the original design. The selective visibility feature gives parents fine-grained control over chore distribution, while the grayed-out completed chores provide clear visual feedback about when tasks will be available again.

The implementation plan balances feature richness with development complexity, ensuring a smooth rollout that doesn't disrupt existing users while providing powerful new capabilities for those who need them.

## Parallel Execution Strategy

To optimize the timeline from 33 days to 18-20 days, the following activities can run in parallel:

### Parallel Track 1: Backend Development
- Week 1: Database Foundation + Service Layer (Days 1-4)
- Week 2: API Layer + Integration (Days 5-6.5)
- Week 3: Support frontend/mobile integration

### Parallel Track 2: Frontend Development  
- Week 1: Planning and design (can start Day 3)
- Week 2: Core UI implementation (Days 5-9)
- Week 3: Polish and integration (Days 10-12)

### Parallel Track 3: Mobile Development
- Week 1: API integration prep (can start Day 4)
- Week 2: Core features (Days 6-11)
- Week 3: Platform optimization (Days 12-15)

### Parallel Track 4: Testing
- Continuous: Unit tests written alongside development
- Week 2-3: Integration testing as features complete
- Week 3-4: E2E and performance testing

## Critical Path Dependencies

1. **Database schema must be finalized** before:
   - Service layer implementation
   - Frontend visibility UI
   - Mobile data models

2. **API endpoints must be available** before:
   - Frontend HTMX integration
   - Mobile API integration
   - Integration testing

3. **Core features must be complete** before:
   - Performance testing
   - Security testing
   - User acceptance testing

## Resource Allocation

### Recommended Team Structure
- **Backend Developer**: 1 senior developer for 6.5 days
- **Frontend Developer**: 1 developer for 7 days
- **Mobile Developer**: 1-2 developers for 9.5 days
- **QA Engineer**: 1 engineer for 9 days (overlapping with development)
- **DevOps**: Support for deployment (1 day)

### Total Effort
- Development: 23 person-days
- Testing: 9 person-days
- Deployment: 1 person-day
- **Total: 33 person-days**

## Appendices

### A. Related Documents
- [Backend Implementation Plan v2](./MASTER-CHORE-LIST-backend-implementation-v2.md) - Detailed backend phases
- [Web Frontend Implementation Plan v2](./MASTER-CHORE-LIST-web-frontend-implementation-v2.md) - Detailed frontend phases
- [Mobile Implementation Plan v2](./MASTER-CHORE-LIST-mobile-implementation-v2.md) - Detailed mobile phases
- [Testing Strategy v2](./MASTER-CHORE-LIST-testing-strategy-v2.md) - Comprehensive testing phases

### B. Technical Specifications
- Visibility API: `/api/v2/chores/{id}/visibility`
- Recurrence Types: daily, weekly, monthly
- Timer Precision: 1-minute accuracy
- Progress Calculation: Linear based on time elapsed
- Database: MySQL 5.7 with new indexes
- Caching: Consider Redis for visibility rules

### C. Design Assets
- Grayed out chore mockups
- Visibility settings UI
- Countdown timer components
- Progress bar styles
- Mobile app screens
- Accessibility guidelines