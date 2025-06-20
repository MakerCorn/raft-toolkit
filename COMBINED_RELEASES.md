# Combined Release Process 🚀

This document provides a quick overview of the new combined release process for RAFT Toolkit.

## Quick Start

Create a combined CLI + Web release with a single command:

```bash
./scripts/create_combined_release.sh 0.2.3
```

## What You Get

Each combined release creates:

- **🏷️ Three Tags**: `cli-v0.2.3`, `web-v0.2.3`, `v0.2.3`
- **🐳 Docker Images**: CLI and Web containers (multi-platform)
- **📦 PyPI Package**: `raft-toolkit==0.2.3` with optional dependencies
- **📝 GitHub Release**: Comprehensive release notes and installation guides

## Installation Options

### CLI Usage
```bash
# Install from PyPI
pip install raft-toolkit==0.2.3

# Run with Docker
docker run ghcr.io/owner/repo:cli-v0.2.3 --help
```

### Web Application
```bash
# Install with web dependencies
pip install raft-toolkit[web]==0.2.3

# Run with Docker
docker run -p 8000:8000 ghcr.io/owner/repo:web-v0.2.3
```

## Release Commands

| Command | Description |
|---------|-------------|
| `./scripts/create_combined_release.sh 0.2.3` | Standard patch release |
| `./scripts/create_combined_release.sh 0.3.0 --type minor` | Minor release with custom type |
| `./scripts/create_combined_release.sh 0.2.4 --skip-tests` | Emergency release (skip tests) |
| `./scripts/create_combined_release.sh 0.2.3 --dry-run` | Preview without executing |

## Release Workflow

1. **🔍 Validation**: Version format, tag conflicts, prerequisites
2. **🧪 Testing**: Comprehensive test suite across Python versions  
3. **🔨 Building**: CLI and Web Docker images (multi-platform)
4. **📝 Updating**: Version bumps and changelog updates
5. **🚀 Publishing**: PyPI package and GitHub release
6. **✅ Verification**: Smoke tests and success notifications

## Monitoring

Monitor release progress:
- **GitHub Actions**: Check workflow status in real-time
- **Script Output**: Interactive progress with option to watch
- **Notifications**: Success/failure notifications with next steps

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Version already exists | Use next available version |
| Test failures | Fix tests or use `--skip-tests` for emergencies |
| Docker build failures | Test builds locally, check platform issues |
| PyPI publishing failed | Verify token, check package validation |

For detailed troubleshooting, see [docs/RELEASES.md](docs/RELEASES.md#troubleshooting).

## Fallback Options

If combined release fails:
- **Individual releases**: Use existing CLI/Web workflows
- **Manual recovery**: Fix specific components and retry
- **Complete rollback**: Remove tags and revert changes

## Benefits

- **⚡ Faster**: Single command vs multiple manual steps
- **🔒 Safer**: Comprehensive validation and testing
- **📦 Coordinated**: Synchronized versioning across components
- **🎯 Consistent**: Standardized release artifacts and documentation
- **🔄 Recoverable**: Built-in rollback and recovery procedures

## Migration

Existing individual release workflows remain available:
- **CLI releases**: `./scripts/create_release.sh cli-v0.2.3`
- **Web releases**: `./scripts/create_release.sh web-v0.2.3`

The combined process is recommended for most releases, with individual releases reserved for component-specific hotfixes.

---

For complete documentation, see [docs/RELEASES.md](docs/RELEASES.md).