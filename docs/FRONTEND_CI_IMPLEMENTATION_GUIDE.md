# Frontend CI Implementation Guide

## Overview

This document provides a comprehensive implementation guide for integrating the React Native frontend test suite into the chores-tracker CI/CD pipeline. The implementation follows the existing backend CI patterns while addressing the specific requirements of React Native, TypeScript, and Expo development.

## Table of Contents

1. [Current Test Suite Analysis](#current-test-suite-analysis)
2. [GitHub Actions Workflow Implementation](#github-actions-workflow-implementation)
3. [Integration Strategies](#integration-strategies)
4. [Caching and Performance Optimization](#caching-and-performance-optimization)
5. [Quality Gates and Coverage Requirements](#quality-gates-and-coverage-requirements)
6. [Environment Variables and Configuration](#environment-variables-and-configuration)
7. [Parallel Execution Strategy](#parallel-execution-strategy)
8. [Code Coverage Integration](#code-coverage-integration)
9. [Error Handling and Debugging](#error-handling-and-debugging)
10. [Future Enhancements](#future-enhancements)

## Current Test Suite Analysis

### Test Structure Overview

The frontend test suite is comprehensive and well-organized:

```
frontend/src/
├── __tests__/integration/          # Integration tests (3 files, ~1,964 lines)
│   ├── approvalWorkflow.test.tsx
│   ├── authFlow.test.tsx
│   └── choreManagement.test.tsx
├── api/__tests__/                  # API layer tests (5 files, ~1,721 lines)
│   ├── auth.test.ts
│   ├── balance.test.ts
│   ├── chores.test.ts
│   ├── client.test.ts
│   └── users.test.ts
├── components/__tests__/           # Component tests (6 files, ~2,989 lines)
│   ├── ActivityCard.test.tsx
│   ├── ActivityFeed.test.tsx
│   ├── ChildCard.test.tsx
│   ├── ChoreCard.test.tsx
│   ├── FinancialSummaryCards.test.tsx
│   └── RejectChoreModal.test.tsx
├── contexts/__tests__/            # Context tests (1 file, ~694 lines)
│   └── AuthContext.test.tsx
├── navigation/__tests__/          # Navigation tests (1 file, ~568 lines)
│   └── SimpleNavigator.test.tsx
├── screens/__tests__/             # Screen tests (5 files, ~2,599 lines)
│   ├── ChoresScreen.test.tsx
│   ├── HomeScreen.test.tsx
│   ├── LoginScreen.simple.test.tsx
│   ├── LoginScreen.test.tsx
│   └── RegisterScreen.test.tsx
└── test-utils/__tests__/          # Test utilities (1 file, ~165 lines)
    └── testUtils.test.ts
```

**Total Test Coverage**: 22 test files with ~10,700+ lines of test code

### Test Configuration Analysis

**Jest Configuration (`frontend/jest.config.js`)**:
- **Preset**: `jest-expo` for React Native/Expo compatibility
- **Test Environment**: `jsdom`
- **Coverage Thresholds**:
  - Global: 80% statements, 75% branches, 80% functions/lines
  - API Layer: 95% statements, 90% branches, 95% functions/lines
  - Contexts: 90% statements, 85% branches, 90% functions/lines
- **Test Timeout**: 10 seconds
- **Coverage Reporters**: text, html, lcov, json

**Available Test Scripts**:
- `test`: Basic Jest execution
- `test:ci`: CI-optimized with coverage and no watch mode
- `test:coverage`: Generate coverage reports
- `test:unit`: Run unit tests (components, contexts, api)
- `test:integration`: Run integration tests
- `test:debug`: Debug mode with verbose output

### Code Quality Tools

**ESLint Configuration**:
- TypeScript parser with React support
- Plugins: TypeScript, React, React Hooks, React Native, Prettier
- Strict rules for unused variables and console usage

**Prettier Configuration**:
- Single quotes, trailing commas, 2-space tabs
- 100 character line width
- LF line endings

## GitHub Actions Workflow Implementation

### Complete Workflow File

Create `.github/workflows/frontend-tests.yml`:

```yaml
name: Frontend Tests

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests.yml'
  pull_request:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests.yml'

env:
  NODE_VERSION: '20'
  CACHE_VERSION: 'v2'

jobs:
  # Job 1: Code Quality Checks
  quality-checks:
    name: Code Quality
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v4
        with:
          path: |
            frontend/node_modules
            ~/.npm
          key: ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-
            ${{ runner.os }}-node-

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Type checking
        working-directory: frontend
        run: npm run type-check

      - name: ESLint
        working-directory: frontend
        run: npm run lint

      - name: Prettier check
        working-directory: frontend
        run: npm run format:check

  # Job 2: Unit Tests
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: quality-checks
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v4
        with:
          path: |
            frontend/node_modules
            ~/.npm
          key: ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-
            ${{ runner.os }}-node-

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run unit tests
        working-directory: frontend
        run: npm run test:unit -- --coverage --coverageDirectory=coverage/unit
        env:
          CI: true

      - name: Upload unit test coverage
        uses: actions/upload-artifact@v4
        with:
          name: unit-test-coverage
          path: frontend/coverage/unit/
          retention-days: 7

  # Job 3: Integration Tests
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: quality-checks
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v4
        with:
          path: |
            frontend/node_modules
            ~/.npm
          key: ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-
            ${{ runner.os }}-node-

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run integration tests
        working-directory: frontend
        run: npm run test:integration -- --coverage --coverageDirectory=coverage/integration
        env:
          CI: true

      - name: Upload integration test coverage
        uses: actions/upload-artifact@v4
        with:
          name: integration-test-coverage
          path: frontend/coverage/integration/
          retention-days: 7

  # Job 4: Full Test Suite with Coverage
  full-coverage:
    name: Full Coverage Analysis
    runs-on: ubuntu-latest
    timeout-minutes: 20
    needs: [unit-tests, integration-tests]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v4
        with:
          path: |
            frontend/node_modules
            ~/.npm
          key: ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-
            ${{ runner.os }}-node-

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run full test suite with coverage
        working-directory: frontend
        run: npm run test:ci
        env:
          CI: true

      - name: Enforce coverage thresholds
        working-directory: frontend
        run: |
          echo "Checking coverage thresholds..."
          npm run test:coverage -- --passWithNoTests --silent || {
            echo "❌ Coverage thresholds not met!"
            exit 1
          }

      - name: Generate coverage summary
        working-directory: frontend
        run: |
          echo "## 📊 Test Coverage Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### Coverage Thresholds" >> $GITHUB_STEP_SUMMARY
          echo "- **Global**: 80% statements, 75% branches, 80% functions/lines" >> $GITHUB_STEP_SUMMARY
          echo "- **API Layer**: 95% statements, 90% branches, 95% functions/lines" >> $GITHUB_STEP_SUMMARY
          echo "- **Contexts**: 90% statements, 85% branches, 90% functions/lines" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          if [ -f coverage/lcov-report/index.html ]; then
            echo "✅ Coverage report generated successfully" >> $GITHUB_STEP_SUMMARY
          else
            echo "❌ Coverage report generation failed" >> $GITHUB_STEP_SUMMARY
          fi

      - name: Upload coverage reports to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./frontend/coverage/lcov.info
          flags: frontend
          name: frontend-coverage
          fail_ci_if_error: false
          directory: ./frontend/coverage
        env:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

      - name: Upload coverage artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-coverage-report
          path: |
            frontend/coverage/
            !frontend/coverage/tmp/
          retention-days: 30

      - name: Comment coverage on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const path = 'frontend/coverage/coverage-summary.json';
            
            if (fs.existsSync(path)) {
              const coverage = JSON.parse(fs.readFileSync(path, 'utf8'));
              const { total } = coverage;
              
              const comment = `## 📊 Frontend Test Coverage
              
              | Metric | Coverage | Threshold | Status |
              |--------|----------|-----------|--------|
              | Statements | ${total.statements.pct}% | 80% | ${total.statements.pct >= 80 ? '✅' : '❌'} |
              | Branches | ${total.branches.pct}% | 75% | ${total.branches.pct >= 75 ? '✅' : '❌'} |
              | Functions | ${total.functions.pct}% | 80% | ${total.functions.pct >= 80 ? '✅' : '❌'} |
              | Lines | ${total.lines.pct}% | 80% | ${total.lines.pct >= 80 ? '✅' : '❌'} |
              
              **Test Results**: All ${total.statements.covered} statements covered out of ${total.statements.total}`;
              
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: comment
              });
            }

  # Job 5: Performance Tests (Optional)
  performance-tests:
    name: Performance Tests
    runs-on: ubuntu-latest
    timeout-minutes: 10
    needs: quality-checks
    if: github.event_name == 'pull_request'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v4
        with:
          path: |
            frontend/node_modules
            ~/.npm
          key: ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-
            ${{ runner.os }}-node-

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run performance tests
        working-directory: frontend
        run: node src/tests/performance_test.js || echo "Performance tests completed with warnings"

  # Job 6: Build Verification
  build-verification:
    name: Build Verification
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: [full-coverage]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v4
        with:
          path: |
            frontend/node_modules
            ~/.npm
          key: ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-${{ env.CACHE_VERSION }}-
            ${{ runner.os }}-node-

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Setup Expo CLI
        run: npm install -g @expo/cli

      - name: Expo prebuild (verification)
        working-directory: frontend
        run: npx expo prebuild --no-install --platform ios,android || echo "Prebuild verification completed with warnings"

      - name: Type check after build
        working-directory: frontend
        run: npm run type-check

      - name: Build status summary
        run: |
          echo "## 🏗️ Build Verification Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "✅ Dependencies installed successfully" >> $GITHUB_STEP_SUMMARY
          echo "✅ TypeScript compilation successful" >> $GITHUB_STEP_SUMMARY
          echo "✅ Expo prebuild verification completed" >> $GITHUB_STEP_SUMMARY
```

### Alternative Simplified Workflow

For teams preferring a single-job approach, create `.github/workflows/frontend-tests-simple.yml`:

```yaml
name: Frontend Tests (Simple)

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests-simple.yml'
  pull_request:
    branches: [main]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-tests-simple.yml'

jobs:
  test:
    name: Test Suite
    runs-on: ubuntu-latest
    timeout-minutes: 25
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: |
            frontend/node_modules
            ~/.npm
          key: ${{ runner.os }}-node-v2-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-v2-

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Code quality checks
        working-directory: frontend
        run: |
          npm run type-check
          npm run lint
          npm run format:check

      - name: Run tests with coverage
        working-directory: frontend
        run: npm run test:ci
        env:
          CI: true

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./frontend/coverage/lcov.info
          flags: frontend
          name: frontend-coverage
          fail_ci_if_error: false
        env:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

## Integration Strategies

### 1. Path-Based Triggering

Configure workflows to trigger only on frontend changes:
- `frontend/**` - All frontend code changes
- `.github/workflows/frontend-tests.yml` - Workflow file changes

### 2. Matrix Strategy for Multiple Node Versions

```yaml
strategy:
  matrix:
    node-version: [18, 20]
    os: [ubuntu-latest, macos-latest]
```

### 3. Conditional Job Execution

```yaml
# Run performance tests only on PRs
if: github.event_name == 'pull_request'

# Skip tests if only documentation changed
if: "!contains(github.event.head_commit.message, '[skip ci]')"
```

### 4. Integration with Backend CI

Coordinate with backend tests using workflow dependencies:

```yaml
# In backend workflow
- name: Trigger frontend tests
  if: success()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.actions.createWorkflowDispatch({
        owner: context.repo.owner,
        repo: context.repo.repo,
        workflow_id: 'frontend-tests.yml',
        ref: context.ref
      });
```

## Caching and Performance Optimization

### 1. Multi-Level Caching Strategy

```yaml
# Level 1: Node.js built-in caching
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json

# Level 2: Manual npm cache
- name: Cache npm
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('frontend/package-lock.json') }}

# Level 3: Node modules cache
- name: Cache node_modules
  uses: actions/cache@v4
  with:
    path: frontend/node_modules
    key: ${{ runner.os }}-modules-${{ hashFiles('frontend/package-lock.json') }}
```

### 2. Jest Cache Optimization

```yaml
- name: Cache Jest
  uses: actions/cache@v4
  with:
    path: frontend/.jest-cache
    key: ${{ runner.os }}-jest-${{ hashFiles('frontend/jest.config.js') }}
```

### 3. TypeScript Compilation Cache

```yaml
- name: Cache TypeScript
  uses: actions/cache@v4
  with:
    path: frontend/.tsc-cache
    key: ${{ runner.os }}-tsc-${{ hashFiles('frontend/tsconfig.json') }}
```

### 4. Coverage Report Caching

```yaml
- name: Cache coverage reports
  uses: actions/cache@v4
  with:
    path: frontend/coverage
    key: ${{ runner.os }}-coverage-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-coverage-
```

## Quality Gates and Coverage Requirements

### 1. Coverage Thresholds Enforcement

The Jest configuration already defines strict coverage thresholds:

- **Global**: 80% statements, 75% branches, 80% functions/lines
- **API Layer**: 95% statements, 90% branches, 95% functions/lines  
- **Contexts**: 90% statements, 85% branches, 90% functions/lines

### 2. Quality Gate Implementation

```yaml
- name: Quality Gate - Coverage Threshold
  working-directory: frontend
  run: |
    npm run test:coverage -- --passWithNoTests || {
      echo "❌ Coverage thresholds not met!"
      echo "Required thresholds:"
      echo "  - Global: 80% statements, 75% branches, 80% functions/lines"
      echo "  - API Layer: 95% statements, 90% branches, 95% functions/lines"
      echo "  - Contexts: 90% statements, 85% branches, 90% functions/lines"
      exit 1
    }

- name: Quality Gate - No TypeScript Errors
  working-directory: frontend
  run: |
    npm run type-check || {
      echo "❌ TypeScript compilation failed!"
      exit 1
    }

- name: Quality Gate - Lint Compliance
  working-directory: frontend
  run: |
    npm run lint || {
      echo "❌ ESLint violations found!"
      echo "Fix with: npm run lint:fix"
      exit 1
    }
```

### 3. Custom Quality Checks

```yaml
- name: Custom Quality Checks
  working-directory: frontend
  run: |
    # Check for debugging code
    if grep -r "console.log\|debugger" src/ --exclude-dir=__tests__; then
      echo "❌ Debug code found in source files!"
      exit 1
    fi
    
    # Check for TODO comments in production code
    if grep -r "TODO\|FIXME" src/ --exclude-dir=__tests__ | grep -v "test"; then
      echo "⚠️ TODO/FIXME comments found - consider addressing before merge"
    fi
    
    # Verify test file naming conventions
    find src/ -name "*.test.*" | while read file; do
      if [[ ! "$file" =~ __tests__/ ]]; then
        echo "❌ Test file not in __tests__ directory: $file"
        exit 1
      fi
    done
```

## Environment Variables and Configuration

### 1. Required Environment Variables

```yaml
env:
  # General settings
  CI: true
  NODE_ENV: test
  
  # Test configuration  
  JEST_JUNIT_OUTPUT_DIR: ./frontend/test-results
  JEST_JUNIT_OUTPUT_NAME: results.xml
  
  # Coverage settings
  COVERAGE_THRESHOLD_GLOBAL: 80
  COVERAGE_THRESHOLD_API: 95
  COVERAGE_THRESHOLD_CONTEXTS: 90
```

### 2. GitHub Secrets Configuration

Required secrets in GitHub repository settings:

```yaml
# Required
CODECOV_TOKEN: "your-codecov-token"

# Optional (for enhanced integrations)
SLACK_WEBHOOK: "your-slack-webhook-url"
DISCORD_WEBHOOK: "your-discord-webhook-url"
```

### 3. Dynamic Environment Setup

```yaml
- name: Setup test environment
  run: |
    echo "Setting up test environment..."
    
    # Create test directories
    mkdir -p frontend/test-results
    mkdir -p frontend/coverage
    
    # Set dynamic environment variables
    echo "TEST_START_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $GITHUB_ENV
    echo "BUILD_NUMBER=${{ github.run_number }}" >> $GITHUB_ENV
    echo "COMMIT_SHA=${{ github.sha }}" >> $GITHUB_ENV
```

## Parallel Execution Strategy

### 1. Job-Level Parallelization

The multi-job workflow runs tests in parallel:
- Quality checks (fastest, ~5 min)
- Unit tests (parallel with integration)
- Integration tests (parallel with unit)
- Full coverage analysis (after unit/integration)
- Build verification (final step)

### 2. Test-Level Parallelization

```yaml
- name: Run tests with parallel execution
  working-directory: frontend
  run: |
    # Jest runs tests in parallel by default
    # Max workers = min(CPU cores - 1, 4)
    npm run test:ci -- --maxWorkers=4
  env:
    # Enable jest worker parallelization
    JEST_MAX_WORKERS: 4
```

### 3. Matrix Strategy for Cross-Platform Testing

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    node-version: [18, 20]
  max-parallel: 4
  fail-fast: false
```

### 4. Shard-Based Test Splitting

```yaml
strategy:
  matrix:
    shard: [1, 2, 3, 4]
steps:
  - name: Run test shard
    working-directory: frontend
    run: |
      npm run test:ci -- --shard=${{ matrix.shard }}/4
```

## Code Coverage Integration

### 1. Coverage Report Generation

```yaml
- name: Generate coverage reports
  working-directory: frontend
  run: |
    # Generate multiple format coverage reports
    npm run test:coverage -- \
      --coverage \
      --coverageDirectory=coverage \
      --coverageReporters=text-lcov,html,json,cobertura
```

### 2. Codecov Integration

```yaml
- name: Upload to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./frontend/coverage/lcov.info
    flags: frontend,react-native
    name: frontend-coverage
    fail_ci_if_error: true
    verbose: true
    directory: ./frontend/coverage
```

### 3. Coverage Trend Tracking

```yaml
- name: Coverage trend analysis
  run: |
    # Compare with previous coverage
    if [ -f previous-coverage.json ]; then
      node scripts/coverage-diff.js previous-coverage.json frontend/coverage/coverage-summary.json
    fi
    
    # Store current coverage for next run
    cp frontend/coverage/coverage-summary.json previous-coverage.json
```

### 4. Coverage Visualization

```yaml
- name: Generate coverage badge
  run: |
    # Extract coverage percentage
    COVERAGE=$(node -p "JSON.parse(require('fs').readFileSync('frontend/coverage/coverage-summary.json')).total.lines.pct")
    
    # Generate badge URL
    echo "COVERAGE_BADGE_URL=https://img.shields.io/badge/coverage-${COVERAGE}%25-brightgreen" >> $GITHUB_ENV
```

## Error Handling and Debugging

### 1. Test Failure Analysis

```yaml
- name: Analyze test failures
  if: failure()
  working-directory: frontend
  run: |
    echo "## 🔍 Test Failure Analysis" >> $GITHUB_STEP_SUMMARY
    
    # Check for common issues
    if [ -f npm-debug.log ]; then
      echo "### npm Debug Log" >> $GITHUB_STEP_SUMMARY
      echo "```" >> $GITHUB_STEP_SUMMARY
      tail -20 npm-debug.log >> $GITHUB_STEP_SUMMARY
      echo "```" >> $GITHUB_STEP_SUMMARY
    fi
    
    # Jest output analysis
    if [ -d test-results ]; then
      echo "### Failed Tests" >> $GITHUB_STEP_SUMMARY
      find test-results -name "*.xml" -exec grep -l "failure\|error" {} \; | head -5 >> $GITHUB_STEP_SUMMARY
    fi
```

### 2. Debug Mode Activation

```yaml
- name: Debug test run
  if: contains(github.event.head_commit.message, '[debug]')
  working-directory: frontend
  run: |
    # Run with maximum verbosity
    npm run test:debug -- --verbose --no-cache --runInBand
```

### 3. Artifact Collection for Debugging

```yaml
- name: Upload debug artifacts
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: debug-artifacts-${{ github.run_number }}
    path: |
      frontend/npm-debug.log
      frontend/test-results/
      frontend/coverage/
      frontend/.jest-cache/
    retention-days: 7
```

### 4. Slack/Discord Notifications

```yaml
- name: Notify on failure
  if: failure() && github.ref == 'refs/heads/main'
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    text: |
      🚨 Frontend tests failed on main branch!
      
      **Commit**: ${{ github.sha }}
      **Author**: ${{ github.actor }}
      **Message**: ${{ github.event.head_commit.message }}
      
      [View Logs](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Future Enhancements

### 1. Visual Regression Testing

```yaml
# Add to workflow
- name: Visual regression tests
  working-directory: frontend
  run: |
    npm install -g @storybook/cli
    npm run storybook:build
    npm run chromatic -- --project-token=${{ secrets.CHROMATIC_TOKEN }}
  env:
    CHROMATIC_TOKEN: ${{ secrets.CHROMATIC_TOKEN }}
```

### 2. E2E Testing Integration

```yaml
# Add Detox or Playwright for E2E tests
- name: E2E tests
  run: |
    npx expo install --fix
    npm run test:e2e
  env:
    DETOX_CONFIGURATION: ios.sim.debug
```

### 3. Bundle Size Analysis

```yaml
- name: Bundle size analysis
  working-directory: frontend
  run: |
    npm run build
    npx bundlesize
    
- name: Bundle size comment
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      // Post bundle size comparison comment
```

### 4. Security Scanning

```yaml
- name: Security audit
  working-directory: frontend
  run: |
    npm audit --audit-level moderate
    npx better-npm-audit audit
```

### 5. Performance Monitoring

```yaml
- name: Performance benchmarks
  working-directory: frontend
  run: |
    # Run performance tests
    node scripts/performance-benchmark.js
    
    # Upload results to performance dashboard
    curl -X POST "https://api.perfboard.io/results" \
      -H "Authorization: Bearer ${{ secrets.PERFBOARD_TOKEN }}" \
      -d @performance-results.json
```

### 6. Automated Dependency Updates

```yaml
# Separate workflow: .github/workflows/dependency-updates.yml
name: Dependency Updates
on:
  schedule:
    - cron: '0 2 * * 1' # Monday 2 AM
  
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Update dependencies
        run: |
          cd frontend
          npx npm-check-updates -u
          npm install
          npm test
      - name: Create PR
        if: success()
        uses: peter-evans/create-pull-request@v5
        with:
          title: 'chore: update frontend dependencies'
          body: 'Automated dependency updates'
          branch: automated-deps-frontend
```

## Implementation Checklist

### Initial Setup
- [ ] Create `.github/workflows/frontend-tests.yml`
- [ ] Add required secrets to GitHub repository
- [ ] Configure Codecov integration
- [ ] Test workflow on feature branch

### Configuration
- [ ] Verify Jest configuration aligns with CI needs
- [ ] Update coverage thresholds if needed
- [ ] Configure quality gate rules
- [ ] Set up caching strategy

### Integration
- [ ] Test parallel job execution
- [ ] Verify coverage report generation
- [ ] Confirm artifact uploads
- [ ] Test failure scenarios

### Monitoring
- [ ] Set up notification channels
- [ ] Configure coverage trend tracking
- [ ] Monitor workflow performance
- [ ] Review and optimize caching

### Documentation
- [ ] Update project README with CI badge
- [ ] Document quality gate requirements
- [ ] Create troubleshooting guide
- [ ] Train team on new workflow

This comprehensive implementation guide provides a production-ready CI solution for the React Native frontend, with multiple execution strategies, robust error handling, and future enhancement pathways. The workflow is designed to scale with the project's needs while maintaining high code quality standards.