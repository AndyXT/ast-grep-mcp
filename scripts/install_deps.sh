#!/bin/bash
# Helper script to install dependencies cleanly, especially ast-grep-py

set -e  # Exit on error

# Check if we have a virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# Clear caches
echo "Clearing caches..."
rm -rf ~/.cache/pip ~/.cache/uv

# Install ast-grep-py first
echo "Installing ast-grep-py 0.37.0..."
uv pip install ast-grep-py==0.37.0 --verbose

# Install the rest of the dependencies
echo "Installing remaining dependencies..."
uv sync --dev

# Verify installation
echo "Verifying ast-grep-py installation..."
python -c "from ast_grep_py import SgRoot; print('✓ Successfully imported SgRoot')"

echo "✅ All dependencies installed successfully!" 