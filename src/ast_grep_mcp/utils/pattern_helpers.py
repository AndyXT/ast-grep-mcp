"""
Utilities for enhancing pattern handling, especially error diagnostics.
"""

import re
import logging
from typing import Dict, Optional, Any
from ..language_handlers import get_handler

logger = logging.getLogger("ast_grep_mcp.pattern_helpers")

# Common pattern syntax errors and their descriptive messages
COMMON_SYNTAX_ERRORS = {
    "mismatched_brackets": "Mismatched brackets, braces, or parentheses",
    "invalid_variable": "Invalid metavariable name format",
    "empty_variable": "Empty metavariable (use $_)",
    "unknown_operator": "Unknown operator or syntax construct",
    "missing_dollar": "Missing $ for metavariable",
    "unclosed_string": "Unclosed string literal",
    "invalid_escape": "Invalid escape sequence",
}

# Language-specific pattern syntax errors and solutions
LANGUAGE_SPECIFIC_ERRORS = {
    "python": {
        "inconsistent_indentation": {
            "message": "Inconsistent indentation in pattern",
            "solution": "Ensure all code within blocks has consistent indentation",
            "example": """
def function():
    $STMT1
    $STMT2
""",
        },
        "missing_colon": {
            "message": "Missing colon at the end of a compound statement",
            "solution": "Add a colon after if/for/while/def statements",
            "example": "if $CONDITION: $$$BODY",
        },
        "lambda_syntax": {
            "message": "Invalid lambda function syntax",
            "solution": "Use the form 'lambda $$$PARAMS: $EXPR'",
            "example": "lambda $$$PARAMS: $EXPR",
        },
    },
    "javascript": {
        "jsx_syntax": {
            "message": "Invalid JSX syntax in pattern",
            "solution": "Ensure JSX tags are properly formed and closed",
            "example": "<$COMPONENT $$$PROPS>$$$CHILDREN</$COMPONENT>",
        },
        "template_literal": {
            "message": "Invalid template literal syntax",
            "solution": "Use backticks for template literals: `text ${$VAR}`",
            "example": "`Hello, ${$NAME}`",
        },
        "arrow_function": {
            "message": "Invalid arrow function syntax",
            "solution": "Use the form '($$$PARAMS) => $$$BODY' or '$PARAM => $EXPR'",
            "example": "($$$PARAMS) => { $$$BODY }",
        },
    },
    "typescript": {
        "type_annotation": {
            "message": "Invalid type annotation",
            "solution": "Use proper TypeScript type annotation syntax",
            "example": "$VAR: $TYPE",
        },
        "generic_type": {
            "message": "Invalid generic type syntax",
            "solution": "Use the form 'Type<$T>'",
            "example": "Array<$TYPE>",
        },
        "interface_syntax": {
            "message": "Invalid interface declaration",
            "solution": "Use the form 'interface $NAME { $$$PROPS }'",
            "example": "interface $NAME { $$$PROPS }",
        },
    },
    "rust": {
        "lifetime_syntax": {
            "message": "Invalid lifetime syntax",
            "solution": "Use the form '$VAR: &'a $TYPE'",
            "example": "$VAR: &'a $TYPE",
        },
        "match_pattern": {
            "message": "Invalid match pattern",
            "solution": "Ensure match arms have proper pattern => expression syntax",
            "example": "match $EXPR { $PATTERN => $RESULT, _ => $DEFAULT }",
        },
        "trait_bound": {
            "message": "Invalid trait bound syntax",
            "solution": "Use the form 'T: Trait'",
            "example": "$T: $TRAIT",
        },
    },
    "c": {
        "pointer_syntax": {
            "message": "Invalid pointer syntax",
            "solution": "Use the form '$TYPE *$VAR' or '*$VAR'",
            "example": "$TYPE *$VAR",
        },
        "struct_syntax": {
            "message": "Invalid struct syntax",
            "solution": "Use the form 'struct $NAME { $$$FIELDS };'",
            "example": "struct $NAME { $$$FIELDS };",
        },
        "preprocessor_directive": {
            "message": "Invalid preprocessor directive",
            "solution": "Preprocessor directives must start with #",
            "example": "#include <$HEADER>",
        },
    },
    "go": {
        "function_syntax": {
            "message": "Invalid function declaration",
            "solution": "Use the form 'func $NAME($$$PARAMS) $RETURN_TYPE { $$$BODY }'",
            "example": "func $NAME($$$PARAMS) $RETURN_TYPE { $$$BODY }",
        },
        "channel_syntax": {
            "message": "Invalid channel syntax",
            "solution": "Use proper Go channel syntax",
            "example": "$CHAN <- $VALUE or $VAR := <-$CHAN",
        },
        "struct_syntax": {
            "message": "Invalid struct syntax",
            "solution": "Use the form 'type $NAME struct { $$$FIELDS }'",
            "example": "type $NAME struct { $$$FIELDS }",
        },
    },
}


