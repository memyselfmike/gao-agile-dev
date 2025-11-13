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

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment..."
    uv venv
    echo "[OK] Virtual environment created"
    echo ""
else
    echo "[1/4] Virtual environment already exists"
    echo ""
fi

# Sync dependencies
echo "[2/4] Syncing dependencies..."
uv sync
echo "[OK] Dependencies synced"
echo ""

# Install package in development mode
echo "[3/4] Installing gao-dev in development mode..."
uv pip install -e .
echo "[OK] gao-dev installed"
echo ""

# Run version check
echo "[4/4] Running version check..."
source .venv/bin/activate
python -m gao_dev.cli.commands version
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
