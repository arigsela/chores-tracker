#!/bin/bash
# Script to run v2 API tests using pytest

echo "Running v2 API Tests with pytest..."
echo "=================================="

# Run tests in Docker environment
docker compose exec api python -m pytest backend/tests/api/v2 -v --cov=backend/app/api/api_v2 --cov-report=term-missing

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "\n✅ All v2 API tests passed!"
else
    echo -e "\n❌ Some tests failed. Please check the output above."
    exit 1
fi