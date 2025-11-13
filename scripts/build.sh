#!/bin/bash
# Build wheel and source distribution for GAO-Dev
#
# Usage: ./scripts/build.sh

set -e

echo "🏗️  Building GAO-Dev package..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info

# Install build dependencies
echo "Installing build dependencies..."
pip install --upgrade pip build setuptools-scm

# Build package
echo "Building package..."
python -m build

# List built artifacts
echo ""
echo "✅ Build complete! Artifacts:"
ls -lh dist/

echo ""
echo "Package contents:"
WHEEL=$(ls dist/*.whl | head -1)
python -m zipfile -l "$WHEEL" | head -20

# Validate wheel
echo ""
echo "Validating wheel..."
pip install --upgrade twine
twine check dist/*

echo ""
echo "✅ Build validation passed!"
echo ""
echo "To install locally:"
echo "  pip install $WHEEL"
