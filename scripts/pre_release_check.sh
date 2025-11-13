#!/bin/bash
# Pre-release validation checks
#
# Usage: ./scripts/pre_release_check.sh

set -e

echo "🔍 Running pre-release checks..."
echo ""

# Check 1: All tests pass
echo "✓ Running test suite..."
pytest --cov=gao_dev --cov-report=term-missing -v
echo ""

# Check 2: No type errors
echo "✓ Type checking..."
mypy gao_dev --strict
echo ""

# Check 3: Code formatting
echo "✓ Checking code format..."
black --check .
ruff check .
echo ""

# Check 4: No uncommitted changes
echo "✓ Checking git status..."
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ Uncommitted changes detected!"
    git status --short
    exit 1
fi
echo "  Clean working tree"
echo ""

# Check 5: On main branch
echo "✓ Checking current branch..."
BRANCH=$(git branch --show-current)
if [[ "$BRANCH" != "main" ]]; then
    echo "❌ Not on main branch! Currently on: $BRANCH"
    exit 1
fi
echo "  On main branch"
echo ""

# Check 6: Up to date with origin
echo "✓ Checking sync with origin..."
git fetch origin
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
if [[ "$LOCAL" != "$REMOTE" ]]; then
    echo "❌ Local branch is not up to date with origin!"
    echo "  Run: git pull origin main"
    exit 1
fi
echo "  Synced with origin/main"
echo ""

# Check 7: All dependencies installable
echo "✓ Checking dependencies..."
pip check
echo ""

echo "✅ All pre-release checks passed!"
echo ""
echo "Ready to release!"
