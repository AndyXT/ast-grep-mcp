"""
Core AstGrepMCP class that encapsulates the MCP server functionality.
"""

from fastmcp import FastMCP
from ..ast_analyzer import AstAnalyzer
from ..language_handlers import get_handler
from ..utils import handle_errors, cached, result_cache
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
import logging
import time
from .config import ServerConfig


class AstGrepMCP:
    """
    Core class for the AST Grep MCP server.
    
    This class encapsulates the MCP server functionality and provides methods for
    registering and running the server.
    """
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """
        Initialize the AstGrepMCP server.
        
        Args:
            config: Server configuration. If None, default configuration is used.
        """
        self.config = config or ServerConfig()
        self.analyzer = AstAnalyzer()
        self.mcp = FastMCP("AstGrepCodeAnalyzer")
        self.logger = self._setup_logger()
        
        # Set cache size from config if available
        if hasattr(self.config, 'cache_size') and self.config.cache_size is not None:
            result_cache.maxsize = self.config.cache_size
            self.logger.info(f"Setting result cache size to {result_cache.maxsize}")
        
        # Register all tools
        self._register_tools()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger for the MCP server."""
        return self.config.setup_logging("ast_grep_mcp")
    
    def _register_tools(self) -> None:
        """Register all available tools with the MCP server."""
        # Use decorators to register tools
        self.analyze_code = self.mcp.tool()(self.analyze_code)
        self.refactor_code = self.mcp.tool()(self.refactor_code)
        self.analyze_file = self.mcp.tool()(self.analyze_file)
        self.search_directory = self.mcp.tool()(self.search_directory)
        self.get_language_patterns = self.mcp.tool()(self.get_language_patterns)
        self.get_supported_languages = self.mcp.tool()(self.get_supported_languages)
        
        # Log registration - updated number of tools
        self.logger.info("Registered 6 tools with the MCP server")
    
    @handle_errors
    @cached
    def analyze_code(self, code: str, language: str, pattern: str) -> Dict[str, Any]:
        """
        Analyze code using ast-grep pattern matching.
        
        Args:
            code: Source code to analyze
            language: Programming language (python, javascript, lua, c, rust, go, etc.)
            pattern: Pattern to search for in the code
            
        Returns:
            Dictionary with pattern matches and their locations
        """
        if language not in self.analyzer.supported_languages:
            self.logger.warning(f"Unsupported language: {language}")
            return {"error": f"Language '{language}' is not supported", "matches": []}
        
        self.logger.debug(f"Analyzing code with pattern: {pattern}")
        start_time = time.time()
        matches = self.analyzer.find_patterns(code, language, pattern)
        elapsed = time.time() - start_time
        
        self.logger.debug(f"Found {len(matches)} matches in {elapsed:.4f}s")
        
        return {
            "matches": matches,
            "count": len(matches),
            "language": language
        }
    
    @handle_errors
    @cached
    def refactor_code(self, code: str, language: str, pattern: str, replacement: str) -> Dict[str, Any]:
        """
        Refactor code by replacing pattern matches with a replacement.
        
        Args:
            code: Source code to refactor
            language: Programming language (python, javascript, lua, c, rust, go, etc.)
            pattern: Pattern to search for in the code
            replacement: Replacement code
            
        Returns:
            Dictionary with refactored code and statistics
        """
        if language not in self.analyzer.supported_languages:
            self.logger.warning(f"Unsupported language: {language}")
            return {"error": f"Language '{language}' is not supported", "success": False}
        
        self.logger.debug(f"Refactoring code with pattern: {pattern}")
        start_time = time.time()
        original_code = code
        refactored_code = self.analyzer.apply_refactoring(code, language, pattern, replacement)
        elapsed = time.time() - start_time
        
        # Count matches (by comparing refactored code with original)
        changes_made = original_code != refactored_code
        
        self.logger.debug(f"Refactoring complete in {elapsed:.4f}s (changes made: {changes_made})")
        
        return {
            "original_code": original_code,
            "refactored_code": refactored_code,
            "success": changes_made,
            "language": language
        }
    
    @handle_errors
    def analyze_file(self, file_path: str, pattern: str) -> Dict[str, Any]:
        """
        Analyze a file using ast-grep pattern matching.
        
        Args:
            file_path: Path to the file to analyze
            pattern: Pattern to search for in the file
            
        Returns:
            Dictionary with pattern matches and their locations
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            self.logger.warning(f"File not found: {file_path}")
            return {"error": f"File '{file_path}' does not exist or is not a file", "matches": []}
        
        # Determine language from file extension
        extension = path.suffix.lower()
        language = None
        
        for lang, exts in self.analyzer.supported_languages.items():
            if extension in exts:
                language = lang
                break
        
        if not language:
            self.logger.warning(f"Unsupported file type: {extension}")
            return {"error": f"Unsupported file type: {extension}", "matches": []}
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            self.logger.debug(f"Analyzing file: {file_path} with pattern: {pattern}")
            start_time = time.time()
            
            # Use the cached analyze_code method
            result = self.analyze_code(code, language, pattern)
            elapsed = time.time() - start_time
            
            self.logger.debug(f"File analysis complete in {elapsed:.4f}s")
            
            return {
                "file": str(path),
                "language": language,
                "matches": result["matches"],
                "count": result["count"]
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return {"error": str(e), "matches": []}
    
    @handle_errors
    def search_directory(
        self, 
        directory: str, 
        pattern: str, 
        parallel: bool = True, 
        max_workers: Optional[int] = None,
        file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for pattern matches in all files in a directory.
        
        Args:
            directory: Directory to search
            pattern: Pattern to search for
            parallel: Whether to use parallel processing (default: True)
            max_workers: Maximum number of worker processes (default: CPU count)
            file_extensions: List of file extensions to include (default: all supported)
            
        Returns:
            Dictionary with matches grouped by file
        """
        self.logger.info(f"Searching directory: {directory}")
        start_time = time.time()
        
        # Create a filter function if file_extensions are specified
        file_filter = None
        if file_extensions:
            extensions_set: Set[str] = set(file_extensions)
            def filter_by_extension(path: Path) -> bool:
                return path.suffix.lower() in extensions_set
            file_filter = filter_by_extension
        
        # Use the analyzer's search_directory method
        result = self.analyzer.search_directory(
            directory, 
            pattern, 
            parallel=parallel, 
            max_workers=max_workers,
            file_filter=file_filter
        )
        
        elapsed = time.time() - start_time
        files_searched = result.get("files_searched", 0)
        files_with_matches = result.get("files_with_matches", 0)
        
        self.logger.info(
            f"Search complete in {elapsed:.2f}s. "
            f"Found matches in {files_with_matches}/{files_searched} files."
        )
        
        # Log cache statistics periodically
        result_cache.log_stats()
        
        return result
    
    @handle_errors
    def get_language_patterns(self, language: str) -> Dict[str, Any]:
        """
        Get common pattern templates for a specific language.
        
        Args:
            language: Programming language (python, javascript, etc.)
            
        Returns:
            Dictionary with pattern templates for the language
        """
        handler = get_handler(language)
        
        if not handler:
            self.logger.warning(f"No handler for language: {language}")
            return {
                "error": f"Language '{language}' is not supported or has no templates",
                "patterns": {}
            }
        
        patterns = handler.get_default_patterns()
        
        return {
            "language": language,
            "patterns": patterns
        }
    
    @handle_errors
    def get_supported_languages(self) -> Dict[str, Any]:
        """
        Get a list of supported languages and their file extensions.
        
        Returns:
            Dictionary with supported languages and their file extensions
        """
        return {
            "languages": self.analyzer.get_supported_languages()
        }
    
    def start(self) -> None:
        """Start the MCP server"""
        if self.config.host != "localhost" or self.config.port != 8080:
            self.logger.warning("Note: FastMCP currently ignores host and port. Using default settings.")
        
        self.logger.info("Starting AST Grep MCP server")
        
        # Log initial cache settings
        self.logger.info(f"Result cache initialized with size: {result_cache.maxsize}")
        
        self.mcp.run() 