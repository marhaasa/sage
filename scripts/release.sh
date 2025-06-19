#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if version type argument is provided
if [ -z "$1" ]; then
  print_error "Please provide a version type: patch, minor, or major"
  print_info "Usage: ./scripts/release.sh [patch|minor|major]"
  exit 1
fi

VERSION_TYPE=$1

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(patch|minor|major)$ ]]; then
  print_error "Version type must be one of: patch, minor, major"
  exit 1
fi

print_info "Preparing to release $VERSION_TYPE version"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
  print_error "You must be on the main branch to create a release"
  print_info "Current branch: $CURRENT_BRANCH"
  exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
  print_error "You have uncommitted changes. Please commit or stash them first."
  exit 1
fi

# Pull latest changes
print_info "Pulling latest changes from origin..."
git pull origin main

# Update version in pyproject.toml
print_info "Updating version in pyproject.toml..."
poetry version $VERSION_TYPE

# Get the new version for display and further use
NEW_VERSION=$(poetry version --short)

# Update version in __init__.py
print_info "Updating version in src/__init__.py..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i "" "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/__init__.py
else
  sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/__init__.py
fi

# Build the package to ensure it builds correctly
print_info "Testing build..."
poetry build

# Clean up test build
rm -rf dist/

# Update CHANGELOG.md (create if it doesn't exist)
if [ ! -f "CHANGELOG.md" ]; then
  print_info "Creating CHANGELOG.md..."
  cat >CHANGELOG.md <<EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

EOF
fi

print_info "Updating CHANGELOG..."
echo ""
echo "What changes should be included in this release?"
echo "Enter changelog entries (one per line). Type 'done' when finished:"
echo ""

# Read changelog entries from user
CHANGELOG_ENTRIES=""
while true; do
  read -r line
  if [ "$line" = "done" ] || [ -z "$line" ]; then
    break
  fi
  CHANGELOG_ENTRIES="${CHANGELOG_ENTRIES}- ${line}\n"
done

if [ -n "$CHANGELOG_ENTRIES" ]; then
  # Get current date
  CURRENT_DATE=$(date +"%Y-%m-%d")

  # Capitalize version type
  if [ "$VERSION_TYPE" = "patch" ]; then
    SECTION="### Fixed"
  elif [ "$VERSION_TYPE" = "minor" ]; then
    SECTION="### Added"
  elif [ "$VERSION_TYPE" = "major" ]; then
    SECTION="### Changed"
  fi

  # Create temporary file with complete new entry
  cat >/tmp/changelog_entry <<EOF

## [$NEW_VERSION] - $CURRENT_DATE

$SECTION
EOF
  echo -e "$CHANGELOG_ENTRIES" >>/tmp/changelog_entry

  # Find the line number of [Unreleased] and insert after it
  UNRELEASED_LINE=$(grep -n "\[Unreleased\]" CHANGELOG.md | cut -d: -f1)
  if [ -n "$UNRELEASED_LINE" ]; then
    # Insert after the Unreleased section (usually line 7)
    INSERT_LINE=$((UNRELEASED_LINE + 2))
    head -n $INSERT_LINE CHANGELOG.md >/tmp/changelog_new
    cat /tmp/changelog_entry >>/tmp/changelog_new
    tail -n +$((INSERT_LINE + 1)) CHANGELOG.md >>/tmp/changelog_new
    mv /tmp/changelog_new CHANGELOG.md
  else
    # Fallback: append to end
    cat /tmp/changelog_entry >>CHANGELOG.md
  fi

  # Clean up temp files
  rm -f /tmp/changelog_entry

  print_info "CHANGELOG.md updated"
else
  print_warning "No changelog entries provided, skipping CHANGELOG update"
fi

# Commit version changes
print_info "Committing version changes..."
if [ -n "$CHANGELOG_ENTRIES" ]; then
  git add pyproject.toml src/__init__.py CHANGELOG.md
else
  git add pyproject.toml src/__init__.py
fi
git commit -m "Bump version to $NEW_VERSION"

# Push changes
print_info "Pushing changes to origin..."
git push origin main

# Create and push tag
print_info "Creating and pushing tag v$NEW_VERSION..."
git tag -a "v$NEW_VERSION" -m "Release version $NEW_VERSION"
git push origin "v$NEW_VERSION"

print_info "🎉 Release process completed!"
print_info "Released version: v$NEW_VERSION"
print_info ""
print_info "The GitHub Action will now:"
print_info "  1. Create a GitHub release"
print_info "  2. Build and upload Python packages"
print_info "  3. Update your homebrew tap automatically"
print_info ""
print_info "You can monitor the progress at:"
print_info "https://github.com/marhaasa/sage/actions"
print_info ""
print_info "Once complete, users can install with:"
print_info "  brew tap marhaasa/tools"
print_info "  brew install marhaasa/tools/sage"
