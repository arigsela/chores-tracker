"""
Comprehensive error scenario testing for reward adjustment API endpoints.

Tests various error conditions including:
- Authentication errors
- Authorization errors
- Validation errors
- Rate limiting
- Malformed requests
"""
import asyncio
import httpx
import json
from decimal import Decimal
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test credentials
PARENT_USERNAME = "testparent2"
PARENT_PASSWORD = "password123"
PARENT2_USERNAME = "testparent"
PARENT2_PASSWORD = "password123"
CHILD_USERNAME = "testchild"
CHILD_PASSWORD = "password123"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


async def print_test_header(test_name: str):
    """Print a formatted test header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== {test_name} ==={Colors.ENDC}")


async def print_result(success: bool, message: str):
    """Print a test result with color."""
    if success:
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


async def get_auth_token(username: str, password: str) -> str:
    """Authenticate and get JWT token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/users/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None


async def test_authentication_errors():
    """Test authentication error scenarios."""
    await print_test_header("Testing Authentication Errors")
    
    # Test 1: Missing token
    print("\n1. Missing authentication token:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            json={"child_id": 2, "amount": "5.00", "reason": "Test"}
        )
        await print_result(
            response.status_code == 401,
            f"Missing token returns 401: {response.status_code}"
        )
    
    # Test 2: Invalid token
    print("\n2. Invalid authentication token:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers={"Authorization": "Bearer invalid_token"},
            json={"child_id": 2, "amount": "5.00", "reason": "Test"}
        )
        await print_result(
            response.status_code == 401,
            f"Invalid token returns 401: {response.status_code}"
        )
    
    # Test 3: Malformed authorization header
    print("\n3. Malformed authorization header:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers={"Authorization": "NotBearer token"},
            json={"child_id": 2, "amount": "5.00", "reason": "Test"}
        )
        await print_result(
            response.status_code == 401,
            f"Malformed header returns 401: {response.status_code}"
        )


async def test_authorization_errors():
    """Test authorization error scenarios."""
    await print_test_header("Testing Authorization Errors")
    
    # Get tokens
    parent_token = await get_auth_token(PARENT_USERNAME, PARENT_PASSWORD)
    parent2_token = await get_auth_token(PARENT2_USERNAME, PARENT2_PASSWORD)
    child_token = await get_auth_token(CHILD_USERNAME, CHILD_PASSWORD)
    
    if not all([parent_token, parent2_token]):
        print(f"{Colors.RED}Failed to get auth tokens{Colors.ENDC}")
        return
    
    # Test 1: Child trying to create adjustment
    if child_token:
        print("\n1. Child trying to create adjustment:")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/adjustments/",
                headers={"Authorization": f"Bearer {child_token}"},
                json={"child_id": 2, "amount": "5.00", "reason": "Child attempt"}
            )
            await print_result(
                response.status_code == 403,
                f"Child creating adjustment returns 403: {response.status_code}"
            )
    
    # Test 2: Parent adjusting another parent's child
    print("\n2. Parent adjusting another parent's child:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers={"Authorization": f"Bearer {parent2_token}"},
            json={"child_id": 2, "amount": "5.00", "reason": "Wrong parent"}
        )
        await print_result(
            response.status_code == 403,
            f"Wrong parent returns 403: {response.status_code}"
        )
    
    # Test 3: Parent viewing another parent's child adjustments
    print("\n3. Parent viewing another parent's child adjustments:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/adjustments/child/2",
            headers={"Authorization": f"Bearer {parent2_token}"}
        )
        await print_result(
            response.status_code == 403,
            f"Wrong parent viewing returns 403: {response.status_code}"
        )


async def test_validation_errors():
    """Test validation error scenarios beyond basic ones."""
    await print_test_header("Testing Advanced Validation Errors")
    
    parent_token = await get_auth_token(PARENT_USERNAME, PARENT_PASSWORD)
    if not parent_token:
        print(f"{Colors.RED}Failed to get auth token{Colors.ENDC}")
        return
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    
    # Test 1: Missing required fields
    print("\n1. Missing required fields:")
    test_cases = [
        ({"amount": "5.00", "reason": "Test"}, "missing child_id"),
        ({"child_id": 2, "reason": "Test"}, "missing amount"),
        ({"child_id": 2, "amount": "5.00"}, "missing reason"),
    ]
    
    for data, description in test_cases:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/adjustments/",
                headers=headers,
                json=data
            )
            await print_result(
                response.status_code == 422,
                f"Request with {description} returns 422: {response.status_code}"
            )
    
    # Test 2: Invalid data types
    print("\n2. Invalid data types:")
    test_cases = [
        ({"child_id": "not_a_number", "amount": "5.00", "reason": "Test"}, "string child_id"),
        ({"child_id": 2, "amount": "not_a_number", "reason": "Test"}, "invalid amount"),
        ({"child_id": 2, "amount": "5.00", "reason": 123}, "numeric reason"),
    ]
    
    for data, description in test_cases:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/adjustments/",
                headers=headers,
                json=data
            )
            await print_result(
                response.status_code == 422,
                f"Request with {description} returns 422: {response.status_code}"
            )
    
    # Test 3: Non-existent child
    print("\n3. Non-existent child:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json={"child_id": 99999, "amount": "5.00", "reason": "Non-existent child"}
        )
        await print_result(
            response.status_code == 404,
            f"Non-existent child returns 404: {response.status_code}"
        )


