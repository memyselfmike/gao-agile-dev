#!/bin/bash
# Install GAO-Dev locally for testing
#
# Usage: ./scripts/install_local.sh

set -e

echo "📦 Installing GAO-Dev locally..."
echo ""

# Build package
./scripts/build.sh

echo ""
echo "Installing package..."

# Uninstall existing
echo "Uninstalling existing GAO-Dev..."
pip uninstall -y gao-dev 2>/dev/null || true

# Install from wheel
echo "Installing from wheel..."
WHEEL=$(ls dist/*.whl | head -1)
pip install "$WHEEL"

# Verify installation
echo ""
echo "Verifying installation..."
gao-dev --version

echo ""
echo "✅ Local installation complete!"
echo ""
echo "Test with:"
echo "  cd /path/to/test-project"
echo "  gao-dev start"