def is_pattern_syntax_error(error_message: str) -> bool:
    """
    Check if an error message indicates a pattern syntax error.

    Args:
        error_message: The error message to check

    Returns:
        True if the error is a pattern syntax error, False otherwise
    """
    syntax_error_indicators = [
        "unexpected token",
        "invalid pattern",
        "syntax error",
        "unclosed",
        "unmatched",
        "unexpected character",
        "malformed",
        "missing",
        "unrecognized",
        "invalid syntax",
        "cannot parse",
        "failed to parse",
    ]

    return any(
        indicator in error_message.lower() for indicator in syntax_error_indicators
    )


def analyze_pattern_error(pattern: str, language: str) -> Dict[str, Any]:
    """
    Analyze a pattern to identify potential syntax errors and provide solutions.

    Args:
        pattern: The pattern to analyze
        language: The programming language

    Returns:
        Dictionary with error information and solutions
    """
    result = {
        "has_errors": False,
        "errors": [],
        "suggestions": [],
        "language_specific": [],
    }

    # Check for basic syntax issues
    error_checks = [
        (
            lambda p: p.count("(") != p.count(")"),
            "mismatched_brackets",
            "Mismatched parentheses ()",
        ),
        (
            lambda p: p.count("[") != p.count("]"),
            "mismatched_brackets",
            "Mismatched brackets []",
        ),
        (
            lambda p: p.count("{") != p.count("}"),
            "mismatched_brackets",
            "Mismatched braces {}",
        ),
        (
            lambda p: p.count("<") != p.count(">")
            and language in ["javascript", "typescript"],
            "mismatched_brackets",
            "Mismatched angle brackets <>",
        ),
        (
            lambda p: re.search(r"\$\$[^$\w]", p),
            "invalid_variable",
            "Invalid metavariable (should be $ or $$$)",
        ),
        (
            lambda p: "$$" in p and "$$$" not in p,
            "invalid_variable",
            "Invalid metavariable (use $$$ for variadic)",
        ),
        (
            lambda p: re.search(r"\$\s+\w", p),
            "invalid_variable",
            "Space after $ in metavariable",
        ),
        (
            lambda p: re.search(r"\$\w*\d+\w*", p) and language not in ["rust"],
            "invalid_variable",
            "Numbers in metavariable names",
        ),
        (
            lambda p: "`" in p
            and ("${" not in p and language in ["javascript", "typescript"]),
            "template_literal",
            "Template literal without ${} interpolation",
        ),
        (
            lambda p: "${" in p
            and "`" not in p
            and language in ["javascript", "typescript"],
            "template_literal",
            "Template syntax outside backticks",
        ),
    ]

    for check_func, error_type, message in error_checks:
        if check_func(pattern):
            result["has_errors"] = True
            result["errors"].append(
                {
                    "type": error_type,
                    "message": message,
                    "solution": COMMON_SYNTAX_ERRORS.get(
                        error_type, "Check syntax documentation"
                    ),
                }
            )

    # Language-specific checks
    if language in LANGUAGE_SPECIFIC_ERRORS:
        lang_errors = LANGUAGE_SPECIFIC_ERRORS[language]

        # Python-specific checks
        if language == "python":
            if ":" in pattern and not re.search(
                r"(if|for|while|def|class|with|try|except|lambda).*:", pattern
            ):
                result["language_specific"].append(lang_errors["missing_colon"])

            if (
                "\n" in pattern
                and re.search(r"\n\s+\S", pattern)
                and not re.search(r"\n\s{4}\S", pattern)
            ):
                result["language_specific"].append(
                    lang_errors["inconsistent_indentation"]
                )

        # JavaScript/TypeScript specific checks
        elif language in ["javascript", "typescript"]:
            if (
                "<" in pattern
                and ">" in pattern
                and not re.search(r"<\/?[A-Za-z]([^<>]*)(\/?)>", pattern)
            ):
                result["language_specific"].append(lang_errors["jsx_syntax"])

            if "=>" in pattern and not re.search(
                r"(\(.*\)|[a-zA-Z_$][0-9a-zA-Z_$]*)\s*=>\s*(\{.*\}|[^{])", pattern
            ):
                result["language_specific"].append(lang_errors["arrow_function"])

    # Extract all metavariables for analysis
    metavars = re.findall(r"\$(\${0,2}\w+)", pattern)
    if metavars:
        result["metavariables"] = metavars

        # Check for common metavariable issues
        for var in metavars:
            if var.startswith("$") and not var.startswith("$$$"):
                result["has_errors"] = True
                result["errors"].append(
                    {
                        "type": "invalid_variable",
                        "message": f"Invalid metavariable syntax: ${var} ($$$ for variadic)",
                        "solution": "Use $ for single capture, $$$ for multiple captures",
                    }
                )

    return result


