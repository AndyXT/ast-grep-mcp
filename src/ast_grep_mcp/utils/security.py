"""
Security utilities for the AST Grep MCP server.

This module provides security functions to prevent command injection and
ensure file access is restricted to approved directories.
"""

import re
import os
from pathlib import Path
from typing import List, Optional
import logging

# Initialize logger
logger = logging.getLogger("ast_grep_mcp.security")


def sanitize_pattern(pattern: str) -> str:
    """
    Sanitize a pattern to prevent command injection.

    Args:
        pattern: Pattern to sanitize

    Returns:
        Sanitized pattern
    """
    if not pattern:
        return ""

    # Make a copy of the original pattern for comparison
    original = pattern

    # Check for safe JavaScript template literals (common in patterns)
    js_template_pattern = re.compile(r"`(.*?\$\{.*?\}.*?)`")

    # Extract any template literals to protect them
    template_placeholders = {}
    template_count = 0

    def save_template(match):
        nonlocal template_count
        placeholder = f"__TEMPLATE_{template_count}__"
        template_placeholders[placeholder] = match.group(0)
        template_count += 1
        return placeholder

    # Save template literals
    if "`" in pattern and "${" in pattern:
        pattern = js_template_pattern.sub(save_template, pattern)

    # First, protect special operators like && and ||
    operator_placeholders = {}

    # Protect && operator
    if "&&" in pattern:
        pattern = pattern.replace("&&", "__AND_OP__")
        operator_placeholders["__AND_OP__"] = "&&"

    # Protect || operator
    if "||" in pattern:
        pattern = pattern.replace("||", "__OR_OP__")
        operator_placeholders["__OR_OP__"] = "||"

    # Protect bitwise OR patterns (x | y | z)
    bitwise_or_pattern = re.compile(r"\b\w+\s+\|\s+\w+(?:\s+\|\s+\w+)*\b")
    if re.search(bitwise_or_pattern, pattern):
        # Replace each match with a placeholder
        bitwise_matches = re.finditer(bitwise_or_pattern, pattern)
        for i, match in enumerate(bitwise_matches):
            placeholder = f"__BITWISE_OR_{i}__"
            operator_placeholders[placeholder] = match.group(0)
            pattern = pattern.replace(match.group(0), placeholder)

    # Protect patterns that look like security issues but are legitimate AST patterns
    ast_pattern_placeholders = {}

    # List of AST pattern keywords that might be mistaken for security issues
    ast_pattern_keywords = [
        r"eval\(\$[A-Za-z_]+\)",  # e.g., eval($EXPR)
        r"exec\(\$[A-Za-z_]+\)",  # e.g., exec($CODE)
        r"Function\(\$[A-Za-z_]+\)",  # e.g., Function($ARGS)
    ]

    # Replace these with placeholders
    for i, keyword in enumerate(ast_pattern_keywords):
        keyword_pattern = re.compile(keyword)
        for match in keyword_pattern.finditer(pattern):
            placeholder = f"__AST_PATTERN_{i}_{match.start()}__"
            ast_pattern_placeholders[placeholder] = match.group(0)
            pattern = pattern[: match.start()] + placeholder + pattern[match.end() :]

    # List of potentially dangerous patterns
    dangerous_patterns = [
        # Command injection - be more careful here
        # Don't remove single pipes as they might be part of AST patterns
        r";\s*(?:rm|del|format|shutdown|reboot)",  # Dangerous commands after semicolon
        r"&&\s*(?:rm|del|format|shutdown|reboot)",  # Dangerous commands after &&
        r"\|\s*(?:rm|del|format|shutdown|reboot)",  # Dangerous commands after pipe
        r"\$\([^)]*\)",  # Command substitution
        r"`[^`]*`",  # Backticks (except in JS templates)
        # Path traversal
        r"\.\./\.\.",
        r"/etc/passwd",
        r"/etc/shadow",
        # Encoded attack vectors
        r"%(?:2[6ef]|3[df]|5[bd]|6[0-9a-f]|7[0-9a-f])",
    ]

    # Remove or replace dangerous patterns
    for dp in dangerous_patterns:
        pattern = re.sub(dp, "", pattern)

    # Restore protected operators
    for placeholder, operator in operator_placeholders.items():
        pattern = pattern.replace(placeholder, operator)

    # Restore AST pattern keywords
    for placeholder, keyword in ast_pattern_placeholders.items():
        pattern = pattern.replace(placeholder, keyword)

    # Restore template literals
    for placeholder, template in template_placeholders.items():
        pattern = pattern.replace(placeholder, template)

    # Log if sanitization occurred
    if pattern != original:
        logger.warning(
            f"Potentially dangerous pattern detected and sanitized: {original[:50]} ->"
        )

    return pattern


def is_safe_path(path: str, safe_roots: Optional[List[str]] = None) -> bool:
    """
    Check if a path is safe to access.

    Args:
        path: Path to check
        safe_roots: List of safe roots. If None or empty, all paths are allowed.

    Returns:
        True if the path is safe, False otherwise
    """
    if not safe_roots:
        # If no safe roots specified, all paths are allowed
        return True

    # Normalize path
    normalized_path = os.path.normpath(os.path.abspath(path))

    # Convert to Path object for easier comparison
    path_obj = Path(normalized_path)

    # Check if the path is within any of the safe roots
    for root in safe_roots:
        normalized_root = os.path.normpath(os.path.abspath(root))
        root_obj = Path(normalized_root)

        try:
            # Check if the path is within the safe root
            # Use relative_to which raises an exception if path is not within root
            path_obj.relative_to(root_obj)
            return True
        except ValueError:
            continue

    return False


def validate_file_access(
    path: str, safe_roots: Optional[List[str]] = None
) -> Optional[str]:
    """
    Validate file access permissions.

    Args:
        path: Path to validate
        safe_roots: List of safe roots. If None, no restrictions are applied.

    Returns:
        Error message if access is not allowed, None otherwise
    """
    if not is_safe_path(path, safe_roots):
        if safe_roots:
            error_msg = f"Access to '{path}' is restricted. Allowed roots: {', '.join(safe_roots)}"
        else:
            error_msg = f"Access to '{path}' is restricted."
        logger.warning(error_msg)
        return error_msg

    # Check for path traversal attempts
    if ".." in path:
        path_obj = Path(path)
        absolute_path = path_obj.resolve()

        # If the resolved path is different from the constructed path
        # after normalization, it might be a path traversal attempt
        if os.path.normpath(path) != os.path.normpath(str(absolute_path)):
            error_msg = f"Possible path traversal attempt detected: {path}"
            logger.warning(error_msg)
            return error_msg

    return None
