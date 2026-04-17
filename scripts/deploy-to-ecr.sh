#!/bin/bash

# Deploy Chores Tracker images to AWS ECR
# Usage:
#   ./scripts/deploy-to-ecr.sh backend 1.0.0
#   ./scripts/deploy-to-ecr.sh frontend 1.0.0
#   ./scripts/deploy-to-ecr.sh all 1.0.0

set -euo pipefail

# Configuration
AWS_REGION="${AWS_REGION:-us-east-2}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-852893458518}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
BACKEND_REPO="${BACKEND_REPO:-chores-tracker-backend}"
FRONTEND_REPO="${FRONTEND_REPO:-chores-tracker-frontend}"
FRONTEND_API_URL="${FRONTEND_API_URL:-https://chores.arigsela.com}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Usage: $0 <component> <version>"
    echo ""
    echo "Components:"
    echo "  backend   - Build and push backend image"
    echo "  frontend  - Build and push frontend image (runs npm ci + npm run build first)"
    echo "  all       - Build and push both images"
    echo ""
    echo "Examples:"
    echo "  $0 backend 1.0.0"
    echo "  $0 frontend 1.0.0"
    echo "  $0 all 1.0.0"
    echo ""
    echo "Environment variables:"
    echo "  AWS_REGION         - AWS region (default: us-east-2)"
    echo "  AWS_ACCOUNT_ID     - AWS account ID (default: 852893458518)"
    echo "  BACKEND_REPO       - Backend ECR repo name (default: chores-tracker-backend)"
    echo "  FRONTEND_REPO      - Frontend ECR repo name (default: chores-tracker-frontend)"
    echo "  FRONTEND_API_URL   - API base URL baked into frontend (default: https://chores.arigsela.com)"
    exit 1
}

# Validate inputs
COMPONENT="${1:-}"
VERSION="${2:-}"

if [[ -z "$COMPONENT" ]] || [[ -z "$VERSION" ]]; then
    usage
fi

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Version must be in format X.Y.Z (e.g., 1.0.0)${NC}"
    exit 1
fi

if [[ "$COMPONENT" != "backend" ]] && [[ "$COMPONENT" != "frontend" ]] && [[ "$COMPONENT" != "all" ]]; then
    echo -e "${RED}Error: Component must be 'backend', 'frontend', or 'all'${NC}"
    usage
fi

# Extract version components for multi-tag strategy
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

# Get the repo root
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

ecr_login() {
    echo -e "${BLUE}Logging into ECR...${NC}"
    aws ecr get-login-password --region "${AWS_REGION}" | \
        docker login --username AWS --password-stdin "${ECR_REGISTRY}"
    echo -e "${GREEN}ECR login successful${NC}"
}

retry_push() {
    local tag=$1
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo -e "  Pushing ${BLUE}${tag}${NC} (attempt ${attempt}/${max_attempts})..."
        if docker push "$tag" 2>/dev/null; then
            echo -e "  ${GREEN}Pushed ${tag}${NC}"
            return 0
        fi
        if [ $attempt -lt $max_attempts ]; then
            echo -e "  ${YELLOW}Retrying in 10 seconds...${NC}"
            sleep 10
        fi
        attempt=$((attempt + 1))
    done

    echo -e "  ${RED}Failed to push ${tag} after ${max_attempts} attempts${NC}"
    return 1
}

build_and_push() {
    local component=$1
    local repo=$2
    local context_dir=$3
    local dockerfile=$4

    echo ""
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}Building ${component} v${VERSION}${NC}"
    echo -e "${BLUE}======================================${NC}"

    local full_image="${ECR_REGISTRY}/${repo}"

    # Build with multi-tag strategy
    local tags=(
        "${full_image}:${VERSION}"
        "${full_image}:${MAJOR}.${MINOR}"
        "${full_image}:${MAJOR}"
        "${full_image}:latest"
    )

    local tag_args=""
    for tag in "${tags[@]}"; do
        tag_args="${tag_args} -t ${tag}"
    done

    echo -e "${YELLOW}Building Docker image...${NC}"

    local build_args="--build-arg BUILD_VERSION=v${VERSION} --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    # Frontend pre-build steps (npm build + dockerignore swap)
    if [[ "$component" == "frontend" ]]; then
        build_args="${build_args} --build-arg VITE_API_URL=${FRONTEND_API_URL}"
    fi

    # shellcheck disable=SC2086
    eval docker build \
        --platform linux/amd64 \
        ${tag_args} \
        ${build_args} \
        -f "${dockerfile}" \
        "${context_dir}"

    echo -e "${GREEN}Build successful${NC}"

    # Get image size
    local image_size
    image_size=$(docker images "${full_image}:${VERSION}" --format "{{.Size}}" | head -1)
    echo -e "  Image size: ${image_size}"

    # Push all tags
    echo -e "${YELLOW}Pushing images to ECR...${NC}"
    for tag in "${tags[@]}"; do
        retry_push "$tag"
    done

    echo -e "${GREEN}${component} v${VERSION} deployed successfully${NC}"
}

