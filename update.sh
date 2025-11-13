#!/bin/bash
# GAO-Dev Update Script for Unix/Linux/Mac
# This script updates GAO-Dev to the latest version from the repository

set -e  # Exit on error (except where explicitly handled)

echo ""
echo "========================================"
echo "GAO-Dev Update Script"
echo "========================================"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "[ERROR] Not in a git repository!"
    echo "Please run this script from the gao-agile-dev directory."
    exit 1
fi

echo "[OK] Git repository detected"
echo ""

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "[WARNING] You have uncommitted changes!"
    echo ""
    echo "Your changes:"
    git status --short
    echo ""
    read -p "Continue with update? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled."
        exit 1
    fi
fi

# Check if uv is installed
USE_UV=1
if ! command -v uv &> /dev/null; then
    echo "[WARNING] uv is not installed!"
    echo "Falling back to pip for dependency updates."
    USE_UV=0
else
    echo "[OK] Found uv"
fi
echo ""

# Show current version
echo "Current version:"
python -m gao_dev.cli.commands version 2>/dev/null || true
echo ""

# Step 1: Pull latest changes
echo "[1/5] Pulling latest changes from GitHub..."
if ! git pull origin main; then
    echo "[ERROR] Failed to pull changes from GitHub"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check your internet connection"
    echo "  - Ensure you have access to the repository"
    echo "  - Try: git fetch origin, then git pull origin main"
    exit 1
fi
echo "[OK] Changes pulled successfully"
echo ""

# Step 2: Update dependencies
echo "[2/5] Updating dependencies..."
if [ $USE_UV -eq 1 ]; then
    if ! uv sync; then
        echo "[ERROR] Failed to sync dependencies with uv"
        exit 1
    fi
    if ! uv pip install -e .; then
        echo "[ERROR] Failed to install gao-dev"
        exit 1
    fi
else
    if ! pip install -e ".[dev]" --upgrade; then
        echo "[ERROR] Failed to update dependencies with pip"
        exit 1
    fi
fi
echo "[OK] Dependencies updated"
echo ""

# Step 3: Run database migrations
echo "[3/5] Running database migrations..."
python -m gao_dev.cli.commands db status || true
echo ""
if ! python -m gao_dev.cli.commands db migrate; then
    echo "[WARNING] Database migrations had issues"
    echo "Run 'gao-dev db status' to check migration status"
else
    echo "[OK] Migrations completed"
fi
echo ""

# Step 4: Check consistency
echo "[4/5] Checking file-database consistency..."
if ! python -m gao_dev.cli.commands migrate consistency-check; then
    echo "[WARNING] Consistency issues found"
    echo "Run 'gao-dev migrate consistency-repair' to fix them"
else
    echo "[OK] Consistency check passed"
fi
echo ""

# Step 5: Verify installation
echo "[5/5] Verifying installation..."
if ! python -m gao_dev.cli.commands version; then
    echo "[ERROR] Installation verification failed"
    exit 1
fi
echo ""

echo "========================================"
echo "Update Complete!"
echo "========================================"
echo ""
echo "New version:"
python -m gao_dev.cli.commands version 2>/dev/null || true
echo ""
echo "Next steps:"
echo "  1. Review CHANGELOG.md for changes"
echo "  2. Run: gao-dev health"
echo "  3. Test your workflows"
echo ""
echo "If you encounter issues:"
echo "  - See UPDATE.md for troubleshooting"
echo "  - Report bugs: https://github.com/memyselfmike/gao-agile-dev/issues"
echo ""
