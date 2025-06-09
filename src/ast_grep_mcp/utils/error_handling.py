"""
Error handling utilities for the ast-grep-mcp package.
"""

import logging
import functools
import traceback
import re
from typing import Any, Callable, Dict, TypeVar, cast, Optional, List
from .error_codes import ErrorCode, ErrorMessageBuilder

# Create a logger for this module
logger = logging.getLogger("ast_grep_mcp.utils.error_handling")

# Type variables for function signatures
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Dict[str, Any]])


def create_unified_error_response(
    error: Exception,
    function_name: str,
    context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
    pattern_help: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a unified error response format.
    
    Args:
        error: The exception that occurred
        function_name: Name of the function where error occurred
        context: Additional context about the error
        suggestions: Helpful suggestions for the user
        pattern_help: Pattern-specific help text
    
    Returns:
        Standardized error response dictionary
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Try to get detailed error information
    if isinstance(error, PatternValidationError):
        # Use the error code system for pattern validation errors
        detailed_error = ErrorMessageBuilder.build_error(
            ErrorCode.PATTERN_SYNTAX_ERROR,
            pattern=context.get("pattern", "") if context else "",
            language=context.get("language", "") if context else ""
        )
    else:
        # Try to enhance other exceptions
        detailed_error = ErrorMessageBuilder.enhance_exception_message(error, context)
    
    response = {
        "success": False,
        "error": {
            "type": error_type,
            "message": error_message,
            "function": function_name,
            "code": detailed_error.code.value,
            "code_name": detailed_error.code.name,
        }
    }
    
    # Add context if provided
    if context:
        response["error"]["context"] = context
    
    # Add pattern help if provided
    if pattern_help:
        response["error"]["pattern_help"] = pattern_help
    
    # Add detailed error information
    if detailed_error.details:
        response["error"]["details"] = detailed_error.details
    
    # Add suggestions from detailed error or provided suggestions
    if detailed_error.suggestions:
        response["error"]["suggestions"] = detailed_error.suggestions
    elif suggestions:
        response["error"]["suggestions"] = suggestions
    else:
        # Default suggestions based on error type
        if error_type == "AttributeError":
            response["error"]["suggestions"] = [
                "This might be a version compatibility issue",
                "Check that the function exists in the current version",
                "Verify input parameters are correct"
            ]
        elif error_type == "KeyError":
            response["error"]["suggestions"] = [
                "Check that all required keys exist in the input",
                "Verify the data structure matches expectations"
            ]
        elif error_type == "ValueError":
            response["error"]["suggestions"] = [
                "Check input values are in the correct format",
                "Verify patterns follow the correct syntax",
                "Ensure language is supported"
            ]
        elif error_type == "TypeError":
            response["error"]["suggestions"] = [
                "Check that arguments are of the correct type",
                "Verify the number of arguments is correct"
            ]
    
    # Add documentation link
    response["error"]["documentation"] = "https://github.com/ast-grep/ast-grep-mcp/blob/main/docs/usage-guide.md"
    
    # Add troubleshooting tips
    response["error"]["troubleshooting"] = [
        "Check the error message and type for specific details",
        "Review the function documentation for correct usage",
        "Try simpler patterns or inputs to isolate the issue"
    ]
    
    return response

# Common pattern examples by language
PATTERN_EXAMPLES = {
    "python": {
        "function_definition": "def $NAME($$$PARAMS):",
        "class_definition": "class $NAME:",
        "for_loop": "for $VAR in $ITER:",
        "if_statement": "if $COND:",
        "import_statement": "import $MODULE",
        "method_call": "$OBJ.$METHOD($$$ARGS)",
        "list_comprehension": "[$EXPR for $VAR in $ITER]",
        "dict_comprehension": "{$KEY: $VALUE for $ITEM in $ITER}",
        "try_except": "try:\n    $$$BODY\nexcept $EXCEPTION:",
        "with_statement": "with $EXPR as $VAR:",
        "decorator": "@$DECORATOR",
        "assignment": "$VAR = $VALUE",
    },
    "javascript": {
        "function_declaration": "function $NAME($$$PARAMS) { $$$BODY }",
        "arrow_function": "($$$PARAMS) => $EXPR",
        "arrow_function_block": "($$$PARAMS) => { $$$BODY }",
        "class_definition": "class $NAME { $$$BODY }",
        "if_statement": "if ($COND) { $$$BODY }",
        "import_statement": "import $NAME from '$MODULE'",
        "export_statement": "export $DECL",
        "const_declaration": "const $NAME = $VALUE",
        "let_declaration": "let $NAME = $VALUE",
        "for_loop": "for ($INIT; $COND; $UPDATE) { $$$BODY }",
        "for_of_loop": "for (const $VAR of $ITER) { $$$BODY }",
        "template_literal": "`$$$TEXT`",
        "object_destructuring": "const { $$$PROPS } = $OBJ",
        "array_destructuring": "const [$$$ITEMS] = $ARR",
        "async_function": "async function $NAME($$$PARAMS) { $$$BODY }",
        "await_expression": "await $EXPR",
    },
    "typescript": {
        "function_declaration": "function $NAME($$$PARAMS): $RETURN_TYPE { $$$BODY }",
        "arrow_function": "($$$PARAMS): $RETURN_TYPE => $EXPR",
        "interface": "interface $NAME { $$$PROPS }",
        "type_definition": "type $NAME = $TYPE",
        "generic_function": "function $NAME<$TYPE>($$$PARAMS): $RETURN { $$$BODY }",
        "enum": "enum $NAME { $$$VALUES }",
        "class_with_types": "class $NAME implements $INTERFACE { $$$BODY }",
        "type_guard": "$VAR is $TYPE",
        "as_expression": "$EXPR as $TYPE",
        "namespace": "namespace $NAME { $$$BODY }",
    },
    "rust": {
        "function": "fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }",
        "struct": "struct $NAME { $$$FIELDS }",
        "enum": "enum $NAME { $$$VARIANTS }",
        "impl_block": "impl $TYPE { $$$METHODS }",
        "trait": "trait $NAME { $$$METHODS }",
        "match_expression": "match $EXPR { $$$ARMS }",
        "if_let": "if let $PATTERN = $EXPR { $$$BODY }",
        "use_statement": "use $PATH",
        "macro_call": "$MACRO!($$$ARGS)",
        "lifetime": "&'$LIFETIME $TYPE",
        "async_fn": "async fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }",
    },
    "go": {
        "function": "func $NAME($$$PARAMS) $RETURN { $$$BODY }",
        "method": "func ($RECEIVER $TYPE) $NAME($$$PARAMS) $RETURN { $$$BODY }",
        "struct": "type $NAME struct { $$$FIELDS }",
        "interface": "type $NAME interface { $$$METHODS }",
        "if_statement": "if $COND { $$$BODY }",
        "for_loop": "for $COND { $$$BODY }",
        "for_range": "for $KEY, $VALUE := range $ITER { $$$BODY }",
        "switch": "switch $EXPR { $$$CASES }",
        "goroutine": "go $FUNC($$$ARGS)",
        "channel_send": "$CHAN <- $VALUE",
        "defer": "defer $EXPR",
    },
    "c": {
        "function": "$RETURN $NAME($$$PARAMS) { $$$BODY }",
        "struct": "struct $NAME { $$$FIELDS };",
        "if_statement": "if ($COND) { $$$BODY }",
        "for_loop": "for ($INIT; $COND; $UPDATE) { $$$BODY }",
        "while_loop": "while ($COND) { $$$BODY }",
        "pointer": "$TYPE *$NAME",
        "typedef": "typedef $TYPE $NAME;",
        "switch": "switch ($EXPR) { $$$CASES }",
        "include": "#include <$HEADER>",
        "define": "#define $NAME $VALUE",
    },
    "lua": {
        "function": "function $NAME($$$PARAMS)\n    $$$BODY\nend",
        "local_function": "local function $NAME($$$PARAMS)\n    $$$BODY\nend",
        "if_statement": "if $COND then\n    $$$BODY\nend",
        "for_loop": "for $VAR = $START, $END do\n    $$$BODY\nend",
        "for_in": "for $KEY, $VALUE in $ITER do\n    $$$BODY\nend",
        "while_loop": "while $COND do\n    $$$BODY\nend",
        "local_var": "local $NAME = $VALUE",
        "table": "{ $$$ITEMS }",
        "method_call": "$OBJ:$METHOD($$$ARGS)",
    }
}

# Default examples for when language is unknown
DEFAULT_PATTERN_EXAMPLES = {
    "variable": "$NAME = $VALUE",
    "function_call": "$FUNCTION($$$ARGS)",
    "block": "{ $$$BODY }",
}


def is_pattern_syntax_error(error: Exception) -> bool:
    """
    Determine if an exception is likely related to pattern syntax.

    Args:
        error: The exception to check.

    Returns:
        True if the error seems to be a pattern syntax error.
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # Check for common pattern syntax error indicators
    syntax_indicators = [
        "syntax",
        "parse",
        "pattern",
        "unexpected",
        "token",
        "invalid pattern",
        "expected",
        "mismatched",
        "format error",
    ]

    # More specific checks to avoid false positives
    if "invalid parameter value" in error_str:
        return False

    return (
        any(indicator in error_str for indicator in syntax_indicators)
        or "SyntaxError" in error_type
    )


def get_pattern_help(language: Optional[str] = None, error_type: Optional[str] = None) -> str:
    """
    Get helpful pattern examples for a specific language.

    Args:
        language: The programming language to get examples for.
        error_type: Optional specific error type to provide targeted help.

    Returns:
        A formatted string with pattern examples.
    """
    # Get the examples for the language, or default if not available
    examples = PATTERN_EXAMPLES.get(language, DEFAULT_PATTERN_EXAMPLES)

    # Select relevant examples based on error content
    if error_type:
        error_lower = error_type.lower()
        # Filter examples that might be relevant to the error
        relevant_examples = {}
        for name, pattern in examples.items():
            if any(keyword in error_lower for keyword in name.split("_")) or \
               any(keyword in error_lower for keyword in ["function", "class", "if", "for", "import"] if keyword in name):
                relevant_examples[name] = pattern
        
        # If we found relevant examples, use those instead
        if relevant_examples:
            examples = relevant_examples
        else:
            # Show the most common patterns
            common_keys = ["function_definition", "function_declaration", "function", 
                          "if_statement", "for_loop", "class_definition", "import_statement"]
            examples = {k: v for k, v in examples.items() if any(ck in k for ck in common_keys)}
            if not examples:  # Fallback to first 5 examples
                examples = dict(list(PATTERN_EXAMPLES.get(language, DEFAULT_PATTERN_EXAMPLES).items())[:5])

    # Format the examples into a helpful message
    examples_str = "\n".join(
        [f"  {name.replace('_', ' ').title()}: {pattern}" for name, pattern in examples.items()]
    )

    # Use "common" if language is not in our predefined examples
    language_display = language if language in PATTERN_EXAMPLES else "common"

    message = (
        f"\n📝 Pattern Syntax Help for {language_display.title()}\n"
        f"{'=' * 50}\n"
        f"\nValid pattern examples:\n{examples_str}"
        f"\n\n🔤 Pattern Syntax Rules:\n"
        f"  • $NAME - captures a single node (identifier, expression, etc.)\n"
        f"  • $$$NAME - captures multiple nodes (variadic - like function parameters)\n"
        f"  • $_ - wildcard that matches any single node\n"
        f"  • Exact code - matches literal code exactly\n"
        f"\n💡 Common Mistakes:\n"
        f"  • Using $$ instead of $$$ for multiple items\n"
        f"  • Missing $ before metavariable names\n"
        f"  • Forgetting colons in Python or semicolons in C/Rust\n"
        f"  • Using uppercase names without $ (NAME vs $NAME)\n"
        f"\n📚 Documentation: https://ast-grep.github.io/reference/pattern-syntax.html"
    )

    return message


def handle_errors(func: F) -> F:
    """
    Decorator to handle exceptions in tool functions consistently.

    This decorator wraps the function in a try/except block and ensures that
    any exceptions are caught, logged, and returned in a consistent format.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        try:
            # Call the original function
            return func(*args, **kwargs)
        except Exception as e:
            # Extract context from function arguments
            context = {}
            if args and hasattr(args[0], '__class__'):
                # Skip 'self' parameter
                arg_names = func.__code__.co_varnames[1:func.__code__.co_argcount]
                for i, (arg_name, arg_value) in enumerate(zip(arg_names, args[1:])):
                    if isinstance(arg_value, (str, int, float, bool, list)):
                        context[arg_name] = arg_value
            
            # Add kwargs to context
            for key, value in kwargs.items():
                if isinstance(value, (str, int, float, bool, list)):
                    context[key] = value
            
            # Check for AttributeError related to missing methods
            if isinstance(e, AttributeError) and "object has no attribute" in str(e):
                suggestions = [
                    "This might be a method that doesn't exist in the current version",
                    "Check for typos in method names",
                    "Ensure all dependencies are properly installed"
                ]
                return create_unified_error_response(e, func.__name__, context, suggestions)
            
            # Get detailed exception info
            error_type = type(e).__name__
            error_message = str(e)
            stack_trace = traceback.format_exc()

            # Log the error
            logger.error(
                f"Error in {func.__name__}: {error_type}: {error_message}\n{stack_trace}"
            )

            # Check if this might be a pattern syntax error
            syntax_help = ""
            if is_pattern_syntax_error(e):
                # Try to extract the language and pattern
                language = None
                pattern = None
                if len(args) >= 2 and func.__name__ in [
                    "analyze_code",
                    "refactor_code",
                ]:
                    language = args[1]  # Second arg is typically language
                    if len(args) >= 3:
                        pattern = args[2]  # Third arg is typically pattern
                elif "language" in kwargs:
                    language = kwargs["language"]
                    pattern = kwargs.get("pattern", None)

                # Get helpful pattern syntax examples
                syntax_help = get_pattern_help(language, error_message)
                
                # Add information about what was searched vs what was found
                if pattern:
                    syntax_help += f"\n\n🔍 Your Pattern: {pattern}"
                    
                    # Try to identify common issues in the pattern
                    issues = []
                    if "$$" in pattern and "$$$" not in pattern:
                        issues.append("• Found $$ - did you mean $$$ for multiple items?")
                    if re.search(r'\b[A-Z][A-Z_]+\b', pattern) and "$" not in pattern:
                        issues.append("• Found uppercase identifiers without $ - add $ prefix for metavariables")
                    if language == "python" and any(kw in pattern for kw in ["if", "for", "def", "class"]) and ":" not in pattern:
                        issues.append("• Missing colon (:) after Python statement")
                    
                    if issues:
                        syntax_help += "\n\n⚠️  Potential Issues:\n" + "\n".join(issues)

            # Format the error message with enhanced information
            formatted_error = f"❌ {error_type}: {error_message}"
            if syntax_help:
                formatted_error = f"{formatted_error}\n{syntax_help}"
            else:
                # Even without pattern syntax error, provide some context
                formatted_error += "\n\n💡 Tip: Check the pattern syntax guide for your language."

            # Prepare pattern help if applicable
            pattern_help = None
            if syntax_help:
                pattern_help = syntax_help
            
            # Extract suggestions based on error analysis
            suggestions = []
            if is_pattern_syntax_error(e):
                suggestions.extend([
                    "Check pattern syntax for your language",
                    "Try simpler patterns first (e.g., 'fn $NAME' instead of complex patterns)",
                    "Use the pattern builder for complex patterns",
                    "Review pattern examples with get_language_patterns()"
                ])
            
            # Return unified error response
            return create_unified_error_response(
                e, 
                func.__name__, 
                context, 
                suggestions if suggestions else None,
                pattern_help
            )

    return cast(F, wrapper)


def handle_method_not_found_error(error: AttributeError, calling_function: str) -> Dict[str, Any]:
    """
    Handle AttributeError for missing methods with helpful suggestions.
    
    Args:
        error: The AttributeError exception
        calling_function: Name of the function that was called
        
    Returns:
        Error response with available methods and suggestions
    """
    error_msg = str(error)
    
    # Extract method name from error message
    import re
    match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_msg)
    if not match:
        return {"error": error_msg, "success": False}
    
    object_type, method_name = match.groups()
    
    # Define available methods for different object types
    available_methods = {
        "AstAnalyzerV2": [
            "analyze_code(code, language, pattern)",
            "refactor_code(code, language, pattern, replacement)",
            "analyze_file(file_path, pattern)",
            "search_directory(directory, pattern, parallel=True, max_workers=None, file_extensions=None)",
            "search_directory_with_context(directory, pattern, context_lines=3, include_metrics=True)",
            "get_language_patterns(language)",
            "get_supported_languages()",
            "validate_pattern(pattern, language, code=None)",
            "preview_refactoring(code, language, pattern, replacement)",
            "suggest_pattern_corrections(pattern, language, error_type=None)",
            "search_directory_stream(directory, pattern, language, stream_config=None)",
            "analyze_project_structure(directory)",
            "run_security_audit(language, directory)",
            "analyze_code_quality(directory)",
            "find_trait_implementations(trait_name, directory)",
            "find_deprecated_usage(directory, include_rust_analyzer_hints=True)",
        ],
        "AstGrepMCP": [
            "analyze_code(code, language, pattern)",
            "refactor_code(code, language, pattern, replacement)", 
            "analyze_file(file_path, pattern)",
            "search_directory(directory, pattern, parallel=True, max_workers=None, file_extensions=None)",
            "get_language_patterns(language)",
            "get_supported_languages()",
            "get_config()",
            "set_config(config)",
            "generate_config(output_file=None)",
            "preview_refactoring(code, language, pattern, replacement)",
            "validate_pattern(pattern, language, code=None)",
            "suggest_pattern_corrections(pattern, language, error_type=None)",
            "search_directory_stream(directory, pattern, language, stream_config=None)",
            "create_rule(rule_id, pattern, message, language=None, severity='warning', fix=None, note=None)",
            "load_rules(file_path)",
            "run_rules(code, language, rule_ids=None, severities=None, file_path=None)",
            "test_rule(rule_config, test_code, language)",
            "compose_rule(rule_id, message, sub_rules, operator='all', language=None, severity='warning', fix=None)",
            "list_rules()",
            "remove_rule(rule_id)",
            "export_rules(output_format='yaml')",
        ]
    }
    
    methods = available_methods.get(object_type, [])
    
    # Find similar method names
    suggestions = []
    if methods and method_name:
        from difflib import get_close_matches
        method_names = [m.split("(")[0] for m in methods]
        close_matches = get_close_matches(method_name, method_names, n=3, cutoff=0.6)
        suggestions = [m for m in methods if any(cm in m for cm in close_matches)]
    
    # Build error message
    error_lines = [f"AttributeError: '{object_type}' object has no attribute '{method_name}'"]
    
    if methods:
        error_lines.append("\nAvailable methods:")
        for method in methods[:10]:  # Show first 10 methods
            error_lines.append(f"  - {method}")
        if len(methods) > 10:
            error_lines.append(f"  ... and {len(methods) - 10} more")
    
    if suggestions:
        error_lines.append("\nDid you mean:")
        for suggestion in suggestions:
            error_lines.append(f"  - {suggestion}")
    
    error_lines.append("\nFor documentation, see: https://github.com/ast-grep/ast-grep-mcp/blob/main/docs/usage-guide.md")
    
    error_message = "\n".join(error_lines)
    
    # Return appropriate error format based on calling function
    if calling_function in ["analyze_code", "analyze_file"]:
        return {"error": error_message, "matches": [], "count": 0}
    elif calling_function == "refactor_code":
        return {"error": error_message, "success": False, "refactored_code": ""}
    else:
        return {"error": error_message, "success": False}


