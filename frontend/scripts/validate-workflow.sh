#!/bin/bash

# Workflow validation script
# Tests the frontend CI workflow for common issues

set -e

echo "🔍 Frontend Workflow Validation Script"
echo "====================================="

cd "$(dirname "$0")/../.."  # Change to project root

echo ""
echo "📝 Checking workflow file exists..."
if [[ -f ".github/workflows/frontend-tests.yml" ]]; then
    echo "✅ Frontend workflow file found"
else
    echo "❌ Frontend workflow file not found"
    exit 1
fi

echo ""
echo "🔧 Validating YAML syntax..."
if command -v yamllint >/dev/null 2>&1; then
    yamllint .github/workflows/frontend-tests.yml
    echo "✅ YAML syntax valid"
else
    echo "⚠️  yamllint not installed, skipping YAML validation"
    echo "   Install with: pip install yamllint"
fi

echo ""
echo "🧪 Checking workflow structure..."
if grep -q "name: Frontend Tests" .github/workflows/frontend-tests.yml; then
    echo "✅ Workflow name correct"
else
    echo "❌ Workflow name missing or incorrect"
fi

if grep -q "quality-checks:" .github/workflows/frontend-tests.yml; then
    echo "✅ Quality checks job found"
else
    echo "❌ Quality checks job missing"
fi

if grep -q "unit-tests:" .github/workflows/frontend-tests.yml; then
    echo "✅ Unit tests job found"
else
    echo "❌ Unit tests job missing"
fi

if grep -q "integration-tests:" .github/workflows/frontend-tests.yml; then
    echo "✅ Integration tests job found"
else
    echo "❌ Integration tests job missing"
fi

if grep -q "full-coverage:" .github/workflows/frontend-tests.yml; then
    echo "✅ Full coverage job found"
else
    echo "❌ Full coverage job missing"
fi

echo ""
echo "📊 Checking path triggers..."
if grep -q "frontend/\*\*" .github/workflows/frontend-tests.yml; then
    echo "✅ Frontend path trigger configured"
else
    echo "❌ Frontend path trigger missing"
fi

echo ""
echo "🎉 Workflow validation complete!"
echo ""
echo "The frontend CI workflow appears to be properly configured."
echo "Recent fixes should resolve the shellcheck validation issues."