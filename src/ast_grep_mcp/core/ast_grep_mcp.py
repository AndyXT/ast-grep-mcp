"""
Core AstGrepMCP class that encapsulates the MCP server functionality.
"""

from fastmcp import FastMCP
from ..ast_analyzer import AstAnalyzer
from ..language_handlers import get_handler, get_all_handlers
from ..utils import handle_errors, cached, result_cache
from ..utils.security import sanitize_pattern, validate_file_access
from ..utils.ignore_handler import IgnoreHandler
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import time
import os
from .config import ServerConfig
from ..utils.pattern_helpers import analyze_pattern_error, enrich_error_message, get_pattern_help


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
        # If config is None, try to load configuration from nearest file
        self.config = config or ServerConfig.find_and_load_config()
        self.analyzer = AstAnalyzer()
        self.mcp = FastMCP("AstGrepCodeAnalyzer")
        self.logger = self._setup_logger()
        
        # Initialize ignore handler
        self.ignore_handler = self._setup_ignore_handler()
        
        # Set cache size from config if available
        if hasattr(self.config, 'cache_size') and self.config.cache_size is not None:
            result_cache.maxsize = self.config.cache_size
            self.logger.info("Setting result cache size to " + str(result_cache.maxsize))
        
        # Log security configuration
        if self.config.safe_roots:
            self.logger.info("File access restricted to: " + ', '.join(self.config.safe_roots))
        else:
            self.logger.warning("No safe roots configured. File access is unrestricted.")
        
        # Register all tools
        self._register_tools()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger for the MCP server."""
        return self.config.setup_logging("ast_grep_mcp")
    
    def _setup_ignore_handler(self) -> IgnoreHandler:
        """Set up the ignore handler for file filtering."""
        ignore_handler = IgnoreHandler()
        
        # Load default ignores if enabled
        if self.config.use_default_ignores:
            ignore_handler.load_default_ignores()
            self.logger.debug("Loaded default ignore patterns")
        
        # Load ignore patterns from configuration
        for pattern in self.config.ignore_patterns:
            ignore_handler.add_pattern(pattern)
        
        # Load ignore file if specified
        if self.config.ignore_file and os.path.exists(self.config.ignore_file):
            if ignore_handler.load_file(self.config.ignore_file):
                self.logger.info(f"Loaded ignore patterns from {self.config.ignore_file}")
            else:
                self.logger.warning(f"Failed to load ignore patterns from {self.config.ignore_file}")
        else:
            # Try to find and load nearest .ast-grepignore file
            ignore_file = ignore_handler.find_nearest_ignore_file()
            if ignore_file:
                if ignore_handler.load_file(ignore_file):
                    self.logger.info(f"Loaded ignore patterns from {ignore_file}")
                else:
                    self.logger.warning(f"Failed to load ignore patterns from {ignore_file}")
        
        return ignore_handler
    
    def _register_tools(self) -> None:
        """Register all available tools with the MCP server."""
        # Use decorators to register tools
        self.analyze_code = self.mcp.tool()(self.analyze_code)
        self.refactor_code = self.mcp.tool()(self.refactor_code)
        self.analyze_file = self.mcp.tool()(self.analyze_file)
        self.search_directory = self.mcp.tool()(self.search_directory)
        self.get_language_patterns = self.mcp.tool()(self.get_language_patterns)
        self.get_supported_languages = self.mcp.tool()(self.get_supported_languages)
        
        # Register new tools for configuration management
        self.get_config = self.mcp.tool()(self.get_config)
        self.set_config = self.mcp.tool()(self.set_config)
        self.generate_config = self.mcp.tool()(self.generate_config)
        
        # Register tools for refactoring preview mode
        self.preview_refactoring = self.mcp.tool()(self.preview_refactoring)
        self.validate_pattern = self.mcp.tool()(self.validate_pattern)
        
        # Log registration - updated number of tools
        self.logger.info("Registered 11 tools with the MCP server")
    
    def _validate_pattern(self, pattern: str, language: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a pattern for the given language.
        
        Args:
            pattern: Pattern to validate
            language: Language to validate for
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Skip validation in relaxed mode
        if self.config.pattern_config.validation_strictness == "relaxed":
            return True, None
        
        # Basic syntax validation (for all strictness levels)
        if not pattern or pattern.strip() == "":
            return False, "Pattern cannot be empty"
        
        # JS/TS template literals need special handling
        if language in ['javascript', 'typescript'] and '`' in pattern:
            # Template literals with ${} are valid in JS/TS, so allow them
            return True, None
        
        # Run additional validation in strict mode
        if self.config.pattern_config.validation_strictness == "strict":
            # Check for balance of brackets, braces, parentheses
            # Skip if dealing with JSX or template literals
            if not (language in ['javascript', 'typescript'] and 
                  ('<' in pattern and '>' in pattern) or 
                  ('${' in pattern)):
                brackets = {'(': ')', '[': ']', '{': '}'}
                stack = []
                
                for char in pattern:
                    if char in brackets.keys():
                        stack.append(char)
                    elif char in brackets.values():
                        if not stack or brackets[stack.pop()] != char:
                            return False, f"Unbalanced brackets in pattern: {pattern}"
                
                if stack:
                    return False, f"Unbalanced brackets in pattern: {pattern}"
            
            # Check for proper variable usage
            var_count = pattern.count('$')
            if var_count > 0:
                triple_var_count = pattern.count('$$$')
                single_var_count = var_count - (triple_var_count * 3)
                
                if single_var_count > 0 and not any(c.isalpha() or c == '_' for c in pattern):
                    return False, "Variable names should follow $ or $$$ prefix"
                
                # Language-specific validation could be added here
        
        return True, None
    
    def _get_pattern_diagnostics(self, pattern: str, language: str, code: str = "") -> Dict[str, Any]:
        """
        Get diagnostic information for a pattern.
        
        Args:
            pattern: The pattern to diagnose
            language: The language of the pattern
            code: Optional code to check against the pattern
            
        Returns:
            Dictionary with diagnostics information
        """
        result = {
            "is_valid": True,
            "pattern": pattern,
            "language": language
        }
        
        # Special case for template literals in JS/TS - always consider valid
        if language in ['javascript', 'typescript'] and ('`' in pattern or '${' in pattern):
            return result
        
        # Special case for JSX in JS/TS - always consider valid
        if language in ['javascript', 'typescript'] and ('<' in pattern and '>' in pattern):
            return result
        
        # First, analyze the pattern for potential errors
        analysis = analyze_pattern_error(pattern, language)
        if analysis["has_errors"]:
            result["is_valid"] = False
            result["error"] = "Pattern syntax issues detected"
            result["error_details"] = analysis["errors"]
            
            # Add language-specific guidance
            if analysis["language_specific"]:
                result["language_guidance"] = analysis["language_specific"]
        
        # Test with code if provided
        if code:
            try:
                matches = self.analyzer.find_patterns(code, language, pattern)
                result["has_matches"] = len(matches) > 0
                result["match_count"] = len(matches)
            except Exception as e:
                result["is_valid"] = False
                error_msg = str(e)
                # Enrich the error message with helpful information
                enhanced_msg = enrich_error_message(error_msg, language, pattern)
                result["error"] = enhanced_msg
                
                # Add pattern help for this language
                result["pattern_help"] = get_pattern_help(language, error_msg)
                
                # Get suggestions for similar working patterns
                try:
                    from ..utils.pattern_suggestions import suggest_patterns, build_suggestion_message
                    suggestions = suggest_patterns(pattern, code, language)
                    if suggestions:
                        result["suggestions"] = suggestions
                        result["suggestion_message"] = build_suggestion_message(pattern, language, suggestions)
                except Exception as sugg_err:
                    self.logger.error(f"Error generating pattern suggestions: {str(sugg_err)}")
        
        return result
    
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
            self.logger.warning("Unsupported language: " + language)
            return {"error": "Language '" + language + "' is not supported", "matches": []}
        
        # Sanitize pattern to prevent command injection
        safe_pattern = sanitize_pattern(pattern)
        if safe_pattern != pattern:
            self.logger.warning("Pattern was sanitized for security reasons")
        
        # Validate pattern if configured
        diagnostics = self._get_pattern_diagnostics(safe_pattern, language, code)
        if not diagnostics["is_valid"] and self.config.pattern_config.validation_strictness != "relaxed":
            error_msg = diagnostics["error"] or "Invalid pattern"
            result = {"error": error_msg, "matches": []}
            
            # Add diagnostic information based on verbosity
            if self.config.diagnostic_config.pattern_diagnostics:
                if "suggestion_message" in diagnostics:
                    result["suggestion_message"] = diagnostics["suggestion_message"]
                if "suggestions" in diagnostics and diagnostics["suggestions"]:
                    result["suggestions"] = diagnostics["suggestions"]
            
            return result
        
        # Log the analysis
        self.logger.debug("Analyzing code with pattern: " + safe_pattern)
        start_time = time.time()
        
        # Perform analysis
        matches = self.analyzer.find_patterns(code, language, safe_pattern)
        elapsed = time.time() - start_time
        
        self.logger.debug("Found " + str(len(matches)) + " matches in " + str(elapsed) + "s")
        
        result = {
            "matches": matches,
            "count": len(matches),
            "language": language
        }
        
        # Add diagnostic information for detailed verbosity
        if (self.config.diagnostic_config.verbosity in ["detailed", "diagnostic"] and 
            self.config.diagnostic_config.pattern_diagnostics):
            result["diagnostics"] = diagnostics
        
        return result
    
    @handle_errors
    def validate_pattern(self, pattern: str, language: str, code: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a pattern for the given language and provide diagnostics.
        
        Args:
            pattern: Pattern to validate
            language: Language to validate for
            code: Optional code to check pattern against
            
        Returns:
            Dictionary with validation results and diagnostics
        """
        if language not in self.analyzer.supported_languages:
            return {"is_valid": False, "error": f"Language '{language}' is not supported"}
        
        # Sanitize pattern
        safe_pattern = sanitize_pattern(pattern)
        if safe_pattern != pattern:
            self.logger.warning("Pattern was sanitized for security reasons")
        
        # Get full diagnostics
        diagnostics = self._get_pattern_diagnostics(safe_pattern, language, code)
        
        result = {
            "is_valid": diagnostics["is_valid"],
            "pattern": safe_pattern,
            "language": language
        }
        
        if not diagnostics["is_valid"]:
            result["error"] = diagnostics["error"]
        
        # Add suggestions and examples based on configuration
        if self.config.diagnostic_config.show_suggestions and "suggestions" in diagnostics:
            result["suggestions"] = diagnostics["suggestions"]
            
            if "suggestion_message" in diagnostics:
                result["suggestion_message"] = diagnostics["suggestion_message"]
        
        if self.config.diagnostic_config.show_examples and "examples" in diagnostics:
            result["examples"] = diagnostics["examples"]
        
        return result
    
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
            self.logger.warning("Unsupported language: " + language)
            return {"error": "Language '" + language + "' is not supported", "success": False, "refactored_code": code}
        
        # Sanitize pattern and replacement to prevent command injection
        safe_pattern = sanitize_pattern(pattern)
        safe_replacement = sanitize_pattern(replacement)
        
        if safe_pattern != pattern or safe_replacement != replacement:
            self.logger.warning("Pattern or replacement was sanitized for security reasons")
        
        # Validate pattern if configured
        if self.config.refactoring_config.validate_replacements:
            diagnostics = self._get_pattern_diagnostics(safe_pattern, language, code)
            if not diagnostics["is_valid"] and self.config.pattern_config.validation_strictness != "relaxed":
                error_msg = diagnostics["error"] or "Invalid pattern"
                result = {
                    "error": error_msg, 
                    "success": False,
                    "refactored_code": code  # Add the original code to the result
                }
                
                # Add diagnostic information based on verbosity
                if self.config.diagnostic_config.pattern_diagnostics:
                    if "suggestion_message" in diagnostics:
                        result["suggestion_message"] = diagnostics["suggestion_message"]
                    if "suggestions" in diagnostics and diagnostics["suggestions"]:
                        result["suggestions"] = diagnostics["suggestions"]
                
                return result
        
        self.logger.debug("Refactoring code with pattern: " + safe_pattern)
        start_time = time.time()
        original_code = code
        
        # Get matches first to count them
        matches_result = self.analyze_code(code, language, safe_pattern)
        matches = matches_result.get("matches", [])
        match_count = len(matches)
        
        # Check if there are too many replacements
        if (self.config.refactoring_config.max_replacements is not None and 
            match_count > self.config.refactoring_config.max_replacements):
            return {
                "error": f"Too many replacements ({match_count}). "
                        f"Maximum allowed: {self.config.refactoring_config.max_replacements}",
                "matches": match_count,
                "success": False,
                "refactored_code": code  # Add the original code to the result
            }
        
        # Apply the refactoring
        refactored_code = self.analyzer.apply_refactoring(
            code, 
            language, 
            safe_pattern, 
            safe_replacement,
            fix_malformed=self.config.refactoring_config.fix_malformed_output,
            enhance_partial=self.config.refactoring_config.enhance_partial_matches
        )
        
        elapsed = time.time() - start_time
        
        # Count matches (by comparing refactored code with original)
        changes_made = original_code != refactored_code
        
        self.logger.debug("Refactoring complete in " + str(elapsed) + "s (changes made: " + str(changes_made) + ")")
        
        result = {
            "original_code": original_code,
            "refactored_code": refactored_code,
            "success": changes_made,
            "language": language,
            "matches": match_count
        }
        
        # Add diagnostic information for detailed verbosity
        if (self.config.diagnostic_config.verbosity in ["detailed", "diagnostic"] and 
            self.config.diagnostic_config.pattern_diagnostics):
            result["pattern_diagnostics"] = self._get_pattern_diagnostics(safe_pattern, language, code)
        
        return result
    
    @handle_errors
    def preview_refactoring(self, code: str, language: str, pattern: str, replacement: str) -> Dict[str, Any]:
        """
        Preview code refactoring without applying changes.
        
        This shows what would be changed by the refactoring.
        
        Args:
            code: Source code to analyze
            language: Programming language
            pattern: Pattern to search for
            replacement: Replacement code
            
        Returns:
            Dictionary with preview information
        """
        if language not in self.analyzer.supported_languages:
            return {"error": f"Language '{language}' is not supported", "matches": []}
        
        # Sanitize inputs
        safe_pattern = sanitize_pattern(pattern)
        safe_replacement = sanitize_pattern(replacement)
        
        # Find matches first
        matches_result = self.analyze_code(code, language, safe_pattern)
        matches = matches_result.get("matches", [])
        
        if "error" in matches_result:
            return matches_result  # Return the error
        
        # Generate preview
        preview = []
        lines = code.split('\n')
        
        # Sort matches by line number (descending) to avoid position shifts
        sorted_matches = sorted(matches, key=lambda m: m['location']['start']['line'], reverse=True)
        
        for match in sorted_matches:
            start_line = match['location']['start']['line']
            end_line = match['location']['end']['line']
            
            # Get context lines
            context_before = max(0, start_line - self.config.output_config.context_lines)
            context_after = min(len(lines), end_line + self.config.output_config.context_lines)
            
            # Create a preview entry
            preview_entry = {
                "match": match,
                "context": {
                    "before": lines[context_before:start_line],
                    "match": lines[start_line:end_line],
                    "after": lines[end_line:context_after]
                },
                "replacement": safe_replacement
            }
            
            preview.append(preview_entry)
        
        # Return the preview information
        return {
            "matches": matches,
            "count": len(matches),
            "preview": preview,
            "language": language,
            "pattern": safe_pattern,
            "replacement": safe_replacement
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
        # Validate file access permissions
        access_error = validate_file_access(file_path, self.config.safe_roots)
        if access_error:
            return {"error": access_error, "matches": []}
        
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            self.logger.warning("File not found: " + file_path)
            return {"error": "File '" + file_path + "' does not exist or is not a file", "matches": []}
        
        # Check if file should be ignored
        if self.ignore_handler.should_ignore(str(path)):
            self.logger.debug(f"Skipping ignored file: {file_path}")
            return {"error": f"File '{file_path}' is ignored by configuration", "matches": []}
        
        # Determine language from file extension
        extension = path.suffix.lower()
        language = None
        
        for lang, exts in self.analyzer.supported_languages.items():
            if extension in exts:
                language = lang
                break
        
        if not language:
            self.logger.warning("Unsupported file type: " + extension)
            return {"error": "Unsupported file type: " + extension, "matches": []}
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            # Sanitize pattern
            safe_pattern = sanitize_pattern(pattern)
            if safe_pattern != pattern:
                self.logger.warning("Pattern was sanitized for security reasons")
            
            self.logger.debug("Analyzing file: " + file_path + " with pattern: " + safe_pattern)
            start_time = time.time()
            
            # Use the cached analyze_code method
            result = self.analyze_code(code, language, safe_pattern)
            elapsed = time.time() - start_time
            
            self.logger.debug("File analysis complete in " + str(elapsed) + "s")
            
            return {
                "file": str(path),
                "language": language,
                "matches": result.get("matches", []),
                "count": result.get("count", 0)
            }
        
        except Exception as e:
            self.logger.error("Error analyzing file " + file_path + ": " + str(e))
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
        # Validate directory access permissions
        access_error = validate_file_access(directory, self.config.safe_roots)
        if access_error:
            return {"error": access_error, "matches": {}}
        
        # Sanitize pattern
        safe_pattern = sanitize_pattern(pattern)
        if safe_pattern != pattern:
            self.logger.warning("Pattern was sanitized for security reasons")
        
        self.logger.info("Searching directory: " + directory)
        start_time = time.time()
        
        # Create a filter function for both extensions and ignore patterns
        def file_filter(path: Path) -> bool:
            # Check if file should be ignored
            if self.ignore_handler.should_ignore(str(path)):
                return False
            
            # Check file extension if specified
            if file_extensions:
                return path.suffix.lower() in file_extensions
            
            # Otherwise, check if the file extension is supported by any language
            ext = path.suffix.lower()
            for exts in self.analyzer.supported_languages.values():
                if ext in exts:
                    return True
            
            return False
        
        # Use the analyzer's search_directory method
        result = self.analyzer.search_directory(
            directory, 
            safe_pattern, 
            parallel=parallel, 
            max_workers=max_workers,
            file_filter=file_filter
        )
        
        elapsed = time.time() - start_time
        files_searched = result.get("files_searched", 0)
        files_with_matches = result.get("files_with_matches", 0)
        
        self.logger.info(
            "Search complete in " + str(elapsed) + "s. "
            "Found matches in " + str(files_with_matches) + "/" + str(files_searched) + " files."
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
            self.logger.warning("No handler for language: " + language)
            return {
                "error": "Language '" + language + "' is not supported or has no templates",
                "patterns": {}
            }
        
        patterns = handler.get_default_patterns()
        
        # Check for language-specific template directory in configuration
        template_dir = None
        if language in self.config.pattern_config.language_templates:
            template_dir = self.config.pattern_config.language_templates[language]
        elif self.config.pattern_config.template_dir:
            # Check for language subdirectory in template_dir
            lang_dir = os.path.join(self.config.pattern_config.template_dir, language)
            if os.path.isdir(lang_dir):
                template_dir = lang_dir
        
        # Load additional patterns from template directory if it exists
        if template_dir and os.path.isdir(template_dir):
            try:
                for file in os.listdir(template_dir):
                    if file.endswith('.yml') or file.endswith('.yaml'):
                        file_path = os.path.join(template_dir, file)
                        with open(file_path, 'r') as f:
                            import yaml
                            custom_patterns = yaml.safe_load(f)
                            if isinstance(custom_patterns, dict):
                                patterns.update(custom_patterns)
                                self.logger.debug(f"Loaded {len(custom_patterns)} patterns from {file_path}")
            except Exception as e:
                self.logger.error(f"Error loading patterns from {template_dir}: {str(e)}")
        
        # Add custom patterns from configuration
        if language in self.config.pattern_config.custom_patterns:
            custom_patterns = self.config.pattern_config.custom_patterns[language]
            if custom_patterns:
                patterns.update(custom_patterns)
                self.logger.debug(f"Added {len(custom_patterns)} custom patterns from configuration")
        
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
        # Use the analyzer's supported languages and enrich with handler information
        base_languages = self.analyzer.supported_languages.copy()
        
        # Get additional information from language handlers
        handlers = get_all_handlers()
        languages = {}
        
        for language, extensions in base_languages.items():
            languages[language] = extensions
        
        for name, handler in handlers.items():
            if name not in languages:
                languages[name] = handler.file_extensions
        
        return {
            "languages": languages
        }
    
    @handle_errors
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Dictionary with the current configuration
        """
        return {
            "config": self.config.to_dict()
        }
    
    @handle_errors
    def set_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the current configuration.
        
        Args:
            config: Dictionary with configuration values to update
            
        Returns:
            Dictionary with the updated configuration
        """
        try:
            # Create a new config with the updated values
            new_config = ServerConfig.from_dict({**self.config.to_dict(), **config})
            
            # Update the current configuration
            self.config = new_config
            
            # Reinitialize components that depend on configuration
            self.logger = self._setup_logger()
            self.ignore_handler = self._setup_ignore_handler()
            
            # Update cache size if changed
            if hasattr(self.config, 'cache_size') and self.config.cache_size is not None:
                result_cache.maxsize = self.config.cache_size
                self.logger.info("Updated result cache size to " + str(result_cache.maxsize))
            
            return {
                "success": True,
                "config": self.config.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @handle_errors
    def generate_config(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a configuration file with the current settings.
        
        Args:
            output_file: Path to save the configuration to
            
        Returns:
            Dictionary with the result
        """
        try:
            if output_file:
                self.config.save_to_file(output_file)
                return {
                    "success": True,
                    "message": f"Configuration saved to {output_file}",
                    "config": self.config.to_dict()
                }
            else:
                # Return YAML representation if no output file specified
                return {
                    "success": True,
                    "config": self.config.to_dict(),
                    "yaml": self.config.to_yaml()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def start(self) -> None:
        """Start the MCP server"""
        if self.config.host != "localhost" or self.config.port != 8080:
            self.logger.warning("Note: FastMCP currently ignores host and port. Using default settings.")
        
        self.logger.info("Starting AST Grep MCP server")
        
        # Log initial cache settings
        self.logger.info("Result cache initialized with size: " + str(result_cache.maxsize))
        
        # Log output and diagnostic configuration
        self.logger.info(f"Output format: {self.config.output_config.format}")
        self.logger.info(f"Diagnostic verbosity: {self.config.diagnostic_config.verbosity}")
        
        # Log refactoring configuration
        if self.config.refactoring_config.preview_mode:
            self.logger.info("Refactoring preview mode enabled")
        
        self.mcp.run() 