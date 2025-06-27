# Workflow Changes to Preserve 'v' Prefix in Docker Tags

This document contains the changes needed to ensure Docker tags include the 'v' prefix (e.g., v2.0.0 instead of 2.0.0).

## Changes to `.github/workflows/deploy-to-ecr.yml`

In the "Extract metadata" step (around line 173), update the semver patterns:

### Before:
```yaml
tags: |
  # Always update latest on main branch pushes
  type=raw,value=latest,enable={{is_default_branch}}
  # Git SHA for immutable reference
  type=sha,prefix=sha-,format=short
  # Timestamp for chronological ordering
  type=raw,value={{date 'YYYYMMDD-HHmmss'}},prefix=build-
  # Semantic versioning (if you create git tags)
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}
  # Branch name (sanitized)
  type=ref,event=branch
  # PR number (if triggered by PR)
  type=ref,event=pr
```

### After:
```yaml
tags: |
  # Always update latest on main branch pushes
  type=raw,value=latest,enable={{is_default_branch}}
  # Git SHA for immutable reference
  type=sha,prefix=sha-,format=short
  # Timestamp for chronological ordering
  type=raw,value={{date 'YYYYMMDD-HHmmss'}},prefix=build-
  # Semantic versioning (preserve 'v' prefix from git tags)
  type=semver,pattern={{raw}}
  type=semver,pattern=v{{major}}.{{minor}}
  # Branch name (sanitized)
  type=ref,event=branch
  # PR number (if triggered by PR)
  type=ref,event=pr
```

## Changes to `.github/workflows/release.yml`

In the "Summary" step (around line 155), update the Docker tag documentation:

### Before:
```yaml
echo "### Docker Image Tags"
echo "The ECR deployment workflow will automatically create the following tags:"
echo "- \`${NEW_VERSION#v}\` (full version)"
echo "- \`${NEW_VERSION#v%.*}\` (major.minor)"
echo "- \`${NEW_VERSION#v%%.*}\` (major only)"
echo "- \`latest\`"
echo "- \`sha-${GITHUB_SHA:0:7}\`"
```

### After:
```yaml
echo "### Docker Image Tags"
echo "The ECR deployment workflow will automatically create the following tags:"
echo "- \`$NEW_VERSION\` (full version with v prefix)"
echo "- \`v${NEW_VERSION#v%%.*}.${NEW_VERSION#v*.}\` (major.minor with v prefix)"
echo "- \`latest\`"
echo "- \`sha-${GITHUB_SHA:0:7}\`"
echo "- \`build-YYYYMMDD-HHmmss\`"
```

## Summary of Changes

1. **deploy-to-ecr.yml**: Changed `pattern={{version}}` to `pattern={{raw}}` to preserve the 'v' prefix
2. **deploy-to-ecr.yml**: Changed `pattern={{major}}.{{minor}}` to `pattern=v{{major}}.{{minor}}` to add 'v' prefix to major.minor tags
3. **release.yml**: Updated the summary output to correctly show that Docker tags will include the 'v' prefix

These changes will ensure that:
- Git tag `v3.0.0` → Docker tags `v3.0.0`, `v3.0`, `latest`, etc.
- The 'v' prefix is preserved throughout the tagging process
- Kubernetes manifests can correctly reference images with the 'v' prefix