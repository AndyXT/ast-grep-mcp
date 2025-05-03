"""
Error handling utilities for the ast-grep-mcp package.
"""

import logging
import functools
import traceback
from typing import Any, Callable, Dict, TypeVar, cast

# Create a logger for this module
logger = logging.getLogger("ast_grep_mcp.utils.error_handling")

# Type variables for function signatures
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Dict[str, Any]])

# Common pattern examples by language
PATTERN_EXAMPLES = {
    "python": {
        "function_definition": "def $NAME($$$PARAMS)",
        "class_definition": "class $NAME",
        "for_loop": "for $VAR in $ITER",
        "if_statement": "if $COND: $$$BODY",
        "import_statement": "import $MODULE"
    },
    "javascript": {
        "function_declaration": "function $NAME($$$PARAMS)",
        "arrow_function": "($$$PARAMS) => $$$BODY",
        "class_definition": "class $NAME",
        "if_statement": "if ($COND) $$$BODY",
        "import_statement": "import $NAME from '$MODULE'"
    },
    "typescript": {
        "function_declaration": "function $NAME($$$PARAMS): $RETURN_TYPE",
        "arrow_function": "($$$PARAMS): $RETURN_TYPE => $$$BODY",
        "interface": "interface $NAME { $$$PROPS }",
        "type_definition": "type $NAME = $TYPE"
    },
    # Add other language examples as needed
}

# Default examples for when language is unknown
DEFAULT_PATTERN_EXAMPLES = {
    "variable": "$NAME = $VALUE",
    "function_call": "$FUNCTION($$$ARGS)",
    "block": "{ $$$BODY }"
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
        "syntax", "parse", "pattern", "unexpected", "token", 
        "invalid pattern", "expected", "mismatched", "format error"
    ]
    
    # More specific checks to avoid false positives
    if "invalid parameter value" in error_str:
        return False
        
    return any(indicator in error_str for indicator in syntax_indicators) or "SyntaxError" in error_type


def get_pattern_help(language: str = None) -> str:
    """
    Get helpful pattern examples for a specific language.
    
    Args:
        language: The programming language to get examples for.
        
    Returns:
        A formatted string with pattern examples.
    """
    # Get the examples for the language, or default if not available
    examples = PATTERN_EXAMPLES.get(language, DEFAULT_PATTERN_EXAMPLES)
    
    # Format the examples into a helpful message
    examples_str = "\n".join([f"  {name}: {pattern}" for name, pattern in examples.items()])
    
    # Use "common" if language is not in our predefined examples
    language_display = language if language in PATTERN_EXAMPLES else "common"
    
    message = (
        f"Pattern syntax error detected. Here are some valid {language_display} pattern examples:"
        f"\n{examples_str}"
        f"\n\nPatterns use $ to define capture variables/placeholders:"
        f"\n  $NAME - captures a single node"
        f"\n  $$$NAME - captures multiple nodes (variadic)"
        f"\n\nFor more details, see the ast-grep pattern documentation."
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
                # Try to extract the language
                language = None
                if len(args) >= 2 and func.__name__ in ["analyze_code", "refactor_code"]:
                    language = args[1]  # Second arg is typically language
                elif "language" in kwargs:
                    language = kwargs["language"]
                    
                # Get helpful pattern syntax examples
                syntax_help = get_pattern_help(language)
            
            # Format the error message with syntax help if available
            formatted_error = f"{error_type}: {error_message}"
            if syntax_help:
                formatted_error = f"{formatted_error}\n\n{syntax_help}"
            
            # Determine the appropriate error response format
            # Check if the function name matches any known patterns
            if func.__name__ == "analyze_code" or func.__name__ == "analyze_file":
                return {
                    "error": formatted_error,
                    "matches": [],
                    "count": 0
                }
            elif func.__name__ == "refactor_code":
                # Extract the code parameter from args or kwargs
                code = ""
                if len(args) >= 1:
                    code = args[0]
                elif "code" in kwargs:
                    code = kwargs["code"]
                
                return {
                    "error": formatted_error,
                    "success": False,
                    "original_code": code,
                    "refactored_code": code  # No changes on error
                }
            elif func.__name__ == "get_language_patterns":
                return {
                    "error": formatted_error,
                    "patterns": {}
                }
            elif func.__name__ == "get_supported_languages":
                return {
                    "error": formatted_error,
                    "languages": {}
                }
            else:
                # Generic error response for other functions
                return {
                    "error": formatted_error,
                    "success": False
                }
    
    return cast(F, wrapper) 