#!/usr/bin/env bash
# Workspace Cleanup Script for Unix/Linux/macOS
# Removes test artifacts, corrupt directories, and temporary files
# Run this before creating a release or committing changes

set -e  # Exit on error

echo "================================================================================"
echo "GAO-Dev Workspace Cleanup"
echo "================================================================================"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

echo "[1/6] Removing corrupt directories..."
rm -rf "C:Projectsgao-agile-devtestsunitcore" 2>/dev/null || true
rm -rf "C:Testingscripts" 2>/dev/null || true
rm -rf "C:Usersmikejgao-final-test" 2>/dev/null || true
rm -rf "Projectsgao-agile-devgao_devwebfrontend" 2>/dev/null || true
rm -rf "Testingvenv-beta" 2>/dev/null || true
rm -rf -- "-p" 2>/dev/null || true
echo "   - Done"

echo "[2/6] Removing test artifacts..."
rm -f gao_dev.db 2>/dev/null || true
rm -f server_output.log 2>/dev/null || true
rm -f nul 2>/dev/null || true
rm -f test_output.log 2>/dev/null || true
rm -f test_output.txt 2>/dev/null || true
rm -f =*.*.* 2>/dev/null || true
echo "   - Done"

echo "[3/6] Removing Playwright artifacts..."
rm -rf .playwright-mcp 2>/dev/null || true
# Remove PNG files except in docs/screenshots
find . -name "*.png" -not -path "*/docs/*" -not -path "*/screenshots/*" -delete 2>/dev/null || true
echo "   - Done"

echo "[4/6] Removing frontend build cache..."
rm -rf gao_dev/web/frontend/.vite 2>/dev/null || true
echo "   - Done"

echo "[5/6] Removing coverage reports..."
rm -f .coverage 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true
echo "   - Done"

echo "[6/6] Removing test transcripts..."
rm -rf .gao-dev/test_transcripts 2>/dev/null || true
rm -rf tests/e2e/debug_reports 2>/dev/null || true
echo "   - Done"

echo ""
echo "================================================================================"
echo "Cleanup Complete!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Run: git status"
echo "  2. Review changes"
echo "  3. Commit clean workspace"
echo ""
