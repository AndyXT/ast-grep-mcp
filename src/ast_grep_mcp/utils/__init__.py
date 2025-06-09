"""
Utility modules for ast-grep-mcp.

This package contains various utility functions and classes
used throughout the ast-grep-mcp codebase.
"""

from .error_handling import handle_errors
from .result_cache import cached, result_cache
from .security import sanitize_pattern, validate_file_access, is_safe_path
from .pattern_diagnostics import create_enhanced_diagnostic, PatternAnalyzer

__all__ = [
    "handle_errors",
    "cached",
    "result_cache",
    "sanitize_pattern",
    "validate_file_access",
    "is_safe_path",
    "create_enhanced_diagnostic",
    "PatternAnalyzer",
]
