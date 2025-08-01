#!/usr/bin/env python3
"""Run Phase 5 tests for reward adjustments feature."""

import subprocess
import sys
import time


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    elapsed_time = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ PASSED in {elapsed_time:.2f}s")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ FAILED in {elapsed_time:.2f}s")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)
    
    return result.returncode == 0


def main():
    """Run all Phase 5 tests."""
    print("PHASE 5 TEST SUITE: Reward Adjustments Feature")
    print("="*60)
    
    # Base command for running tests in Docker
    base_cmd = "docker compose exec api python -m pytest -xvs"
    
    # Define test suites
    test_suites = [
        {
            "name": "Unit Tests - RewardAdjustmentService",
            "cmd": f"{base_cmd} backend/tests/services/test_reward_adjustment_service.py",
            "description": "Testing business logic and validation rules"
        },
        {
            "name": "Repository Tests - RewardAdjustmentRepository",
            "cmd": f"{base_cmd} backend/tests/repositories/test_reward_adjustment_repository.py",
            "description": "Testing data access layer and calculations"
        },
        {
            "name": "API Integration Tests",
            "cmd": f"{base_cmd} backend/tests/api/v1/test_reward_adjustments.py",
            "description": "Testing REST endpoints and authentication"
        },
        {
            "name": "Concurrent Adjustment Tests",
            "cmd": f"{base_cmd} backend/tests/test_concurrent_adjustments.py -m slow",
            "description": "Testing race conditions and concurrent operations"
        }
    ]
    
    # Run each test suite
    results = []
    total_start = time.time()
    
    for suite in test_suites:
        print(f"\n\n{'#'*60}")
        print(f"# {suite['name']}")
        print(f"# {suite['description']}")
        print('#'*60)
        
        success = run_command(suite['cmd'], suite['name'])
        results.append((suite['name'], success))
    
    # Summary
    total_time = time.time() - total_start
    print(f"\n\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {len(results)} test suites")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.2f}s")
    
    # Run coverage report if all tests passed
    if failed == 0:
        print(f"\n{'='*60}")
        print("COVERAGE REPORT")
        print('='*60)
        
        coverage_cmd = f"{base_cmd} --cov=backend/app/services/reward_adjustment_service --cov=backend/app/repositories/reward_adjustment --cov=backend/app/api/v1/reward_adjustments --cov-report=term-missing backend/tests/services/test_reward_adjustment_service.py backend/tests/repositories/test_reward_adjustment_repository.py backend/tests/api/v1/test_reward_adjustments.py"
        
        run_command(coverage_cmd, "Test Coverage Analysis")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()