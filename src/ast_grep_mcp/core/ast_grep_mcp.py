"""
Core AstGrepMCP class that encapsulates the MCP server functionality.
"""

from fastmcp import FastMCP
from ..ast_analyzer_v2 import AstAnalyzerV2
from ..language_handlers import get_handler, get_all_handlers
from ..utils import handle_errors, cached, result_cache
from ..utils.error_handling import PatternValidationError
from ..utils.security import sanitize_pattern, validate_file_access
from ..utils.ignore_handler import IgnoreHandler
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import time
import os
import re
from .config import ServerConfig
from ..utils.pattern_helpers import get_pattern_help
from ..utils.pattern_diagnostics import create_enhanced_diagnostic
from ..utils.pattern_autocorrect import (
    PatternAutoCorrector,
    create_pattern_suggestion_message,
)
from ..utils.streaming import StreamConfig
from .rule_tools import RuleTools
from ..utils.pattern_builder import PatternBuilder, PatternLibrary
from ..utils.pagination import ResponsePaginator
from ..utils.pattern_simplifier import PatternSimplifier
from .pattern_guide_tools import PatternGuideTools
from ..utils.common_patterns import CommonPatternLibrary, PatternRecommender, PatternCategory
from ..utils.pattern_fixer import PatternFixer, FuzzyPatternMatcher
from ..utils.enhanced_diagnostics import EnhancedDiagnostics


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
        self.analyzer = AstAnalyzerV2(
            cache_size=self.config.cache_size,
            performance_config=self.config.performance_config
        )
        self.mcp = FastMCP("AstGrepCodeAnalyzer")
        self.logger = self._setup_logger()

        # Initialize ignore handler
        self.ignore_handler = self._setup_ignore_handler()

        # Initialize pattern autocorrector
        self.autocorrector = PatternAutoCorrector()
        
        # Initialize rule tools
        self.rule_tools = RuleTools()
        
        # Initialize pattern guide tools
        self.pattern_guide = PatternGuideTools()
        
        # Initialize paginator
        self.paginator = ResponsePaginator(self.logger)
        
        # Initialize pattern simplifier
        self.pattern_simplifier = PatternSimplifier()

        # Configure cache settings
        self._configure_cache()

        # Log security configuration
        self._log_security_config()

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
                self.logger.info(
                    f"Loaded ignore patterns from {self.config.ignore_file}"
                )
            else:
                self.logger.warning(
                    f"Failed to load ignore patterns from {self.config.ignore_file}"
                )
        else:
            # Try to find and load nearest .ast-grepignore file
            ignore_file = ignore_handler.find_nearest_ignore_file()
            if ignore_file:
                if ignore_handler.load_file(ignore_file):
                    self.logger.info(f"Loaded ignore patterns from {ignore_file}")
                else:
                    self.logger.warning(
                        f"Failed to load ignore patterns from {ignore_file}"
                    )

        return ignore_handler

    def _configure_cache(self) -> None:
        """Configure result cache settings based on config."""
        if hasattr(self.config, "cache_size") and self.config.cache_size is not None:
            result_cache.maxsize = self.config.cache_size
            self.logger.info(
                "Setting result cache size to " + str(result_cache.maxsize)
            )

    def _log_security_config(self) -> None:
        """Log the current security configuration."""
        if self.config.safe_roots:
            self.logger.info(
                "File access restricted to: " + ", ".join(self.config.safe_roots)
            )
        else:
            self.logger.warning(
                "No safe roots configured. File access is unrestricted."
            )
    
    def _normalize_directory_path(self, directory: str) -> Path:
        """
        Normalize and validate a directory path.
        
        Args:
            directory: Directory path (relative or absolute)
            
        Returns:
            Normalized absolute Path object
            
        Raises:
            ValueError: If directory doesn't exist or is not a directory
        """
        dir_path = Path(directory).resolve()
        
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")
            
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
            
        return dir_path

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

        # Register pattern suggestion tool
        self.suggest_pattern_corrections = self.mcp.tool()(
            self.suggest_pattern_corrections
        )

        # Register streaming search tool
        self.search_directory_stream = self.mcp.tool()(self.search_directory_stream)
        
        # Register enhanced search with context
        self.search_directory_with_context = self.mcp.tool()(self.search_directory_with_context)
        
        # Register security audit tools
        self.run_security_audit = self.mcp.tool()(self.run_security_audit)
        
        # Register pattern builder tool
        self.build_pattern = self.mcp.tool()(self.build_pattern)
        
        # Register cross-file analysis tools
        self.find_trait_implementations = self.mcp.tool()(self.find_trait_implementations)
        self.find_function_calls = self.mcp.tool()(self.find_function_calls)
        self.analyze_dependencies = self.mcp.tool()(self.analyze_dependencies)
        
        # Register project analysis tools
        self.analyze_project_structure = self.mcp.tool()(self.analyze_project_structure)
        self.analyze_code_quality = self.mcp.tool()(self.analyze_code_quality)
        self.generate_review_report = self.mcp.tool()(self.generate_review_report)

        # Register rule-based analysis tools
        self.create_rule = self.mcp.tool()(self.rule_tools.create_rule)
        self.load_rules = self.mcp.tool()(self.rule_tools.load_rules)
        self.run_rules = self.mcp.tool()(self.rule_tools.run_rules)
        self.test_rule = self.mcp.tool()(self.rule_tools.test_rule)
        self.compose_rule = self.mcp.tool()(self.rule_tools.compose_rule)
        self.list_rules = self.mcp.tool()(self.rule_tools.list_rules)
        self.remove_rule = self.mcp.tool()(self.rule_tools.remove_rule)
        self.export_rules = self.mcp.tool()(self.rule_tools.export_rules)
        
        # Register pattern guide tools
        self.get_pattern_syntax_guide = self.mcp.tool()(self.pattern_guide.get_pattern_syntax_guide)
        self.get_pattern_examples = self.mcp.tool()(self.pattern_guide.get_pattern_examples)
        self.explain_pattern = self.mcp.tool()(self.pattern_guide.explain_pattern)
        
        # Register new improvement tools
        self.pattern_builder = self.mcp.tool()(self.pattern_builder)
        self.get_pattern_template = self.mcp.tool()(self.get_pattern_template)
        self.batch_search = self.mcp.tool()(self.batch_search)
        self.search_stream = self.mcp.tool()(self.search_stream)
        self.create_smart_pattern = self.mcp.tool()(self.create_smart_pattern)

        # Log registration - updated number of tools
        self.logger.info("Registered 38 tools with the MCP server")

    def _validate_pattern(
        self, pattern: str, language: str
    ) -> Tuple[bool, Optional[str]]:
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
        if language in ["javascript", "typescript"] and "`" in pattern:
            # Template literals with ${} are valid in JS/TS, so allow them
            return True, None

        # Run additional validation in strict mode
        if self.config.pattern_config.validation_strictness == "strict":
            # Check for balance of brackets, braces, parentheses
            # Skip if dealing with JSX or template literals
            if not (
                language in ["javascript", "typescript"]
                and ("<" in pattern and ">" in pattern)
                or ("${" in pattern)
            ):
                brackets = {"(": ")", "[": "]", "{": "}"}
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
            var_count = pattern.count("$")
            if var_count > 0:
                triple_var_count = pattern.count("$$$")
                single_var_count = var_count - (triple_var_count * 3)

                if single_var_count > 0 and not any(
                    c.isalpha() or c == "_" for c in pattern
                ):
                    return False, "Variable names should follow $ or $$$ prefix"

                # Language-specific validation could be added here

        return True, None

    def _get_pattern_diagnostics(
        self, pattern: str, language: str, code: str = ""
    ) -> Dict[str, Any]:
        """
        Get diagnostic information for a pattern.

        Args:
            pattern: The pattern to diagnose
            language: The language of the pattern
            code: Optional code to check against the pattern

        Returns:
            Dictionary with diagnostics information
        """
        # First, check for obviously invalid patterns
        pattern_is_valid = True
        actual_error = None
        validation_details = []
        
        # CRITICAL FIX: Add basic sanity checks for obviously invalid patterns
        if not pattern.strip():
            pattern_is_valid = False
            actual_error = "Empty pattern"
            validation_details.append({
                "type": "empty_pattern",
                "message": "Pattern cannot be empty",
                "severity": "error"
            })
        
        # Check for unmatched brackets/braces/parentheses
        bracket_pairs = [('[', ']'), ('(', ')'), ('{', '}')]
        for open_char, close_char in bracket_pairs:
            open_count = pattern.count(open_char)
            close_count = pattern.count(close_char)
            if open_count != close_count:
                pattern_is_valid = False
                actual_error = f"Unmatched {open_char}{close_char} brackets"
                validation_details.append({
                    "type": "unmatched_brackets",
                    "message": f"Unmatched {open_char}{close_char}: found {open_count} '{open_char}' and {close_count} '{close_char}'",
                    "severity": "error"
                })
        
        # Check for invalid characters or sequences that should never be in patterns
        invalid_sequences = ['[[[', ']]]', '(()', '))(', '{{)', '}}{']
        for seq in invalid_sequences:
            if seq in pattern:
                pattern_is_valid = False
                actual_error = f"Invalid character sequence: {seq}"
                validation_details.append({
                    "type": "invalid_sequence",
                    "message": f"Invalid character sequence '{seq}' found in pattern",
                    "severity": "error"
                })
        
        # If pattern already failed basic checks, don't proceed with ast-grep validation
        if not pattern_is_valid:
            result = {
                "is_valid": False,
                "pattern": pattern,
                "language": language,
                "error": actual_error,
                "error_details": validation_details
            }
            return result
        
        try:
            # Create a simple test code if none provided
            if not code:
                # Use language-specific test code
                test_codes = {
                    "python": "def test(): pass\nclass Test: pass\nx = 1",
                    "javascript": "function test() {}\nconst x = 1;\nclass Test {}",
                    "typescript": "function test(): void {}\nconst x: number = 1;\nclass Test {}",
                    "rust": "fn test() {}\nstruct Test {}\nlet x = 1;",
                    "go": "func test() {}\ntype Test struct {}\nvar x = 1",
                    "c": "void test() {}\nstruct Test {};\nint x = 1;",
                }
                code = test_codes.get(language, "test")
            
            # Enhanced validation: Try to parse the pattern itself
            # This will help catch syntax errors early
            try:
                # Import ast-grep-py for direct pattern validation
                from ast_grep_py import SgRoot
                
                # Try to create a root node with the pattern as if it were code
                # This helps validate basic syntax
                try:
                    pattern_root = SgRoot(pattern, language)
                    # If we can parse it, check if it's a valid pattern
                    pattern_node = pattern_root.root()
                    
                    # Basic checks for pattern-specific syntax
                    if "$" in pattern:
                        # Check metavariable syntax
                        import re
                        # Valid metavariables: $NAME, $$NAME (invalid), $$$NAME
                        metavar_pattern = re.compile(r'\$(\$*)?(\w*)')
                        for match in metavar_pattern.finditer(pattern):
                            dollars = match.group(1) or ""
                            name = match.group(2)
                            
                            if dollars == "$":  # $$ is invalid
                                validation_details.append({
                                    "type": "invalid_metavar",
                                    "message": "Invalid metavariable syntax '$$' - use $ for single capture or $$$ for variadic",
                                    "position": match.start()
                                })
                                pattern_is_valid = False
                            elif not name and match.group(0) != "$_":
                                validation_details.append({
                                    "type": "empty_metavar",
                                    "message": f"Empty metavariable name at position {match.start()}",
                                    "position": match.start()
                                })
                                pattern_is_valid = False
                            elif name and name[0].isdigit():
                                validation_details.append({
                                    "type": "invalid_metavar_name",
                                    "message": f"Metavariable cannot start with number at position {match.start()}",
                                    "position": match.start()
                                })
                                pattern_is_valid = False
                                
                except Exception as parse_err:
                    # Pattern contains syntax that can't be parsed as regular code
                    # This is often OK for patterns, so we don't mark as invalid yet
                    self.logger.debug(f"Pattern parse check: {parse_err}")
                
                # Now try to actually use the pattern
                test_result = self.analyzer.analyze_code(code, language, pattern)
                test_matches = test_result.get("matches", []) if test_result else []
                # If no exception was raised, the pattern syntax is valid
                pattern_is_valid = pattern_is_valid and True
                
            except PatternValidationError as pve:
                pattern_is_valid = False
                actual_error = str(pve)
            except Exception as e:
                # Check if it's an ast-grep specific error
                error_str = str(e)
                if "invalid pattern" in error_str.lower() or "syntax error" in error_str.lower():
                    pattern_is_valid = False
                    actual_error = error_str
                    
                    # Try to extract more specific error information
                    if "expected" in error_str.lower():
                        validation_details.append({
                            "type": "syntax_error",
                            "message": error_str,
                            "severity": "error"
                        })
                else:
                    # Other exceptions might not be pattern-related
                    pattern_is_valid = False
                    actual_error = str(e)
                
        except Exception as e:
            # If ast-grep throws an exception, the pattern is invalid
            pattern_is_valid = False
            actual_error = str(e)

        # Use the enhanced diagnostics system for suggestions
        enhanced_diagnostic = create_enhanced_diagnostic(pattern, language, actual_error, code)
        
        # Merge our validation details with enhanced diagnostics
        if validation_details:
            if "errors" not in enhanced_diagnostic:
                enhanced_diagnostic["errors"] = []
            enhanced_diagnostic["errors"].extend(validation_details)

        # Build the result
        result = {
            "is_valid": pattern_is_valid,
            "pattern": pattern,
            "language": language,
        }

        # Special case for template literals in JS/TS - always consider valid
        if language in ["javascript", "typescript"] and (
            "`" in pattern or "${" in pattern
        ):
            result["is_valid"] = True
            return result

        # Special case for JSX in JS/TS - always consider valid
        if language in ["javascript", "typescript"] and (
            "<" in pattern and ">" in pattern
        ):
            result["is_valid"] = True
            return result

        # Add error information if not valid
        if not pattern_is_valid:
            if actual_error:
                result["error"] = f"Pattern failed validation: {actual_error}"
            else:
                result["error"] = enhanced_diagnostic.get(
                    "help_message", "Pattern validation failed"
                )
            result["error_details"] = enhanced_diagnostic.get("errors", [])

            # Add corrected pattern if available
            if "corrected_pattern" in enhanced_diagnostic:
                result["corrected_pattern"] = enhanced_diagnostic["corrected_pattern"]
                result["correction_confidence"] = enhanced_diagnostic[
                    "correction_confidence"
                ]

        # Test with code if provided
        if code and pattern_is_valid:  # Only test if pattern is valid
            try:
                analysis_result = self.analyzer.analyze_code(code, language, pattern)
                matches = analysis_result.get("matches", []) if analysis_result else []
                result["has_matches"] = len(matches) > 0
                result["match_count"] = len(matches)
            except Exception as e:
                result["is_valid"] = False
                error_msg = str(e)

                # Create a new enhanced diagnostic with the error message
                error_diagnostic = create_enhanced_diagnostic(
                    pattern, language, error_msg, code
                )

                # Use the enhanced error message
                result["error"] = error_diagnostic.get("help_message", error_msg)

                # Add pattern help for this language
                result["pattern_help"] = get_pattern_help(language, error_msg)

                # Add suggestions from enhanced diagnostics
                if "suggestions" in error_diagnostic:
                    result["suggestions"] = error_diagnostic["suggestions"]

                # Add corrected pattern if available
                if "corrected_pattern" in error_diagnostic:
                    result["corrected_pattern"] = error_diagnostic["corrected_pattern"]
                    result["correction_confidence"] = error_diagnostic[
                        "correction_confidence"
                    ]

                # Get additional suggestions for similar working patterns
                try:
                    from ..utils.pattern_suggestions import (
                        suggest_patterns,
                        build_suggestion_message,
                    )

                    suggestions = suggest_patterns(pattern, code, language)
                    if suggestions:
                        if "suggestions" not in result:
                            result["suggestions"] = []
                        result["suggestions"].extend(suggestions)
                        result["suggestion_message"] = build_suggestion_message(
                            pattern, language, suggestions
                        )
                except Exception as sugg_err:
                    self.logger.error(
                        f"Error generating pattern suggestions: {str(sugg_err)}"
                    )

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
            return {
                "error": "Language '" + language + "' is not supported",
                "matches": [],
            }

        # Sanitize pattern to prevent command injection
        safe_pattern = sanitize_pattern(pattern)
        if safe_pattern != pattern:
            self.logger.warning("Pattern was sanitized for security reasons")

        # Validate pattern if configured
        diagnostics = self._get_pattern_diagnostics(safe_pattern, language, code)
        if (
            not diagnostics["is_valid"]
            and self.config.pattern_config.validation_strictness != "relaxed"
        ):
            error_msg = diagnostics["error"] or "Invalid pattern"
            result = {"error": error_msg, "matches": []}

            # Add diagnostic information based on verbosity
            if self.config.diagnostic_config.pattern_diagnostics:
                if "suggestion_message" in diagnostics:
                    result["suggestion_message"] = diagnostics["suggestion_message"]
                if "suggestions" in diagnostics and diagnostics["suggestions"]:
                    result["suggestions"] = diagnostics["suggestions"]

                # Add corrected pattern if available with high confidence
                if (
                    "corrected_pattern" in diagnostics
                    and diagnostics.get("correction_confidence", 0) > 0.7
                ):
                    result["corrected_pattern"] = diagnostics["corrected_pattern"]
                    result["correction_confidence"] = diagnostics[
                        "correction_confidence"
                    ]
                    result["correction_hint"] = (
                        f"Did you mean: {diagnostics['corrected_pattern']}?"
                    )

            return result

        # Log the analysis
        self.logger.debug("Analyzing code with pattern: " + safe_pattern)
        start_time = time.time()

        # Perform analysis
        analysis_result = self.analyzer.analyze_code(code, language, safe_pattern)
        matches = analysis_result.get("matches", []) if analysis_result else []
        elapsed = time.time() - start_time

        self.logger.debug(
            "Found " + str(len(matches)) + " matches in " + str(elapsed) + "s"
        )
        
        # If no matches found, try pattern fixes
        if len(matches) == 0:
            self.logger.info(f"No matches found for pattern '{safe_pattern}', trying alternatives...")
            
            # Get alternative patterns from the fixer
            alternatives = PatternFixer.fix_pattern(safe_pattern, language)
            
            # Also try fuzzy patterns if enabled
            if self.config.pattern_config.fuzzy_matching:
                fuzzy_alternatives = FuzzyPatternMatcher.make_pattern_fuzzy(safe_pattern, language)
                alternatives.extend(fuzzy_alternatives)
            
            # Remove duplicates and original pattern
            alternatives = list(dict.fromkeys(alternatives))
            if safe_pattern in alternatives:
                alternatives.remove(safe_pattern)
            
            # Try each alternative
            for alt_pattern in alternatives[:5]:  # Limit to 5 alternatives
                self.logger.debug(f"Trying alternative pattern: {alt_pattern}")
                alt_result = self.analyzer.analyze_code(code, language, alt_pattern)
                alt_matches = alt_result.get("matches", []) if alt_result else []
                
                if len(alt_matches) > 0:
                    self.logger.info(f"Found {len(alt_matches)} matches with alternative pattern: {alt_pattern}")
                    matches = alt_matches
                    result = {
                        "matches": matches, 
                        "count": len(matches), 
                        "language": language,
                        "pattern_used": alt_pattern,
                        "original_pattern": safe_pattern,
                        "pattern_fixed": True,
                        "fix_reason": PatternFixer.explain_pattern_issue(safe_pattern, language)
                    }
                    return result

        result = {"matches": matches, "count": len(matches), "language": language}
        
        # Add debugging info when no matches found
        if len(matches) == 0 and self.config.diagnostic_config.verbosity in ["detailed", "diagnostic"]:
            # Get enhanced diagnostics
            diagnosis = EnhancedDiagnostics.diagnose_pattern_failure(
                safe_pattern, 
                language, 
                code[:500],  # First 500 chars as context
                None
            )
            
            result["debug_info"] = {
                "pattern_used": safe_pattern,
                "pattern_normalized": safe_pattern != pattern,
                "code_length": len(code),
                "language": language,
                "suggestion": self._get_pattern_suggestion(language, pattern),
                "help": diagnosis["helpful_message"]
            }
            
            # Add specific diagnostics
            if diagnosis["likely_issues"]:
                result["pattern_issues"] = diagnosis["likely_issues"]
            
            if diagnosis["suggested_patterns"]:
                result["try_these_patterns"] = [
                    s["pattern"] for s in diagnosis["suggested_patterns"][:3]
                ]
            
            if diagnosis["examples_that_would_match"]:
                result["pattern_examples"] = diagnosis["examples_that_would_match"][:2]
            
            # Add common pattern examples for the language
            from ..language_handlers import get_handler
            handler = get_handler(language)
            if handler:
                common_patterns = handler.get_default_patterns()
                if common_patterns:
                    result["debug_info"]["common_patterns"] = dict(list(common_patterns.items())[:5])

        # Add diagnostic information for detailed verbosity
        if (
            self.config.diagnostic_config.verbosity in ["detailed", "diagnostic"]
            and self.config.diagnostic_config.pattern_diagnostics
        ):
            result["diagnostics"] = diagnostics

        return result
    
    def _get_pattern_suggestion(self, language: str, pattern: str) -> str:
        """Get pattern suggestion based on language and pattern."""
        suggestions = []
        
        # Language-specific suggestions
        if language == "rust":
            if "fn" in pattern and "$$$PARAMS" in pattern:
                suggestions.append("For Rust functions, use 'fn $NAME' or 'async fn $NAME' instead of complex parameter patterns")
            elif "async" in pattern:
                suggestions.append("Try 'async fn $NAME' or 'pub async fn $NAME'")
            elif "impl" in pattern:
                suggestions.append("Try 'impl $TYPE' or 'impl $TRAIT for $TYPE'")
        elif language == "python":
            if "def" in pattern and ":" not in pattern:
                suggestions.append("Python functions need colons: 'def $NAME($$$PARAMS):'")
            elif "class" in pattern and ":" not in pattern:
                suggestions.append("Python classes need colons: 'class $NAME:'")
        elif language in ["javascript", "typescript"]:
            if "function" in pattern and "{" not in pattern:
                suggestions.append("JavaScript functions need braces: 'function $NAME($$$PARAMS) { $$$BODY }'")
            elif "=>" in pattern:
                suggestions.append("Arrow functions: '($$$PARAMS) => $EXPR' or '($$$PARAMS) => { $$$BODY }'")
        
        # General suggestions
        if "$$" in pattern and "$$$" not in pattern:
            suggestions.append("Use $$$ for multiple items (like parameters), not $$")
        
        if re.search(r'\b[A-Z_]+\b', pattern) and "$" not in pattern:
            suggestions.append("Add $ prefix to metavariables (e.g., $NAME instead of NAME)")
        
        # Build final suggestion message
        if suggestions:
            return "\n".join(suggestions)
        else:
            return f"Try simpler patterns first. See pattern examples with 'get_language_patterns' for {language}."

    @handle_errors
    def validate_pattern(
        self, pattern: str, language: str, code: Optional[str] = None
    ) -> Dict[str, Any]:
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
            return {
                "is_valid": False,
                "error": f"Language '{language}' is not supported",
                "supported_languages": list(self.analyzer.supported_languages),
            }

        # Sanitize pattern
        safe_pattern = sanitize_pattern(pattern)
        if safe_pattern != pattern:
            self.logger.warning("Pattern was sanitized for security reasons")

        # Get full diagnostics
        diagnostics = self._get_pattern_diagnostics(safe_pattern, language, code)

        result = {
            "is_valid": diagnostics["is_valid"],
            "pattern": safe_pattern,
            "language": language,
            "diagnostics": {
                "errors": diagnostics.get("error_details", []),
                "has_errors": not diagnostics["is_valid"],
            },
        }

        # Add error message if not valid
        if not diagnostics["is_valid"]:
            result["error"] = diagnostics.get("error", "Pattern validation failed")

            # Add detailed error breakdown
            if "error_details" in diagnostics:
                error_summary = []
                for err in diagnostics["error_details"]:
                    if isinstance(err, dict):
                        msg = err.get("message", "Unknown error")
                        if "position" in err:
                            msg += f" at position {err['position']}"
                        error_summary.append(msg)
                if error_summary:
                    result["error_summary"] = error_summary

        # Add corrected pattern if available
        if (
            "corrected_pattern" in diagnostics
            and diagnostics.get("correction_confidence", 0) > 0.7
        ):
            result["corrected_pattern"] = diagnostics["corrected_pattern"]
            result["correction_confidence"] = diagnostics["correction_confidence"]
            result["correction_hint"] = (
                f"Did you mean: {diagnostics['corrected_pattern']}?"
            )

        # Add suggestions based on configuration
        if self.config.diagnostic_config.show_suggestions:
            suggestions = diagnostics.get("suggestions", [])
            if suggestions:
                result["suggestions"] = suggestions

            if "suggestion_message" in diagnostics:
                result["suggestion_message"] = diagnostics["suggestion_message"]

        # Add pattern examples based on configuration
        if self.config.diagnostic_config.show_examples:
            # Get language handler for examples
            handler = get_handler(language)
            if handler:
                patterns = handler.get_default_patterns()
                if patterns:
                    # Show a few relevant examples
                    examples = []
                    pattern_lower = pattern.lower()
                    for name, example in patterns.items():
                        if any(
                            keyword in pattern_lower
                            for keyword in name.lower().split("_")
                        ):
                            examples.append({"name": name, "pattern": example})
                        if len(examples) >= 3:
                            break

                    # If no relevant examples found, show the first 3
                    if not examples:
                        examples = [
                            {"name": name, "pattern": pat}
                            for name, pat in list(patterns.items())[:3]
                        ]

                    result["examples"] = examples

        # Add test results if code was provided
        if code and "has_matches" in diagnostics:
            result["test_results"] = {
                "has_matches": diagnostics["has_matches"],
                "match_count": diagnostics.get("match_count", 0),
            }

        return result

    @handle_errors
    @cached
    def refactor_code(
        self, code: str, language: str, pattern: str, replacement: str
    ) -> Dict[str, Any]:
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
            return {
                "error": "Language '" + language + "' is not supported",
                "success": False,
                "refactored_code": code,
            }

        # Sanitize pattern and replacement to prevent command injection
        safe_pattern = sanitize_pattern(pattern)
        safe_replacement = sanitize_pattern(replacement)

        if safe_pattern != pattern or safe_replacement != replacement:
            self.logger.warning(
                "Pattern or replacement was sanitized for security reasons"
            )

        # Validate pattern if configured
        if self.config.refactoring_config.validate_replacements:
            diagnostics = self._get_pattern_diagnostics(safe_pattern, language, code)
            if (
                not diagnostics["is_valid"]
                and self.config.pattern_config.validation_strictness != "relaxed"
            ):
                error_msg = diagnostics["error"] or "Invalid pattern"
                result = {
                    "error": error_msg,
                    "success": False,
                    "refactored_code": code,  # Add the original code to the result
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
        if (
            self.config.refactoring_config.max_replacements is not None
            and match_count > self.config.refactoring_config.max_replacements
        ):
            return {
                "error": f"Too many replacements ({match_count}). "
                f"Maximum allowed: {self.config.refactoring_config.max_replacements}",
                "matches": match_count,
                "success": False,
                "refactored_code": code,  # Add the original code to the result
            }

        # Apply the refactoring
        refactored_code = self.analyzer.apply_refactoring(
            code,
            language,
            safe_pattern,
            safe_replacement
        )

        elapsed = time.time() - start_time

        # Count matches (by comparing refactored code with original)
        changes_made = original_code != refactored_code

        self.logger.debug(
            "Refactoring complete in "
            + str(elapsed)
            + "s (changes made: "
            + str(changes_made)
            + ")"
        )

        result = {
            "original_code": original_code,
            "refactored_code": refactored_code,
            "success": changes_made,
            "language": language,
            "matches": match_count,
        }

        # Add diagnostic information for detailed verbosity
        if (
            self.config.diagnostic_config.verbosity in ["detailed", "diagnostic"]
            and self.config.diagnostic_config.pattern_diagnostics
        ):
            result["pattern_diagnostics"] = self._get_pattern_diagnostics(
                safe_pattern, language, code
            )

        return result

    @handle_errors
    def preview_refactoring(
        self, code: str, language: str, pattern: str, replacement: str
    ) -> Dict[str, Any]:
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
        lines = code.split("\n")

        # Sort matches by line number (descending) to avoid position shifts
        sorted_matches = sorted(
            matches, key=lambda m: m["location"]["start"]["line"], reverse=True
        )

        for match in sorted_matches:
            start_line = match["location"]["start"]["line"]
            end_line = match["location"]["end"]["line"]

            # Get context lines
            context_before = max(
                0, start_line - self.config.output_config.context_lines
            )
            context_after = min(
                len(lines), end_line + self.config.output_config.context_lines
            )

            # Create a preview entry
            preview_entry = {
                "match": match,
                "context": {
                    "before": lines[context_before:start_line],
                    "match": lines[start_line:end_line],
                    "after": lines[end_line:context_after],
                },
                "replacement": safe_replacement,
            }

            preview.append(preview_entry)

        # Return the preview information
        return {
            "matches": matches,
            "count": len(matches),
            "preview": preview,
            "language": language,
            "pattern": safe_pattern,
            "replacement": safe_replacement,
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
            return {
                "error": "File '" + file_path + "' does not exist or is not a file",
                "matches": [],
            }

        # Check if file should be ignored
        if self.ignore_handler.should_ignore(str(path)):
            self.logger.debug(f"Skipping ignored file: {file_path}")
            return {
                "error": f"File '{file_path}' is ignored by configuration",
                "matches": [],
            }

        # Determine language from file extension
        extension = path.suffix.lower()
        language = None

        # If using AstAnalyzerV2, use language_extensions mapping
        if hasattr(self.analyzer, 'language_extensions'):
            language = self.analyzer.language_extensions.get(extension)
        else:
            # For backward compatibility with original AstAnalyzer
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

            self.logger.debug(
                "Analyzing file: " + file_path + " with pattern: " + safe_pattern
            )
            start_time = time.time()

            # Use the cached analyze_code method
            result = self.analyze_code(code, language, safe_pattern)
            elapsed = time.time() - start_time

            self.logger.debug("File analysis complete in " + str(elapsed) + "s")

            return {
                "file": str(path),
                "language": language,
                "matches": result.get("matches", []),
                "count": result.get("count", 0),
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
        file_extensions: Optional[List[str]] = None,
        page: int = 1,
        page_size: Optional[int] = None,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search for pattern matches in all files in a directory.

        Args:
            directory: Directory to search
            pattern: Pattern to search for
            parallel: Whether to use parallel processing (default: True)
            max_workers: Maximum number of worker processes (default: CPU count)
            file_extensions: List of file extensions to include (default: all supported)
            page: Page number for pagination (1-based)
            page_size: Number of results per page (auto-calculated if None)
            max_results: Maximum total number of results to return (limits before pagination)

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
            
            # If using AstAnalyzerV2, check language_extensions
            if hasattr(self.analyzer, 'language_extensions'):
                return ext in self.analyzer.language_extensions
            else:
                # For backward compatibility with original AstAnalyzer
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
            file_filter=file_filter,
        )

        elapsed = time.time() - start_time
        files_searched = result.get("files_searched", 0)
        files_with_matches = result.get("files_with_matches", 0)

        self.logger.info(
            "Search complete in " + str(elapsed) + "s. "
            "Found matches in "
            + str(files_with_matches)
            + "/"
            + str(files_searched)
            + " files."
        )
        
        # Try pattern fixes if no matches found
        if files_with_matches == 0 and self.config.pattern_config.fuzzy_matching:
            self.logger.info(f"No matches found for pattern '{safe_pattern}', trying alternatives...")
            
            # Detect language from file extensions
            detected_language = None
            if file_extensions:
                ext_map = {
                    ".rs": "rust",
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".go": "go",
                    ".c": "c",
                }
                for ext in file_extensions:
                    if ext in ext_map:
                        detected_language = ext_map[ext]
                        break
            
            if detected_language:
                # Get alternative patterns
                alternatives = PatternFixer.fix_pattern(safe_pattern, detected_language)
                fuzzy_alternatives = FuzzyPatternMatcher.make_pattern_fuzzy(safe_pattern, detected_language)
                alternatives.extend(fuzzy_alternatives)
                
                # Remove duplicates and original
                alternatives = list(dict.fromkeys(alternatives))
                if safe_pattern in alternatives:
                    alternatives.remove(safe_pattern)
                
                # Try each alternative (limit to 3 for performance)
                for alt_pattern in alternatives[:3]:
                    self.logger.info(f"Trying alternative pattern: {alt_pattern}")
                    alt_result = self.analyzer.search_directory(
                        directory,
                        alt_pattern,
                        parallel=parallel,
                        max_workers=max_workers,
                        file_filter=file_filter,
                    )
                    
                    if alt_result.get("files_with_matches", 0) > 0:
                        self.logger.info(f"Found matches with alternative pattern: {alt_pattern}")
                        result = alt_result
                        result["pattern_used"] = alt_pattern
                        result["original_pattern"] = safe_pattern
                        result["pattern_fixed"] = True
                        result["fix_reason"] = PatternFixer.explain_pattern_issue(safe_pattern, detected_language)
                        files_with_matches = result.get("files_with_matches", 0)
                        break
        
        # Add debug info if still no matches found
        if files_with_matches == 0:
            # Detect language from file extensions
            detected_language = None
            if file_extensions:
                ext_map = {
                    ".rs": "rust",
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".go": "go",
                    ".c": "c",
                }
                for ext in file_extensions:
                    if ext in ext_map:
                        detected_language = ext_map[ext]
                        break
            
            result["debug_info"] = {
                "pattern_used": safe_pattern,
                "original_pattern": pattern if pattern != safe_pattern else None,
                "files_searched": files_searched,
                "suggestion": (
                    "No matches found. Try:\n"
                    "1. Use simpler patterns (e.g., 'async fn' instead of 'async fn $NAME')\n"
                    "2. Check file extensions match the language\n"
                    "3. Use find_pattern() for natural language search\n"
                    "4. Use get_common_patterns() to see working patterns"
                ),
                "pattern_help": self._get_pattern_suggestion(detected_language or "unknown", pattern)
            }
            
            # Use pattern simplifier to suggest alternatives
            if detected_language:
                simplified_patterns = self.pattern_simplifier.simplify_pattern(safe_pattern, detected_language)
                if simplified_patterns:
                    result["debug_info"]["simplified_patterns"] = [
                        {"pattern": p, "description": desc} 
                        for p, desc in simplified_patterns[:5]  # Limit to 5 suggestions
                    ]
                
                # Add pattern examples
                examples = self.pattern_simplifier.get_pattern_examples(detected_language)
                if examples:
                    # Show most relevant examples
                    result["debug_info"]["pattern_examples"] = {}
                    for category, patterns in examples.items():
                        result["debug_info"]["pattern_examples"][category] = patterns[:3]

        # Log cache statistics periodically
        result_cache.log_stats()
        
        # Apply max_results limit if specified
        if max_results and "matches" in result:
            total_matches = sum(
                len(matches) if isinstance(matches, list) else 0 
                for matches in result["matches"].values()
            )
            
            if total_matches > max_results:
                # Sort files by match count to keep most relevant
                sorted_files = sorted(
                    result["matches"].items(),
                    key=lambda x: len(x[1]) if isinstance(x[1], list) else 0,
                    reverse=True
                )
                
                # Keep only enough files to reach max_results
                limited_matches = {}
                matches_added = 0
                
                for file_path, matches in sorted_files:
                    if matches_added >= max_results:
                        break
                    
                    matches_list = matches if isinstance(matches, list) else []
                    remaining = max_results - matches_added
                    
                    if len(matches_list) <= remaining:
                        limited_matches[file_path] = matches_list
                        matches_added += len(matches_list)
                    else:
                        # Truncate matches to fit within limit
                        limited_matches[file_path] = matches_list[:remaining]
                        matches_added = max_results
                        
                result["matches"] = limited_matches
                result["truncated"] = True
                result["original_total_matches"] = total_matches
        
        # Check if pagination is needed
        if self.paginator.should_paginate(result, "search") or page > 1 or page_size is not None:
            # Convert matches dict to a list for pagination
            match_items = []
            for file_path, matches in result.get("matches", {}).items():
                match_items.append({
                    "file": file_path,
                    "matches": matches,
                    "count": len(matches) if isinstance(matches, list) else 0
                })
            
            # Sort by match count (most matches first)
            match_items.sort(key=lambda x: x["count"], reverse=True)
            
            # Create summary function
            def create_search_summary(items):
                return {
                    "total_files": len(items),
                    "total_matches": sum(item["count"] for item in items),
                    "files_with_matches": sum(1 for item in items if item["count"] > 0),
                    "top_files": [
                        {"file": item["file"], "matches": item["count"]} 
                        for item in items[:5]
                    ]
                }
            
            # Paginate the results
            paginated = self.paginator.paginate_list(
                match_items,
                page=page,
                page_size=page_size,
                response_type="search",
                summary_fn=create_search_summary
            )
            
            # Convert back to expected format
            paginated_matches = {}
            for item in paginated.items:
                paginated_matches[item["file"]] = item["matches"]
            
            # Create a minimal response to ensure we stay within token limits
            response = {
                "matches": paginated_matches,
                "pagination": paginated.to_dict()["pagination"],
                "summary": paginated.summary,
            }
            
            # Only add additional fields if we have room
            minimal_response_size = self.paginator.estimate_tokens(response)
            limit = self.paginator.TOKEN_LIMITS.get("search", 15000)
            
            # Add optional fields only if they won't exceed limits
            if minimal_response_size < limit * 0.9:  # Keep 10% buffer
                response["files_searched"] = result.get("files_searched", 0)
                response["elapsed_time"] = elapsed
                response["pattern"] = pattern
                response["directory"] = directory
            
            return response

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
                "error": "Language '"
                + language
                + "' is not supported or has no templates",
                "patterns": {},
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
                    if file.endswith(".yml") or file.endswith(".yaml"):
                        file_path = os.path.join(template_dir, file)
                        with open(file_path, "r") as f:
                            import yaml

                            custom_patterns = yaml.safe_load(f)
                            if isinstance(custom_patterns, dict):
                                patterns.update(custom_patterns)
                                self.logger.debug(
                                    f"Loaded {len(custom_patterns)} patterns from {file_path}"
                                )
            except Exception as e:
                self.logger.error(
                    f"Error loading patterns from {template_dir}: {str(e)}"
                )

        # Add custom patterns from configuration
        if language in self.config.pattern_config.custom_patterns:
            custom_patterns = self.config.pattern_config.custom_patterns[language]
            if custom_patterns:
                patterns.update(custom_patterns)
                self.logger.debug(
                    f"Added {len(custom_patterns)} custom patterns from configuration"
                )

        return {"language": language, "patterns": patterns}

    @handle_errors
    def get_supported_languages(self) -> Dict[str, Any]:
        """
        Get a list of supported languages and their file extensions.

        Returns:
            Dictionary with supported languages and their file extensions
        """
        # Build language to extensions mapping
        languages = {}
        
        # If using AstAnalyzerV2, handle it differently
        if hasattr(self.analyzer, 'language_extensions'):
            # Reverse the mapping from extensions to languages
            for ext, lang in self.analyzer.language_extensions.items():
                if lang not in languages:
                    languages[lang] = []
                languages[lang].append(ext)
        else:
            # For backward compatibility with original AstAnalyzer
            base_languages = self.analyzer.supported_languages.copy()
            for language, extensions in base_languages.items():
                languages[language] = extensions

        # Get additional information from language handlers
        handlers = get_all_handlers()
        for name, handler in handlers.items():
            if name not in languages:
                languages[name] = handler.file_extensions

        return {"languages": languages}

    @handle_errors
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.

        Returns:
            Dictionary with the current configuration
        """
        return {"config": self.config.to_dict()}

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
            if (
                hasattr(self.config, "cache_size")
                and self.config.cache_size is not None
            ):
                result_cache.maxsize = self.config.cache_size
                self.logger.info(
                    "Updated result cache size to " + str(result_cache.maxsize)
                )

            return {"success": True, "config": self.config.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
                    "config": self.config.to_dict(),
                }
            else:
                # Return YAML representation if no output file specified
                return {
                    "success": True,
                    "config": self.config.to_dict(),
                    "yaml": self.config.to_yaml(),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @handle_errors
    def suggest_pattern_corrections(
        self, pattern: str, language: str, error_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest corrections for an invalid or problematic pattern.

        Args:
            pattern: The pattern to get suggestions for
            language: The programming language
            error_type: Optional specific error type to get fixes for

        Returns:
            Dictionary with correction suggestions
        """
        if language not in self.analyzer.supported_languages:
            return {
                "success": False,
                "error": f"Language '{language}' is not supported",
                "supported_languages": list(self.analyzer.supported_languages),
            }

        # Get suggestions from the autocorrector
        suggestions = self.autocorrector.suggest_corrections(pattern, language)

        # Get quick fixes if error_type is specified
        quick_fixes = []
        if error_type:
            quick_fixes = self.autocorrector.get_quick_fixes(
                pattern, language, error_type
            )

        # Try to auto-correct the pattern
        auto_corrected = self.autocorrector.auto_correct_pattern(pattern, language)

        # Format suggestions
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append(
                {
                    "pattern": suggestion.suggested,
                    "confidence": suggestion.confidence,
                    "reason": suggestion.reason,
                    "fixes": suggestion.applied_fixes,
                }
            )

        result = {
            "success": True,
            "original_pattern": pattern,
            "language": language,
            "suggestions": formatted_suggestions,
            "suggestion_count": len(formatted_suggestions),
        }

        # Add auto-corrected pattern if available
        if auto_corrected and auto_corrected != pattern:
            result["auto_corrected"] = auto_corrected
            result["auto_correction_available"] = True
        else:
            result["auto_correction_available"] = False

        # Add quick fixes if available
        if quick_fixes:
            result["quick_fixes"] = quick_fixes

        # Add formatted message
        if suggestions:
            result["message"] = create_pattern_suggestion_message(suggestions)

        # Validate the top suggestion if available
        if suggestions and suggestions[0].confidence > 0.7:
            validation = self._get_pattern_diagnostics(
                suggestions[0].suggested, language
            )
            if validation["is_valid"]:
                result["top_suggestion_valid"] = True
                result["recommended_pattern"] = suggestions[0].suggested
            else:
                result["top_suggestion_valid"] = False

        return result

    @handle_errors
    def search_directory_stream(
        self,
        directory: str,
        pattern: str,
        language: str,
        stream_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search a directory with streaming support for large result sets.

        This method returns immediately with streaming configuration.
        Actual results should be retrieved through a separate streaming endpoint.

        Args:
            directory: Directory to search
            pattern: Pattern to search for
            language: Programming language
            stream_config: Optional streaming configuration

        Returns:
            Dictionary with streaming session information
        """
        if language not in self.analyzer.supported_languages:
            return {
                "success": False,
                "error": f"Language '{language}' is not supported",
                "supported_languages": list(self.analyzer.supported_languages),
            }

        # Validate directory
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {directory}"}

        if not dir_path.is_dir():
            return {"success": False, "error": f"Path is not a directory: {directory}"}

        # Validate file access if configured
        if not validate_file_access(str(dir_path), self.config.safe_roots):
            self.logger.warning(f"Access denied to directory: {directory}")
            return {
                "success": False,
                "error": f"Access denied to directory: {directory}",
            }

        # Sanitize pattern
        safe_pattern = sanitize_pattern(pattern)
        if safe_pattern != pattern:
            self.logger.warning("Pattern was sanitized for security reasons")

        # Create streaming configuration
        config = StreamConfig()
        if stream_config:
            if "batch_size" in stream_config:
                config.batch_size = stream_config["batch_size"]
            if "max_results_per_file" in stream_config:
                config.max_results_per_file = stream_config["max_results_per_file"]
            if "enable_progress" in stream_config:
                config.enable_progress = stream_config["enable_progress"]

        # Count files to be searched
        extensions = self._get_extensions_for_language(language)
        total_files = 0
        for ext in extensions:
            files = list(dir_path.rglob(f"*{ext}"))
            # Apply ignore patterns
            files = [f for f in files if not self.ignore_handler.should_ignore(str(f))]
            total_files += len(files)

        # Create streaming session info
        session_id = f"stream_{int(time.time() * 1000)}"

        return {
            "success": True,
            "session_id": session_id,
            "streaming_config": {
                "batch_size": config.batch_size,
                "max_results_per_file": config.max_results_per_file,
                "enable_progress": config.enable_progress,
            },
            "search_info": {
                "directory": str(dir_path),
                "pattern": safe_pattern,
                "language": language,
                "estimated_files": total_files,
                "file_extensions": extensions,
            },
            "message": (
                f"Streaming search configured for {total_files} files. "
                "Results will be streamed in batches."
            ),
            "note": (
                "This is a placeholder for streaming functionality. "
                "In a real implementation, use the session_id to retrieve streamed results."
            ),
        }

    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for a language."""
        extension_map = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "rust": [".rs"],
            "go": [".go"],
            "c": [".c", ".h"],
            "lua": [".lua"],
        }
        return extension_map.get(language, [])
    
    @handle_errors
    def search_directory_with_context(
        self,
        directory: str,
        pattern: str,
        context_lines: int = 3,
        include_metrics: bool = True,
        parallel: bool = True,
        max_workers: Optional[int] = None,
        file_extensions: Optional[List[str]] = None,
        page: int = 1,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search for pattern matches in a directory with context and metrics.
        
        Args:
            directory: Directory to search
            pattern: Pattern to search for
            context_lines: Number of lines to show before/after matches
            include_metrics: Whether to include code metrics
            parallel: Whether to use parallel processing
            max_workers: Maximum number of worker processes
            file_extensions: List of file extensions to include
            
        Returns:
            Dictionary with matches, context, and metrics
        """
        # Validate directory access permissions
        access_error = validate_file_access(directory, self.config.safe_roots)
        if access_error:
            return {"error": access_error, "matches": {}}
        
        # Normalize and validate directory path
        try:
            dir_path = self._normalize_directory_path(directory)
        except ValueError as e:
            return {"error": str(e), "matches": {}}
        
        # Sanitize pattern but preserve AST metavariables
        safe_pattern = sanitize_pattern(pattern)
        if safe_pattern != pattern:
            self.logger.warning(f"Pattern was sanitized for security reasons: '{pattern}' -> '{safe_pattern}'")
        
        self.logger.info(f"Searching directory with context: {dir_path}")
        start_time = time.time()
        
        # Create file filter
        def file_filter(path: Path) -> bool:
            if self.ignore_handler.should_ignore(str(path)):
                return False
            
            if file_extensions:
                return path.suffix.lower() in file_extensions
            
            ext = path.suffix.lower()
            for exts in self.analyzer.supported_languages.values():
                if ext in exts:
                    return True
            return False
        
        # Process files and collect results with context
        results_with_context = {}
        total_matches = 0
        total_files = 0
        files_with_matches = 0
        
        # Get all files to process (dir_path already normalized)
        files_to_process = []
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_filter(file_path):
                files_to_process.append(file_path)
        
        total_files = len(files_to_process)
        
        if parallel and len(files_to_process) > 1:
            # Process files in parallel
            import concurrent.futures
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for file_path in files_to_process:
                    future = executor.submit(
                        self._process_file_with_context,
                        file_path, safe_pattern, context_lines, include_metrics
                    )
                    futures[future] = file_path
                
                for future in concurrent.futures.as_completed(futures):
                    file_path = futures[future]
                    try:
                        result = future.result()
                        if result and result["matches"]:
                            results_with_context[str(file_path)] = result
                            total_matches += result["match_count"]
                            files_with_matches += 1
                    except Exception as e:
                        self.logger.error(f"Error processing {file_path}: {e}")
        else:
            # Process files sequentially
            for file_path in files_to_process:
                try:
                    result = self._process_file_with_context(
                        file_path, safe_pattern, context_lines, include_metrics
                    )
                    if result and result["matches"]:
                        results_with_context[str(file_path)] = result
                        total_matches += result["match_count"]
                        files_with_matches += 1
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
        
        elapsed = time.time() - start_time
        
        # Calculate overall metrics if requested
        overall_metrics = {}
        if include_metrics:
            overall_metrics = self._calculate_directory_metrics(results_with_context)
        
        self.logger.info(
            f"Search with context complete in {elapsed:.2f}s. "
            f"Found {total_matches} matches in {files_with_matches}/{total_files} files."
        )
        
        # Prepare result
        result = {
            "directory": directory,
            "pattern": safe_pattern,
            "total_files_searched": total_files,
            "files_with_matches": files_with_matches,
            "total_matches": total_matches,
            "context_lines": context_lines,
            "results": results_with_context,
            "metrics": overall_metrics if include_metrics else None,
            "elapsed_time": elapsed,
        }
        
        # Check if pagination is needed
        if self.paginator.should_paginate(result, "search"):
            # Convert results dict to a list for pagination
            result_items = []
            for file_path, file_result in results_with_context.items():
                result_items.append({
                    "file": file_path,
                    "result": file_result,
                    "match_count": file_result.get("match_count", 0)
                })
            
            # Sort by match count (most matches first)
            result_items.sort(key=lambda x: x["match_count"], reverse=True)
            
            # Create summary function
            def create_context_summary(items):
                return {
                    "total_files": len(items),
                    "total_matches": sum(item["match_count"] for item in items),
                    "files_with_matches": sum(1 for item in items if item["match_count"] > 0),
                    "context_lines": context_lines,
                    "top_files": [
                        {"file": item["file"], "matches": item["match_count"]} 
                        for item in items[:5]
                    ]
                }
            
            # Paginate the results
            paginated = self.paginator.paginate_list(
                result_items,
                page=page,
                page_size=page_size,
                response_type="search",
                summary_fn=create_context_summary
            )
            
            # Convert back to expected format
            paginated_results = {}
            for item in paginated.items:
                paginated_results[item["file"]] = item["result"]
            
            # Return paginated response
            return {
                "directory": directory,
                "pattern": safe_pattern,
                "total_files_searched": total_files,
                "files_with_matches": files_with_matches,
                "total_matches": total_matches,
                "context_lines": context_lines,
                "results": paginated_results,
                "pagination": paginated.to_dict()["pagination"],
                "summary": paginated.summary,
                "metrics": overall_metrics if include_metrics else None,
                "elapsed_time": elapsed,
            }
        
        return result
    
    def _process_file_with_context(
        self,
        file_path: Path,
        pattern: str,
        context_lines: int,
        include_metrics: bool
    ) -> Optional[Dict[str, Any]]:
        """Process a single file and return matches with context."""
        try:
            # Determine language
            extension = file_path.suffix.lower()
            language = None
            
            # Handle both AstAnalyzerV2 (with language_extensions) and original AstAnalyzer
            if hasattr(self.analyzer, 'language_extensions'):
                # AstAnalyzerV2 uses language_extensions mapping
                language = self.analyzer.language_extensions.get(extension)
            else:
                # Original AstAnalyzer uses supported_languages dict
                for lang, exts in self.analyzer.supported_languages.items():
                    if extension in exts:
                        language = lang
                        break
            
            if not language:
                return None
            
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
            
            # Find matches using analyze_code for consistency with other functions
            analysis_result = self.analyzer.analyze_code(content, language, pattern)
            matches = analysis_result.get("matches", []) if analysis_result else []
            
            if not matches:
                return None
            
            # Add context to each match
            matches_with_context = []
            for match in matches:
                start_line = match["location"]["start"]["line"] - 1  # 0-indexed
                end_line = match["location"]["end"]["line"]
                
                # Calculate context boundaries
                context_start = max(0, start_line - context_lines)
                context_end = min(len(lines), end_line + context_lines)
                
                # Extract context
                before_context = lines[context_start:start_line]
                match_lines = lines[start_line:end_line]
                after_context = lines[end_line:context_end]
                
                match_with_context = {
                    **match,
                    "context": {
                        "before": before_context,
                        "match": match_lines,
                        "after": after_context,
                        "start_line": context_start + 1,  # 1-indexed for display
                        "end_line": context_end,
                    }
                }
                matches_with_context.append(match_with_context)
            
            result = {
                "matches": matches_with_context,
                "match_count": len(matches),
                "language": language,
            }
            
            # Calculate file metrics if requested
            if include_metrics:
                metrics = self._calculate_file_metrics(content, language, matches)
                result["metrics"] = metrics
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def _calculate_file_metrics(
        self,
        content: str,
        language: str,
        matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate code metrics for a file."""
        lines = content.split("\n")
        
        # Basic metrics
        metrics = {
            "total_lines": len(lines),
            "non_empty_lines": sum(1 for line in lines if line.strip()),
            "match_density": len(matches) / len(lines) if lines else 0,
        }
        
        # Language-specific metrics
        if language == "python":
            metrics.update(self._calculate_python_metrics(content))
        elif language in ["javascript", "typescript"]:
            metrics.update(self._calculate_js_metrics(content))
        elif language == "rust":
            metrics.update(self._calculate_rust_metrics(content))
        
        return metrics
    
    def _calculate_python_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate Python-specific metrics."""
        import ast
        try:
            tree = ast.parse(content)
            
            # Count different node types
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            imports = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)))
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
            }
        except:
            return {}
    
    def _calculate_js_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate JavaScript/TypeScript metrics."""
        # Simple regex-based metrics
        import re
        
        functions = len(re.findall(r'\bfunction\s+\w+', content))
        arrow_functions = len(re.findall(r'=>', content))
        classes = len(re.findall(r'\bclass\s+\w+', content))
        imports = len(re.findall(r'\bimport\s+', content))
        
        return {
            "functions": functions + arrow_functions,
            "classes": classes,
            "imports": imports,
        }
    
    def _calculate_rust_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate Rust-specific metrics."""
        import re
        
        functions = len(re.findall(r'\bfn\s+\w+', content))
        structs = len(re.findall(r'\bstruct\s+\w+', content))
        enums = len(re.findall(r'\benum\s+\w+', content))
        traits = len(re.findall(r'\btrait\s+\w+', content))
        impls = len(re.findall(r'\bimpl\s+', content))
        
        return {
            "functions": functions,
            "structs": structs,
            "enums": enums,
            "traits": traits,
            "implementations": impls,
        }
    
    def _calculate_directory_metrics(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall metrics for directory search results."""
        total_lines = 0
        total_functions = 0
        total_classes = 0
        language_distribution = {}
        
        for file_path, file_result in results.items():
            if "metrics" in file_result:
                metrics = file_result["metrics"]
                total_lines += metrics.get("total_lines", 0)
                total_functions += metrics.get("functions", 0)
                total_classes += metrics.get("classes", 0) + metrics.get("structs", 0)
            
            language = file_result.get("language", "unknown")
            language_distribution[language] = language_distribution.get(language, 0) + 1
        
        return {
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "language_distribution": language_distribution,
            "average_matches_per_file": sum(r["match_count"] for r in results.values()) / len(results) if results else 0,
        }
    
    @handle_errors
    def run_security_audit(
        self,
        language: str,
        directory: str,
        severity_filter: Optional[List[str]] = None,
        custom_rules_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a comprehensive security audit on a codebase.
        
        Args:
            language: Programming language to audit (python, rust, javascript, etc.)
            directory: Directory to audit
            severity_filter: Filter results by severity (error, warning, info)
            custom_rules_path: Path to custom rules file (optional)
            
        Returns:
            Dictionary with security audit results
        """
        # Map languages to security rule files
        rules_dir = Path(__file__).parent.parent.parent.parent / "rules"
        
        security_rule_files = {
            "python": rules_dir / "python-security.yaml",
            "rust": rules_dir / "rust-security-enhanced.yaml",  # Use enhanced rules
            "javascript": rules_dir / "javascript-best-practices.yaml",
            "typescript": rules_dir / "javascript-best-practices.yaml",
        }
        
        # Fall back to original rules if enhanced doesn't exist
        if language == "rust" and not (rules_dir / "rust-security-enhanced.yaml").exists():
            security_rule_files["rust"] = rules_dir / "rust-security.yaml"
        
        rule_file = security_rule_files.get(language)
        if not rule_file or not rule_file.exists():
            # Try to find a rule file for the language
            rule_file = rules_dir / f"{language}-security.yaml"
            if not rule_file.exists():
                return {
                    "error": f"No security rules available for language: {language}",
                    "supported_languages": list(security_rule_files.keys()),
                }
        
        # Load security rules
        self.logger.info(f"Loading security rules from {rule_file}")
        loaded_rules = self.rule_tools.load_rules(str(rule_file))
        
        if not loaded_rules.get("success"):
            return {
                "error": f"Failed to load security rules: {loaded_rules.get('error', 'Unknown error')}",
            }
        
        rule_ids = loaded_rules["rule_ids"]
        
        # Load custom rules if provided
        if custom_rules_path:
            custom_rules = self.rule_tools.load_rules(custom_rules_path)
            if custom_rules.get("success"):
                rule_ids.extend(custom_rules["rule_ids"])
        
        self.logger.info(f"Running security audit with {len(rule_ids)} rules on {directory}")
        
        # Normalize and validate directory path
        try:
            dir_path = self._normalize_directory_path(directory)
        except ValueError as e:
            return {"error": str(e)}
        
        # Filter by language extensions
        extensions = self._get_extensions_for_language(language)
        files_to_audit = []
        
        for ext in extensions:
            files = list(dir_path.rglob(f"*{ext}"))
            files = [f for f in files if not self.ignore_handler.should_ignore(str(f))]
            files_to_audit.extend(files)
        
        total_files = len(files_to_audit)
        findings_by_severity = {"error": [], "warning": [], "info": [], "hint": []}
        findings_by_rule = {}
        total_findings = 0
        max_findings_per_severity = 50  # Limit findings to prevent token overflow
        
        # Process each file
        for file_path in files_to_audit:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Run rules on the file
                results = self.rule_tools.run_rules(
                    content,
                    language,
                    rule_ids=rule_ids,
                    severities=severity_filter,
                    file_path=str(file_path)
                )
                
                if results.get("matches"):
                    for finding in results["matches"]:
                        # Check if we've reached the limit for this severity
                        severity = finding.get("severity", "info")
                        if len(findings_by_severity[severity]) >= max_findings_per_severity:
                            continue  # Skip if we've reached the limit
                        
                        # Add file path to finding
                        finding["file"] = str(file_path.relative_to(dir_path))
                        
                        # Categorize by severity
                        findings_by_severity[severity].append(finding)
                        
                        # Categorize by rule (but limit rule findings too)
                        rule_id = finding.get("rule_id", "unknown")
                        if rule_id not in findings_by_rule:
                            findings_by_rule[rule_id] = {
                                "rule_id": rule_id,
                                "message": finding.get("message", ""),
                                "severity": severity,
                                "findings": []
                            }
                        
                        # Limit findings per rule to 20
                        if len(findings_by_rule[rule_id]["findings"]) < 20:
                            findings_by_rule[rule_id]["findings"].append(finding)
                        
                        total_findings += 1
                        
            except Exception as e:
                self.logger.error(f"Error auditing file {file_path}: {e}")
        
        # Calculate risk score (simple scoring system)
        risk_score = (
            len(findings_by_severity["error"]) * 10 +
            len(findings_by_severity["warning"]) * 5 +
            len(findings_by_severity["info"]) * 1
        ) / max(total_files, 1)
        
        risk_level = "low"
        if risk_score > 10:
            risk_level = "critical"
        elif risk_score > 5:
            risk_level = "high"
        elif risk_score > 2:
            risk_level = "medium"
        
        # Generate summary
        summary = {
            "language": language,
            "directory": str(directory),
            "total_files_audited": total_files,
            "total_findings": total_findings,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "findings_by_severity": {
                sev: len(findings) for sev, findings in findings_by_severity.items()
            },
            "findings_by_rule": findings_by_rule,
            "detailed_findings": findings_by_severity,
            "rules_used": len(rule_ids),
        }
        
        # Add recommendations
        recommendations = []
        if findings_by_severity["error"]:
            recommendations.append("Address all critical security errors immediately")
        if findings_by_rule.get("hardcoded-password") or findings_by_rule.get("hardcoded-secrets"):
            recommendations.append("Move all hardcoded secrets to environment variables or secure storage")
        if findings_by_rule.get("sql-injection-risk") or findings_by_rule.get("sql-query-construction"):
            recommendations.append("Use parameterized queries to prevent SQL injection")
        if language == "rust" and findings_by_rule.get("unsafe-block-usage"):
            recommendations.append("Review all unsafe blocks and document their necessity")
        
        summary["recommendations"] = recommendations
        
        # Add truncation warnings if we hit limits
        truncation_info = {}
        for severity, findings in findings_by_severity.items():
            if len(findings) >= max_findings_per_severity:
                truncation_info[f"{severity}_truncated"] = True
                truncation_info[f"{severity}_showing"] = max_findings_per_severity
        
        # Check if any rules hit their limit
        truncated_rules = [rule_id for rule_id, rule_info in findings_by_rule.items() 
                          if len(rule_info["findings"]) >= 20]
        if truncated_rules:
            truncation_info["rules_truncated"] = truncated_rules
        
        if truncation_info:
            summary["truncation_info"] = truncation_info
            summary["note"] = "Results were limited to prevent token overflow. Use run_security_audit_streaming() for complete results."
        
        return summary
    
    @handle_errors
    def build_pattern(
        self,
        pattern_type: str,
        language: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build complex patterns using the pattern builder.
        
        Args:
            pattern_type: Type of pattern to build (e.g., "function", "class", "custom")
            language: Programming language
            options: Pattern-specific options
            
        Returns:
            Dictionary with the built pattern and examples
        """
        try:
            options = options or {}
            
            # Create a pattern builder for the language
            builder = PatternBuilder(language)
        except Exception as e:
            return {
                "error": f"Failed to initialize pattern builder: {str(e)}",
                "pattern_type": pattern_type,
                "language": language,
                "suggestion": "Ensure the language is supported and pattern type is valid."
            }
        
        # Build pattern based on type
        if pattern_type == "function":
            name = options.get("name")
            is_async = options.get("async", False)
            visibility = options.get("visibility")
            name_pattern = options.get("name_pattern")
            return_type = options.get("return_type")
            parameters = options.get("parameters")
            
            # Build the base pattern
            if is_async:
                builder.async_function(name, simple=False)
            else:
                builder.function(name)
                
            # Get the base pattern
            base_pattern = builder.build()
            
            # Now enhance the pattern based on options
            if language == "rust":
                # Handle Rust-specific patterns
                pattern_parts = []
                
                # Add visibility
                if visibility:
                    pattern_parts.append(visibility)
                
                # Parse the base pattern and rebuild with options
                if is_async:
                    pattern_parts.append("async")
                pattern_parts.append("fn")
                
                # Handle name pattern
                if name_pattern:
                    # Extract the wildcard pattern
                    if name_pattern.endswith(".*"):
                        # Convert regex-style to ast-grep style
                        prefix = name_pattern[:-2]
                        pattern_parts.append(f"{prefix}$NAME")
                    else:
                        pattern_parts.append(name_pattern)
                elif name:
                    pattern_parts.append(name)
                else:
                    pattern_parts.append("$NAME")
                    
                # Add parameters
                if parameters:
                    pattern_parts.append(f"({parameters})")
                else:
                    pattern_parts.append("($$$PARAMS)")
                    
                # Add return type
                if return_type:
                    # Handle pattern-style return types
                    if return_type.startswith("Result<"):
                        pattern_parts.append(f"-> {return_type}")
                    else:
                        pattern_parts.append(f"-> {return_type}")
                        
                # Add body
                pattern_parts.append("{ $$$BODY }")
                
                pattern = " ".join(pattern_parts)
                
            elif language in ["javascript", "typescript"]:
                # Handle JS/TS patterns
                pattern_parts = []
                
                if visibility:
                    pattern_parts.append(visibility)
                    
                if is_async:
                    pattern_parts.append("async")
                    
                pattern_parts.append("function")
                
                # Handle name pattern
                if name_pattern:
                    if name_pattern.endswith(".*"):
                        prefix = name_pattern[:-2]
                        pattern_parts.append(f"{prefix}$NAME")
                    else:
                        pattern_parts.append(name_pattern)
                elif name:
                    pattern_parts.append(name)
                else:
                    pattern_parts.append("$NAME")
                    
                # Add parameters
                if parameters:
                    pattern_parts.append(f"({parameters})")
                else:
                    pattern_parts.append("($$$PARAMS)")
                    
                # Add return type for TypeScript
                if return_type and language == "typescript":
                    pattern_parts.append(f": {return_type}")
                    
                pattern_parts.append("{ $$$BODY }")
                pattern = " ".join(pattern_parts)
                
            elif language == "python":
                # Handle Python patterns
                pattern_parts = []
                
                # Python doesn't have visibility modifiers in the same way
                if is_async:
                    pattern_parts.append("async")
                    
                pattern_parts.append("def")
                
                # Handle name pattern
                if name_pattern:
                    if name_pattern.endswith(".*"):
                        prefix = name_pattern[:-2]
                        pattern_parts.append(f"{prefix}$NAME")
                    else:
                        pattern_parts.append(name_pattern)
                elif name:
                    pattern_parts.append(name)
                else:
                    pattern_parts.append("$NAME")
                    
                # Add parameters
                if parameters:
                    pattern_parts.append(f"({parameters})")
                else:
                    pattern_parts.append("($$$PARAMS)")
                    
                # Add return type annotation if specified
                if return_type:
                    pattern_parts.append(f"-> {return_type}")
                    
                pattern_parts.append(": $$$BODY")
                pattern = " ".join(pattern_parts)
                
            else:
                # For other languages, use the base pattern
                pattern = base_pattern
                
            # Add decorators/attributes if specified (already handled above for visibility)
            if language == "python" and options.get("decorator"):
                pattern = f"@{options['decorator']}\n{pattern}"
            elif language == "python" and options.get("decorators"):
                dec_lines = [f"@{dec}" for dec in options["decorators"]]
                pattern = "\n".join(dec_lines) + "\n" + pattern
            elif language == "rust" and options.get("attribute"):
                pattern = f"#[{options['attribute']}]\n{pattern}"
                
        elif pattern_type == "class":
            name = options.get("name")
            builder.class_definition(name)
            pattern = builder.build()
            
        elif pattern_type == "method_call":
            obj = options.get("object")
            method = options.get("method")
            builder.method_call(obj, method)
            pattern = builder.build()
            
        elif pattern_type == "import":
            module = options.get("module")
            builder.import_statement(module)
            pattern = builder.build()
            
        elif pattern_type == "if_statement":
            condition = options.get("condition")
            builder.if_statement(condition)
            pattern = builder.build()
            
        elif pattern_type == "loop":
            loop_type = options.get("loop_type", "for")
            builder.loop(loop_type)
            pattern = builder.build()
            
        elif pattern_type == "try_catch":
            builder.try_catch()
            pattern = builder.build()
            
        elif pattern_type == "unsafe_block" and language == "rust":
            builder.unsafe_block()
            pattern = builder.build()
            
        elif pattern_type == "impl_block" and language == "rust":
            trait = options.get("trait")
            type_name = options.get("type")
            builder.impl_block(trait, type_name)
            pattern = builder.build()
            
        elif pattern_type == "arrow_function" and language in ["javascript", "typescript"]:
            params = options.get("params")
            is_async = options.get("async", False)
            with_block = options.get("with_block", False)
            builder.arrow_function(params, is_async, with_block)
            pattern = builder.build()
            
        elif pattern_type == "custom":
            # Build custom pattern from components
            components = options.get("components", [])
            for component in components:
                comp_type = component.get("type")
                if comp_type == "literal":
                    builder.literal(component["value"])
                elif comp_type == "metavar":
                    builder.metavar(component["name"])
                elif comp_type == "multi_metavar":
                    builder.multi_metavar(component["name"])
                elif comp_type == "any":
                    builder.any(*component.get("patterns", []))
                elif comp_type == "all":
                    builder.all(*component.get("patterns", []))
                elif comp_type == "not":
                    builder.not_pattern(component.get("pattern", ""))
                elif comp_type == "inside":
                    builder.inside(component.get("pattern", ""))
                elif comp_type == "has":
                    builder.has(component.get("pattern", ""))
                elif comp_type == "function":
                    builder.function(component.get("name"))
                elif comp_type == "class":
                    builder.class_definition(component.get("name"))
                elif comp_type == "method_call":
                    builder.method_call(component.get("object"), component.get("method"))
                    
            pattern = builder.build()
            
        elif pattern_type == "complex_function":
            # Use the enhanced pattern builder for complex functions
            name = options.get("name")
            with_args = options.get("with_args", True)
            with_body = options.get("with_body", True)
            return_type = options.get("return_type")
            is_async = options.get("async", False)
            
            # Build the function
            if is_async:
                builder.async_function(name, with_args, with_body, return_type)
            else:
                builder.function(name, with_args, with_body, return_type)
            
            # Add language-specific decorations
            base_pattern = builder.build()
            
            if language == "python":
                decorators = options.get("decorators", [])
                if decorators:
                    decorator_lines = [f"@{dec}" for dec in decorators]
                    pattern = "\n".join(decorator_lines) + "\n" + base_pattern
                else:
                    pattern = base_pattern
            elif language == "rust":
                attributes = options.get("attributes", [])
                visibility = options.get("visibility")
                parts = []
                for attr in attributes:
                    parts.append(f"#[{attr}]")
                if visibility:
                    parts.append(visibility)
                if parts:
                    pattern = "\n".join(parts) + "\n" + base_pattern.replace("fn", parts[-1] + " fn" if visibility else "fn", 1)
                else:
                    pattern = base_pattern
            elif language in ["javascript", "typescript"]:
                export = options.get("export", False)
                if export:
                    pattern = f"export {base_pattern}"
                else:
                    pattern = base_pattern
            else:
                pattern = base_pattern
                
        elif pattern_type == "complex_class" and language in ["javascript", "typescript"]:
            # Build complex class patterns for JS/TS
            name = options.get("name", "$NAME")
            extends = options.get("extends")
            implements = options.get("implements", [])
            
            parts = [f"class {name}"]
            if extends:
                parts.append(f"extends {extends}")
            if implements and language == "typescript":
                parts.append(f"implements {', '.join(implements)}")
            parts.append("{ $$$BODY }")
            
            pattern = " ".join(parts)
            
        elif pattern_type == "complex_rust_function" and language == "rust":
            # Build complex Rust function patterns
            name = options.get("name", "$NAME")
            generics = options.get("generics", [])
            params = options.get("params", "$$$PARAMS")
            return_type = options.get("return_type", "")
            is_async = options.get("async", False)
            is_pub = options.get("public", False)
            where_clause = options.get("where")
            
            parts = []
            if is_pub:
                parts.append("pub")
            if is_async:
                parts.append("async")
            parts.append("fn")
            
            # Add name with generics
            if generics:
                parts.append(f"{name}<{', '.join(generics)}>")
            else:
                parts.append(name)
                
            # Add parameters
            parts.append(f"({params})")
            
            # Add return type
            if return_type:
                parts.append(f"-> {return_type}")
                
            # Add where clause if present
            if where_clause:
                pattern = " ".join(parts) + f" where {where_clause} {{ $$$BODY }}"
            else:
                pattern = " ".join(parts) + " { $$$BODY }"
            
        else:
            # Try to get from common patterns library
            library = PatternLibrary.get_common_patterns(language)
            if pattern_type in library:
                pattern = library[pattern_type].build()
            else:
                return {
                    "error": f"Unknown pattern type: {pattern_type}",
                    "available_types": [
                        "function", "class", "method_call", "import", 
                        "if_statement", "loop", "try_catch", "custom"
                    ] + list(library.keys()),
                    "language_specific": self._get_language_specific_patterns(language)
                }
        
        # Generate examples
        try:
            examples = self._generate_pattern_examples(pattern, language)
        except Exception as e:
            self.logger.warning(f"Failed to generate examples: {e}")
            examples = []
        
        return {
            "pattern": pattern,
            "pattern_type": pattern_type,
            "language": language,
            "options": options,
            "examples": examples,
            "description": self._get_pattern_description(pattern_type, language),
            "related_patterns": self._get_related_patterns(pattern_type, language),
        }
    
    def _get_language_specific_patterns(self, language: str) -> List[str]:
        """Get language-specific pattern types."""
        specific = {
            "python": ["decorator", "list_comprehension", "dict_comprehension", "lambda"],
            "javascript": ["arrow_function", "promise", "console_log"],
            "typescript": ["arrow_function", "interface", "type_definition"],
            "rust": ["unsafe_block", "impl_block", "match_expression", "derive"],
        }
        return specific.get(language, [])
    
    def _generate_pattern_examples(self, pattern: str, language: str) -> List[Dict[str, str]]:
        """Generate example code that would match the pattern."""
        examples = []
        
        # Generate basic example
        if "function" in pattern or "def" in pattern or "fn" in pattern:
            if language == "python":
                examples.append({
                    "code": "def calculate_sum(a, b):\n    return a + b",
                    "description": "Simple function that would match this pattern"
                })
            elif language == "javascript":
                examples.append({
                    "code": "function calculateSum(a, b) {\n    return a + b;\n}",
                    "description": "Simple function that would match this pattern"
                })
                
        elif "class" in pattern:
            if language == "python":
                examples.append({
                    "code": "class Calculator:\n    def add(self, a, b):\n        return a + b",
                    "description": "Class definition that would match this pattern"
                })
                
        return examples
    
    def _get_pattern_description(self, pattern_type: str, language: str) -> str:
        """Get description for a pattern type."""
        descriptions = {
            "function": f"Matches function definitions in {language}",
            "class": f"Matches class definitions in {language}",
            "method_call": "Matches method calls on objects",
            "import": f"Matches import statements in {language}",
            "if_statement": "Matches conditional if statements",
            "loop": "Matches loop constructs (for/while)",
            "try_catch": f"Matches error handling blocks in {language}",
            "unsafe_block": "Matches unsafe blocks in Rust",
            "impl_block": "Matches implementation blocks in Rust",
            "arrow_function": "Matches arrow function expressions",
        }
        return descriptions.get(pattern_type, f"Matches {pattern_type} patterns")
    
    def _get_available_options(self, pattern_type: str, language: str) -> Dict[str, str]:
        """Get available options for a pattern type."""
        options = {
            "function": {
                "name": "Function name (optional)",
                "async": "Make it async function (boolean)",
                "with_args": "Include parameters (boolean, default True)",
                "with_body": "Include body (boolean, default True)",
                "return_type": "Return type annotation (optional)",
                "decorator": "Python decorator (optional)",
                "visibility": "Rust visibility modifier (optional)"
            },
            "class": {
                "name": "Class/struct name (optional)",
                "extends": "Base class (JS/TS)",
                "implements": "Interfaces (TS)"
            },
            "arrow_function": {
                "params": "Parameter names (optional)",
                "async": "Make it async (boolean)",
                "with_block": "Use block body instead of expression (boolean)"
            }
        }
        return options.get(pattern_type, {})
    
    def _get_related_patterns(self, pattern_type: str, language: str) -> List[str]:
        """Get related pattern types."""
        related = {
            "function": ["async_function", "method_call", "arrow_function"],
            "class": ["method_call", "constructor"],
            "import": ["export", "require"],
            "if_statement": ["switch", "ternary"],
            "loop": ["for_each", "while", "do_while"],
        }
        return related.get(pattern_type, [])
    
    @handle_errors
    def find_trait_implementations(
        self,
        trait_name: str,
        directory: str,
        language: str = "rust"
    ) -> Dict[str, Any]:
        """
        Find all implementations of a trait across a codebase (Rust-specific).
        
        Args:
            trait_name: Name of the trait to find implementations for
            directory: Directory to search
            language: Programming language (default: rust)
            
        Returns:
            Dictionary with trait implementations
        """
        if language != "rust":
            return {
                "error": "Trait implementations are Rust-specific",
                "suggestion": "For other languages, use find_interface_implementations or find_class_inheritance"
            }
        
        # Build simpler patterns for trait implementations (complex patterns often fail)
        # Start with simplest patterns that are most likely to work
        pattern = f"impl {trait_name} for $TYPE"
        
        # Also search for generic implementations with simpler pattern
        generic_pattern = f"impl<$$$GENERICS> {trait_name} for $TYPE"
        
        self.logger.info(f"Searching for implementations of trait: {trait_name}")
        
        # Search for both patterns
        results = self.search_directory(directory, pattern, file_extensions=[".rs"])
        generic_results = self.search_directory(directory, generic_pattern, file_extensions=[".rs"])
        
        # Combine results
        all_implementations = {}
        
        # Process regular implementations
        for file_path, file_data in results.get("matches", {}).items():
            # Handle both direct matches array and nested structure
            if isinstance(file_data, dict):
                matches = file_data.get("matches", [])
            elif isinstance(file_data, list):
                matches = file_data
            else:
                continue
                
            for match in matches:
                # Extract the implementing type
                impl_type = match.get("metavariables", {}).get("TYPE", "Unknown")
                
                if file_path not in all_implementations:
                    all_implementations[file_path] = []
                    
                all_implementations[file_path].append({
                    "implementing_type": impl_type,
                    "trait": trait_name,
                    "location": match["location"],
                    "is_generic": False,
                    "match_text": match["match"]
                })
        
        # Process generic implementations
        for file_path, file_data in generic_results.get("matches", {}).items():
            # Handle both direct matches array and nested structure
            if isinstance(file_data, dict):
                matches = file_data.get("matches", [])
            elif isinstance(file_data, list):
                matches = file_data
            else:
                continue
                
            for match in matches:
                impl_type = match.get("metavariables", {}).get("TYPE", "Unknown")
                generics = match.get("metavariables", {}).get("GENERICS", "")
                
                if file_path not in all_implementations:
                    all_implementations[file_path] = []
                    
                all_implementations[file_path].append({
                    "implementing_type": impl_type,
                    "trait": trait_name,
                    "generics": generics,
                    "location": match["location"],
                    "is_generic": True,
                    "match_text": match["match"]
                })
        
        # Count unique implementing types
        implementing_types = set()
        for impls in all_implementations.values():
            for impl in impls:
                implementing_types.add(impl["implementing_type"])
        
        return {
            "trait": trait_name,
            "directory": directory,
            "implementations": all_implementations,
            "total_implementations": sum(len(impls) for impls in all_implementations.values()),
            "implementing_types": list(implementing_types),
            "files_with_implementations": list(all_implementations.keys()),
        }
    
    @handle_errors
    def find_function_calls(
        self,
        function_name: str,
        directory: str,
        language: str,
        include_methods: bool = True
    ) -> Dict[str, Any]:
        """
        Find all calls to a specific function across a codebase.
        
        Args:
            function_name: Name of the function to find calls for
            directory: Directory to search
            language: Programming language
            include_methods: Whether to include method calls
            
        Returns:
            Dictionary with function call locations
        """
        patterns = []
        
        # Function call patterns for different languages
        if language == "python":
            patterns.append(f"{function_name}($$$ARGS)")
            if include_methods:
                # Use $EXPR for method calls as it's more general
                patterns.append(f"$EXPR.{function_name}($$$ARGS)")
        elif language in ["javascript", "typescript"]:
            patterns.append(f"{function_name}($$$ARGS)")
            if include_methods:
                patterns.append(f"$EXPR.{function_name}($$$ARGS)")
            # Also check for async calls
            patterns.append(f"await {function_name}($$$ARGS)")
        elif language == "rust":
            patterns.append(f"{function_name}($$$ARGS)")
            if include_methods:
                # Use $EXPR for method calls - more general than $OBJ
                patterns.append(f"$EXPR.{function_name}($$$ARGS)")
            # Check for macro calls
            patterns.append(f"{function_name}!($$$ARGS)")
        elif language == "go":
            patterns.append(f"{function_name}($$$ARGS)")
            if include_methods:
                patterns.append(f"$EXPR.{function_name}($$$ARGS)")
        
        all_calls = {}
        total_calls = 0
        
        # Search for each pattern
        for pattern in patterns:
            results = self.search_directory(
                directory, 
                pattern,
                file_extensions=self._get_extensions_for_language(language)
            )
            
            matches_dict = results.get("matches", {})
            for file_path, file_matches in matches_dict.items():
                if file_path not in all_calls:
                    all_calls[file_path] = []
                
                # Handle case where file_matches might be a dict with 'matches' key
                if isinstance(file_matches, dict):
                    matches = file_matches.get("matches", [])
                else:
                    matches = file_matches if isinstance(file_matches, list) else []
                
                for match in matches:
                    call_info = {
                        "function": function_name,
                        "location": match.get("location", {}),
                        "match_text": match.get("text", match.get("match", "")),
                        "is_method_call": "." in pattern,
                    }
                    
                    # Extract object name for method calls
                    metavars = match.get("metavariables", {})
                    if "OBJ" in metavars:
                        call_info["object"] = metavars["OBJ"]
                    
                    # Extract arguments if available
                    if "ARGS" in metavars:
                        call_info["arguments"] = metavars["ARGS"]
                    
                    all_calls[file_path].append(call_info)
                    total_calls += 1
        
        # Analyze call patterns
        call_patterns = self._analyze_call_patterns(all_calls)
        
        return {
            "function_name": function_name,
            "directory": directory,
            "language": language,
            "calls": all_calls,
            "total_calls": total_calls,
            "files_with_calls": list(all_calls.keys()),
            "call_patterns": call_patterns,
        }
    
    def _analyze_call_patterns(self, calls: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze patterns in function calls."""
        patterns = {
            "direct_calls": 0,
            "method_calls": 0,
            "unique_objects": set(),
            "call_frequency_by_file": {},
        }
        
        for file_path, file_calls in calls.items():
            patterns["call_frequency_by_file"][file_path] = len(file_calls)
            
            for call in file_calls:
                if call.get("is_method_call"):
                    patterns["method_calls"] += 1
                    if "object" in call:
                        patterns["unique_objects"].add(call["object"])
                else:
                    patterns["direct_calls"] += 1
        
        patterns["unique_objects"] = list(patterns["unique_objects"])
        return patterns
    
    @handle_errors
    def analyze_dependencies(
        self,
        directory: str,
        language: str,
        analyze_external: bool = True,
        page: int = 1,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze import dependencies across a codebase.
        
        Args:
            directory: Directory to analyze
            language: Programming language
            analyze_external: Whether to analyze external dependencies
            
        Returns:
            Dictionary with dependency analysis
        """
        import_patterns = {
            "python": [
                "import $MODULE",
                "from $MODULE import $$$ITEMS",
                "import $MODULE as $ALIAS",
            ],
            "javascript": [
                "import $$$ITEMS from '$MODULE'",
                "import '$MODULE'",
                "const $VAR = require('$MODULE')",
                "import * as $ALIAS from '$MODULE'",
            ],
            "typescript": [
                "import $$$ITEMS from '$MODULE'",
                "import '$MODULE'",
                "import * as $ALIAS from '$MODULE'",
                "import type { $$$TYPES } from '$MODULE'",
            ],
            "rust": [
                "use $MODULE",
                "use $MODULE::$$$ITEMS",
                "use $MODULE as $ALIAS",
                "extern crate $CRATE",
            ],
            "go": [
                "import \"$MODULE\"",
                "import $ALIAS \"$MODULE\"",
                "import ($$$IMPORTS)",
            ],
        }
        
        patterns = import_patterns.get(language, [])
        if not patterns:
            return {
                "error": f"No import patterns defined for language: {language}",
                "supported_languages": list(import_patterns.keys()),
            }
        
        all_imports = {}
        dependency_graph = {}
        external_deps = set()
        internal_deps = set()
        
        # Search for each import pattern
        for pattern in patterns:
            results = self.search_directory(
                directory,
                pattern,
                file_extensions=self._get_extensions_for_language(language),
                page_size=None  # Disable pagination for dependency analysis
            )
            
            # Handle both paginated and non-paginated results
            matches_dict = results.get("matches", {})
            if "pagination" in results and "summary" in results:
                # It's a paginated response, but we disabled pagination so it should have all results
                pass
            
            for file_path, file_data in matches_dict.items():
                if file_path not in all_imports:
                    all_imports[file_path] = []
                    dependency_graph[file_path] = set()
                
                # Extract the actual matches list from the file data
                match_list = file_data.get("matches", []) if isinstance(file_data, dict) else []
                
                for match in match_list:
                    module = match.get("metavariables", {}).get("MODULE", "")
                    if not module:
                        module = match.get("metavariables", {}).get("CRATE", "")
                    
                    import_info = {
                        "module": module,
                        "location": match["location"],
                        "match_text": match["match"],
                        "items": match.get("metavariables", {}).get("ITEMS", ""),
                        "alias": match.get("metavariables", {}).get("ALIAS", ""),
                    }
                    
                    all_imports[file_path].append(import_info)
                    dependency_graph[file_path].add(module)
                    
                    # Classify as internal or external
                    if self._is_external_dependency(module, language):
                        external_deps.add(module)
                    else:
                        internal_deps.add(module)
        
        # Convert sets to lists for JSON serialization
        for file_path in dependency_graph:
            dependency_graph[file_path] = list(dependency_graph[file_path])
        
        # Analyze dependency metrics
        metrics = self._calculate_dependency_metrics(dependency_graph)
        
        # Prepare full result
        result = {
            "directory": directory,
            "language": language,
            "imports": all_imports,
            "dependency_graph": dependency_graph,
            "external_dependencies": list(external_deps),
            "internal_dependencies": list(internal_deps),
            "metrics": metrics,
            "files_analyzed": len(all_imports),
        }
        
        # Check if pagination is needed
        if page_size is not None or self.paginator.should_paginate(result, "analysis"):
            # Convert imports dict to list for pagination
            import_items = []
            for file_path, imports in all_imports.items():
                import_items.append({
                    "file": file_path,
                    "imports": imports
                })
            
            # Sort by number of imports
            import_items.sort(key=lambda x: len(x["imports"]), reverse=True)
            
            # Create summary function
            def create_import_summary(items):
                total_imports = sum(len(item["imports"]) for item in items)
                return {
                    "total_files": len(items),
                    "total_imports": total_imports,
                    "average_imports_per_file": total_imports / len(items) if items else 0,
                    "external_dependencies": list(external_deps)[:10],  # Top 10 external deps
                    "internal_dependencies": list(internal_deps)[:10],  # Top 10 internal deps
                    "metrics": metrics
                }
            
            # Paginate the imports
            paginated = self.paginator.paginate_list(
                import_items,
                page=page,
                page_size=page_size,
                response_type="analysis",
                summary_fn=create_import_summary
            )
            
            # Convert back to expected format
            paginated_imports = {}
            for item in paginated.items:
                paginated_imports[item["file"]] = item["imports"]
            
            # Build paginated dependency graph (only for files in current page)
            paginated_graph = {}
            for file_path in paginated_imports:
                if file_path in dependency_graph:
                    paginated_graph[file_path] = dependency_graph[file_path]
            
            return {
                "imports": paginated_imports,
                "dependency_graph": paginated_graph,
                "pagination": paginated.to_dict()["pagination"],
                "summary": paginated.summary,
                "language": language,
                "directory": directory,
                "note": "Full dependency analysis available in summary. Use pagination to navigate."
            }
        
        return result
    
    def _is_external_dependency(self, module: str, language: str) -> bool:
        """Determine if a module is an external dependency."""
        if language == "python":
            # Python standard library or third-party if no dots or starts with known packages
            return not module.startswith(".") and not module.startswith("src.")
        elif language in ["javascript", "typescript"]:
            # External if doesn't start with ./ or ../
            return not module.startswith("./") and not module.startswith("../")
        elif language == "rust":
            # External if it's a crate (no ::)
            return "::" not in module and module not in ["self", "super", "crate"]
        elif language == "go":
            # External if contains domain name
            return "." in module and "/" in module
        return True
    
    def _calculate_dependency_metrics(self, dependency_graph: Dict[str, List[str]]) -> Dict[str, Any]:
        """Calculate dependency metrics."""
        metrics = {
            "average_dependencies_per_file": 0,
            "max_dependencies": 0,
            "min_dependencies": float('inf'),
            "most_dependent_files": [],
            "circular_dependencies": [],
        }
        
        if not dependency_graph:
            return metrics
        
        dep_counts = {f: len(deps) for f, deps in dependency_graph.items()}
        
        metrics["average_dependencies_per_file"] = sum(dep_counts.values()) / len(dep_counts)
        metrics["max_dependencies"] = max(dep_counts.values()) if dep_counts else 0
        metrics["min_dependencies"] = min(dep_counts.values()) if dep_counts else 0
        
        # Find most dependent files
        sorted_files = sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)
        metrics["most_dependent_files"] = [
            {"file": f, "dependency_count": c} 
            for f, c in sorted_files[:5]
        ]
        
        # Simple circular dependency detection (would need more sophisticated analysis)
        # This is a placeholder - real implementation would need proper graph traversal
        
        return metrics
    
    @handle_errors
    def analyze_project_structure(
        self,
        directory: str
    ) -> Dict[str, Any]:
        """
        Analyze the overall structure of a project.
        
        Args:
            directory: Root directory to analyze
            
        Returns:
            Dictionary with project structure analysis
        """
        # CRITICAL FIX: Properly resolve directory path relative to CWD
        original_directory = directory
        dir_path = Path(directory).resolve()
        
        self.logger.info(f"Analyzing project structure: {original_directory} -> {dir_path}")
        
        if not dir_path.exists():
            return {
                "error": f"Directory not found: {original_directory} (resolved to {dir_path})",
                "requested_directory": original_directory,
                "resolved_directory": str(dir_path),
                "current_working_directory": str(Path.cwd())
            }
        
        if not dir_path.is_dir():
            return {
                "error": f"Path exists but is not a directory: {original_directory} (resolved to {dir_path})",
                "requested_directory": original_directory,
                "resolved_directory": str(dir_path),
                "current_working_directory": str(Path.cwd())
            }
        
        # Collect project statistics
        file_stats = {
            "total_files": 0,
            "files_by_language": {},
            "files_by_extension": {},
            "directories": 0,
            "max_depth": 0,
        }
        
        # Size statistics
        size_stats = {
            "total_size_bytes": 0,
            "average_file_size": 0,
            "largest_files": [],
        }
        
        # Code statistics
        code_stats = {
            "total_lines": 0,
            "lines_by_language": {},
            "files_with_tests": [],
            "documentation_files": [],
        }
        
        file_sizes = []
        
        # Walk through the project using resolved path
        for root, dirs, files in os.walk(str(dir_path)):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self.ignore_handler.should_ignore(os.path.join(root, d))]
            
            # Calculate depth
            depth = len(Path(root).relative_to(dir_path).parts)
            file_stats["max_depth"] = max(file_stats["max_depth"], depth)
            file_stats["directories"] += 1
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip ignored files
                if self.ignore_handler.should_ignore(str(file_path)):
                    continue
                
                file_stats["total_files"] += 1
                
                # Get file extension and language
                ext = file_path.suffix.lower()
                file_stats["files_by_extension"][ext] = file_stats["files_by_extension"].get(ext, 0) + 1
                
                # Determine language
                language = None
                # If using AstAnalyzerV2, use language_extensions mapping
                if hasattr(self.analyzer, 'language_extensions'):
                    language = self.analyzer.language_extensions.get(ext)
                else:
                    # For backward compatibility with original AstAnalyzer
                    for lang, exts in self.analyzer.supported_languages.items():
                        if ext in exts:
                            language = lang
                            break
                
                if language:
                    file_stats["files_by_language"][language] = file_stats["files_by_language"].get(language, 0) + 1
                
                # Get file size
                try:
                    size = file_path.stat().st_size
                    size_stats["total_size_bytes"] += size
                    file_sizes.append((str(file_path.relative_to(dir_path)), size))
                    
                    # Count lines for code files
                    if language:
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                lines = len(f.readlines())
                                code_stats["total_lines"] += lines
                                code_stats["lines_by_language"][language] = code_stats["lines_by_language"].get(language, 0) + lines
                        except:
                            pass
                    
                    # Identify test files
                    if "test" in file.lower() or "spec" in file.lower():
                        code_stats["files_with_tests"].append(str(file_path.relative_to(dir_path)))
                    
                    # Identify documentation
                    if ext in [".md", ".rst", ".txt", ".adoc"]:
                        code_stats["documentation_files"].append(str(file_path.relative_to(dir_path)))
                        
                except Exception as e:
                    self.logger.error(f"Error processing file {file_path}: {e}")
        
        # Calculate averages and find largest files
        if file_stats["total_files"] > 0:
            size_stats["average_file_size"] = size_stats["total_size_bytes"] / file_stats["total_files"]
            
        # Sort files by size and get top 10
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        size_stats["largest_files"] = [
            {"file": f, "size_bytes": s, "size_mb": round(s / (1024 * 1024), 2)}
            for f, s in file_sizes[:10]
        ]
        
        # Detect project type
        project_type = self._detect_project_type(dir_path)
        
        # Generate summary with both original and resolved paths
        summary = {
            "directory": str(dir_path),
            "requested_directory": original_directory,
            "current_working_directory": str(Path.cwd()),
            "project_type": project_type,
            "file_statistics": file_stats,
            "size_statistics": size_stats,
            "code_statistics": code_stats,
            "primary_language": max(file_stats["files_by_language"].items(), key=lambda x: x[1])[0] if file_stats["files_by_language"] else "unknown",
            "has_tests": len(code_stats["files_with_tests"]) > 0,
            "test_file_ratio": len(code_stats["files_with_tests"]) / file_stats["total_files"] if file_stats["total_files"] > 0 else 0,
        }
        
        return summary
    
    def _detect_project_type(self, project_path: Path) -> str:
        """Detect the type of project based on config files."""
        config_indicators = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile"],
            "javascript": ["package.json", "yarn.lock", "npm-shrinkwrap.json"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "go": ["go.mod", "go.sum"],
            "ruby": ["Gemfile", "Gemfile.lock"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "dotnet": ["*.csproj", "*.sln", "*.fsproj"],
        }
        
        for lang, indicators in config_indicators.items():
            for indicator in indicators:
                if "*" in indicator:
                    # Handle glob patterns
                    if list(project_path.glob(indicator)):
                        return lang
                elif (project_path / indicator).exists():
                    return lang
        
        return "unknown"
    
    @handle_errors
    def analyze_code_quality(
        self,
        directory: str,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze code quality metrics across a project.
        
        Args:
            directory: Directory to analyze
            include_metrics: Whether to include detailed metrics
            
        Returns:
            Dictionary with code quality analysis
        """
        quality_issues = {
            "code_smells": [],
            "complexity_issues": [],
            "naming_issues": [],
            "documentation_issues": [],
        }
        
        # Define code smell patterns for different languages
        code_smell_patterns = {
            "python": {
                "empty_except": "except: pass",
                "broad_except": "except Exception:",
                "todo_comment": "# TODO",
                "fixme_comment": "# FIXME",
                "long_line": r".{121,}",  # Lines over 120 chars
            },
            "javascript": {
                "console_log": "console.log($$$)",
                "debugger": "debugger",
                "var_usage": "var $VAR",
                "todo_comment": "// TODO",
                "fixme_comment": "// FIXME",
            },
            "rust": {
                "unwrap_usage": "$EXPR.unwrap()",
                "todo_macro": "todo!()",
                "unimplemented": "unimplemented!()",
                "println_debug": "println!($$$)",
            },
        }
        
        total_issues = 0
        files_analyzed = set()  # Track unique files
        
        # Analyze each language
        for language, patterns in code_smell_patterns.items():
            extensions = self._get_extensions_for_language(language)
            
            for pattern_name, pattern in patterns.items():
                try:
                    results = self.search_directory(
                        directory,
                        pattern,
                        file_extensions=extensions,
                        page_size=None  # Disable pagination for quality analysis
                    )
                except Exception as e:
                    self.logger.debug(f"Error searching with pattern '{pattern}' for {language}: {e}")
                    continue
                
                # Handle both paginated and non-paginated results
                matches_dict = results.get("matches", {})
                if isinstance(matches_dict, dict) and matches_dict:
                    for file_path, file_matches in matches_dict.items():
                        if not isinstance(file_path, str):
                            continue
                        files_analyzed.add(file_path)
                        
                        # Handle case where file_matches might be a dict with 'matches' key
                        if isinstance(file_matches, dict):
                            matches = file_matches.get("matches", [])
                        elif isinstance(file_matches, list):
                            matches = file_matches
                        else:
                            continue  # Skip invalid file_matches
                        
                        if not isinstance(matches, list):
                            continue
                            
                        for match in matches:
                            if not isinstance(match, dict):
                                continue
                                
                            issue = {
                                "type": pattern_name,
                                "file": file_path,
                                "location": match.get("location", {}),
                                "severity": self._get_issue_severity(pattern_name),
                                "message": self._get_issue_message(pattern_name, language),
                            }
                            
                            # Categorize issue
                            if pattern_name in ["empty_except", "broad_except", "var_usage", "unwrap_usage"]:
                                quality_issues["code_smells"].append(issue)
                            elif "comment" in pattern_name:
                                quality_issues["documentation_issues"].append(issue)
                            
                            total_issues += 1
        
        # Calculate metrics
        metrics = {}
        if include_metrics:
            metrics = {
                "total_issues": total_issues,
                "issues_by_type": {
                    "code_smells": len(quality_issues["code_smells"]),
                    "complexity": len(quality_issues["complexity_issues"]),
                    "naming": len(quality_issues["naming_issues"]),
                    "documentation": len(quality_issues["documentation_issues"]),
                },
                "files_with_issues": len(set(
                    issue["file"] 
                    for category in quality_issues.values() 
                    for issue in category
                    if isinstance(category, list) and isinstance(issue, dict) and "file" in issue
                )),
                "average_issues_per_file": total_issues / len(files_analyzed) if len(files_analyzed) > 0 else 0,
            }
        
        # Generate quality score (simple scoring)
        quality_score = max(0, 100 - (total_issues * 2))  # Deduct 2 points per issue
        quality_grade = "A" if quality_score >= 90 else "B" if quality_score >= 80 else "C" if quality_score >= 70 else "D" if quality_score >= 60 else "F"
        
        return {
            "directory": directory,
            "quality_score": quality_score,
            "quality_grade": quality_grade,
            "issues": quality_issues,
            "metrics": metrics,
            "recommendations": self._generate_quality_recommendations(quality_issues),
        }
    
    def _get_issue_severity(self, issue_type: str) -> str:
        """Get severity level for an issue type."""
        high_severity = ["empty_except", "broad_except", "debugger", "unwrap_usage"]
        medium_severity = ["var_usage", "console_log", "println_debug"]
        
        if issue_type in high_severity:
            return "high"
        elif issue_type in medium_severity:
            return "medium"
        return "low"
    
    def _get_issue_message(self, issue_type: str, language: str) -> str:
        """Get descriptive message for an issue type."""
        messages = {
            "empty_except": "Empty except block - specify exception types",
            "broad_except": "Catching broad Exception - be more specific",
            "console_log": "Console.log in production code",
            "debugger": "Debugger statement in code",
            "var_usage": "Use 'let' or 'const' instead of 'var'",
            "unwrap_usage": "Using unwrap() can cause panics",
            "todo_comment": "TODO comment found",
            "fixme_comment": "FIXME comment found",
        }
        return messages.get(issue_type, f"{issue_type} detected")
    
    def _generate_quality_recommendations(self, issues: Dict[str, List]) -> List[str]:
        """Generate recommendations based on quality issues."""
        recommendations = []
        
        # Safely check for code smells
        code_smells = issues.get("code_smells", [])
        if isinstance(code_smells, list) and code_smells:
            recommendations.append("Address code smells to improve maintainability")
            
        # Safely check for documentation issues
        doc_issues = issues.get("documentation_issues", [])
        if isinstance(doc_issues, list) and doc_issues:
            todo_count = sum(1 for i in doc_issues 
                           if isinstance(i, dict) and 
                           isinstance(i.get("type"), str) and 
                           "todo" in i["type"].lower())
            if todo_count > 10:
                recommendations.append(f"High number of TODOs ({todo_count}) - consider addressing or creating issues")
        
        return recommendations
    
    @handle_errors
    def generate_review_report(
        self,
        directory: str,
        output_format: str = "markdown",
        include_security: bool = True,
        include_quality: bool = True,
        include_metrics: bool = True,
        summary_only: bool = False,
        page: int = 1,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive code review report.
        
        Args:
            directory: Directory to review
            output_format: Format for the report (markdown, json)
            include_security: Whether to include security analysis
            include_quality: Whether to include quality analysis
            include_metrics: Whether to include metrics
            
        Returns:
            Dictionary with the review report
        """
        self.logger.info(f"Generating comprehensive review report for: {directory}")
        
        report_sections = {}
        
        # 1. Project Overview
        report_sections["project_overview"] = self.analyze_project_structure(directory)
        
        # 2. Security Analysis (if requested)
        if include_security:
            primary_language = report_sections["project_overview"].get("primary_language", "unknown")
            if primary_language != "unknown":
                security_audit = self.run_security_audit(primary_language, directory)
                report_sections["security_analysis"] = security_audit
        
        # 3. Code Quality Analysis (if requested)
        if include_quality:
            quality_analysis = self.analyze_code_quality(directory, include_metrics)
            report_sections["quality_analysis"] = quality_analysis
        
        # 4. Dependency Analysis
        primary_language = report_sections["project_overview"].get("primary_language", "unknown")
        if primary_language != "unknown":
            dep_analysis = self.analyze_dependencies(directory, primary_language)
            report_sections["dependency_analysis"] = dep_analysis
        
        # 5. Generate formatted report
        if output_format == "markdown":
            formatted_report = self._format_report_as_markdown(report_sections)
        else:
            formatted_report = report_sections
        
        # 6. Overall assessment
        overall_score = self._calculate_overall_score(report_sections)
        
        # Prepare full result
        result = {
            "directory": directory,
            "report_sections": report_sections,
            "formatted_report": formatted_report,
            "overall_score": overall_score,
            "executive_summary": self._generate_executive_summary(report_sections, overall_score),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # If summary only requested, return just the executive summary
        if summary_only:
            return {
                "directory": directory,
                "overall_score": overall_score,
                "executive_summary": result["executive_summary"],
                "timestamp": result["timestamp"],
                "summary_mode": True,
                "note": "Full report available with summary_only=False"
            }
        
        # Check if pagination is needed
        if page_size is not None or self.paginator.should_paginate(result, "analysis"):
            # For reports, we'll paginate the formatted report by sections
            sections = []
            
            # Convert report sections to a list for pagination
            if include_metrics and "project_structure" in report_sections:
                sections.append({
                    "section": "project_structure",
                    "title": "Project Structure Analysis",
                    "content": report_sections["project_structure"]
                })
            
            if include_security and "security" in report_sections:
                sections.append({
                    "section": "security",
                    "title": "Security Analysis",
                    "content": report_sections["security"]
                })
            
            if include_quality and "quality" in report_sections:
                sections.append({
                    "section": "quality",
                    "title": "Code Quality Analysis",
                    "content": report_sections["quality"]
                })
            
            if "dependencies" in report_sections:
                sections.append({
                    "section": "dependencies",
                    "title": "Dependency Analysis",
                    "content": report_sections["dependencies"]
                })
            
            # Create summary function
            def create_report_summary(items):
                return {
                    "overall_score": overall_score,
                    "executive_summary": result["executive_summary"],
                    "total_sections": len(items),
                    "sections_included": [item["section"] for item in items]
                }
            
            # Paginate sections
            paginated = self.paginator.paginate_list(
                sections,
                page=page,
                page_size=page_size or 2,  # Default 2 sections per page
                response_type="analysis",
                summary_fn=create_report_summary
            )
            
            # Format the paginated sections
            paginated_report = ""
            paginated_sections = {}
            for item in paginated.items:
                paginated_sections[item["section"]] = item["content"]
                # Add to formatted report if markdown
                if output_format == "markdown":
                    paginated_report += f"\n## {item['title']}\n\n"
                    # Format the section content
                    if item["section"] == "security" and "results" in item["content"]:
                        # Limit security results
                        limited_results = item["content"].copy()
                        if "results" in limited_results:
                            limited_results["results"] = limited_results["results"][:20]
                            limited_results["results_truncated"] = True
                        paginated_report += self._format_security_section(limited_results)
                    elif item["section"] == "quality" and "issues" in item["content"]:
                        # Limit quality issues
                        limited_quality = item["content"].copy()
                        if "issues" in limited_quality:
                            for category in limited_quality["issues"]:
                                if isinstance(limited_quality["issues"][category], list):
                                    limited_quality["issues"][category] = limited_quality["issues"][category][:10]
                        paginated_report += self._format_quality_section(limited_quality)
                    else:
                        paginated_report += str(item["content"]) + "\n"
            
            return {
                "directory": directory,
                "report_sections": paginated_sections,
                "formatted_report": paginated_report,
                "pagination": paginated.to_dict()["pagination"],
                "summary": paginated.summary,
                "timestamp": result["timestamp"],
                "note": "Report paginated by sections. Use pagination to see all sections."
            }
        
        return result
    
    def _format_report_as_markdown(self, sections: Dict[str, Any]) -> str:
        """Format the report sections as markdown."""
        md = []
        
        # Title
        md.append("# Code Review Report")
        md.append(f"\nGenerated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Project Overview
        if "project_overview" in sections:
            overview = sections["project_overview"]
            if not overview.get("error"):
                md.append("## Project Overview")
                md.append(f"- **Primary Language**: {overview.get('primary_language', 'Unknown')}")
                file_stats = overview.get('file_statistics', {})
                md.append(f"- **Total Files**: {file_stats.get('total_files', 0)}")
                code_stats = overview.get('code_statistics', {})
                md.append(f"- **Total Lines**: {code_stats.get('total_lines', 0):,}")
                md.append(f"- **Has Tests**: {'Yes' if overview.get('has_tests', False) else 'No'}")
                md.append("")
        
        # Security Analysis
        if "security_analysis" in sections:
            security = sections["security_analysis"]
            if not security.get("error"):
                md.append("## Security Analysis")
                md.append(f"- **Risk Level**: {security.get('risk_level', 'Unknown').upper()}")
                md.append(f"- **Total Findings**: {security.get('total_findings', 0)}")
                
                if security.get("findings_by_severity"):
                    md.append("\n### Findings by Severity")
                    for severity, count in security["findings_by_severity"].items():
                        if count > 0:
                            md.append(f"- {severity.capitalize()}: {count}")
                
                if security.get("recommendations"):
                    md.append("\n### Security Recommendations")
                    for rec in security["recommendations"]:
                        md.append(f"- {rec}")
                md.append("")
        
        # Quality Analysis
        if "quality_analysis" in sections:
            quality = sections["quality_analysis"]
            md.append("## Code Quality")
            md.append(f"- **Quality Grade**: {quality.get('quality_grade', 'N/A')}")
            md.append(f"- **Quality Score**: {quality.get('quality_score', 0)}/100")
            
            if quality.get("metrics"):
                md.append(f"- **Total Issues**: {quality['metrics']['total_issues']}")
            
            if quality.get("recommendations"):
                md.append("\n### Quality Recommendations")
                for rec in quality["recommendations"]:
                    md.append(f"- {rec}")
            md.append("")
        
        return "\n".join(md)
    
    def _calculate_overall_score(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall project score."""
        scores = {
            "security": 100,
            "quality": 100,
            "maintainability": 100,
        }
        
        # Security score
        if "security_analysis" in sections:
            risk_level = sections["security_analysis"].get("risk_level", "low")
            risk_scores = {"low": 90, "medium": 70, "high": 40, "critical": 20}
            scores["security"] = risk_scores.get(risk_level, 50)
        
        # Quality score
        if "quality_analysis" in sections:
            scores["quality"] = sections["quality_analysis"].get("quality_score", 70)
        
        # Maintainability score (based on test coverage and documentation)
        if "project_overview" in sections:
            test_ratio = sections["project_overview"].get("test_file_ratio", 0)
            scores["maintainability"] = min(100, test_ratio * 200)  # 50% test files = 100 score
        
        # Overall score
        overall = sum(scores.values()) / len(scores)
        
        return {
            "overall": round(overall, 1),
            "breakdown": scores,
            "grade": "A" if overall >= 90 else "B" if overall >= 80 else "C" if overall >= 70 else "D" if overall >= 60 else "F"
        }
    
    def _generate_executive_summary(self, sections: Dict[str, Any], overall_score: Dict[str, Any]) -> str:
        """Generate executive summary of the review."""
        summary_parts = []
        
        # Overall assessment
        grade = overall_score["grade"]
        score = overall_score["overall"]
        summary_parts.append(f"Overall project grade: {grade} ({score}/100)")
        
        # Key findings
        if "security_analysis" in sections:
            risk = sections["security_analysis"].get("risk_level", "unknown")
            findings = sections["security_analysis"].get("total_findings", 0)
            if findings > 0:
                summary_parts.append(f"Security: {findings} issues found ({risk} risk)")
        
        if "quality_analysis" in sections:
            quality_grade = sections["quality_analysis"].get("quality_grade", "N/A")
            summary_parts.append(f"Code quality: Grade {quality_grade}")
        
        # Primary concerns
        concerns = []
        if overall_score["breakdown"]["security"] < 70:
            concerns.append("security vulnerabilities")
        if overall_score["breakdown"]["quality"] < 70:
            concerns.append("code quality issues")
        if overall_score["breakdown"]["maintainability"] < 70:
            concerns.append("low test coverage")
        
        if concerns:
            summary_parts.append(f"Primary concerns: {', '.join(concerns)}")
        
        return " | ".join(summary_parts)
    
    @handle_errors
    def get_common_patterns(
        self,
        language: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get common pre-built patterns for a language.
        
        Args:
            language: Programming language (rust, javascript, python, etc.)
            category: Optional category filter (functions, error_handling, async_code, etc.)
            
        Returns:
            Dictionary with common patterns
        """
        try:
            # Convert category string to enum if provided
            pattern_category = None
            if category:
                try:
                    pattern_category = PatternCategory(category)
                except ValueError:
                    return {
                        "error": f"Invalid category: {category}",
                        "available_categories": [c.value for c in PatternCategory],
                        "suggestion": "Use one of the available categories or omit for all patterns"
                    }
            
            # Get patterns
            patterns = CommonPatternLibrary.get_patterns(language, pattern_category)
            
            if not patterns:
                return {
                    "error": f"No patterns found for language: {language}",
                    "supported_languages": ["rust", "javascript", "typescript", "python"],
                    "suggestion": "Check the language is supported"
                }
            
            # Format patterns for response
            formatted_patterns = []
            for pattern in patterns:
                formatted_patterns.append({
                    "name": pattern.name,
                    "pattern": pattern.pattern,
                    "description": pattern.description,
                    "category": pattern.category.value,
                    "examples": pattern.examples,
                    "variations": pattern.variations or [],
                    "notes": pattern.notes
                })
            
            return {
                "language": language,
                "category": category,
                "patterns": formatted_patterns,
                "total": len(formatted_patterns),
                "usage": "Use the 'pattern' field directly in search_directory or analyze_code"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting common patterns: {e}")
            return {
                "error": str(e),
                "suggestion": "Check the language and category parameters"
            }
    
    @handle_errors
    def find_pattern(
        self,
        query: str,
        language: str,
        directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find code using natural language query or pattern name.
        
        This method provides an easy way to search for common patterns without
        knowing the exact AST syntax.
        
        Args:
            query: Natural language query or pattern name (e.g., "async functions", "unwrap calls")
            language: Programming language
            directory: Optional directory to search in
            
        Returns:
            Search results or pattern recommendations
        """
        try:
            # First, try to find matching common patterns
            recommendations = PatternRecommender.recommend_patterns(language, query)
            
            if not recommendations:
                # Try direct pattern library search
                recommendations = CommonPatternLibrary.search_patterns(language, query)
            
            if not recommendations:
                return {
                    "error": "No patterns found for query",
                    "query": query,
                    "language": language,
                    "suggestion": "Try a more specific query or use get_common_patterns to see available patterns"
                }
            
            # If no directory specified, just return the patterns
            if not directory:
                formatted_patterns = []
                for pattern in recommendations:
                    formatted_patterns.append({
                        "name": pattern.name,
                        "pattern": pattern.pattern,
                        "description": pattern.description,
                        "examples": pattern.examples,
                        "usage": f"Use search_directory('{directory or '/path/to/code'}', '{pattern.pattern}')"
                    })
                
                return {
                    "query": query,
                    "language": language,
                    "found_patterns": formatted_patterns,
                    "suggestion": "Provide a directory parameter to search for these patterns"
                }
            
            # If directory specified, search using the first recommended pattern
            best_pattern = recommendations[0]
            
            self.logger.info(f"Using pattern '{best_pattern.name}': {best_pattern.pattern}")
            
            # Try the main pattern first
            result = self.search_directory(directory, best_pattern.pattern)
            
            # If no matches and there are variations, try them
            if result.get("files_with_matches", 0) == 0 and best_pattern.variations:
                for variation in best_pattern.variations:
                    self.logger.info(f"Trying variation: {variation}")
                    result = self.search_directory(directory, variation)
                    if result.get("files_with_matches", 0) > 0:
                        result["pattern_used"] = variation
                        result["pattern_name"] = best_pattern.name
                        break
            else:
                result["pattern_used"] = best_pattern.pattern
                result["pattern_name"] = best_pattern.name
            
            # Add pattern info to result
            result["query"] = query
            result["pattern_info"] = {
                "name": best_pattern.name,
                "description": best_pattern.description,
                "variations_available": len(best_pattern.variations) if best_pattern.variations else 0
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in find_pattern: {e}")
            return {
                "error": str(e),
                "query": query,
                "language": language
            }
    
    @handle_errors
    def find_code_like(
        self,
        example_code: str,
        language: str,
        directory: str,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Find code similar to an example.
        
        This method attempts to extract patterns from example code and find similar code.
        
        Args:
            example_code: Example code snippet
            language: Programming language
            directory: Directory to search
            similarity_threshold: How similar matches should be (0-1)
            
        Returns:
            Search results with similar code
        """
        try:
            # First, try to parse the example to understand its structure
            root = self.analyzer.parse_code(example_code, language)
            if not root:
                return {
                    "error": "Failed to parse example code",
                    "suggestion": "Ensure the example code is valid"
                }
            
            # Try to identify the main pattern in the example
            # This is a simplified approach - could be enhanced
            patterns_to_try = []
            
            # Check for common patterns in the example
            if language == "rust":
                if "async fn" in example_code:
                    patterns_to_try.append("async fn $NAME")
                if ".unwrap()" in example_code:
                    patterns_to_try.append("unwrap()")
                if "spawn(" in example_code:
                    patterns_to_try.append("spawn($$$ARGS)")
                if ".await" in example_code:
                    patterns_to_try.append(".await")
                    
            elif language in ["javascript", "typescript"]:
                if "async function" in example_code:
                    patterns_to_try.append("async function $NAME")
                if "=>" in example_code:
                    patterns_to_try.append("($$$PARAMS) => $BODY")
                if "await " in example_code:
                    patterns_to_try.append("await $EXPR")
                    
            elif language == "python":
                if "async def" in example_code:
                    patterns_to_try.append("async def $NAME")
                if "try:" in example_code:
                    patterns_to_try.append("try:\n    $$$TRY\nexcept $EXCEPTION:\n    $$$EXCEPT")
                if "print(" in example_code:
                    patterns_to_try.append("print($$$ARGS)")
            
            if not patterns_to_try:
                return {
                    "error": "Could not identify patterns in example code",
                    "suggestion": "Try using find_pattern with a natural language query instead"
                }
            
            # Try each pattern and collect results
            all_matches = {}
            patterns_used = []
            
            for pattern in patterns_to_try:
                result = self.search_directory(directory, pattern)
                if result.get("files_with_matches", 0) > 0:
                    patterns_used.append(pattern)
                    for file, matches in result.get("matches", {}).items():
                        if file not in all_matches:
                            all_matches[file] = []
                        all_matches[file].extend(matches)
            
            return {
                "example_code": example_code,
                "patterns_identified": patterns_used,
                "matches": all_matches,
                "files_with_matches": len(all_matches),
                "total_matches": sum(len(matches) for matches in all_matches.values()),
                "suggestion": "Results show code with similar patterns to your example"
            }
            
        except Exception as e:
            self.logger.error(f"Error in find_code_like: {e}")
            return {
                "error": str(e),
                "suggestion": "Ensure the example code is valid"
            }

    @handle_errors
    def pattern_builder(self, language: str) -> Dict[str, Any]:
        """
        Get a pattern builder for simplified pattern construction.
        
        Args:
            language: Programming language
            
        Returns:
            Pattern builder interface information
        """
        
        return {
            "language": language,
            "builder_methods": [
                {"method": "function(name=None)", "description": "Build function pattern"},
                {"method": "async_function(name=None)", "description": "Build async function pattern"},
                {"method": "with_params(params=None)", "description": "Add parameters"},
                {"method": "with_body(body=None)", "description": "Add body"},
                {"method": "returns(return_type)", "description": "Add return type"},
                {"method": "method_call(object=None, method=None)", "description": "Build method call"},
                {"method": "if_statement(condition=None)", "description": "Build if statement"},
                {"method": "build()", "description": "Get final pattern"},
            ],
            "example": """
# Python example:
builder = SimplePatternBuilder('python')
pattern = builder.function().with_params().with_body().build()
# Result: def $NAME($$$PARAMS):\n    $$$BODY

# Rust example:
builder = SimplePatternBuilder('rust')
pattern = builder.async_function().with_params().returns('Result<()>').with_body().build()
# Result: async fn $NAME($$$PARAMS) -> Result<()> { $$$BODY }
""",
            "note": "Use the SimplePatternBuilder class directly for programmatic access"
        }
    
    @handle_errors
    def get_pattern_template(
        self,
        template_name: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Get a pattern template with examples and metadata.
        
        Args:
            template_name: Name of the template
            language: Programming language
            
        Returns:
            Template with pattern, replacement, examples, and variables
        """
        from ..utils.pattern_templates import PatternTemplateLibrary
        
        template = PatternTemplateLibrary.get_template(template_name, language)
        
        if not template:
            # Get all available templates
            all_templates = PatternTemplateLibrary.get_all_templates(language)
            return {
                "error": f"Template '{template_name}' not found for {language}",
                "available_templates": list(all_templates.keys()),
                "suggestion": "Use one of the available templates"
            }
        
        return {
            "name": template.name,
            "description": template.description,
            "pattern": template.pattern,
            "replacement": template.replacement,
            "language": template.language,
            "example_matches": template.example_matches,
            "variables": template.variables,
            "category": template.category,
            "notes": template.notes,
            "confidence": template.confidence,
            "usage": f"Use pattern '{template.pattern}' in search_directory or analyze_code"
        }
    
    @handle_errors
    def batch_search(
        self,
        patterns: List[Dict[str, str]],
        directory: str,
        parallel: bool = True,
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple pattern searches in parallel.
        
        Args:
            patterns: List of pattern dictionaries with 'pattern' and 'name' keys
            directory: Directory to search
            parallel: Whether to run in parallel
            max_workers: Maximum parallel workers
            
        Returns:
            Aggregated results from all searches
        """
        from ..utils.batch_operations import (
            BatchSearcher, 
            BatchSearchRequest,
            aggregate_batch_results
        )
        
        # Validate directory
        validated_directory = directory
        
        # Create batch searcher
        searcher = BatchSearcher(
            search_func=self.search_directory,
            max_workers=max_workers if parallel else 1
        )
        
        # Convert pattern dicts to requests
        requests = []
        for p in patterns:
            if not isinstance(p, dict) or "pattern" not in p:
                continue
                
            requests.append(BatchSearchRequest(
                pattern=p["pattern"],
                name=p.get("name", p["pattern"][:20]),
                category=p.get("category"),
                description=p.get("description"),
                severity=p.get("severity", "info")
            ))
        
        if not requests:
            return {
                "error": "No valid patterns provided",
                "suggestion": "Each pattern should have at least 'pattern' and 'name' keys"
            }
        
        # Execute batch search
        results = searcher.batch_search(
            requests=requests,
            directory=validated_directory,
            parallel=parallel
        )
        
        # Aggregate results
        aggregated = aggregate_batch_results(results)
        
        return aggregated
    
    @handle_errors
    def search_stream(
        self,
        pattern: str,
        directory: str,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Create a streaming search that auto-paginates results.
        
        Args:
            pattern: Pattern to search for
            directory: Directory to search
            page_size: Results per page
            
        Returns:
            Stream configuration for retrieving results
        """
        
        # This would return stream configuration
        # In a real implementation, this would set up a streaming endpoint
        return {
            "stream_id": f"stream_{id(pattern)}_{id(directory)}",
            "pattern": pattern,
            "directory": directory,
            "page_size": page_size,
            "status": "ready",
            "usage": "Use the stream_id to retrieve results progressively",
            "note": "Full streaming requires WebSocket or SSE support"
        }
    
    @handle_errors
    def create_smart_pattern(
        self,
        description: str,
        language: str,
        examples: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a pattern from natural language description and examples.
        
        Args:
            description: What you want to find
            language: Programming language
            examples: Optional code examples
            
        Returns:
            Generated pattern(s) with confidence scores
        """
        from ..utils.simple_pattern_builder import create_pattern_for_concept
        
        # CRITICAL FIX: Better error handling and fallbacks
        try:
            result = create_pattern_for_concept(description, language)
            
            # If no patterns were generated, provide helpful fallback
            if not result.get("patterns"):
                # Try to extract patterns from examples if provided
                if examples:
                    from ..utils.simple_pattern_builder import SimplePatternBuilder
                    fallback_patterns = []
                    for example in examples[:3]:  # Use first 3 examples
                        pattern = SimplePatternBuilder.from_example(example, language)
                        if pattern and pattern != example:  # Only if it was actually transformed
                            fallback_patterns.append(pattern)
                    
                    if fallback_patterns:
                        result["patterns"] = fallback_patterns
                        result["note"] = "Patterns generated from provided examples"
                        result["confidence"] = 0.6
                    else:
                        # Last resort: provide very basic patterns
                        result["patterns"] = [
                            "$NAME($$$ARGS)",  # Generic function call
                            "$OBJ.$METHOD($$$ARGS)",  # Generic method call
                        ]
                        result["note"] = "Generic patterns provided as fallback"
                        result["confidence"] = 0.3
                        result["suggestions"] = [
                            "Try a more specific description (e.g., 'async functions', 'error handling')",
                            "Provide code examples to improve pattern generation",
                            "Use specific keywords related to your search"
                        ]
                else:
                    # No examples, provide language-specific fallbacks
                    if language == "rust":
                        fallback = ["fn $NAME($$$ARGS)", "$OBJ.$METHOD($$$ARGS)", "$VAR.$FIELD"]
                    elif language == "python":
                        fallback = ["def $NAME($$$ARGS)", "$OBJ.$METHOD($$$ARGS)", "$VAR.$ATTR"]
                    elif language in ["javascript", "typescript"]:
                        fallback = ["function $NAME($$$ARGS)", "$OBJ.$METHOD($$$ARGS)", "$VAR.$PROP"]
                    else:
                        fallback = ["$NAME($$$ARGS)", "$OBJ.$METHOD($$$ARGS)"]
                    
                    result["patterns"] = fallback
                    result["note"] = f"Basic {language} patterns provided as fallback"
                    result["confidence"] = 0.4
                    result["suggestions"] = [
                        f"Try more specific descriptions for {language} code",
                        "Provide code examples to improve pattern accuracy",
                        "Use language-specific terms (e.g., 'functions', 'methods', 'structs')"
                    ]
            
            # If examples provided, try to refine patterns
            if examples and result["patterns"]:
                refined_patterns = []
                
                for pattern in result["patterns"]:
                    if isinstance(pattern, str):
                        confidence = result.get("confidence", 0.8)
                        
                        # Increase confidence if pattern elements appear in examples
                        pattern_lower = pattern.lower()
                        for example in examples:
                            example_lower = example.lower()
                            # More sophisticated matching
                            common_words = set(pattern_lower.split()) & set(example_lower.split())
                            if common_words:
                                confidence += 0.1 * len(common_words) / len(pattern_lower.split())
                        
                        refined_patterns.append({
                            "pattern": pattern,
                            "confidence": min(confidence, 1.0)
                        })
                    else:
                        # Pattern is already a dict
                        refined_patterns.append(pattern)
                
                result["patterns"] = refined_patterns
                result["refined_with_examples"] = True
            else:
                # Convert simple strings to pattern objects
                if result["patterns"] and isinstance(result["patterns"][0], str):
                    pattern_objects = []
                    for pattern in result["patterns"]:
                        pattern_objects.append({
                            "pattern": pattern,
                            "confidence": result.get("confidence", 0.8)
                        })
                    result["patterns"] = pattern_objects
            
            # Add usage examples
            result["usage_examples"] = [
                f"Use pattern '{p.get('pattern', p) if isinstance(p, dict) else p}' to search {language} code"
                for p in result["patterns"][:3]
            ]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Smart pattern generation failed: {e}")
            return {
                "concept": description,
                "language": language,
                "patterns": [],
                "error": f"Pattern generation failed: {str(e)}",
                "suggestions": [
                    "Try a simpler description",
                    "Check that the language is supported",
                    "Provide specific code examples"
                ],
                "confidence": 0.0
            }

    def start(self) -> None:
        """Start the MCP server"""
        if self.config.host != "localhost" or self.config.port != 8080:
            self.logger.warning(
                "Note: FastMCP currently ignores host and port. Using default settings."
            )

        self.logger.info("Starting AST Grep MCP server")

        # Log initial cache settings
        self.logger.info(
            "Result cache initialized with size: " + str(result_cache.maxsize)
        )

        # Log output and diagnostic configuration
        self.logger.info(f"Output format: {self.config.output_config.format}")
        self.logger.info(
            f"Diagnostic verbosity: {self.config.diagnostic_config.verbosity}"
        )

        # Log refactoring configuration
        if self.config.refactoring_config.preview_mode:
            self.logger.info("Refactoring preview mode enabled")

        self.mcp.run()
