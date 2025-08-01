# Reward Adjustments - Manual Testing Plan

**Feature**: Reward Adjustments System  
**Environment**: Local Development (Docker Compose)  
**Last Updated**: 2025-08-01

## Prerequisites

1. **Start the application**:
   ```bash
   docker-compose up
   ```

2. **Verify the application is running**:
   - API Documentation: http://localhost:8000/docs
   - Main Application: http://localhost:8000

3. **Database is migrated** (should be automatic, but verify):
   ```bash
   docker compose exec api python -m alembic -c backend/alembic.ini current
   ```
   Should show the latest migration including `reward_adjustments` table.

## Test Data Setup

### Important Note on User Creation

There are two ways to create users:
- **Parent accounts**: Use `/api/v1/users/register` endpoint (no authentication required)
- **Child accounts**: Use `/api/v1/users/` endpoint (requires parent authentication)

### Create Test Users

1. **Create a parent account** (single line command):
   ```bash
   curl -X POST http://localhost:8000/api/v1/users/register -F "username=testparent1" -F "email=parent1@test.com" -F "password=TestPass123" -F "is_parent=true"
   ```
   
   Note: 
   - Password simplified to avoid copy/paste issues with special characters
   - If you get an error about username already existing, try a different username (e.g., testparent2, testparent3, etc.)
   
   Expected response: JSON with user details including the ID.

2. **Login as parent to get token**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/users/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=testparent1&password=TestPass123"
   ```
   
   Save the `access_token` from the response. Example:
   ```bash
   export PARENT_TOKEN="<paste_token_here>"
   ```

3. **Create two child accounts** (requires parent authentication):
   ```bash
   # Child 1 (single line)
   curl -X POST http://localhost:8000/api/v1/users/ -H "Content-Type: application/json" -H "Authorization: Bearer $PARENT_TOKEN" -d '{"username":"child1","password":"ChildPass123","is_parent":false}'

   # Child 2 (single line)
   curl -X POST http://localhost:8000/api/v1/users/ -H "Content-Type: application/json" -H "Authorization: Bearer $PARENT_TOKEN" -d '{"username":"child2","password":"ChildPass123","is_parent":false}'
   ```
   
   Note: Child accounts don't require email addresses. The parent_id is automatically set from the authenticated parent's token.

4. **Get child IDs**:
   ```bash
   curl http://localhost:8000/api/v1/users/children \
     -H "Authorization: Bearer $PARENT_TOKEN"
   ```
   Note the IDs for `child1` and `child2`.

## Test Scenarios

**Important**: In the commands below, replace placeholder IDs with your actual IDs:
- Replace `8` with your actual child1 ID
- Replace `9` with your actual child2 ID
- You can find these IDs from the "Get child IDs" step above

### 1. Basic Adjustment Creation (Happy Path)

**Test**: Parent creates a positive adjustment for child1

First, note the child IDs from the previous step (e.g., child1=8, child2=9).

```bash
# Replace 8 with your actual child1 ID
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": 8,
    "amount": "10.00",
    "reason": "Helped with extra chores around the house"
  }'
```

**Expected Result**:
- Status: 201 Created
- Response includes adjustment ID, timestamps, and all fields
- Amount shows as "10.00"

### 2. Negative Adjustment (Penalty)

**Test**: Parent creates a negative adjustment for child1

```bash
# Using child1 ID from earlier (replace 8 with your actual ID)
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": 8,
    "amount": "-5.00",
    "reason": "Broke household rule - no TV for a week"
  }'
```

**Expected Result**:
- Status: 201 Created
- Amount shows as "-5.00"

### 3. View Adjustments

**Test**: Parent views all adjustments

```bash
# Get all adjustments
curl http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $PARENT_TOKEN"

# Get adjustments for specific child (replace 8 with your child ID)
curl "http://localhost:8000/api/v1/adjustments/?child_id=8" \
  -H "Authorization: Bearer $PARENT_TOKEN"
