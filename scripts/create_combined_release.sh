#!/bin/bash

#
# Combined Release Script for RAFT Toolkit
# Creates coordinated CLI + Web releases with proper versioning
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
CHANGELOG_FILE="$PROJECT_ROOT/CHANGELOG.md"

# Functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS] <version>

Create a combined CLI + Web release for RAFT Toolkit.

ARGUMENTS:
    <version>           Release version (e.g., 0.2.3, 1.0.0-beta.1)

OPTIONS:
    -t, --type TYPE     Release type: patch|minor|major (optional, auto-detected)
    -n, --notes TEXT    Custom release notes (optional, uses changelog)
    -s, --skip-tests    Skip test execution (emergency releases only)
    -d, --dry-run       Show what would be done without executing
    -h, --help          Show this help message

EXAMPLES:
    $0 0.2.3                    # Create patch release 0.2.3
    $0 0.3.0 --type minor       # Create minor release 0.3.0
    $0 1.0.0-beta.1 --skip-tests # Create beta release, skip tests
    $0 0.2.4 --dry-run          # Preview release 0.2.4 without executing

WORKFLOW:
    1. Validates version format and checks for conflicts
    2. Prepares changelog and version updates
    3. Runs comprehensive test suite (unless --skip-tests)
    4. Builds both CLI and Web Docker images
    5. Updates version in code and commits changes
    6. Publishes to PyPI with unified package
    7. Creates GitHub release with combined tags
    8. Provides post-release summary and next steps

For more information, see docs/RELEASES.md
EOF
}

validate_version() {
    local version="$1"
    
    # Check semantic version format
    if ! echo "$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$'; then
        error "Invalid version format: $version"
        error "Expected semantic version format (e.g., 1.2.3 or 1.2.3-beta.1)"
        return 1
    fi
    
    # Check if version already exists
    if git tag --list | grep -qE "^(v$version|cli-v$version|web-v$version)$"; then
        error "Version $version already exists as a tag"
        git tag --list | grep -E "^(v$version|cli-v$version|web-v$version)$" | sed 's/^/  - /'
        return 1
    fi
    
    log "Version $version is valid and available"
    return 0
}

get_current_version() {
    if [ -f "$PYPROJECT_FILE" ]; then
        grep '^version = ' "$PYPROJECT_FILE" | sed 's/version = "\(.*\)"/\1/'
    else
        error "pyproject.toml not found at $PYPROJECT_FILE"
        return 1
    fi
}

detect_release_type() {
    local current_version="$1"
    local new_version="$2"
    
    # Parse versions
    local current_major current_minor current_patch
    local new_major new_minor new_patch
    
    IFS='.' read -r current_major current_minor current_patch_full <<< "$current_version"
    current_patch="${current_patch_full%%-*}"  # Remove pre-release suffix
    
    IFS='.' read -r new_major new_minor new_patch_full <<< "$new_version"  
    new_patch="${new_patch_full%%-*}"  # Remove pre-release suffix
    
    if [ "$new_major" -gt "$current_major" ]; then
        echo "major"
    elif [ "$new_minor" -gt "$current_minor" ]; then
        echo "minor"
    elif [ "$new_patch" -gt "$current_patch" ]; then
        echo "patch"
    else
        echo "unknown"
    fi
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if we're in git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "Not in a git repository"
        return 1
    fi
    
    # Check if working directory is clean
    if ! git diff-index --quiet HEAD --; then
        error "Working directory is not clean. Please commit or stash changes."
        git status --porcelain
        return 1
    fi
    
    # Check if on main branch
    local current_branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ]; then
        warn "Not on main branch (currently on: $current_branch)"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Aborted by user"
            return 1
        fi
    fi
    
    # Check for required tools
    local missing_tools=()
    for tool in git gh docker; do
        if ! command -v "$tool" > /dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
        error "Please install missing tools and try again"
        return 1
    fi
    
    # Check GitHub CLI authentication
    if ! gh auth status > /dev/null 2>&1; then
        error "GitHub CLI not authenticated. Run 'gh auth login' first."
        return 1
    fi
    
    success "Prerequisites check passed"
    return 0
}

