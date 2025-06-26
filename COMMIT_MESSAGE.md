# Suggested Commit Message

## feat: Add ECR deployment GitHub Action workflow

### What's Added:
- **ECR Deployment Workflow** (`.github/workflows/deploy-to-ecr.yml`)
  - Automated Docker image build and push to Amazon ECR
  - Triggers on push to main branch and manual dispatch
  - Multi-tag strategy (latest, SHA, timestamp, semver)
  - Docker layer caching for faster builds
  - Trivy security vulnerability scanning
  - Cleanup job for old images
  - Comprehensive build metadata and reporting

- **Workflow Validation** (`.github/workflows/validate-workflows.yml`)
  - Validates GitHub Actions syntax on PRs
  - Uses actionlint and yamllint for comprehensive checks
  - Prevents broken workflows from being merged

- **Test Script** (`scripts/test-ecr-workflow.sh`)
  - Local validation before pushing changes
  - Checks YAML syntax, Docker build, and configuration

- **Documentation**
  - `ECR_DEPLOYMENT_GUIDE.md` - Step-by-step implementation guide
  - `ECR_WORKFLOW_IMPLEMENTATION_SUMMARY.md` - Technical summary

### Key Features:
- 🔒 Security scanning with Trivy
- 🚀 Optimized builds with caching
- 🏷️ Comprehensive tagging strategy
- 📊 Detailed deployment reporting
- 🔄 Automatic cleanup of old images

### Next Steps:
1. Configure AWS ECR repository
2. Add GitHub secrets for AWS credentials
3. Test deployment on merge to main

This workflow provides a production-ready CI/CD pipeline for containerized deployments.