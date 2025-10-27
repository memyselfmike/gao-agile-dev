#!/bin/bash
# GAO-Dev Setup Script for Unix/Linux/Mac
# This script sets up the GAO-Dev development environment using uv

set -e

echo ""
echo "========================================"
echo "GAO-Dev Environment Setup"
echo "========================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv is not installed!"
    echo ""
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "[OK] Found uv"
echo ""

# Sync dependencies
echo "[1/3] Syncing dependencies..."
uv sync
echo "[OK] Dependencies synced"
echo ""

# Install package in development mode
echo "[2/3] Installing gao-dev in development mode..."
uv pip install -e .
echo "[OK] gao-dev installed"
echo ""

# Run version check
echo "[3/3] Running version check..."
uv run gao-dev version
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Activate the environment: source .venv/bin/activate"
echo "  2. Run: gao-dev --help"
echo "  3. Initialize a project: gao-dev init --name 'My Project'"
echo ""
