"""
Error codes and detailed error messages for ast-grep MCP.

This module provides a centralized error handling system with specific error codes
and detailed messages to help users understand and fix issues.
"""

from enum import Enum
from typing import Dict, Optional, Any
import re


class ErrorCode(Enum):
    """Error codes for different types of failures."""
    
    # Pattern errors (1000-1999)
    PATTERN_SYNTAX_ERROR = 1001
    PATTERN_TOO_COMPLEX = 1002
    PATTERN_INVALID_METAVAR = 1003
    PATTERN_UNBALANCED_DELIMITERS = 1004
    PATTERN_UNSUPPORTED_CONSTRUCT = 1005
    
    # Language errors (2000-2999)
    LANGUAGE_NOT_SUPPORTED = 2001
    LANGUAGE_DETECTION_FAILED = 2002
    
    # File/Directory errors (3000-3999)
    FILE_NOT_FOUND = 3001
    DIRECTORY_NOT_FOUND = 3002
    FILE_ACCESS_DENIED = 3003
    FILE_TOO_LARGE = 3004
    FILE_ENCODING_ERROR = 3005
    
    # Processing errors (4000-4999)
    PARSING_FAILED = 4001
    TIMEOUT_ERROR = 4002
    MEMORY_ERROR = 4003
    CONCURRENT_PROCESSING_ERROR = 4004
    
    # Configuration errors (5000-5999)
    CONFIG_INVALID = 5001
    CONFIG_MISSING_REQUIRED = 5002
    
    # Rule errors (6000-6999)
    RULE_INVALID = 6001
    RULE_CONFLICT = 6002
    RULE_NOT_FOUND = 6003
    
    # General errors (9000-9999)
    UNKNOWN_ERROR = 9999


