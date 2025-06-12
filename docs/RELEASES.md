# Release Process

This document describes how to create and manage releases for the RAFT Toolkit.

## Overview

The RAFT Toolkit uses an automated release process triggered by git tags. When a version tag is pushed to the repository, it automatically:

1. Creates a GitHub release with generated release notes
2. Builds and publishes Docker images to GitHub Container Registry
3. Builds and publishes Python packages to PyPI (for version tags)
4. Updates the project documentation

## Creating a Release

### Method 1: Using the Release Script (Recommended)

The easiest way to create a release is using the provided script:

```bash
./scripts/create_release.sh
```

This script will:
- Check that your working directory is clean
- Ensure you're on the main branch
- Pull the latest changes
- Show the current version and suggest increments
- Create and push the appropriate tag

### Method 2: Manual Tag Creation

If you prefer to create tags manually:

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Create and push a version tag
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

## Release Workflow

### Triggers

The release workflow (`.github/workflows/release.yml`) is triggered by:

1. **Tag pushes**: `git push origin v*` - Creates a full release
2. **Manual dispatch**: Manually trigger via GitHub Actions UI
3. **Workflow run**: When tests complete successfully (but won't create a release automatically)

### Workflow Jobs

1. **check-tests**: Validates the trigger and determines if a release should be created
2. **create-release**: Creates the GitHub release and generates release notes
3. **build-release-images**: Builds and publishes Docker images
4. **publish-packages**: Builds and publishes Python packages
5. **update-documentation**: Updates GitHub Pages documentation
6. **notify-completion**: Sends completion notifications

### Release Artifacts

Each release produces:

- **GitHub Release**: With auto-generated release notes
- **Docker Images**: 
  - `ghcr.io/owner/repo:version-production` (Full web application)
  - `ghcr.io/owner/repo:version-cli` (CLI-only version)
- **Python Package**: Published to PyPI (for version tags only)
- **SBOM**: Software Bill of Materials for security scanning
- **Documentation**: Updated GitHub Pages site

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

### Common Issues

1. **"Resource not accessible by integration"**
   - The workflow is trying to create a release without proper permissions
   - Ensure the workflow was triggered by a tag push, not a branch push

2. **"Tag already exists"**
   - The tag already exists in the repository
   - Delete the tag and recreate: `git tag -d v1.2.3 && git push origin :refs/tags/v1.2.3`

3. **"Tests failed"**
   - The test workflow must pass before a release can be created
   - Check the test results and fix any failures

4. **"Build failed"**
   - Check the build logs for specific error messages
   - Common issues: dependency conflicts, Docker build failures

### Manual Release Recovery

If the automated release fails, you can:

1. **Fix the issue** and trigger the workflow again via manual dispatch
2. **Create a new patch version** with the fix
3. **Manually create the release** on GitHub if only the release creation failed

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