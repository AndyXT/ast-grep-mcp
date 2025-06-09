"""
Server module for the ast-grep-mcp package.

This module maintains backward compatibility with the previous functional API.
"""

from fastmcp import FastMCP
from .ast_analyzer import AstAnalyzer
from typing import Dict, Any, Optional
from .core import AstGrepMCP, ServerConfig

# Initialize the analyzer
analyzer = AstAnalyzer()

# Create an MCP server
mcp = FastMCP("AstGrepCodeAnalyzer")


# Singleton class for AstGrepMCP to replace global variable
class AstGrepMCPSingleton:
    _instance: Optional[AstGrepMCP] = None

    @classmethod
    def get_instance(cls) -> AstGrepMCP:
        """Get the singleton instance of AstGrepMCP."""
        if cls._instance is None:
            cls._instance = AstGrepMCP()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None


def _get_ast_grep_mcp() -> AstGrepMCP:
    """Get the singleton instance of AstGrepMCP."""
    return AstGrepMCPSingleton.get_instance()


@mcp.tool()
def analyze_code(code: str, language: str, pattern: str) -> Dict[str, Any]:
    """
    Analyze code using ast-grep pattern matching

    Args:
        code: Source code to analyze
        language: Programming language (python, javascript, lua, c, rust, go, etc.)
        pattern: Pattern to search for in the code

    Returns:
        Dictionary with pattern matches and their locations
    """
    # Delegate to the AstGrepMCP instance
    return _get_ast_grep_mcp().analyze_code(code, language, pattern)


@mcp.tool()
def refactor_code(
    code: str, language: str, pattern: str, replacement: str
) -> Dict[str, Any]:
    """
    Refactor code by replacing pattern matches with a replacement

    Args:
        code: Source code to refactor
        language: Programming language (python, javascript, lua, c, rust, go, etc.)
        pattern: Pattern to search for in the code
        replacement: Replacement code

    Returns:
        Dictionary with refactored code and statistics
    """
    # Delegate to the AstGrepMCP instance
    return _get_ast_grep_mcp().refactor_code(code, language, pattern, replacement)


@mcp.tool()
def analyze_file(file_path: str, pattern: str) -> Dict[str, Any]:
    """
    Analyze a file using ast-grep pattern matching

    Args:
        file_path: Path to the file to analyze
        pattern: Pattern to search for in the file

    Returns:
        Dictionary with pattern matches and their locations
    """
    # Delegate to the AstGrepMCP instance
    return _get_ast_grep_mcp().analyze_file(file_path, pattern)


@mcp.tool()
def get_language_patterns(language: str) -> Dict[str, Any]:
    """
    Get common pattern templates for a specific language

    Args:
        language: Programming language (python, javascript, etc.)

    Returns:
        Dictionary with pattern templates for the language
    """
    # Delegate to the AstGrepMCP instance
    return _get_ast_grep_mcp().get_language_patterns(language)


@mcp.tool()
def get_supported_languages() -> Dict[str, Any]:
    """
    Get a list of supported languages and their file extensions

    Returns:
        Dictionary with supported languages and their file extensions
    """
    # Delegate to the AstGrepMCP instance
    return _get_ast_grep_mcp().get_supported_languages()


def run_server(host: str = "localhost", port: int = 8080):
    """Run the MCP server"""
    # Create a configuration with the provided host and port
    config = ServerConfig(host=host, port=port)

    # Create an instance with this configuration and start it
    instance = AstGrepMCP(config)
    instance.start()
