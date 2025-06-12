#!/bin/bash

# Create Release Script
# This script helps create a new release by creating and pushing a git tag
# which will trigger the release workflow.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if git is clean
check_git_clean() {
    if [[ -n $(git status --porcelain) ]]; then
        print_color $RED "Error: Git working directory is not clean. Please commit or stash changes."
        git status --short
        exit 1
    fi
}

# Function to check if on main branch
check_main_branch() {
    local current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]]; then
        print_color $YELLOW "Warning: You are not on the main branch. Current branch: $current_branch"
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to get the latest tag
get_latest_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0"
}

# Function to increment version
increment_version() {
    local version=$1
    local increment_type=$2
    
    # Remove 'v' prefix if present
    version=${version#v}
    
    # Split version into parts
    IFS='.' read -ra PARTS <<< "$version"
    local major=${PARTS[0]:-0}
    local minor=${PARTS[1]:-0}
    local patch=${PARTS[2]:-0}
    
    case $increment_type in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            print_color $RED "Invalid increment type: $increment_type"
            exit 1
            ;;
    esac
    
    echo "v$major.$minor.$patch"
}

# Function to create and push tag
create_tag() {
    local tag=$1
    
    print_color $BLUE "Creating tag: $tag"
    git tag -a "$tag" -m "Release $tag"
    
    print_color $BLUE "Pushing tag to origin..."
    git push origin "$tag"
    
    print_color $GREEN "✅ Tag $tag created and pushed successfully!"
    print_color $YELLOW "The release workflow will now be triggered automatically."
    print_color $YELLOW "Monitor the progress at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
}

# Main function
main() {
    print_color $BLUE "🚀 RAFT Toolkit Release Creator"
    echo
    
    # Check prerequisites
    print_color $YELLOW "Checking prerequisites..."
    check_git_clean
    check_main_branch
    
    # Pull latest changes
    print_color $YELLOW "Pulling latest changes..."
    git pull origin main
    
    # Get current version
    local current_tag=$(get_latest_tag)
    print_color $BLUE "Current version: $current_tag"
    
    # Ask for increment type
    echo
    print_color $YELLOW "Select version increment type:"
    echo "1) Patch (bug fixes): ${current_tag} -> $(increment_version $current_tag patch)"
    echo "2) Minor (new features): ${current_tag} -> $(increment_version $current_tag minor)"
    echo "3) Major (breaking changes): ${current_tag} -> $(increment_version $current_tag major)"
    echo "4) Custom version"
    echo "5) Cancel"
    echo
    
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            new_tag=$(increment_version $current_tag patch)
            ;;
        2)
            new_tag=$(increment_version $current_tag minor)
            ;;
        3)
            new_tag=$(increment_version $current_tag major)
            ;;
        4)
            read -p "Enter custom version (e.g., v1.2.3): " custom_version
            if [[ ! $custom_version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                print_color $RED "Invalid version format. Use format: vX.Y.Z"
                exit 1
            fi
            new_tag=$custom_version
            ;;
        5)
            print_color $YELLOW "Release cancelled."
            exit 0
            ;;
        *)
            print_color $RED "Invalid choice."
            exit 1
            ;;
    esac
    
    # Confirm the release
    echo
    print_color $YELLOW "About to create release: $new_tag"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_color $YELLOW "Release cancelled."
        exit 0
    fi
    
    # Create the tag
    create_tag $new_tag
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi