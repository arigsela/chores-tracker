# Release Process Guide

This document describes the release process for the Chores Tracker application, including versioning strategy, release workflow, and Docker image tagging.

## Table of Contents

1. [Semantic Versioning](#semantic-versioning)
2. [Release Types](#release-types)
3. [Creating a Release](#creating-a-release)
4. [Docker Image Tags](#docker-image-tags)
5. [Release Checklist](#release-checklist)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/), which uses the format:

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incompatible API changes (breaking changes)
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

### Examples

- `1.0.0` → `2.0.0`: Breaking change (e.g., removed API endpoint, changed authentication)
- `1.0.0` → `1.1.0`: New feature (e.g., added new endpoint, new UI component)
- `1.0.0` → `1.0.1`: Bug fix (e.g., fixed validation error, corrected UI issue)

## Release Types

### Patch Release (Bug Fixes)
Use for:
- Bug fixes
- Security patches
- Documentation updates
- Minor dependency updates

### Minor Release (New Features)
Use for:
- New API endpoints
- New UI features
- Non-breaking improvements
- New optional configuration

### Major Release (Breaking Changes)
Use for:
- API changes that break compatibility
- Database schema changes requiring migration
- Removal of deprecated features
- Major architectural changes

## Creating a Release

### Prerequisites

1. Ensure all tests are passing:
   ```bash
   docker compose exec api python -m pytest
   ```

2. Ensure CI/CD pipeline is green:
   - Check GitHub Actions tab
   - Verify all workflows are passing

3. Update documentation if needed:
   - README.md
   - API documentation
   - CLAUDE.md

### Using the Release and Deploy Workflow

1. **Navigate to GitHub Actions**
   - Go to the repository on GitHub
   - Click on the "Actions" tab
   - Select "Release and Deploy" workflow

2. **Run the Workflow**
   - Click "Run workflow"
   - Select the branch (usually `main`)
   - Choose release type:
     - `patch`: For bug fixes (1.0.0 → 1.0.1)
     - `minor`: For new features (1.0.0 → 1.1.0)
     - `major`: For breaking changes (1.0.0 → 2.0.0)
     - `custom`: For specific version (enter manually)
   - Optional: Add release notes (auto-generated if empty)
   - Optional: Check "Skip Docker build and ECR deployment" for release-only
   - Click "Run workflow"

3. **Monitor the Release**
   - Watch the workflow execution
   - Check for any errors
   - Verify the release was created

4. **Verify the Release**
   - Check the "Releases" page
   - Ensure release notes are accurate
   - Verify the tag was created

### Manual Release Process (Fallback)

If the workflow fails, you can create a release manually:

```bash
# Fetch latest changes
git fetch origin
git checkout main
git pull origin main

# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag
git push origin v1.0.0

# Create release on GitHub UI
# Go to Releases → Draft a new release → Select the tag
```

## Docker Image Tags

The combined release and deploy workflow automatically creates multiple Docker image tags:

### Version Tags
- **Full version**: `1.2.3` (exact version)
- **Minor version**: `1.2` (latest patch of this minor version)
- **Major version**: `1` (latest minor/patch of this major version)
- **Latest**: `latest` (most recent release)

### Additional Tags
- **SHA tag**: `sha-abc1234` (git commit SHA)
- **Timestamp**: `build-20240626-123456` (build time)
- **Branch**: `main` (branch name)

### Example

For release `v1.2.3`, these tags are created:
```
chores-tracker:1.2.3    # Exact version
chores-tracker:1.2      # Latest patch of v1.2
chores-tracker:1        # Latest v1.x.x
chores-tracker:latest   # Most recent release
chores-tracker:sha-abc1234
chores-tracker:build-20240626-123456
```

## Release Checklist

Before creating a release, ensure:

- [ ] All tests are passing locally
- [ ] CI/CD pipeline is green
- [ ] Code has been reviewed and approved
- [ ] Documentation is up to date
- [ ] CLAUDE.md reflects any new changes
- [ ] No sensitive data in code or commits
- [ ] Dependencies are up to date
- [ ] Database migrations are tested
- [ ] Performance impact assessed

After creating a release:

- [ ] Verify release appears on GitHub
- [ ] Check Docker images in ECR
- [ ] Test pulling the new image
- [ ] Update deployment environments
- [ ] Notify team of new release
- [ ] Monitor for any issues

## Troubleshooting

### Release Workflow Fails

1. **Version Already Exists**
   - Error: "Tag vX.Y.Z already exists"
   - Solution: Use a different version number
   
2. **Invalid Version Format**
   - Error: "Version must be in format X.Y.Z"
   - Solution: Use proper semantic version format

3. **Permissions Issue**
   - Error: "Resource not accessible by integration"
   - Solution: Check GitHub Actions permissions

### ECR Deployment Fails

1. **Authentication Error**
   - Check AWS credentials are configured
   - Verify ECR repository exists
   - Check IAM permissions

2. **Image Push Fails**
   - Verify Docker build succeeds locally
   - Check ECR repository policies
   - Ensure sufficient storage

### Common Issues

1. **Forgot to Update Version**
   - The workflow calculates the next version automatically
   - No manual version bumping needed

2. **Release Notes Missing Commits**
   - Ensure you're releasing from the correct branch
   - Check that all commits are pushed

3. **Docker Tags Not Created**
   - ECR deployment runs after release creation
   - Check the deploy-to-ecr workflow status

## Best Practices

### Before Release

1. **Test Thoroughly**
   ```bash
   # Run full test suite
   docker compose exec api python -m pytest -v
   
   # Check test coverage
   docker compose exec api python -m pytest --cov=backend/app
   ```

2. **Review Changes**
   ```bash
   # View commits since last release
   git log v1.0.0..HEAD --oneline
   
   # Review changed files
   git diff v1.0.0..HEAD --name-only
   ```

3. **Update Documentation**
   - Review README.md for accuracy
   - Update API documentation if needed
   - Check inline code documentation

### Release Notes

Good release notes should include:

1. **Summary** - Brief overview of the release
2. **New Features** - List of new functionality
3. **Bug Fixes** - Issues resolved
4. **Breaking Changes** - Any incompatibilities
5. **Migration Guide** - If applicable
6. **Contributors** - Recognition for contributions

Example:
```markdown
## What's Changed

### New Features
- Added bulk chore assignment for parents (#123)
- Implemented reward history tracking (#124)

### Bug Fixes
- Fixed date validation in chore creation (#125)
- Resolved JWT token expiration issue (#126)

### Breaking Changes
- API endpoint `/api/v1/users` now requires authentication

### Contributors
- @username1
- @username2
```

### Post-Release

1. **Monitor the Release**
   - Check application logs
   - Monitor error rates
   - Verify functionality

2. **Communication**
   - Notify team members
   - Update project documentation
   - Post in relevant channels

3. **Deployment**
   - Deploy to staging first
   - Run smoke tests
   - Deploy to production
   - Verify deployment

## Rollback Procedure

If a release causes issues:

1. **Immediate Rollback**
   ```bash
   # Pull previous version
   docker pull <ecr-repo>:1.2.2  # Previous version
   
   # Deploy previous version
   # Update your deployment configuration
   ```

2. **Fix Forward**
   - Create a hotfix branch
   - Fix the issue
   - Create a patch release
   - Deploy the fix

3. **Document the Issue**
   - Create incident report
   - Update release notes
   - Add regression test

## Version History

To view all releases:

1. **GitHub UI**: Go to Releases page
2. **Command Line**: 
   ```bash
   git tag -l "v*" --sort=-version:refname
   ```
3. **ECR Images**:
   ```bash
   aws ecr describe-images --repository-name chores-tracker \
     --query 'sort_by(imageDetails,& imagePushedAt)[*].imageTags[]' \
     --output table
   ```

---

**Last Updated**: December 26, 2024  
**Maintained By**: Chores Tracker Team