class DetailedError:
    """Represents a detailed error with code, message, and context."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list] = None
    ):
        self.code = code
        self.message = message
        self.details = details
        self.context = context or {}
        self.suggestions = suggestions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "error_code": self.code.value,
            "error_name": self.code.name,
            "message": self.message,
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.context:
            result["context"] = self.context
        
        if self.suggestions:
            result["suggestions"] = self.suggestions
        
        return result


class ErrorMessageBuilder:
    """Builds detailed error messages based on error type and context."""
    
    # Error message templates
    ERROR_TEMPLATES = {
        ErrorCode.PATTERN_SYNTAX_ERROR: {
            "message": "Invalid pattern syntax",
            "details": "The pattern '{pattern}' contains syntax errors for {language}",
            "suggestions": [
                "Check that all metavariables start with $ (single) or $$$ (multiple)",
                "Ensure delimiters (parentheses, braces, brackets) are balanced",
                "Verify the pattern follows {language} syntax rules",
            ]
        },
        ErrorCode.PATTERN_TOO_COMPLEX: {
            "message": "Pattern is too complex",
            "details": "The pattern '{pattern}' is too complex and may not work reliably",
            "suggestions": [
                "Try breaking down the pattern into simpler components",
                "Remove body and parameter captures (e.g., use 'fn $NAME' instead of 'fn $NAME($$$PARAMS) { $$$BODY }')",
                "Use multiple simpler patterns instead of one complex pattern",
            ]
        },
        ErrorCode.PATTERN_INVALID_METAVAR: {
            "message": "Invalid metavariable syntax",
            "details": "The pattern contains invalid metavariable '{metavar}'",
            "suggestions": [
                "Use $NAME for single captures",
                "Use $$$NAME for multiple captures",
                "Metavariable names should contain only letters, numbers, and underscores",
            ]
        },
        ErrorCode.PATTERN_UNBALANCED_DELIMITERS: {
            "message": "Unbalanced delimiters in pattern",
            "details": "The pattern has unmatched {delimiter_type}",
            "suggestions": [
                "Check that all opening delimiters have matching closing ones",
                "Count the number of {delimiter_type} to ensure they match",
            ]
        },
        ErrorCode.LANGUAGE_NOT_SUPPORTED: {
            "message": "Language not supported",
            "details": "The language '{language}' is not supported",
            "suggestions": [
                "Supported languages: {supported_languages}",
                "Check the spelling of the language name",
                "Use lowercase language names (e.g., 'python' not 'Python')",
            ]
        },
        ErrorCode.FILE_NOT_FOUND: {
            "message": "File not found",
            "details": "The file '{file_path}' does not exist",
            "suggestions": [
                "Check the file path for typos",
                "Ensure the file exists at the specified location",
                "Use absolute paths for clarity",
            ]
        },
        ErrorCode.DIRECTORY_NOT_FOUND: {
            "message": "Directory not found",
            "details": "The directory '{directory}' does not exist",
            "suggestions": [
                "Check the directory path for typos",
                "Ensure the directory exists",
                "Create the directory if needed",
            ]
        },
        ErrorCode.FILE_ACCESS_DENIED: {
            "message": "Access denied",
            "details": "Cannot access '{path}' due to insufficient permissions",
            "suggestions": [
                "Check file/directory permissions",
                "Ensure the file is not locked by another process",
                "Run with appropriate permissions if needed",
            ]
        },
        ErrorCode.FILE_ENCODING_ERROR: {
            "message": "File encoding error",
            "details": "Cannot read '{file_path}' due to encoding issues",
            "suggestions": [
                "Ensure the file is UTF-8 encoded",
                "Check for binary files that shouldn't be analyzed",
                "Add the file to ignore patterns if it's not source code",
            ]
        },
        ErrorCode.PARSING_FAILED: {
            "message": "Failed to parse code",
            "details": "Cannot parse the code as {language}",
            "suggestions": [
                "Verify the file contains valid {language} code",
                "Check for syntax errors in the source file",
                "Ensure the correct language is specified",
            ]
        },
        ErrorCode.TIMEOUT_ERROR: {
            "message": "Operation timed out",
            "details": "The operation exceeded the timeout of {timeout} seconds",
            "suggestions": [
                "Try searching a smaller directory",
                "Use more specific file extensions to reduce scope",
                "Increase the timeout if processing large codebases",
            ]
        },
        ErrorCode.RULE_INVALID: {
            "message": "Invalid rule configuration",
            "details": "The rule '{rule_id}' has invalid configuration",
            "suggestions": [
                "Check the rule syntax in the configuration file",
                "Ensure all required fields are present",
                "Validate the pattern in the rule",
            ]
        },
    }
    
    @classmethod
    def build_error(
        cls,
        code: ErrorCode,
        **context
    ) -> DetailedError:
        """
        Build a detailed error message.
        
        Args:
            code: The error code
            **context: Context variables for the error message
            
        Returns:
            DetailedError object
        """
        template = cls.ERROR_TEMPLATES.get(code, {
            "message": "An error occurred",
            "details": str(code),
            "suggestions": ["Please check the logs for more information"]
        })
        
        # Format the message and details with context
        message = template["message"]
        details = template.get("details", "")
        suggestions = template.get("suggestions", [])
        
        # Replace placeholders in details
        if details and context:
            try:
                details = details.format(**context)
            except KeyError:
                pass  # Keep original if formatting fails
        
        # Replace placeholders in suggestions
        formatted_suggestions = []
        for suggestion in suggestions:
            try:
                formatted_suggestions.append(suggestion.format(**context))
            except KeyError:
                formatted_suggestions.append(suggestion)
        
        return DetailedError(
            code=code,
            message=message,
            details=details,
            context=context,
            suggestions=formatted_suggestions
        )
    
    @classmethod
    def enhance_exception_message(
        cls,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> DetailedError:
        """
        Enhance an exception with detailed error information.
        
        Args:
            exception: The exception to enhance
            context: Additional context about the error
            
        Returns:
            DetailedError object
        """
        error_str = str(exception)
        context = context or {}
        
        # Try to determine error type from exception message
        if "not supported" in error_str.lower() and "language" in error_str.lower():
            return cls.build_error(ErrorCode.LANGUAGE_NOT_SUPPORTED, **context)
        elif "no such file" in error_str.lower() or "not found" in error_str.lower():
            if "directory" in error_str.lower():
                return cls.build_error(ErrorCode.DIRECTORY_NOT_FOUND, **context)
            else:
                return cls.build_error(ErrorCode.FILE_NOT_FOUND, **context)
        elif "permission" in error_str.lower() or "access" in error_str.lower():
            return cls.build_error(ErrorCode.FILE_ACCESS_DENIED, **context)
        elif "timeout" in error_str.lower():
            return cls.build_error(ErrorCode.TIMEOUT_ERROR, **context)
        elif "encoding" in error_str.lower() or "decode" in error_str.lower():
            return cls.build_error(ErrorCode.FILE_ENCODING_ERROR, **context)
        elif "pattern" in error_str.lower() and ("invalid" in error_str.lower() or "error" in error_str.lower()):
            # Check for specific pattern errors
            if any(delim in error_str for delim in ["parenthes", "brace", "bracket"]):
                delimiter_type = "delimiters"
                if "parenthes" in error_str:
                    delimiter_type = "parentheses"
                elif "brace" in error_str:
                    delimiter_type = "braces"
                elif "bracket" in error_str:
                    delimiter_type = "brackets"
                context["delimiter_type"] = delimiter_type
                return cls.build_error(ErrorCode.PATTERN_UNBALANCED_DELIMITERS, **context)
            elif "complex" in error_str.lower():
                return cls.build_error(ErrorCode.PATTERN_TOO_COMPLEX, **context)
            elif "$" in error_str:
                # Extract the problematic metavar if possible
                metavar_match = re.search(r'\$+\w+', error_str)
                if metavar_match:
                    context["metavar"] = metavar_match.group()
                return cls.build_error(ErrorCode.PATTERN_INVALID_METAVAR, **context)
            else:
                return cls.build_error(ErrorCode.PATTERN_SYNTAX_ERROR, **context)
        elif "parse" in error_str.lower() or "syntax" in error_str.lower():
            return cls.build_error(ErrorCode.PARSING_FAILED, **context)
        else:
            # Unknown error
            return DetailedError(
                code=ErrorCode.UNKNOWN_ERROR,
                message="An unexpected error occurred",
                details=error_str,
                context=context,
                suggestions=["Please check the error details and try again"]
            )