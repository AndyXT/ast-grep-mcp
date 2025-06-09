"""
Enhanced error handling with actionable error messages.
"""
from typing import Dict, Any, Optional, Callable, List
import functools
import logging


class EnhancedError(Exception):
    """Enhanced error with actionable suggestions."""
    
    def __init__(self, message: str, suggestions: List[str] = None, error_code: str = None):
        super().__init__(message)
        self.suggestions = suggestions or []
        self.error_code = error_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error": str(self),
            "error_code": self.error_code,
            "suggestions": self.suggestions,
            "documentation": self._get_documentation_link(),
        }
    
    def _get_documentation_link(self) -> Optional[str]:
        """Get relevant documentation link based on error code."""
        doc_links = {
            "TOKEN_LIMIT": "https://docs.ast-grep-mcp.com/errors/token-limit",
            "PATTERN_INVALID": "https://docs.ast-grep-mcp.com/pattern-syntax",
            "FILE_ACCESS": "https://docs.ast-grep-mcp.com/security",
        }
        return doc_links.get(self.error_code)


class TokenLimitError(EnhancedError):
    """Error when response exceeds token limit."""
    
    def __init__(self, actual_tokens: int, limit: int, response_type: str = "search"):
        message = f"Response size ({actual_tokens} tokens) exceeds {response_type} limit ({limit} tokens)"
        
        suggestions = [
            "Use search_summary() for an overview without full match details",
            "Narrow your search with a specific subdirectory",
            "Add file_extensions filter (e.g., file_extensions=['.py'])",
            "Use page_size parameter (try page_size=5)",
            "Use search_stream() for progressive result loading",
        ]
        
        if response_type == "search":
            suggestions.insert(0, "Example: search_summary(pattern='fn $NAME', directory='.')")
        
        super().__init__(message, suggestions, "TOKEN_LIMIT")
        self.actual_tokens = actual_tokens
        self.limit = limit


class PatternSyntaxError(EnhancedError):
    """Error with pattern syntax."""
    
    def __init__(self, pattern: str, issue: str, language: str):
        message = f"Invalid pattern syntax: {issue}"
        
        suggestions = [
            f"Use pattern_wizard('{self._describe_intent(pattern)}', language='{language}')",
            "Use $ for single token capture (not $$)",
            "Use $$$ for multiple tokens capture",
            "Check pattern with validate_pattern() first",
            "See pattern examples with get_pattern_examples()",
        ]
        
        super().__init__(message, suggestions, "PATTERN_INVALID")
        self.pattern = pattern
        self.language = language
    
    def _describe_intent(self, pattern: str) -> str:
        """Try to describe what the user might be looking for."""
        if "fn" in pattern or "function" in pattern:
            return "find functions"
        elif "class" in pattern:
            return "find classes"
        elif "import" in pattern:
            return "find imports"
        return "search code"


class FileAccessError(EnhancedError):
    """Error with file access permissions."""
    
    def __init__(self, path: str, reason: str):
        message = f"Cannot access {path}: {reason}"
        
        suggestions = [
            "Check if the path exists and is readable",
            "Ensure you have permission to access this directory",
            "Use relative paths from the current working directory",
            "Check configured safe_roots in the MCP server",
        ]
        
        super().__init__(message, suggestions, "FILE_ACCESS")
        self.path = path


def enhanced_error_handler(response_type: str = "default"):
    """Decorator for enhanced error handling."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Check for token limit issues
                if isinstance(result, dict) and "error" not in result:
                    # Estimate token count
                    from ..utils.pagination import ResponsePaginator
                    paginator = ResponsePaginator()
                    estimated_tokens = paginator.estimate_tokens(result)
                    limit = paginator.TOKEN_LIMITS.get(response_type, 20000)
                    
                    if estimated_tokens > limit:
                        raise TokenLimitError(estimated_tokens, limit, response_type)
                
                return result
                
            except TokenLimitError:
                raise  # Re-raise our enhanced errors
            except PatternSyntaxError:
                raise
            except FileAccessError:
                raise
            except Exception as e:
                # Convert other errors to enhanced errors
                logger = logging.getLogger(__name__)
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                
                # Try to provide helpful suggestions based on error
                suggestions = []
                error_str = str(e).lower()
                
                if "pattern" in error_str or "syntax" in error_str:
                    suggestions = [
                        "Check pattern syntax with validate_pattern()",
                        "Use pattern_wizard() for pattern suggestions",
                        "See examples with get_pattern_examples()",
                    ]
                elif "file" in error_str or "directory" in error_str:
                    suggestions = [
                        "Check if the file/directory exists",
                        "Use absolute paths or paths relative to current directory",
                        "Ensure you have read permissions",
                    ]
                elif "timeout" in error_str:
                    suggestions = [
                        "Try searching a smaller directory",
                        "Use file_extensions to limit file types",
                        "Reduce the number of parallel workers",
                    ]
                
                raise EnhancedError(str(e), suggestions)
        
        return wrapper
    return decorator


def format_error_response(error: Exception) -> Dict[str, Any]:
    """Format any error into a helpful response."""
    if isinstance(error, EnhancedError):
        return error.to_dict()
    
    # Generic error formatting
    error_str = str(error)
    error_type = type(error).__name__
    
    # Try to provide generic helpful suggestions
    suggestions = ["Check the error message for details"]
    
    if "token" in error_str.lower() or "size" in error_str.lower():
        suggestions = [
            "Try reducing the search scope",
            "Use pagination parameters",
            "Filter by file extensions",
        ]
    elif "permission" in error_str.lower() or "access" in error_str.lower():
        suggestions = [
            "Check file permissions",
            "Ensure the path is correct",
            "Verify the MCP server configuration",
        ]
    
    return {
        "error": error_str,
        "error_type": error_type,
        "suggestions": suggestions,
    }


class ErrorContext:
    """Context manager for enhanced error handling."""
    
    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            # Log with context
            self.logger.error(
                f"Error during {self.operation}: {exc_val}",
                extra={"context": self.context}
            )
            
            # Enhance certain errors
            if isinstance(exc_val, Exception) and not isinstance(exc_val, EnhancedError):
                # Try to provide more context
                if "pattern" in self.context:
                    raise PatternSyntaxError(
                        self.context["pattern"],
                        str(exc_val),
                        self.context.get("language", "unknown")
                    ) from exc_val
                elif "path" in self.context or "directory" in self.context:
                    path = self.context.get("path") or self.context.get("directory")
                    raise FileAccessError(path, str(exc_val)) from exc_val
            
        return False  # Don't suppress the exception