# Release Process

This document describes how to create and manage releases for the RAFT Toolkit.

## Overview

The RAFT Toolkit supports multiple release strategies:

1. **Combined Release** (Recommended): Coordinates both CLI and Web components in a single release
2. **Individual Releases**: Separate CLI-only or Web-only releases
3. **Legacy Release**: Unified release process (deprecated)

## Release Types

### Combined Release (Recommended)

Creates a coordinated release of both CLI and Web components with unified versioning:

- **Tags Created**: `cli-v{version}`, `web-v{version}`, `v{version}`
- **Docker Images**: Both CLI and Web containers
- **PyPI Package**: Single package with optional web dependencies
- **Use Case**: Most releases, major version updates, coordinated feature releases

### Individual Component Releases

Creates focused releases for specific components:

- **CLI Release**: `cli-v{version}` tag, CLI container only
- **Web Release**: `web-v{version}` tag, Web container only  
- **Use Case**: Component-specific hotfixes, security patches, independent updates

## Creating a Combined Release

### Method 1: Using the Combined Release Script (Recommended)

The easiest way to create a combined release:

```bash
./scripts/create_combined_release.sh <version>
```

**Examples:**
```bash
# Standard patch release
./scripts/create_combined_release.sh 0.2.3

# Minor release with custom notes
./scripts/create_combined_release.sh 0.3.0 --type minor --notes "Major new features"

# Emergency release (skip tests)
./scripts/create_combined_release.sh 0.2.4 --skip-tests

# Preview without executing
./scripts/create_combined_release.sh 0.2.3 --dry-run
```

**Script Features:**
- Pre-flight validation and prerequisite checks
- Auto-detection of release type (patch/minor/major)
- Interactive confirmation with preview
- Integration with GitHub CLI for workflow dispatch
- Progress monitoring and post-release verification

### Method 2: Manual Workflow Dispatch

Trigger the combined release workflow manually:

1. Go to **Actions** → **Combined Release (CLI + Web)**
2. Click **Run workflow**
3. Enter the version and select options
4. Click **Run workflow**

### Method 3: Legacy Individual Releases

For component-specific releases, use the existing workflows:

```bash
# CLI-only release
./scripts/create_release.sh cli-v0.2.3

# Web-only release  
./scripts/create_release.sh web-v0.2.3
```

## Combined Release Workflow

### Triggers

The combined release workflow (`.github/workflows/release-combined.yml`) is triggered by:

1. **Manual dispatch**: Workflow dispatch with version input (recommended)
2. **Script execution**: Using `scripts/create_combined_release.sh`

### Workflow Phases

#### Phase 1: Validation and Preparation
1. **validate-and-prepare**: Version format validation, tag conflict checking, changelog extraction
2. **test-suite**: Comprehensive testing across Python versions (unless `--skip-tests`)

#### Phase 2: Container Builds
3. **build-cli**: Build and test CLI Docker image (multi-platform)
4. **build-web**: Build and test Web Docker image (multi-platform)

#### Phase 3: Release Creation
5. **update-version**: Update `pyproject.toml` and `CHANGELOG.md`, commit changes
6. **publish-pypi**: Build and publish unified Python package to PyPI
7. **create-release**: Create GitHub release with all three tags

#### Phase 4: Notifications
8. **notify-success**: Success summary with links and next steps
9. **notify-failure**: Failure notification with troubleshooting guidance

### Release Artifacts

Each combined release produces:

#### **GitHub Release**
- **Combined tag**: `v{version}` (primary release)
- **Component tags**: `cli-v{version}`, `web-v{version}`
- **Release notes**: Auto-generated from changelog or custom input

#### **Docker Images**
- **CLI Images**:
  - `ghcr.io/owner/repo:cli-v{version}`
  - `ghcr.io/owner/repo:cli-latest`
  - `ghcr.io/owner/repo:cli-{version}`
- **Web Images**:
  - `ghcr.io/owner/repo:web-v{version}`
  - `ghcr.io/owner/repo:web-latest`
  - `ghcr.io/owner/repo:web-{version}`
- **Platforms**: `linux/amd64`, `linux/arm64`
- **Security**: SBOM included, vulnerability scanning

#### **Python Package**
- **Package**: `raft-toolkit=={version}` on PyPI
- **Install Options**:
  - CLI: `pip install raft-toolkit=={version}`
  - Web: `pip install raft-toolkit[web]=={version}`
  - Full: `pip install raft-toolkit[all]=={version}`