async def test_rate_limiting():
    """Test rate limiting."""
    await print_test_header("Testing Rate Limiting")
    
    parent_token = await get_auth_token(PARENT_USERNAME, PARENT_PASSWORD)
    if not parent_token:
        print(f"{Colors.RED}Failed to get auth token{Colors.ENDC}")
        return
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    
    # Test: Exceed rate limit for create endpoint (30/min)
    print("\n1. Testing create endpoint rate limit (30 requests/min):")
    print("Making 35 rapid requests...")
    
    success_count = 0
    rate_limited_count = 0
    
    async with httpx.AsyncClient() as client:
        for i in range(35):
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/adjustments/",
                headers=headers,
                json={
                    "child_id": 2,
                    "amount": "1.00",
                    "reason": f"Rate limit test {i+1}"
                }
            )
            if response.status_code == 201:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.1)
    
    await print_result(
        rate_limited_count > 0,
        f"Rate limiting activated: {success_count} succeeded, {rate_limited_count} rate limited"
    )


async def test_malformed_requests():
    """Test malformed request scenarios."""
    await print_test_header("Testing Malformed Requests")
    
    parent_token = await get_auth_token(PARENT_USERNAME, PARENT_PASSWORD)
    if not parent_token:
        print(f"{Colors.RED}Failed to get auth token{Colors.ENDC}")
        return
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    
    # Test 1: Invalid JSON
    print("\n1. Invalid JSON body:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers={**headers, "Content-Type": "application/json"},
            content='{"child_id": 2, "amount": "5.00", "reason": "Test"'  # Missing closing brace
        )
        await print_result(
            response.status_code in [400, 422],
            f"Invalid JSON returns 400/422: {response.status_code}"
        )
    
    # Test 2: Wrong content type
    print("\n2. Wrong content type:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers={**headers, "Content-Type": "text/plain"},
            content='{"child_id": 2, "amount": "5.00", "reason": "Test"}'
        )
        await print_result(
            response.status_code in [415, 422],
            f"Wrong content type returns 415/422: {response.status_code}"
        )
    
    # Test 3: Empty body
    print("\n3. Empty request body:")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json={}
        )
        await print_result(
            response.status_code == 422,
            f"Empty body returns 422: {response.status_code}"
        )


async def test_edge_cases():
    """Test edge case scenarios."""
    await print_test_header("Testing Edge Cases")
    
    parent_token = await get_auth_token(PARENT_USERNAME, PARENT_PASSWORD)
    if not parent_token:
        print(f"{Colors.RED}Failed to get auth token{Colors.ENDC}")
        return
    
    headers = {"Authorization": f"Bearer {parent_token}"}
    
    # Test 1: Maximum values
    print("\n1. Maximum allowed values:")
    async with httpx.AsyncClient() as client:
        # Max positive amount
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json={
                "child_id": 2,
                "amount": "999.99",
                "reason": "Maximum positive adjustment test"
            }
        )
        await print_result(
            response.status_code == 201,
            f"Max positive amount (999.99) accepted: {response.status_code}"
        )
        
        # Max negative amount
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json={
                "child_id": 2,
                "amount": "-999.99",
                "reason": "Maximum negative adjustment test"
            }
        )
        await print_result(
            response.status_code == 201,
            f"Max negative amount (-999.99) accepted: {response.status_code}"
        )
    
    # Test 2: Very long reason (exactly 500 chars)
    print("\n2. Maximum length reason (500 characters):")
    long_reason = "x" * 500
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/adjustments/",
            headers=headers,
            json={
                "child_id": 2,
                "amount": "1.00",
                "reason": long_reason
            }
        )
        await print_result(
            response.status_code == 201,
            f"500-character reason accepted: {response.status_code}"
        )
    
    # Test 3: Pagination limits
    print("\n3. Pagination edge cases:")
    async with httpx.AsyncClient() as client:
        # Negative skip
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/adjustments/child/2?skip=-1",
            headers=headers
        )
        await print_result(
            response.status_code == 422,
            f"Negative skip returns 422: {response.status_code}"
        )
        
        # Limit exceeding maximum
        response = await client.get(
            f"{BASE_URL}{API_PREFIX}/adjustments/child/2?limit=101",
            headers=headers
        )
        await print_result(
            response.status_code == 422,
            f"Limit > 100 returns 422: {response.status_code}"
        )


async def main():
    """Run all error scenario tests."""
    print(f"{Colors.BOLD}Comprehensive Error Scenario Testing for Reward Adjustments API{Colors.ENDC}")
    print("=" * 70)
    
    # Run all test suites
    await test_authentication_errors()
    await test_authorization_errors()
    await test_validation_errors()
    await test_malformed_requests()
    await test_edge_cases()
    
    # Rate limiting test (run last as it might affect other tests)
    print(f"\n{Colors.YELLOW}Note: Skipping rate limit test to avoid affecting other tests{Colors.ENDC}")
    print("To test rate limiting, run: await test_rate_limiting()")
    
    print(f"\n{Colors.BOLD}=== All Error Scenario Tests Complete ==={Colors.ENDC}")


if __name__ == "__main__":
    asyncio.run(main())