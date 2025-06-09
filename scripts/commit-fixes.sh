#!/bin/bash
# Script to commit and push the fixes for CI issues

set -e  # Exit on error

# Check that we're in the root directory of the repository
if [ ! -f "pyproject.toml" ]; then
    echo "Error: This script must be run from the root of the repository"
    exit 1
fi

# Ensure the commit message file exists
if [ ! -f "commit-message.txt" ]; then
    echo "Error: commit-message.txt not found"
    exit 1
fi

# Add all the modified files
git add .github/workflows/python-ci.yml
git add pyproject.toml
git add scripts/install_deps.sh
git add TROUBLESHOOTING.md
git add README.md
git add src/ast_grep_mcp/core/ast_grep_mcp.py
git add src/ast_grep_mcp/server.py
git add tests/test_core.py
git add tests/test_error_handling.py
git add tests/test_logging.py
git add tests/test_pattern_helpers.py
git add tests/test_server.py
git add tests/test_utils.py
git add integration_tests/__init__.py
git add integration_tests/client_test.py

# Commit with the prepared message
git commit -F commit-message.txt

# Push to the remote repository (can be enabled manually)
echo "Changes committed successfully!"
echo ""
echo "To push to the remote repository, run:"
echo "git push origin main" 