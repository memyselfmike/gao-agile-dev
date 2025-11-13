#!/bin/bash
# GAO-Dev Start Script
# This script ensures the environment is set up and launches gao-dev

set -e

echo ""
echo "========================================"
echo "GAO-Dev Startup"
echo "========================================"
echo ""

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "[ERROR] Not in gao-agile-dev project root!"
    echo "Please cd to the project directory first."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv is not installed!"
    echo ""
    echo "Install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

echo "[OK] Found uv"
echo ""

# Check if .venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "[INFO] Virtual environment not found, creating..."
    uv venv
    echo "[OK] Virtual environment created"
    echo ""
fi

# Sync dependencies if needed
echo "[INFO] Syncing dependencies..."
uv sync
echo "[OK] Dependencies synced"
echo ""

# Install package in editable mode
echo "[INFO] Installing gao-dev..."
uv pip install -e .
echo "[OK] gao-dev installed"
echo ""

# Activate the virtual environment
echo "[INFO] Activating virtual environment..."
source .venv/bin/activate

# Verify installation
if ! command -v gao-dev &> /dev/null; then
    echo "[WARNING] gao-dev command not available yet"
    echo "Using: python -m gao_dev.cli.commands"
    echo ""
fi

# Show version
echo "========================================"
echo "Environment Ready!"
echo "========================================"
echo ""
python -m gao_dev.cli.commands version 2>/dev/null || echo "GAO-Dev installed"
echo ""

# Check for command line arguments
if [ $# -eq 0 ]; then
    # No arguments, start interactive chat
    echo "Starting interactive chat..."
    echo "To run a specific command, use: ./start.sh <command>"
    echo "Example: ./start.sh --help"
    echo ""
    python -m gao_dev.cli.commands start
else
    # Run with provided arguments
    python -m gao_dev.cli.commands "$@"
fi
