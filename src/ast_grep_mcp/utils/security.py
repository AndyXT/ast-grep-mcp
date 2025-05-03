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
    Sanitize ast-grep pattern to prevent command injection.
    
    This function removes potentially dangerous shell constructs that could
    be used for command injection or other security exploits.
    
    Args:
        pattern: The pattern string to sanitize
        
    Returns:
        Sanitized pattern string
    """
    if not pattern:
        return ""
    
    # Keep a copy of the original pattern for comparison
    original_pattern = pattern
    
    # Remove the most dangerous shell constructs
    
    # Remove backticks (command execution)
    pattern = re.sub(r'`[^`]*`', '', pattern)
    
    # Remove command substitution
    pattern = re.sub(r'\$\([^)]*\)', '', pattern)
    
    # If the pattern was modified, log a warning
    if pattern != original_pattern:
        logger.warning(f"Potentially dangerous pattern detected and sanitized: {original_pattern} -> {pattern}")
    
    return pattern

def is_safe_path(path: str, safe_roots: List[str] = None) -> bool:
    """
    Check if a file path is inside a list of safe root directories.
    
    This function helps prevent directory traversal attacks by ensuring
    file access is restricted to approved directories.
    
    Args:
        path: Path to check
        safe_roots: List of approved root directories. If None or empty,
                   no restrictions are applied.
                   
    Returns:
        True if the path is safe, False otherwise
    """
    if not safe_roots:
        # If no safe roots are specified, consider it safe (but log a warning)
        logger.warning("No safe roots specified, allowing access to: " + path)
        return True
    
    try:
        # Resolve to absolute path, resolving any symlinks
        abs_path = Path(os.path.abspath(path)).resolve()
        
        # Check if the path is within any of the safe roots
        for root in safe_roots:
            # Resolve the safe root as well
            safe_root = Path(os.path.abspath(root)).resolve()
            
            # Check if the path is inside the safe root
            if str(abs_path).startswith(str(safe_root)):
                return True
        
        # If we get here, path is outside all safe roots
        logger.warning(f"Attempted access to path outside safe roots: {path}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking path safety: {str(e)}")
        return False

def validate_file_access(file_path: str, safe_roots: List[str] = None) -> Optional[str]:
    """
    Validate file access and return an error message if access is denied.
    
    Args:
        file_path: Path to validate
        safe_roots: List of approved root directories
        
    Returns:
        Error message if access is denied, None if access is allowed
    """
    if not is_safe_path(file_path, safe_roots):
        error_msg = f"Access denied: {file_path} is outside of approved directories"
        logger.warning(error_msg)
        return error_msg
    
    return None 