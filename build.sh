#!/bin/bash
# Build script for core-open-ssa package

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Building core-open-ssa ==="

# Clean previous builds (ignore errors for permission issues)
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info 2>/dev/null || true

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Resolve the venv python/pip across Windows (Scripts) and POSIX (bin) layouts
if [ -x ".venv/Scripts/python.exe" ]; then
    VENV_PY=".venv/Scripts/python.exe"
else
    VENV_PY=".venv/bin/python"
fi

# Install build tool
echo "Installing build tool..."
"$VENV_PY" -m pip install --upgrade pip build -q

# Build the package
echo "Building package..."
"$VENV_PY" -m build

echo ""
echo "=== Build complete ==="
echo "Output files:"
ls -la dist/

echo ""
echo "To install locally:"
echo "  pip install dist/core_open_ssa-*.whl"
echo ""
echo "To install in another project:"
echo "  pip install /path/to/core-open-ssa/dist/core_open_ssa-*.whl"