deploy_backend() {
    build_and_push \
        "backend" \
        "${BACKEND_REPO}" \
        "${REPO_ROOT}" \
        "${REPO_ROOT}/Dockerfile"
}

# Frontend needs JS build + dockerignore swap before docker build.
# Restore dockerignore on exit (success or failure) so working tree stays clean.
frontend_prepare() {
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    (cd "${REPO_ROOT}/frontend" && npm ci)

    echo -e "${YELLOW}Building frontend (npm run build)...${NC}"
    (cd "${REPO_ROOT}/frontend" && npm run build)

    if [[ ! -d "${REPO_ROOT}/frontend/dist" ]]; then
        echo -e "${RED}Error: frontend/dist was not produced by npm run build${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Swapping .dockerignore to include dist/...${NC}"
    if [[ -f "${REPO_ROOT}/frontend/.dockerignore" ]]; then
        cp "${REPO_ROOT}/frontend/.dockerignore" "${REPO_ROOT}/frontend/.dockerignore.backup"
    fi
    cp "${REPO_ROOT}/frontend/.dockerignore.working" "${REPO_ROOT}/frontend/.dockerignore"
}

frontend_cleanup() {
    if [[ -f "${REPO_ROOT}/frontend/.dockerignore.backup" ]]; then
        echo -e "${YELLOW}Restoring original .dockerignore...${NC}"
        mv "${REPO_ROOT}/frontend/.dockerignore.backup" "${REPO_ROOT}/frontend/.dockerignore"
    fi
}

deploy_frontend() {
    trap frontend_cleanup EXIT
    frontend_prepare

    build_and_push \
        "frontend" \
        "${FRONTEND_REPO}" \
        "${REPO_ROOT}/frontend" \
        "${REPO_ROOT}/frontend/Dockerfile.working"

    frontend_cleanup
    trap - EXIT
}

# Main
echo -e "${BLUE}Chores Tracker - Deploy to ECR${NC}"
echo -e "Component: ${YELLOW}${COMPONENT}${NC}"
echo -e "Version:   ${YELLOW}${VERSION}${NC}"
echo -e "Registry:  ${YELLOW}${ECR_REGISTRY}${NC}"
echo ""

# Pre-flight checks
echo -e "${YELLOW}Pre-flight checks...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed${NC}"
    exit 1
fi
echo -e "  ${GREEN}docker found${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: aws CLI is not installed${NC}"
    exit 1
fi
echo -e "  ${GREEN}aws CLI found${NC}"

if [[ "$COMPONENT" == "frontend" ]] || [[ "$COMPONENT" == "all" ]]; then
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}Error: npm is not installed (required for frontend build)${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}npm found${NC}"
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured. Run 'aws configure' or set AWS_PROFILE${NC}"
    exit 1
fi
echo -e "  ${GREEN}AWS credentials valid${NC}"

# Login to ECR
ecr_login

# Deploy
case "$COMPONENT" in
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    all)
        deploy_backend
        deploy_frontend
        ;;
esac

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update the image tag in the GitOps manifests (arigsela/kubernetes):"
echo "   - base-apps/chores-tracker-backend/deployments.yaml"
echo "   - base-apps/chores-tracker-frontend/deployments.yaml"
echo "2. Commit and push to arigsela/kubernetes to trigger ArgoCD sync"
echo ""
echo -e "${BLUE}Tip:${NC} the GitHub Actions 'Release and Deploy' workflow automates"
echo "versioning, release notes, and the GitOps PR. Consider using it for"
echo "production releases: gh workflow run backend-release-and-deploy.yml"
