# Mobile App API Integration Flow

## API Endpoints Summary

### Authentication & User Data
```
POST /users/login           → Login with credentials
GET  /users/me             → Get current user (includes balance)
```

### Chores
```
GET  /chores/              → List chores (filtered by role)
POST /chores/{id}/complete → Mark chore as complete
```

### Adjustments (NEW)
```
POST /adjustments/         → Create adjustment (parents only)
GET  /adjustments/child/{id} → Get child's adjustments
```

## Data Flow Diagrams

### 1. Child User - Balance Display Flow
```
┌─────────────────┐
│   App Launch    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     GET /users/me
│  Check Auth     │ ──────────────────► Backend
└────────┬────────┘                     Returns: {
         │                                id: 2,
         ▼                                username: "sarah",
┌─────────────────┐                       role: "child",
│ Store User Data │                       balance: 25.50  ← NEW
└────────┬────────┘                     }
         │
         ▼
┌─────────────────┐
│ Display Balance │ ← Shows $25.50
└─────────────────┘
```

### 2. Chore Completion → Balance Update Flow
```
┌──────────────────┐
│ Child Completes  │
│     Chore        │
└────────┬─────────┘
         │
         ▼
    POST /chores/123/complete
         │
         ▼
┌──────────────────┐
│ Backend Updates  │
│  Chore Status    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Parent Approves  │ (Web or Mobile)
└────────┬─────────┘
         │
         ▼
    POST /chores/123/approve
    { reward_amount: 5.00 }
         │
         ▼
┌──────────────────┐
│ Backend Updates  │
│ Child Balance    │ balance += 5.00
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Child Refreshes │
│    Balance       │ GET /users/me
└──────────────────┘ Shows: $30.50
```

### 3. Parent Adjustment Flow
```
┌──────────────────┐
│ Parent Opens     │
│ Child Management │
└────────┬─────────┘
         │
         ▼
    GET /users/     
    (Returns children with balances)
         │
         ▼
┌──────────────────┐
│ Parent Taps      │
│ "Adjust Balance" │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Enter Amount &   │
│     Reason       │ Amount: +10.00
└────────┬─────────┘ Reason: "Extra help"
         │
         ▼
    POST /adjustments/
    {
      child_id: 2,
      amount: 10.00,
      reason: "Extra help with groceries"
    }
         │
         ▼
┌──────────────────┐
│ Backend Updates  │
│ Child Balance    │ balance += 10.00
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Success Message  │
│ List Refreshes   │ Shows new balance
└──────────────────┘
```

## State Management Flow

### AuthContext State Updates
```
                    ┌─────────────┐
                    │ AuthContext │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│     User      │  │    Balance    │  │   Methods     │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ id: 2         │  │ balance: 25.50│  │ refreshBalance│
│ username:     │  │ lastUpdate:   │  │ updateBalance │
│   "sarah"     │  │   Date        │  │ login/logout  │
│ role: "child" │  └───────────────┘  └───────────────┘
└───────────────┘
```

### Component Data Flow
```
App
 │
 ├─ AuthProvider (manages user & balance state)
 │   │
 │   ├─ ChildHomeScreen
 │   │   ├─ BalanceCard (reads balance from context)
 │   │   └─ ChoreList (triggers balance refresh)
 │   │
 │   └─ ParentHomeScreen
 │       └─ ChildManagementScreen
 │           ├─ Child List (shows balances)
 │           └─ AdjustmentModal (updates balance)
```

## Error Handling Flow

### API Error → User Feedback
```
API Call Fails
     │
     ▼
┌────────────────┐
│ Check Status   │
└────────┬───────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
   4XX       5XX
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│ Toast   │ │ Retry   │
│ Error   │ │ Option  │
└─────────┘ └─────────┘

Common Errors:
- 400: Invalid data (show specific message)
- 403: Unauthorized (redirect to login)
- 404: Not found (show friendly message)
- 500: Server error (show retry option)
```

## Caching Strategy

### Balance Caching
```
┌─────────────────┐
│ Fetch Balance   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Store in:
│ Update Context  │ ──► - AuthContext (runtime)
└────────┬────────┘     - AsyncStorage (persist)
         │
         ▼
┌─────────────────┐
│ Check Freshness │ → If < 5 seconds old,
└─────────────────┘   skip refresh
```

### Offline Queue
```
┌─────────────────┐
│ Create Adjust   │
└────────┬────────┘
         │
         ▼
    Network Check
         │
    ┌────┴────┐
    │         │
  Online   Offline
    │         │
    ▼         ▼
┌───────┐ ┌────────┐
│ Send  │ │ Queue  │
│ Now   │ │ Later  │
└───────┘ └────────┘
            │
            ▼
      On Reconnect
            │
            ▼
      Process Queue
```

## Performance Optimizations

### 1. Debounced Balance Refresh
```javascript
// Don't refresh if updated in last 5 seconds
if (Date.now() - lastBalanceUpdate < 5000) return;
```

### 2. Optimistic Updates
```javascript
// Update UI immediately
updateBalance(currentBalance + adjustmentAmount);

// Then sync with backend
await adjustmentService.createAdjustment(...);
```

### 3. Lazy Loading
```javascript
// Load adjustment history only when needed
const AdjustmentHistory = lazy(() => 
  import('./screens/AdjustmentHistoryScreen')
);
```

## Testing API Calls

### Using cURL
```bash
# Get user with balance
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Create adjustment
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": 2,
    "amount": 10.00,
    "reason": "Good behavior bonus"
  }'
```

### Expected Responses
```json
// GET /users/me
{
  "id": 2,
  "username": "sarah",
  "role": "child",
  "is_parent": false,
  "balance": 25.50,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2025-01-02T12:00:00"
}

// POST /adjustments/ (success)
{
  "id": 1,
  "child_id": 2,
  "parent_id": 1,
  "amount": 10.00,
  "reason": "Good behavior bonus",
  "created_at": "2025-01-02T15:30:00"
}

// Error response
{
  "detail": "Adjustment would result in negative balance"
}
```

## Mobile-Specific Considerations

1. **Network Reliability**: Implement retry logic with exponential backoff
2. **Token Expiry**: Auto-refresh tokens before API calls
3. **Background Sync**: Use background tasks for balance updates
4. **Push Notifications**: Notify children of balance changes (future)
5. **Biometric Auth**: Quick access while maintaining security

---

This document provides a complete overview of how the mobile app integrates with the backend API for balance and adjustment features.