#!/usr/bin/env python3
"""
Script to set up Git pre-commit hooks for AST-Grep analysis.
"""

import os
import sys
import stat
from pathlib import Path

# Path to the Git hooks directory
HOOKS_DIR = ".git/hooks"

# Pre-commit hook content - use raw string to avoid escape sequence issues
PRE_COMMIT_HOOK = r"""#!/bin/sh
# AST-Grep pre-commit hook
# Analyzes changed Python files using AST-Grep patterns

# Get all staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    echo "No Python files to check."
    exit 0
fi

# Create temporary directory for analysis
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Create temporary output file
TEMP_OUTPUT=$(mktemp)
echo "Created temporary output file: $TEMP_OUTPUT"

# Set up a cleanup function to remove temp directory on exit
cleanup() {
    echo "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    rm -f "$TEMP_OUTPUT"
}
trap cleanup EXIT

# Copy the staged files to the temporary directory
echo "Copying staged files to temporary directory..."
for file in $STAGED_FILES; do
    # Skip analyze_codebase.py file
    if [ "$(basename "$file")" = "analyze_codebase.py" ]; then
        echo "Skipping analysis of analyze_codebase.py"
        continue
    fi
    
    # Create parent directories if needed
    mkdir -p "$TEMP_DIR/$(dirname "$file")"
    # Copy the file
    git show ":$file" > "$TEMP_DIR/$file"
done

# Check if the temp directory contains any Python files
PYTHON_FILES=$(find "$TEMP_DIR" -name "*.py")
if [ -z "$PYTHON_FILES" ]; then
    echo "No Python files to check after excluding analyze_codebase.py."
    exit 0
fi

# Run AST-Grep analysis on staged files using the temporary directory
echo "Running AST-Grep analysis on staged files..."
uv run python analyze_codebase.py --directory "$TEMP_DIR" --output "$TEMP_OUTPUT"

# Check for only certain critical issues
echo "Checking for critical issues..."
uv run python - "$TEMP_OUTPUT" << 'EOF'
import json
import sys

# Load analysis results
with open(sys.argv[1], 'r') as f:
    results = json.load(f)

# Only check for certain critical issues
critical_patterns = [
    "global_variable",      # Block global variables
    "nested_loops"         # Block nested loops
]

critical_issues = [r for r in results if r.get('pattern_name') in critical_patterns]

if critical_issues:
    print(f"Found {len(critical_issues)} critical issues that should be fixed:")
    for issue in critical_issues:
        print(f"- {issue['file']}:{issue['line']} - {issue['pattern_name']}: {issue['text']}")
    sys.exit(1)
else:
    # No critical issues found
    print("No critical issues found in this commit. Other issues can be fixed later.")
    sys.exit(0)
EOF

# Use the exit code from the Python script
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Please fix these issues before committing."
    exit 1
fi

echo "AST-Grep analysis passed."
exit 0
"""


def setup_git_hooks():
    """Set up Git pre-commit hooks for AST-Grep."""
    # Check if the .git directory exists
    if not os.path.isdir(".git"):
        print(
            "Error: Not a Git repository. Please run this script from the repository root."
        )
        return False

    # Create hooks directory if it doesn't exist
    hooks_dir = Path(HOOKS_DIR)
    hooks_dir.mkdir(exist_ok=True)

    # Write pre-commit hook
    pre_commit_path = hooks_dir / "pre-commit"
    with open(pre_commit_path, "w") as f:
        f.write(PRE_COMMIT_HOOK)

    # Make the hook executable
    os.chmod(
        pre_commit_path,
        os.stat(pre_commit_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
    )

    print(f"Git pre-commit hook installed at {pre_commit_path}")
    print(
        "The hook will check your Python files for critical code smells before each commit."
    )

    return True


if __name__ == "__main__":
    if not setup_git_hooks():
        sys.exit(1)
