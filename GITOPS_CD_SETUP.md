# GitOps CD Setup for Chores-Tracker

## Overview

This document describes the Continuous Deployment (CD) enhancement added to the `release-and-deploy.yml` GitHub Actions workflow. The CD portion automatically creates a Pull Request in the GitOps repository (`arigsela/kubernetes`) after successfully building and pushing Docker images to ECR.

## What's New

### 1. New Workflow Inputs

- **`update_gitops`** (boolean, default: true)
  - Controls whether to update the GitOps repository after a successful release
  
- **`auto_merge`** (boolean, default: false)
  - When enabled, automatically merges the GitOps PR after creation
  - Use with caution - recommended only for non-production environments

### 2. New Job: `gitops-update`

This job runs after `release-and-deploy` completes successfully and:
1. Checks out the kubernetes repository
2. Updates the deployment manifest with the new image version using `yq`
3. Creates a Pull Request with the changes
4. Optionally enables auto-merge on the PR

### 3. Required Secret

- **`GITOPS_PAT`**: Personal Access Token with `repo` scope for the `arigsela/kubernetes` repository
  - This token must have write access to create branches and pull requests
  - Recommended: Use a dedicated machine account's PAT for security

## How It Works

### Execution Flow

```
1. Release & Deploy Job
   ├── Create GitHub Release
   ├── Build Docker Image
   └── Push to ECR
       ↓
2. GitOps Update Job (if enabled)
   ├── Clone kubernetes repo
   ├── Update deployment.yaml
   ├── Create PR
   └── Optional: Auto-merge
       ↓
3. ArgoCD (automatic)
   └── Syncs and deploys after PR merge
```

### Conditions

The GitOps update job only runs when ALL of these conditions are met:
- Previous job succeeded
- Docker image was pushed to ECR
- `skip_deploy` is not true
- `update_gitops` is not false
- `GITOPS_PAT` secret is configured

## Setup Instructions

### 1. Create Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token (classic) with `repo` scope
3. Save the token securely

### 2. Add Secret to Repository

1. Go to your repository's Settings → Secrets and variables → Actions
2. Add a new secret named `GITOPS_PAT`
3. Paste the PAT token value

### 3. Usage

When triggering the workflow:

```yaml
# Basic usage (creates PR, manual merge required)
update_gitops: true
auto_merge: false

# Auto-merge for development deployments
update_gitops: true
auto_merge: true

# Skip GitOps update
update_gitops: false
```

## Pull Request Details

The automated PR includes:
- **Title**: `chore: update chores-tracker to vX.Y.Z`
- **Branch**: `update-chores-tracker-X.Y.Z`
- **Labels**: `deployment`, `automated`, `chores-tracker`
- **Assignee**: arigsela
- **Body**: Contains deployment details, checklist, and links to release

## Security Considerations

1. **PAT Security**:
   - Use a dedicated machine account if possible
   - Limit PAT scope to only what's needed
   - Rotate the token regularly

2. **Auto-merge Caution**:
   - Only use auto-merge for non-production environments
   - Ensure proper branch protection rules are in place
   - Review ArgoCD sync policies

## Troubleshooting

### GitOps Update Skipped

Check the workflow logs for warnings:
- "GITOPS_PAT secret not configured"
- "AWS secrets not configured"

### PR Creation Failed

Common issues:
- PAT doesn't have sufficient permissions
- Target repository branch protection prevents push
- Network issues accessing external repository

### yq Installation Failed

The workflow downloads yq automatically. If it fails:
- Check GitHub's rate limits
- Verify internet connectivity in runners

## Example Workflow Run

1. Developer triggers workflow with release type "minor"
2. Workflow creates release v3.2.0
3. Docker image pushed as `chores-tracker:3.2.0`
4. GitOps job creates PR to update deployment
5. PR shows image change: `3.1.0` → `3.2.0`
6. After merge, ArgoCD deploys within minutes

## Future Enhancements

- Support for multiple environments (dev/staging/prod)
- Slack/Teams notifications for PR creation
- Automated rollback on deployment failures
- Integration with Argo Rollouts for canary deployments