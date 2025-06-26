# ECR Deployment GitHub Action Implementation Guide

## Overview

This document serves as a comprehensive guide for implementing a GitHub Action that builds and deploys Docker images to Amazon Elastic Container Registry (ECR) when code is merged to the main branch.

**Document Status**: 🟡 In Progress  
**Last Updated**: December 26, 2024  
**Estimated Total Time**: 2-3 hours

## Implementation Progress

- [x] Created `.github/workflows/deploy-to-ecr.yml`
- [x] Added multi-stage deployment (build-and-push, cleanup, notify)
- [x] Configured Docker layer caching
- [x] Added Trivy security scanning
- [x] Created workflow validation script
- [ ] AWS resources setup pending
- [ ] GitHub secrets configuration pending

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [AWS Setup](#aws-setup)
4. [GitHub Repository Setup](#github-repository-setup)
5. [Implementation Steps](#implementation-steps)
6. [Testing & Validation](#testing--validation)
7. [Post-Deployment](#post-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)
10. [Decision Log](#decision-log)

## Quick Start

For experienced users who want to skip to implementation:

1. Create ECR repository: `aws ecr create-repository --repository-name chores-tracker`
2. Create IAM user with ECR permissions
3. Add GitHub secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECR_REPOSITORY`
4. Add workflow file: `.github/workflows/deploy-to-ecr.yml`
5. Push to main branch to test

## Prerequisites

### Required Tools
- [ ] AWS CLI installed and configured locally
- [ ] Docker installed locally for testing
- [ ] GitHub repository admin access
- [ ] Basic understanding of Docker and GitHub Actions

### Required Information
- [ ] AWS Account ID: `______________`
- [ ] AWS Region: `______________`
- [ ] ECR Repository Name: `chores-tracker` (recommended)
- [ ] GitHub Repository: `chores-tracker`

## AWS Setup

### 1. Create ECR Repository (15 minutes)

- [ ] **Step 1.1**: Login to AWS Console or use CLI
  ```bash
  aws ecr create-repository \
    --repository-name chores-tracker \
    --region <your-region> \
    --image-scanning-configuration scanOnPush=true
  ```
  
- [ ] **Step 1.2**: Note the repository URI
  ```
  Repository URI: ________________________________
  ```

- [ ] **Step 1.3**: Enable image scanning (security best practice)

### 2. Create IAM User for GitHub Actions (20 minutes)

- [ ] **Step 2.1**: Create IAM policy
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "GetAuthorizationToken",
        "Effect": "Allow",
        "Action": [
          "ecr:GetAuthorizationToken"
        ],
        "Resource": "*"
      },
      {
        "Sid": "ManageRepositoryContents",
        "Effect": "Allow",
        "Action": [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:DescribeImages",
          "ecr:BatchGetImage"
        ],
        "Resource": "arn:aws:ecr:<region>:<account-id>:repository/chores-tracker"
      }
    ]
  }
  ```
  Policy Name: `GitHubActions-ECR-ChoresTracker`

- [ ] **Step 2.2**: Create IAM user
  ```bash
  aws iam create-user --user-name github-actions-chores-tracker
  ```

- [ ] **Step 2.3**: Attach policy to user
  ```bash
  aws iam attach-user-policy \
    --user-name github-actions-chores-tracker \
    --policy-arn arn:aws:iam::<account-id>:policy/GitHubActions-ECR-ChoresTracker
  ```

- [ ] **Step 2.4**: Create access keys
  ```bash
  aws iam create-access-key --user-name github-actions-chores-tracker
  ```
  
  Record credentials:
  ```
  Access Key ID: ________________________________
  Secret Access Key: ________________________________
  ```

### 3. Configure ECR Lifecycle Policy (10 minutes)

- [ ] **Step 3.1**: Create lifecycle policy to manage image retention
  ```json
  {
    "rules": [
      {
        "rulePriority": 1,
        "description": "Keep last 50 images",
        "selection": {
          "tagStatus": "any",
          "countType": "imageCountMoreThan",
          "countNumber": 50
        },
        "action": {
          "type": "expire"
        }
      }
    ]
  }
  ```

- [ ] **Step 3.2**: Apply policy
  ```bash
  aws ecr put-lifecycle-policy \
    --repository-name chores-tracker \
    --lifecycle-policy-text file://lifecycle-policy.json
  ```

## GitHub Repository Setup

### 4. Configure GitHub Secrets (15 minutes)

Navigate to: Settings → Secrets and variables → Actions

- [ ] **Secret 1**: `AWS_ACCESS_KEY_ID`
  - Value: From step 2.4
  - Added: ☐

- [ ] **Secret 2**: `AWS_SECRET_ACCESS_KEY`
  - Value: From step 2.4
  - Added: ☐

- [ ] **Secret 3**: `AWS_REGION`
  - Value: Your AWS region (e.g., us-east-1)
  - Added: ☐

- [ ] **Secret 4**: `ECR_REPOSITORY`
  - Value: `chores-tracker`
  - Added: ☐

### 5. Create GitHub Environments (Optional, 10 minutes)

- [ ] **Step 5.1**: Create "production" environment
  - Protection rules: ☐ Required reviewers
  - Deployment branches: `main` only

## Implementation Steps

### 6. Create Workflow File (30 minutes)

- [ ] **Step 6.1**: Create directory structure
  ```bash
  mkdir -p .github/workflows
  ```

- [ ] **Step 6.2**: Create workflow file `.github/workflows/deploy-to-ecr.yml`
  
- [ ] **Step 6.3**: Add workflow configuration (see implementation section)

- [ ] **Step 6.4**: Commit and push to a feature branch first

### 7. Workflow Configuration Checklist

The workflow should include:

- [ ] **Triggers**
  - [ ] Push to main branch
  - [ ] Manual workflow dispatch
  - [ ] Ignore paths for docs and tests

- [ ] **Jobs**
  - [ ] Build and push job
  - [ ] Security scanning (optional)
  - [ ] Notification (optional)

- [ ] **Steps**
  - [ ] Checkout code
  - [ ] Configure AWS credentials
  - [ ] Login to ECR
  - [ ] Set up Docker Buildx
  - [ ] Cache Docker layers
  - [ ] Generate metadata and tags
  - [ ] Build and push image
  - [ ] Scan for vulnerabilities

## Testing & Validation

### 8. Pre-Deployment Testing (20 minutes)

- [ ] **Test 8.1**: Validate GitHub secrets are set
  ```yaml
  # Add a test job to workflow temporarily
  test-secrets:
    runs-on: ubuntu-latest
    steps:
      - name: Test secrets
        run: |
          if [ -z "${{ secrets.AWS_ACCESS_KEY_ID }}" ]; then
            echo "AWS_ACCESS_KEY_ID is not set"
            exit 1
          fi
  ```

- [ ] **Test 8.2**: Local Docker build
  ```bash
  docker build -t chores-tracker:test .
  ```

- [ ] **Test 8.3**: Test AWS credentials locally
  ```bash
  aws ecr get-login-password --region <region> | \
    docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
  ```

### 9. Deployment Testing (15 minutes)

- [ ] **Test 9.1**: Create test branch and PR
  ```bash
  git checkout -b test/ecr-deployment
  git add .github/workflows/deploy-to-ecr.yml
  git commit -m "Add ECR deployment workflow"
  git push origin test/ecr-deployment
  ```

- [ ] **Test 9.2**: Merge PR to main

- [ ] **Test 9.3**: Monitor GitHub Actions tab for workflow execution

- [ ] **Test 9.4**: Verify image in ECR
  ```bash
  aws ecr describe-images --repository-name chores-tracker
  ```

## Post-Deployment

### 10. Verification Checklist (10 minutes)

- [ ] **Verify 10.1**: Workflow completed successfully
- [ ] **Verify 10.2**: Image appears in ECR with correct tags
- [ ] **Verify 10.3**: Image scanning results (if enabled)
- [ ] **Verify 10.4**: Docker pull works
  ```bash
  docker pull <account-id>.dkr.ecr.<region>.amazonaws.com/chores-tracker:latest
  ```

### 11. Documentation Updates (10 minutes)

- [ ] Update README.md with deployment information
- [ ] Document the ECR repository URI
- [ ] Add deployment badge to README
- [ ] Update CLAUDE.md with CD information

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Failures**
   - Check IAM permissions
   - Verify secrets are correctly set
   - Ensure region matches

2. **Build Failures**
   - Check Dockerfile syntax
   - Verify build context
   - Check for missing files

3. **Push Failures**
   - Verify repository exists
   - Check ECR repository permissions
   - Ensure image size limits

4. **Workflow Not Triggering**
   - Check branch protection rules
   - Verify workflow file syntax
   - Check workflow triggers

## Maintenance

### Regular Tasks

- [ ] **Monthly**: Review and rotate AWS access keys
- [ ] **Quarterly**: Audit ECR images and costs
- [ ] **Quarterly**: Update GitHub Action versions
- [ ] **Annually**: Review IAM permissions (least privilege)

### Monitoring

- [ ] Set up AWS CloudWatch alarms for ECR
- [ ] Configure GitHub Action failure notifications
- [ ] Monitor ECR storage costs
- [ ] Track deployment frequency and success rate

## Decision Log

| Decision | Rationale | Date | Author |
|----------|-----------|------|--------|
| Use aws-actions/amazon-ecr-login@v2 | Official AWS action, well-maintained | TBD | TBD |
| Multi-tag strategy (sha, latest, timestamp) | Enables easy rollback and tracking | TBD | TBD |
| Enable image scanning | Security best practice, minimal cost | TBD | TBD |
| 50 image retention policy | Balance between history and cost | TBD | TBD |

## Glossary

- **ECR**: Elastic Container Registry - AWS managed Docker registry
- **IAM**: Identity and Access Management - AWS service for managing access
- **Buildx**: Docker CLI plugin for extended build capabilities
- **Image Tag**: Label attached to Docker image for identification
- **Lifecycle Policy**: Rules for automatic image cleanup in ECR

## Next Steps

After completing this implementation:

1. Consider implementing staging deployments
2. Add container orchestration (ECS/EKS)
3. Implement blue-green deployments
4. Add performance monitoring
5. Create disaster recovery plan

---

**Document Version**: 1.0.0  
**Status Indicators**:
- 🟢 Complete
- 🟡 In Progress
- 🔴 Blocked
- ⚪ Not Started