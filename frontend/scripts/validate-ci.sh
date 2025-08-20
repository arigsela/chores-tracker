#!/bin/bash

# Frontend CI Validation Script
# This script runs the same checks that will run in CI to validate locally

set -e  # Exit on any error

echo "🚀 Frontend CI Validation Script"
echo "================================"

cd "$(dirname "$0")/.."  # Change to frontend directory

echo ""
echo "📦 Installing dependencies..."
npm ci

echo ""
echo "🔍 Running TypeScript compilation check..."
npm run type-check
echo "✅ TypeScript compilation passed"

echo ""
echo "🔧 Running ESLint check..."
npm run lint
echo "✅ ESLint check passed"

echo ""
echo "💅 Running Prettier format check..."
npm run format:check
echo "✅ Prettier format check passed"

echo ""
echo "🐛 Checking for debug code..."
if grep -r "console\.log\|debugger\|\.only\|\.skip" src/ --include="*.ts" --include="*.tsx" 2>/dev/null; then
    echo "⚠️  Warning: Found debug code in source files"
    echo "Please remove console.log, debugger, .only, or .skip before committing"
else
    echo "✅ No debug code found"
fi

echo ""
echo "🧪 Running unit tests..."
npm run test:unit -- --passWithNoTests
echo "✅ Unit tests passed"

echo ""
echo "🔗 Running integration tests..."
npm run test:integration -- --passWithNoTests
echo "✅ Integration tests passed"

echo ""
echo "📊 Running full test suite with coverage..."
npm run test:ci
echo "✅ Full test suite with coverage passed"

echo ""
echo "🎉 All CI checks passed! Your code is ready for CI."
echo ""
echo "Coverage report generated in: coverage/index.html"
echo "Run 'open coverage/index.html' to view detailed coverage"