```

**Expected Result**:
- Status: 200 OK
- Returns array of adjustments
- Filtering by child_id returns only that child's adjustments

### 4. Check Balance in Allowance Summary

**Test**: View updated balance including adjustments

1. **Via API**:
   ```bash
   curl http://localhost:8000/api/v1/users/summary \
     -H "Authorization: Bearer $PARENT_TOKEN"
   ```

2. **Via Browser**:
   - Navigate to http://localhost:8000
   - Login as parent
   - Go to "Allowance Summary"
   - Check that child1's balance shows adjustments (+$10 - $5 = +$5 in adjustments)

**Expected Result**:
- Adjustments column shows the net adjustment amount
- Balance Due includes adjustments in calculation

### 5. UI Testing - Adjustment Forms

**Test**: Use the inline adjustment form

1. **Via Browser**:
   - Login as parent at http://localhost:8000
   - Go to "Allowance Summary"
   - Click "Adjust" button next to child1
   - Fill in the inline form:
     - Amount: 15.00
     - Reason: "Perfect test scores this week!"
   - Submit the form

**Expected Result**:
- Form appears inline below the child's row
- After submission, allowance summary updates automatically
- New adjustment reflected in balance

### 6. Authorization Tests

**Test 6.1**: Child cannot create adjustments

```bash
# Login as child1
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=child1&password=ChildPass123!"

# Save token as CHILD_TOKEN

# Try to create adjustment
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": <CHILD1_ID>,
    "amount": "100.00",
    "reason": "I deserve it!"
  }'
```

**Expected Result**:
- Status: 403 Forbidden
- Error: "Only parents can create reward adjustments"

**Test 6.2**: Child cannot view adjustments

```bash
curl http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $CHILD_TOKEN"
```

**Expected Result**:
- Status: 403 Forbidden
- Error: "Children cannot view reward adjustments in this version"

### 7. Validation Tests

**Test 7.1**: Zero amount rejection

```bash
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": <CHILD1_ID>,
    "amount": "0.00",
    "reason": "Zero test"
  }'
```

**Expected Result**:
- Status: 422 Unprocessable Entity
- Error mentions amount cannot be zero

**Test 7.2**: Amount too large

```bash
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": <CHILD1_ID>,
    "amount": "1000.00",
    "reason": "Too much!"
  }'
```

**Expected Result**:
- Status: 422 Unprocessable Entity
- Error mentions amount must be less than or equal to 999.99

**Test 7.3**: Empty reason

```bash
curl -X POST http://localhost:8000/api/v1/adjustments/ \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": <CHILD1_ID>,
    "amount": "5.00",
    "reason": ""
  }'
```

**Expected Result**:
- Status: 422 Unprocessable Entity
- Error about reason being required

### 8. Negative Balance Prevention

**Test**: Try to create adjustment that would result in negative balance

1. **Reset child2 to have only $10 in adjustments**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/adjustments/ \
     -H "Authorization: Bearer $PARENT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "child_id": <CHILD2_ID>,
       "amount": "10.00",
       "reason": "Starting balance"
     }'
   ```

2. **Try to deduct $20**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/adjustments/ \
     -H "Authorization: Bearer $PARENT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "child_id": <CHILD2_ID>,
       "amount": "-20.00",
       "reason": "Large penalty"
     }'
   ```

**Expected Result**:
- Status: 400 Bad Request
- Error: "Adjustment would result in negative balance. Current balance: $10.00"

### 9. Quick Amount Buttons (UI)

**Test**: Use quick amount buttons in inline form

1. **Via Browser**:
   - Login as parent
   - Go to "Allowance Summary"
   - Click "Adjust" for a child
   - Click the quick amount buttons (+$5, +$10, -$5, -$10)
   - Add a reason and submit

**Expected Result**:
- Clicking buttons fills in the amount field
- Form submits successfully
- Balance updates immediately

### 10. Pagination Test

**Test**: Create many adjustments and test pagination

```bash
# Create 15 adjustments for child1
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/v1/adjustments/ \
    -H "Authorization: Bearer $PARENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"child_id\": <CHILD1_ID>,
      \"amount\": \"1.00\",
      \"reason\": \"Test adjustment $i\"
    }"
