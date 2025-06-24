#!/bin/bash
# Test the specific failing tests to verify our fixes

echo "Testing CI fixes..."
echo "=================="

# Set testing environment
export TESTING=true

# Run the specific failing tests
echo "1. Testing range reward edge case..."
docker compose exec api python -m pytest backend/tests/api/v1/test_range_reward_edge_cases.py::test_approve_range_reward_with_negative_value -xvs

echo -e "\n2. Testing unit of work service methods..."
docker compose exec api python -m pytest backend/tests/test_unit_of_work_service_methods.py -xvs

echo -e "\nDone! Check results above."