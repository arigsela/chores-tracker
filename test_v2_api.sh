#!/bin/bash

# Test script for v2 API endpoints using curl
BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

echo "Testing v2 API endpoints..."
echo "=================================================="

# Test 1: Register a parent user
echo -e "\n1. Testing parent registration..."
PARENT_USERNAME="testparent_${TIMESTAMP}"
PARENT_EMAIL="${PARENT_USERNAME}@example.com"

REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v2/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "'${PARENT_USERNAME}'",
    "password": "TestPassword123",
    "email": "'${PARENT_EMAIL}'",
    "is_parent": true
  }')

echo "Response: $REGISTER_RESPONSE"

# Test 2: Login with the parent account
echo -e "\n2. Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v2/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${PARENT_USERNAME}&password=TestPassword123")

echo "Response: $LOGIN_RESPONSE"

# Extract token using grep and sed
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
  echo "Failed to extract token!"
  exit 1
fi

echo "Token extracted successfully"

# Test 3: Get current user
echo -e "\n3. Testing get current user..."
curl -s -X GET "${BASE_URL}/api/v2/users/me" \
  -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool

# Test 4: Register a child user
echo -e "\n4. Testing child registration..."
CHILD_USERNAME="testchild_${TIMESTAMP}"

CHILD_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v2/users/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "username": "'${CHILD_USERNAME}'",
    "password": "ChildPass123",
    "is_parent": false
  }')

echo "Response: $CHILD_RESPONSE"

# Extract child ID
CHILD_ID=$(echo $CHILD_RESPONSE | grep -o '"id":[0-9]*' | sed 's/"id"://')

if [ -z "$CHILD_ID" ]; then
  echo "Failed to extract child ID!"
  exit 1
fi

echo "Child ID: $CHILD_ID"

# Test 5: Create a chore
echo -e "\n5. Testing chore creation..."
curl -s -X POST "${BASE_URL}/api/v2/chores/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "title": "Test Chore",
    "description": "This is a test chore",
    "assignee_id": '${CHILD_ID}',
    "reward": 5.0,
    "is_range_reward": false,
    "cooldown_days": 0,
    "recurrence_type": "none"
  }' | python3 -m json.tool

# Test 6: Get chores list
echo -e "\n6. Testing get chores..."
curl -s -X GET "${BASE_URL}/api/v2/chores/" \
  -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool

# Test 7: Get chore statistics
echo -e "\n7. Testing chore statistics..."
curl -s -X GET "${BASE_URL}/api/v2/chores/stats/summary" \
  -H "Authorization: Bearer ${TOKEN}" | python3 -m json.tool

echo -e "\n=================================================="
echo "v2 API testing complete!"