preview_changes() {
    local version="$1"
    local release_type="$2"
    local current_version
    current_version=$(get_current_version)
    
    cat << EOF

${BLUE}=== COMBINED RELEASE PREVIEW ===${NC}

Current Version: ${current_version}
New Version:     ${version}
Release Type:    ${release_type}

${BLUE}Tags to be created:${NC}
  • cli-v${version}  (CLI component)
  • web-v${version}  (Web component)  
  • v${version}      (Combined release)

${BLUE}Docker Images:${NC}
  • ghcr.io/${GITHUB_REPOSITORY:-owner/repo}:cli-v${version}
  • ghcr.io/${GITHUB_REPOSITORY:-owner/repo}:web-v${version}
  • ghcr.io/${GITHUB_REPOSITORY:-owner/repo}:cli-latest
  • ghcr.io/${GITHUB_REPOSITORY:-owner/repo}:web-latest

${BLUE}PyPI Package:${NC}
  • raft-toolkit==${version}

${BLUE}Files to be updated:${NC}
  • pyproject.toml (version bump)
  • CHANGELOG.md (release entry)

${BLUE}Workflow steps:${NC}
  1. Validate version and run tests
  2. Build CLI Docker image (linux/amd64, linux/arm64)
  3. Build Web Docker image (linux/amd64, linux/arm64)  
  4. Update version in code and commit
  5. Publish to PyPI
  6. Create GitHub release with all tags
  7. Post-release verification

EOF
}

trigger_release() {
    local version="$1"
    local release_type="$2"
    local skip_tests="${3:-false}"
    local release_notes="${4:-}"
    
    log "Triggering combined release workflow..."
    
    # Prepare GitHub CLI command
    local gh_cmd=(
        gh workflow run release-combined.yml
        --field "version=$version"
        --field "release_type=$release_type"
        --field "skip_tests=$skip_tests"
    )
    
    if [ -n "$release_notes" ]; then
        gh_cmd+=(--field "release_notes=$release_notes")
    fi
    
    # Execute workflow
    if "${gh_cmd[@]}"; then
        success "Release workflow triggered successfully"
        
        # Wait a moment for workflow to appear
        sleep 3
        
        # Show workflow status
        log "You can monitor the release progress at:"
        gh run list --workflow=release-combined.yml --limit=1 --json url --jq '.[0].url'
        
        # Or watch it
        echo
        read -p "Watch the release progress? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gh run watch
        fi
        
    else
        error "Failed to trigger release workflow"
        return 1
    fi
}

main() {
    local version=""
    local release_type=""
    local skip_tests="false"
    local release_notes=""
    local dry_run="false"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                release_type="$2"
                shift 2
                ;;
            -n|--notes)
                release_notes="$2"
                shift 2
                ;;
            -s|--skip-tests)
                skip_tests="true"
                shift
                ;;
            -d|--dry-run)
                dry_run="true"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                if [ -z "$version" ]; then
                    version="$1"
                else
                    error "Multiple versions specified: $version, $1"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Validate required arguments
    if [ -z "$version" ]; then
        error "Version is required"
        usage
        exit 1
    fi
    
    # Validate version format
    if ! validate_version "$version"; then
        exit 1
    fi
    
    # Auto-detect release type if not provided
    if [ -z "$release_type" ]; then
        local current_version
        current_version=$(get_current_version)
        release_type=$(detect_release_type "$current_version" "$version")
        
        if [ "$release_type" = "unknown" ]; then
            warn "Could not auto-detect release type"
            release_type="patch"
        fi
        
        log "Auto-detected release type: $release_type"
    fi
    
    # Validate release type
    if [[ ! "$release_type" =~ ^(patch|minor|major)$ ]]; then
        error "Invalid release type: $release_type (must be patch, minor, or major)"
        exit 1
    fi
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check prerequisites (skip in dry-run mode)
    if [ "$dry_run" = "false" ]; then
        if ! check_prerequisites; then
            exit 1
        fi
    fi
    
    # Show preview
    preview_changes "$version" "$release_type"
    
    # Confirm or execute
    if [ "$dry_run" = "true" ]; then
        success "Dry-run completed. Use without --dry-run to execute."
        exit 0
    fi
    
    echo
    read -p "Proceed with this combined release? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        warn "Release cancelled by user"
        exit 0
    fi
    
    # Execute release
    if trigger_release "$version" "$release_type" "$skip_tests" "$release_notes"; then
        success "Combined release initiated successfully!"
        
        cat << EOF

${GREEN}🎉 Release v${version} is now in progress!${NC}

${BLUE}Next steps:${NC}
  • Monitor the workflow progress in GitHub Actions
  • Verify the release when complete:
    - Check PyPI: https://pypi.org/project/raft-toolkit/${version}/
    - Test CLI: docker run ghcr.io/${GITHUB_REPOSITORY:-owner/repo}:cli-v${version} --help
    - Test Web: docker run -p 8000:8000 ghcr.io/${GITHUB_REPOSITORY:-owner/repo}:web-v${version}
  • Update any dependent projects
  • Announce the release to stakeholders

${BLUE}Troubleshooting:${NC}
  If the release fails, check the workflow logs and:
  • Fix any issues and re-run
  • Use emergency rollback if needed
  • Contact the development team for assistance

Happy releasing! 🚀
EOF
    else
        error "Failed to initiate release"
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi