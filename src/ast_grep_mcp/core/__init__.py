"""
Core module for the ast-grep-mcp package.

This module contains the core functionality for the ast-grep MCP server.
"""

from .config import ServerConfig
from .ast_grep_mcp import AstGrepMCP

__all__ = ["ServerConfig", "AstGrepMCP"] 