def get_pattern_help(
    language: str, error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get help for pattern writing based on language and optional error message.

    Args:
        language: The programming language
        error_message: Optional error message

    Returns:
        Dictionary with pattern help information
    """
    help_info = {
        "language": language,
        "syntax_examples": [],
        "common_patterns": [],
        "common_errors": [],
    }

    # Add basic syntax information for all languages
    help_info["basic_syntax"] = {
        "$VAR": "Match a single node, capturing it as VAR",
        "$$$VARS": "Match multiple nodes, capturing them as VARS",
        "$_": "Match any single node without capturing",
        "$$$_": "Match any sequence of nodes without capturing",
    }

    # Add language-specific examples
    handler = get_handler(language)
    if handler:
        patterns = handler.get_default_patterns()
        # Get a few representative patterns - avoid unnecessary list conversion
        if patterns:
            # Only convert to list if we need to slice it
            if len(patterns) > 5:
                # Convert to list only when necessary for slicing
                examples = list(patterns.items())[:5]
            else:
                # Use items directly when no slicing needed
                examples = patterns.items()
            help_info["syntax_examples"] = examples

    # Add common errors and solutions
    if language in LANGUAGE_SPECIFIC_ERRORS:
        help_info["common_errors"] = [
            {"error": error, "details": details}
            for error, details in LANGUAGE_SPECIFIC_ERRORS[language].items()
        ]

    # Add specific help for the error message if provided
    if error_message and is_pattern_syntax_error(error_message):
        error_analysis = analyze_pattern_error(
            "", language
        )  # Analyze empty pattern as fallback
        help_info["error_analysis"] = error_analysis

    return help_info


def enrich_error_message(error_message: str, language: str, pattern: str) -> str:
    """
    Enhance an error message with helpful information about pattern syntax.

    Args:
        error_message: The original error message
        language: The programming language
        pattern: The pattern causing the error

    Returns:
        Enhanced error message with syntax help
    """
    if not is_pattern_syntax_error(error_message):
        return error_message

    # Get basic pattern help
    help_info = get_pattern_help(language)

    # Analyze the pattern for specific errors
    analysis = analyze_pattern_error(pattern, language)

    # Build the enhanced error message
    enhanced_msg = f"{error_message}\n\nPattern syntax error detected. Here are some valid common pattern examples:\n"

    # Add examples from the language handler
    if help_info["syntax_examples"]:
        for name, example in help_info["syntax_examples"][:3]:  # Just show the first 3
            enhanced_msg += f"  {name}: {example}\n"

    # Add basic syntax explanation
    enhanced_msg += "\nPatterns use $ to define capture variables/placeholders:\n"
    enhanced_msg += "  $NAME - captures a single node\n"
    enhanced_msg += "  $$$NAME - captures multiple nodes (variadic)\n"

    # Add language-specific suggestions if available
    if analysis["language_specific"]:
        enhanced_msg += "\nCommon issues in this language:\n"
        for error in analysis["language_specific"][:2]:  # Show just the first 2
            enhanced_msg += f"  - {error['message']}: {error['solution']}\n"
            if "example" in error:
                enhanced_msg += f"    Example: {error['example']}\n"

    # Point to documentation
    enhanced_msg += "\nFor more details, see the ast-grep pattern documentation."

    return enhanced_msg


def generate_alternative_patterns(pattern: str, language: str) -> list[str]:
    """
    Generate alternative patterns that might match when the original doesn't.
    
    For example, if the pattern is "async fn new", also try:
    - "pub async fn new" (with visibility modifier)
    - "async fn $NAME" (with metavariable)
    
    Args:
        pattern: The original pattern
        language: The programming language
        
    Returns:
        List of alternative patterns to try
    """
    alternatives = []
    
    if language == "rust":
        # Handle async function patterns
        if "async fn " in pattern:
            # Check if it already has visibility modifier
            has_visibility = any(pattern.startswith(vis + " ") for vis in ["pub", "pub(crate)", "pub(super)"])
            
            if pattern.startswith("async fn "):
                # No visibility modifier, add alternatives with visibility
                alternatives.append(f"pub {pattern}")
                alternatives.append(f"pub(crate) {pattern}")
            
            # If it has a specific name, try with metavariable
            parts = pattern.split()
            # Find the position of 'fn' to get the function name
            fn_index = parts.index("fn") if "fn" in parts else -1
            if fn_index >= 0 and fn_index + 1 < len(parts) and not parts[fn_index + 1].startswith("$"):
                # Replace specific name with metavariable
                new_parts = parts[:fn_index + 1] + ["$NAME"] + parts[fn_index + 2:]
                metavar_pattern = " ".join(new_parts)
                alternatives.append(metavar_pattern)
        
        # Handle regular function patterns
        elif pattern.startswith("fn ") and "async" not in pattern:
            # Also look for async versions
            alternatives.append(f"async {pattern}")
            if not any(pattern.startswith(vis + " ") for vis in ["pub", "pub(crate)", "pub(super)"]):
                alternatives.append(f"pub {pattern}")
                alternatives.append(f"pub async {pattern}")
    
    elif language in ["javascript", "typescript"]:
        # Handle function patterns
        if pattern.startswith("function "):
            # Also try arrow functions
            parts = pattern.split()
            if len(parts) >= 2 and not parts[1].startswith("$"):
                name = parts[1]
                alternatives.append(f"const {name} = ($$$PARAMS) => $$$BODY")
                alternatives.append(f"const {name} = async ($$$PARAMS) => $$$BODY")
        
        # Handle async patterns
        if pattern.startswith("async function "):
            parts = pattern.split()
            if len(parts) >= 3 and not parts[2].startswith("$"):
                name = parts[2]
                alternatives.append(f"const {name} = async ($$$PARAMS) => $$$BODY")
    
    return alternatives
