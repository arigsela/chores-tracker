# Frontend ESLint Fix Strategy

## 🚨 Current Status: 306 ESLint Issues Detected

The CI is now configured to run with advisory ESLint checking, but there are **306 issues** (239 errors, 67 warnings) that should be addressed for code quality.

## 📊 Issue Breakdown

### Critical Issues (239 errors)
1. **TypeScript/Any Types**: `@typescript-eslint/no-explicit-any` (85+ occurrences)
2. **Unused Variables**: `@typescript-eslint/no-unused-vars` (40+ occurrences)
3. **Import/Require Issues**: `@typescript-eslint/no-var-requires` (60+ occurrences)
4. **React Hooks Violations**: `react-hooks/rules-of-hooks` (8 occurrences)
5. **React JSX Issues**: `react/no-unescaped-entities` (15+ occurrences)
6. **Environment Issues**: `no-undef` (25+ occurrences in test files)

### Warning Issues (67 warnings)
1. **Console Statements**: `no-console` (40+ occurrences)
2. **React Hook Dependencies**: `react-hooks/exhaustive-deps` (10+ occurrences)
3. **Inline Styles**: `react-native/no-inline-styles` (5+ occurrences)

## 🎯 Prioritized Fix Strategy

### Phase 1: Quick Wins (Can be automated) - Priority 1

#### 1.1 Auto-fixable Issues
```bash
# Run ESLint with auto-fix
npm run lint:fix
```

**Expected fixes**:
- Some unused variable removals
- Some formatting issues
- Basic style corrections

#### 1.2 Console Statement Cleanup
```bash
# Find all console statements
grep -r "console\." src/ --include="*.ts" --include="*.tsx"

# Strategy: 
# - Remove debug console.log statements
# - Keep intentional logging (mark with eslint-disable-next-line)
# - Add proper logging utility if needed
```

### Phase 2: Structural Fixes - Priority 2

#### 2.1 Fix Import Statements
Replace `require()` with proper ES6 imports:
```typescript
// Before
const mockModule = require('../../api/mocks');

// After  
import { mockModule } from '../../api/mocks';
```

#### 2.2 Remove Unused Variables
Go through each file and:
- Remove truly unused variables
- Prefix with `_` for intentionally unused parameters
- Add proper typing instead of removing

#### 2.3 Fix React JSX Issues
```typescript
// Before
<Text>Don't use unescaped quotes</Text>

// After
<Text>Don&apos;t use unescaped quotes</Text>
// or
<Text>{"Don't use unescaped quotes"}</Text>
```

### Phase 3: Type Safety Improvements - Priority 3

#### 3.1 Replace `any` Types
Systematic replacement of `any` with proper types:
```typescript
// Before
const mockApi: any = jest.fn();

// After
const mockApi: jest.MockedFunction<typeof realApi> = jest.fn();
```

#### 3.2 Fix React Hooks Violations
**Critical**: Fix hooks called conditionally
```typescript
// Before (WRONG)
if (isParent) {
  const [chores, setChores] = useState([]);
}

// After (CORRECT)
const [chores, setChores] = useState([]);
// Handle conditional logic in useEffect or render
```

### Phase 4: Environment and Test Fixes - Priority 4

#### 4.1 Fix Test Environment Issues
Update test files with proper globals:
```typescript
// Add to jest setup or individual files
/* eslint-env jest, node */
```

#### 4.2 Performance Test File
The `performance_test.js` has many `no-undef` errors. Options:
- Add proper ESLint environment config
- Convert to proper test format
- Move to scripts directory if not a test

## 🛠️ Implementation Plan

### Option A: Gradual Fix (Recommended)
1. **Phase 1 this week**: Auto-fixable issues and console cleanup
2. **Phase 2 next week**: Import and unused variable cleanup  
3. **Phase 3 ongoing**: Type improvements as time permits
4. **Phase 4 later**: Test environment and remaining issues

### Option B: File-by-file Approach
1. **Pick 1-2 files per day** for complete ESLint compliance
2. **Start with most critical files** (API layer, core components)
3. **Graduate files** from advisory to strict checking

### Option C: Category-focused Approach
1. **Week 1**: All console statement cleanup
2. **Week 2**: All unused variable removal
3. **Week 3**: All import statement fixes
4. **Week 4**: Type improvements

## 🔧 Immediate Actions

### 1. Enable Selective Strict Checking
Create ESLint configuration to be strict on new files:
```javascript
// .eslintrc.js - Add overrides
overrides: [
  {
    // Strict checking for new files
    files: ['src/components/New*.tsx', 'src/screens/New*.tsx'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': 'error',
    }
  }
]
```

### 2. Add Pre-commit Hook (Optional)
```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged"
    }
  },
  "lint-staged": {
    "src/**/*.{ts,tsx}": ["eslint --fix", "prettier --write"]
  }
}
```

### 3. Create ESLint Fix Script
```bash
#!/bin/bash
# scripts/fix-eslint-category.sh
echo "Fixing ESLint issues by category..."

case "$1" in
  "console")
    echo "Removing console statements..."
    # Custom script to handle console.log removal
    ;;
  "unused")
    echo "Removing unused variables..."
    eslint src/ --fix --rule '@typescript-eslint/no-unused-vars: error'
    ;;
  "imports")
    echo "Fixing import statements..."
    # Custom conversion script
    ;;
esac
```

## 📋 Quick Reference Commands

```bash
# Check specific rule violations
npx eslint src/ --format=table --rule '@typescript-eslint/no-explicit-any: error'

# Fix specific file
npx eslint src/path/to/file.tsx --fix

# Count issues by rule
npm run lint -- --format=json | jq '.[] | .messages[].ruleId' | sort | uniq -c

# Check only errors (ignore warnings)
npm run lint -- --quiet
```

## 🎯 Success Criteria

### Phase 1 Complete When:
- [ ] ESLint errors < 150 (from 239)
- [ ] All console.log statements removed or justified
- [ ] At least 5 files are fully ESLint compliant

### Phase 2 Complete When:
- [ ] ESLint errors < 75
- [ ] All require() statements converted to imports
- [ ] No unused variables in core components

### Phase 3 Complete When:
- [ ] ESLint errors < 20
- [ ] No critical React hooks violations
- [ ] Proper types instead of `any` in API layer

### Full Compliance When:
- [ ] Zero ESLint errors
- [ ] Only justified warnings remain
- [ ] CI can run strict ESLint checking

## 🚀 Current Recommendation

**Start with Option A (Gradual Fix)** combined with **selective strict checking**:

1. **Keep CI advisory** for now (provides immediate feedback)
2. **Enable strict checking** for new files only
3. **Fix by category** starting with auto-fixable issues
4. **Track progress** through reduced error count

This approach maintains the green CI while systematically improving code quality and establishing standards for new development.

The CI is now configured to be helpful rather than blocking, giving you the benefits of automated checking while providing a clear improvement path.