done

# Test pagination
curl "http://localhost:8000/api/v1/adjustments/?limit=5&skip=0" \
  -H "Authorization: Bearer $PARENT_TOKEN"

curl "http://localhost:8000/api/v1/adjustments/?limit=5&skip=5" \
  -H "Authorization: Bearer $PARENT_TOKEN"
```

**Expected Result**:
- First request returns 5 adjustments
- Second request returns next 5 adjustments
- No overlap between pages

## Browser-Based Testing Checklist

### Parent User Flow

- [ ] Login as parent
- [ ] Navigate to Allowance Summary
- [ ] See "Adjust" button for each child
- [ ] Click "Adjust" button - inline form appears
- [ ] Fill form with positive amount and submit
- [ ] See success message and updated balance
- [ ] Click "Adjust" again for negative amount
- [ ] Submit and see updated balance
- [ ] Try to submit with $0 - see validation error
- [ ] Try to submit with empty reason - see validation error
- [ ] Use quick amount buttons (+$5, +$10, -$5, -$10)
- [ ] Character counter shows remaining characters for reason

### Child User Flow

- [ ] Login as child
- [ ] Navigate to Allowance Summary
- [ ] Should NOT see "Adjust" button
- [ ] Should see total balance including adjustments
- [ ] Cannot access adjustment endpoints directly

## Performance Testing

### Rate Limiting

**Test**: Verify rate limits are enforced

```bash
# Make 31 POST requests rapidly (limit is 30/minute)
for i in {1..31}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/v1/adjustments/ \
    -H "Authorization: Bearer $PARENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "child_id": <CHILD1_ID>,
      "amount": "1.00",
      "reason": "Rate limit test"
    }' \
    -w "\nStatus: %{http_code}\n"
done
```

**Expected Result**:
- First 30 requests: Status 201
- 31st request: Status 429 (Too Many Requests)

## Troubleshooting

### Common Issues

1. **"Invalid authentication credentials" error**:
   - Your token has expired (tokens expire after 30 minutes)
   - Re-login to get a new token:
   ```bash
   curl -X POST http://localhost:8000/api/v1/users/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=testparent1&password=TestPass123"
   export PARENT_TOKEN="<new_token>"
   ```

1. **"Child user not found" error**:
   - Verify the child_id is correct
   - Ensure the child belongs to the logged-in parent

2. **"Adjustment would result in negative balance"**:
   - Check current balance before applying penalties
   - Add positive adjustments first if testing penalties

3. **Form not appearing in UI**:
   - Check browser console for JavaScript errors
   - Ensure HTMX library is loaded
   - Verify authentication token is valid

### Debug Commands

```bash
# Check if migration was applied
docker compose exec api python -m alembic -c backend/alembic.ini history

# View database directly
docker compose exec db mysql -u root -p<password> chores_tracker -e "SELECT * FROM reward_adjustments;"

# Check API logs
docker compose logs -f api

# Verify user relationships
docker compose exec db mysql -u root -p<password> chores_tracker -e "SELECT id, username, is_parent, parent_id FROM users;"
```

## Success Criteria

- [ ] All positive adjustment scenarios work correctly
- [ ] All negative adjustment scenarios work correctly
- [ ] Authorization properly enforced (parents only)
- [ ] Validation rules prevent invalid data
- [ ] Negative balance prevention works
- [ ] UI forms function properly with HTMX
- [ ] Allowance summary shows correct totals
- [ ] Rate limiting protects endpoints
- [ ] Pagination works for large datasets

## Notes

- The MVP version does not allow children to view their adjustment history
- Adjustments are immutable - no edit or delete functionality
- All amounts must be between -999.99 and 999.99
- Reasons must be between 3 and 500 characters