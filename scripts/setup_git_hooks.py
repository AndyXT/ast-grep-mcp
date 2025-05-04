#!/usr/bin/env python3
"""
Script to set up Git pre-commit hooks for AST-Grep analysis.
"""

import os
import sys
import stat
from pathlib import Path

# Path to the Git hooks directory
HOOKS_DIR = '.git/hooks'

# Pre-commit hook content - use raw string to avoid escape sequence issues
PRE_COMMIT_HOOK = r'''#!/bin/sh
# AST-Grep pre-commit hook
# Analyzes changed Python files using AST-Grep patterns

# Get all staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    echo "No Python files to check."
    exit 0
fi

# Run AST-Grep analysis on staged files
echo "Running AST-Grep analysis on staged files..."
python -m ast_grep_mcp.analyze_codebase --files $STAGED_FILES --pattern-file ast-grep-patterns.yml

# Check if the analysis found critical issues
if [ $? -ne 0 ]; then
    echo "AST-Grep found critical issues in your code."
    echo "Please fix these issues before committing."
    exit 1
fi

echo "AST-Grep analysis passed."
exit 0
'''

def setup_git_hooks():
    """Set up Git pre-commit hooks for AST-Grep."""
    # Check if the .git directory exists
    if not os.path.isdir('.git'):
        print("Error: Not a Git repository. Please run this script from the repository root.")
        return False
    
    # Create hooks directory if it doesn't exist
    hooks_dir = Path(HOOKS_DIR)
    hooks_dir.mkdir(exist_ok=True)
    
    # Write pre-commit hook
    pre_commit_path = hooks_dir / 'pre-commit'
    with open(pre_commit_path, 'w') as f:
        f.write(PRE_COMMIT_HOOK)
    
    # Make the hook executable
    os.chmod(pre_commit_path, os.stat(pre_commit_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    print(f"Git pre-commit hook installed at {pre_commit_path}")
    print("The hook will check your Python files for code smells and anti-patterns before each commit.")
    
    return True

if __name__ == "__main__":
    if not setup_git_hooks():
        sys.exit(1) 