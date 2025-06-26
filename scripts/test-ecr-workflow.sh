#!/bin/bash

# Test script for ECR deployment workflow
# This script performs local validation before pushing to GitHub

set -e

echo "🔍 Testing ECR Deployment Workflow..."
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required files exist
echo -e "\n${YELLOW}1. Checking required files...${NC}"
if [ -f ".github/workflows/deploy-to-ecr.yml" ]; then
    echo -e "${GREEN}✓ deploy-to-ecr.yml exists${NC}"
else
    echo -e "${RED}✗ deploy-to-ecr.yml not found${NC}"
    exit 1
fi

if [ -f "Dockerfile" ]; then
    echo -e "${GREEN}✓ Dockerfile exists${NC}"
else
    echo -e "${RED}✗ Dockerfile not found${NC}"
    exit 1
fi

# Validate YAML syntax
echo -e "\n${YELLOW}2. Validating YAML syntax...${NC}"
if command -v python3 &> /dev/null; then
    python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy-to-ecr.yml'))" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ YAML syntax is valid${NC}"
    else
        echo -e "${RED}✗ YAML syntax error${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Python not found, skipping YAML validation${NC}"
fi

# Check for required secrets in workflow
echo -e "\n${YELLOW}3. Checking for required secrets usage...${NC}"
REQUIRED_SECRETS=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "AWS_REGION" "ECR_REPOSITORY")
for secret in "${REQUIRED_SECRETS[@]}"; do
    if grep -q "\${{ secrets.$secret }}" .github/workflows/deploy-to-ecr.yml; then
        echo -e "${GREEN}✓ $secret is referenced${NC}"
    else
        echo -e "${RED}✗ $secret is not referenced${NC}"
        exit 1
    fi
done

# Test Docker build locally
echo -e "\n${YELLOW}4. Testing Docker build locally...${NC}"
if command -v docker &> /dev/null; then
    echo "Building Docker image..."
    if docker build -t chores-tracker:test . > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker build successful${NC}"
        
        # Get image size
        IMAGE_SIZE=$(docker images chores-tracker:test --format "{{.Size}}")
        echo -e "${GREEN}  Image size: $IMAGE_SIZE${NC}"
        
        # Clean up test image
        docker rmi chores-tracker:test > /dev/null 2>&1
    else
        echo -e "${RED}✗ Docker build failed${NC}"
        echo "Run 'docker build -t chores-tracker:test .' to see detailed error"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Docker not found, skipping build test${NC}"
fi

# Check workflow triggers
echo -e "\n${YELLOW}5. Checking workflow triggers...${NC}"
if grep -q "branches:" .github/workflows/deploy-to-ecr.yml && grep -q "- main" .github/workflows/deploy-to-ecr.yml; then
    echo -e "${GREEN}✓ Triggers on main branch${NC}"
else
    echo -e "${RED}✗ Main branch trigger not found${NC}"
fi

if grep -q "workflow_dispatch:" .github/workflows/deploy-to-ecr.yml; then
    echo -e "${GREEN}✓ Manual trigger enabled${NC}"
else
    echo -e "${YELLOW}⚠ Manual trigger not enabled${NC}"
fi

# Summary
echo -e "\n${YELLOW}======================================"
echo -e "Summary:${NC}"
echo -e "${GREEN}✓ Workflow file is ready for deployment${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Ensure GitHub secrets are configured:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION"
echo "   - ECR_REPOSITORY"
echo "2. Commit and push to a feature branch"
echo "3. Create a PR to test the workflow"
echo "4. Merge to main to trigger deployment"
echo -e "\n${GREEN}Good luck! 🚀${NC}"