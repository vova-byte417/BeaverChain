#!/bin/bash
# ============================================
# BeaverChain Auto-Commit Script
# Handles conventional commits and milestone tagging
# ============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Configuration
COMMIT_TYPES=("feat" "fix" "docs" "style" "refactor" "test" "chore" "perf" "ci")
SCOPES=("model-registry" "frontend" "prompt-engine" "guardrails" "workflow" "infra" "deps")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Help message
show_help() {
    cat << EOF
${BLUE}BeaverChain Auto-Commit Script${NC}

Usage: $(basename "$0") [OPTIONS] <type> <scope> <message>

Options:
  -m, --milestone    Mark this commit as a milestone (triggers minor version bump)
  -p, --patch        Trigger patch version bump
  -M, --major        Trigger major version bump
  -t, --tag          Create git tag after commit
  -h, --help         Show this help message

Commit Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation changes
  style:    Code style changes
  refactor: Code refactoring
  test:     Adding or updating tests
  chore:    Maintenance tasks
  perf:     Performance improvements
  ci:       CI/CD changes

Scopes:
  model-registry, frontend, prompt-engine, guardrails, workflow, infra, deps

Examples:
  $(basename "$0") feat frontend "Add model version comparison view"
  $(basename "$0") -m fix model-registry "Fix database connection leak"
  $(basename "$0") -t feat model-registry "v1.0.0 MVP release"
EOF
}

# Parse arguments
MILESTONE=false
TAG=false
BUMP_TYPE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--milestone)
            MILESTONE=true
            BUMP_TYPE="minor"
            shift
            ;;
        -p|--patch)
            BUMP_TYPE="patch"
            shift
            ;;
        -M|--major)
            BUMP_TYPE="major"
            shift
            ;;
        -t|--tag)
            TAG=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -lt 3 ]]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    show_help
    exit 1
fi

TYPE="$1"
SCOPE="$2"
MESSAGE="$3"

# Validate commit type
if [[ ! " ${COMMIT_TYPES[@]} " =~ " ${TYPE} " ]]; then
    echo -e "${RED}Error: Invalid commit type '$TYPE'${NC}"
    echo "Valid types: ${COMMIT_TYPES[*]}"
    exit 1
fi

# Validate scope
if [[ ! " ${SCOPES[@]} " =~ " ${SCOPE} " ]]; then
    echo -e "${YELLOW}Warning: Unknown scope '$SCOPE' - continuing anyway${NC}"
fi

# Build commit message
FULL_COMMIT_MSG="${TYPE}(${SCOPE}): ${MESSAGE}"

if [[ "$MILESTONE" == true ]]; then
    FULL_COMMIT_MSG="${FULL_COMMIT_MSG}

[MILESTONE] This commit marks a completed milestone."
fi

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}BeaverChain Auto-Commit${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "Commit message:"
echo -e "  ${GREEN}${FULL_COMMIT_MSG}${NC}"
echo ""

# Stage all changes
echo "Staging changes..."
git add -A

# Commit
echo "Creating commit..."
git commit -m "$FULL_COMMIT_MSG"
echo -e "${GREEN}Commit created successfully!${NC}"

# Handle version bump and tagging
if [[ -n "$BUMP_TYPE" ]] || [[ "$TAG" == true ]]; then
    echo ""
    echo "Bumping version..."
    
    # Get current version
    if [[ -f VERSION ]]; then
        CURRENT_VERSION=$(cat VERSION)
    else
        CURRENT_VERSION="0.0.0"
    fi
    
    # Split version
    IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
    
    # Determine bump type if not set
    if [[ -z "$BUMP_TYPE" ]]; then
        case "$TYPE" in
            feat) BUMP_TYPE="minor" ;;
            fix|perf) BUMP_TYPE="patch" ;;
            *) BUMP_TYPE="patch" ;;
        esac
    fi
    
    # Apply bump
    case "$BUMP_TYPE" in
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        patch)
            PATCH=$((PATCH + 1))
            ;;
    esac
    
    NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
    
    # Update VERSION file
    echo "$NEW_VERSION" > VERSION
    git add VERSION
    git commit --amend --no-edit
    
    echo -e "${GREEN}Version bumped: ${CURRENT_VERSION} -> ${NEW_VERSION}${NC}"
    
    # Create tag
    if [[ "$TAG" == true ]] || [[ "$MILESTONE" == true ]]; then
        echo ""
        echo "Creating git tag v${NEW_VERSION}..."
        git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}: ${MESSAGE}"
        echo -e "${GREEN}Tag v${NEW_VERSION} created successfully!${NC}"
    fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Auto-commit completed successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "To push changes and tags:"
echo "  git push && git push --tags"