# Custom exception classes
class AstGrepError(Exception):
    """Base exception for ast-grep-mcp errors"""
    pass


class PatternValidationError(AstGrepError):
    """Raised when a pattern is invalid"""

    def __init__(self, message: str, pattern: Optional[str] = None, 
                 language: Optional[str] = None, suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.pattern = pattern
        self.language = language
        self.suggestions = suggestions or []
        self.help_url = "https://ast-grep.github.io/reference/pattern-syntax.html"


class UnsupportedLanguageError(AstGrepError):
    """Raised when a language is not supported"""

    def __init__(self, message: str, language: Optional[str] = None, 
                 supported_languages: Optional[List[str]] = None):
        super().__init__(message)
        self.language = language
        self.supported_languages = supported_languages or []


class MethodNotFoundError(AstGrepError):
    """Raised when a method is not found"""
    
    def __init__(self, method_name: str, available_methods: Optional[List[str]] = None, 
                 suggestions: Optional[List[str]] = None):
        self.method_name = method_name
        self.available_methods = available_methods or []
        self.suggestions = suggestions or []
        
        message = f"Method '{method_name}' not found."
        if self.available_methods:
            message += "\n\nAvailable methods:\n"
            for method in self.available_methods[:10]:
                message += f"  - {method}\n"
            if len(self.available_methods) > 10:
                message += f"  ... and {len(self.available_methods) - 10} more\n"
        
        if self.suggestions:
            message += "\n\nDid you mean:\n"
            for suggestion in self.suggestions:
                message += f"  - {suggestion}\n"
                
        message += "\n\nFor documentation, see: https://github.com/ast-grep/ast-grep-mcp/blob/main/docs/usage-guide.md"
        super().__init__(message)