#### **Documentation**
- Updated release documentation
- Version-specific installation guides
- Container usage examples

## Version Numbering

We follow [Semantic Versioning (SemVer)](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### Examples

- `v1.0.0` - Major release with potential breaking changes
- `v1.1.0` - Minor release with new features
- `v1.1.1` - Patch release with bug fixes
- `v2.0.0-beta.1` - Pre-release version

## Pre-releases

For pre-release versions, use suffixes like:
- `v1.2.0-alpha.1` - Alpha version
- `v1.2.0-beta.1` - Beta version  
- `v1.2.0-rc.1` - Release candidate

Pre-releases are automatically marked as such in GitHub releases.

## Release Notes

Release notes are automatically generated from:

1. **CHANGELOG.md**: If present, extracts the relevant section
2. **Git commits**: If no changelog, uses commit messages since the last tag
3. **Default template**: If neither is available, uses a generic template

### Improving Release Notes

To get better release notes:

1. **Maintain CHANGELOG.md**: Keep an `[Unreleased]` section updated
2. **Use conventional commits**: Follow conventional commit format
3. **Write descriptive commit messages**: Focus on the "why" not the "what"

## Troubleshooting

### Combined Release Issues

#### **Version Conflicts**
```
❌ Version 0.2.3 already exists as a tag
```
**Solution**: Check existing tags and increment version
```bash
git tag --list | grep "0.2.3"
# Use next available version: 0.2.4
```

#### **Test Failures**
```
❌ Comprehensive test suite failed
```
**Solutions**:
- Fix failing tests and retry
- Use `--skip-tests` for emergency releases only
- Check specific test output in workflow logs

#### **Docker Build Failures**
```
❌ CLI/Web image build failed
```
**Common causes**:
- Dependency conflicts in requirements
- Platform-specific build issues
- Resource limitations during multi-platform builds

**Solutions**:
```bash
# Test build locally
docker build --target cli .
docker build --target production .

# Check platform-specific issues
docker buildx build --platform linux/amd64,linux/arm64 .
```

#### **PyPI Publishing Failures**
```
❌ Package upload failed
```
**Common causes**:
- Version already exists on PyPI
- Authentication issues
- Package validation failures

**Solutions**:
- Verify PYPI_API_TOKEN secret is valid
- Check package contents: `twine check dist/*`
- Ensure version is incremented properly

#### **Partial Release Failures**

If combined release partially fails:

1. **CLI succeeded, Web failed**: 
   - Manually trigger web-only release
   - Update combined release notes
   
2. **Containers succeeded, PyPI failed**:
   - Manually publish to PyPI
   - Update release with PyPI links

3. **GitHub release creation failed**:
   - Manually create release with existing tags
   - Copy release notes from workflow

### Recovery Procedures

#### **Complete Rollback**
```bash
# Delete all created tags
git tag -d v0.2.3 cli-v0.2.3 web-v0.2.3
git push origin :refs/tags/v0.2.3
git push origin :refs/tags/cli-v0.2.3  
git push origin :refs/tags/web-v0.2.3

# Revert version commit if created
git revert <commit-hash>
git push origin main
```

#### **Partial Recovery**
```bash
# Re-run workflow with manual dispatch
gh workflow run release-combined.yml \
  --field version=0.2.3 \
  --field release_type=patch

# Monitor progress
gh run watch
```

### Individual Release Fallback

If combined release consistently fails, fall back to individual releases:

```bash
# Create CLI release
gh workflow run release-cli.yml --field version=0.2.3

# Create Web release  
gh workflow run release-web.yml --field version=0.2.3

# Manually create combined GitHub release
gh release create v0.2.3 \
  --title "RAFT Toolkit v0.2.3" \
  --notes "Combined release of CLI and Web components"
```

## Monitoring Releases

Monitor release progress:

1. **GitHub Actions**: Check the Actions tab for workflow status
2. **GitHub Releases**: Verify the release was created properly
3. **Container Registry**: Confirm Docker images were published
4. **PyPI**: Check that the Python package was published (for version tags)

## Security Considerations

- All release artifacts include SBOMs for security scanning
- Docker images are scanned for vulnerabilities
- Only version tags trigger PyPI publishing
- All artifacts are signed and verifiable

## Contact

For issues with the release process, please:
1. Check the troubleshooting section above
2. Review the workflow logs in GitHub Actions
3. Open an issue with the error details