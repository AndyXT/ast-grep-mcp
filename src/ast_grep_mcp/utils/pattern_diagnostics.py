"""
Enhanced pattern diagnostics and error recovery for ast-grep patterns.

This module provides advanced error analysis, recovery suggestions, and
automatic pattern correction capabilities.
"""

import re
import difflib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("ast_grep_mcp.pattern_diagnostics")


class ErrorSeverity(Enum):
    """Severity levels for pattern errors."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PatternError:
    """Represents a specific error in a pattern."""

    type: str
    message: str
    severity: ErrorSeverity
    position: Optional[int] = None
    length: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class PatternDiagnostic:
    """Complete diagnostic information for a pattern."""

    pattern: str
    language: str
    errors: List[PatternError]
    suggestions: List[str]
    corrected_pattern: Optional[str] = None
    confidence_score: float = 0.0
    is_valid: bool = False


class PatternAnalyzer:
    """Advanced pattern analyzer with error recovery capabilities."""

    def __init__(self):
        self.common_patterns = self._load_common_patterns()
        self.error_patterns = self._compile_error_patterns()

    def _load_common_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load common valid patterns for each language."""
        return {
            "python": {
                "function_def": "def $NAME($$$PARAMS):",
                "class_def": "class $NAME:",
                "if_statement": "if $COND:",
                "for_loop": "for $VAR in $ITER:",
                "while_loop": "while $COND:",
                "try_except": "try:\n    $$$BODY\nexcept $EXCEPTION:",
                "list_comp": "[$EXPR for $VAR in $ITER]",
                "dict_comp": "{$KEY: $VALUE for $ITEM in $ITER}",
                "lambda": "lambda $$$PARAMS: $EXPR",
                "import": "import $MODULE",
                "from_import": "from $MODULE import $NAME",
                "assignment": "$VAR = $VALUE",
                "method_call": "$OBJ.$METHOD($$$ARGS)",
                "decorator": "@$DECORATOR",
                "with_statement": "with $EXPR as $VAR:",
            },
            "javascript": {
                "function": "function $NAME($$$PARAMS) { $$$BODY }",
                "arrow_func": "($$$PARAMS) => $EXPR",
                "arrow_func_block": "($$$PARAMS) => { $$$BODY }",
                "class": "class $NAME { $$$BODY }",
                "if_statement": "if ($COND) { $$$BODY }",
                "for_loop": "for ($INIT; $COND; $UPDATE) { $$$BODY }",
                "for_of": "for (const $VAR of $ITER) { $$$BODY }",
                "for_in": "for (const $VAR in $OBJ) { $$$BODY }",
                "while_loop": "while ($COND) { $$$BODY }",
                "const_decl": "const $NAME = $VALUE",
                "let_decl": "let $NAME = $VALUE",
                "var_decl": "var $NAME = $VALUE",
                "import": "import $NAME from '$MODULE'",
                "export": "export $DECL",
                "jsx_element": "<$TAG $$$PROPS>$$$CHILDREN</$TAG>",
                "jsx_self_closing": "<$TAG $$$PROPS />",
                "template_literal": "`$$$TEXT`",
                "object_method": "$NAME($$$PARAMS) { $$$BODY }",
                "async_function": "async function $NAME($$$PARAMS) { $$$BODY }",
                "await_expr": "await $EXPR",
            },
            "typescript": {
                "typed_function": "function $NAME($$$PARAMS): $RETURN_TYPE { $$$BODY }",
                "typed_arrow": "($$$PARAMS): $RETURN_TYPE => $EXPR",
                "interface": "interface $NAME { $$$PROPS }",
                "type_alias": "type $NAME = $TYPE",
                "generic_function": "function $NAME<$TYPE>($$$PARAMS): $RETURN { $$$BODY }",
                "enum": "enum $NAME { $$$VALUES }",
                "namespace": "namespace $NAME { $$$BODY }",
                "type_guard": "$VAR is $TYPE",
                "as_expr": "$EXPR as $TYPE",
                "readonly": "readonly $PROP: $TYPE",
            },
            "rust": {
                "function": "fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }",
                "struct": "struct $NAME { $$$FIELDS }",
                "enum": "enum $NAME { $$$VARIANTS }",
                "impl": "impl $TYPE { $$$METHODS }",
                "trait": "trait $NAME { $$$METHODS }",
                "match": "match $EXPR { $$$ARMS }",
                "if_let": "if let $PATTERN = $EXPR { $$$BODY }",
                "while_let": "while let $PATTERN = $EXPR { $$$BODY }",
                "lifetime": "&'$LIFETIME $TYPE",
                "generic": "$NAME<$TYPE>",
                "macro_call": "$MACRO!($$$ARGS)",
                "use": "use $PATH",
                "mod": "mod $NAME { $$$BODY }",
            },
            "go": {
                "function": "func $NAME($$$PARAMS) $RETURN { $$$BODY }",
                "method": "func ($RECEIVER $TYPE) $NAME($$$PARAMS) $RETURN { $$$BODY }",
                "struct": "type $NAME struct { $$$FIELDS }",
                "interface": "type $NAME interface { $$$METHODS }",
                "if": "if $COND { $$$BODY }",
                "for": "for $COND { $$$BODY }",
                "for_range": "for $KEY, $VALUE := range $ITER { $$$BODY }",
                "switch": "switch $EXPR { $$$CASES }",
                "case": "case $VALUE: $$$BODY",
                "select": "select { $$$CASES }",
                "channel_send": "$CHAN <- $VALUE",
                "channel_recv": "$VAR := <-$CHAN",
                "defer": "defer $EXPR",
                "go": "go $FUNC($$$ARGS)",
                "import": "import $PACKAGE",
            },
            "c": {
                "function": "$RETURN $NAME($$$PARAMS) { $$$BODY }",
                "struct": "struct $NAME { $$$FIELDS };",
                "typedef": "typedef $TYPE $NAME;",
                "if": "if ($COND) { $$$BODY }",
                "for": "for ($INIT; $COND; $UPDATE) { $$$BODY }",
                "while": "while ($COND) { $$$BODY }",
                "switch": "switch ($EXPR) { $$$CASES }",
                "case": "case $VALUE: $$$BODY",
                "pointer": "$TYPE *$NAME",
                "array": "$TYPE $NAME[$SIZE]",
                "include": "#include <$HEADER>",
                "define": "#define $NAME $VALUE",
                "ifdef": "#ifdef $NAME",
            },
        }

    def _compile_error_patterns(self) -> List[Tuple[re.Pattern, str, str, bool]]:
        """Compile regex patterns for common errors."""
        return [
            # Missing dollar signs for metavariables - be very conservative
            # Only flag if it's a standalone uppercase word that looks like a placeholder
            # and is not part of actual code syntax
            (
                re.compile(r"(?<![a-zA-Z])(FUNC|NAME|TYPE|VAR|ARG|PARAM|BODY|EXPR|VALUE|MSG)(?![a-zA-Z_0-9:(){}=])"),
                "missing_dollar",
                "Consider adding $ prefix if this is a metavariable",
                False,
            ),
            # Double dollar instead of triple
            (
                re.compile(r"\$\$([A-Z_]+)(?!\$)"),
                "invalid_variadic",
                "Use $$$ for variadic capture",
                True,
            ),
            # Space after dollar sign
            (
                re.compile(r"\$\s+(\w+)"),
                "space_after_dollar",
                "Remove space after $",
                True,
            ),
            # Missing closing bracket/brace/paren - more specific pattern
            (
                re.compile(r"(\{[^}]*$|\[[^\]]*$|\([^)]*$)"),
                "unclosed_bracket",
                "Add closing bracket",
                False,
            ),
            # Extra closing bracket/brace/paren
            (
                re.compile(r"^[^{\[(*]*(\}|\]|\))"),
                "extra_closing",
                "Remove extra closing bracket",
                False,
            ),
            # Invalid metavariable names (starting with number)
            (
                re.compile(r"\$(\d+\w*)"),
                "invalid_var_name",
                "Metavariable cannot start with number",
                False,
            ),
            # Common typos in language constructs
            (re.compile(r"\bfucntion\b"), "typo", "Did you mean 'function'?", True),
            (re.compile(r"\bfuntcion\b"), "typo", "Did you mean 'function'?", True),
            (re.compile(r"\bclss\b"), "typo", "Did you mean 'class'?", True),
            (re.compile(r"\bimprot\b"), "typo", "Did you mean 'import'?", True),
        ]

    def analyze_pattern(
        self, pattern: str, language: str, code: Optional[str] = None
    ) -> PatternDiagnostic:
        """
        Perform comprehensive analysis of a pattern.

        Args:
            pattern: The pattern to analyze
            language: The programming language
            code: Optional code context

        Returns:
            Complete diagnostic information
        """
        errors = []
        suggestions: List[str] = []

        # Check for empty pattern
        if not pattern or pattern.strip() == "":
            errors.append(
                PatternError(
                    type="empty_pattern",
                    message="Pattern cannot be empty",
                    severity=ErrorSeverity.ERROR,
                    suggestion="Provide a valid pattern for the code you want to match",
                )
            )
            return PatternDiagnostic(
                pattern=pattern,
                language=language,
                errors=errors,
                suggestions=suggestions,
                is_valid=False,
            )

        # Check bracket balance
        bracket_errors = self._check_bracket_balance(pattern)
        errors.extend(bracket_errors)

        # Check metavariable syntax
        metavar_errors = self._check_metavariables(pattern)
        errors.extend(metavar_errors)

        # Apply error pattern detection
        pattern_errors = self._detect_pattern_errors(pattern)
        errors.extend(pattern_errors)

        # Language-specific validation
        lang_errors = self._language_specific_validation(pattern, language)
        errors.extend(lang_errors)

        # Generate suggestions based on errors
        suggestions = self._generate_suggestions(pattern, language, errors)

        # Attempt automatic correction
        corrected_pattern = None
        confidence_score = 0.0
        if errors and any(e.auto_fixable for e in errors):
            corrected_pattern, confidence_score = self._auto_correct_pattern(
                pattern, errors
            )

        # Calculate validity - only CRITICAL errors affect validity
        # Most patterns should be considered valid unless there's a critical syntax error
        has_critical_errors = (
            len(
                [
                    e
                    for e in errors
                    if e.severity == ErrorSeverity.CRITICAL
                ]
            )
            > 0
        )
        is_valid = not has_critical_errors and pattern.strip() != ""

        return PatternDiagnostic(
            pattern=pattern,
            language=language,
            errors=errors,
            suggestions=suggestions,
            corrected_pattern=corrected_pattern,
            confidence_score=confidence_score,
            is_valid=is_valid,
        )

    def _check_bracket_balance(self, pattern: str) -> List[PatternError]:
        """Check for balanced brackets, braces, and parentheses."""
        errors = []
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []

        for i, char in enumerate(pattern):
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    errors.append(
                        PatternError(
                            type="extra_closing_bracket",
                            message=f"Extra closing '{char}' at position {i}",
                            severity=ErrorSeverity.CRITICAL,
                            position=i,
                            length=1,
                            suggestion=f"Remove the extra '{char}'",
                            auto_fixable=True,
                        )
                    )
                else:
                    opening, pos = stack.pop()
                    if brackets[opening] != char:
                        errors.append(
                            PatternError(
                                type="mismatched_bracket",
                                message=f"Mismatched brackets: '{opening}' at {pos} and '{char}' at {i}",
                                severity=ErrorSeverity.CRITICAL,
                                position=pos,
                                length=i - pos + 1,
                                suggestion=f"Replace '{char}' with '{brackets[opening]}'",
                                auto_fixable=True,
                            )
                        )

        # Check for unclosed brackets
        for opening, pos in stack:
            errors.append(
                PatternError(
                    type="unclosed_bracket",
                    message=f"Unclosed '{opening}' at position {pos}",
                    severity=ErrorSeverity.CRITICAL,
                    position=pos,
                    length=1,
                    suggestion=f"Add closing '{brackets[opening]}' at the end",
                    auto_fixable=True,
                )
            )

        return errors

    def _check_metavariables(self, pattern: str) -> List[PatternError]:
        """Check metavariable syntax."""
        errors = []

        # Find all potential metavariables
        metavar_pattern = re.compile(r"\$(\${0,2})?(\w*)")

        for match in metavar_pattern.finditer(pattern):
            dollars = match.group(1) or ""
            name = match.group(2)
            pos = match.start()

            # Check for invalid number of dollar signs
            if dollars == "$$":
                errors.append(
                    PatternError(
                        type="invalid_variadic",
                        message=f"Invalid metavariable syntax '$$' at position {pos}",
                        severity=ErrorSeverity.WARNING,
                        position=pos,
                        length=len(match.group(0)),
                        suggestion="Use $$$ for variadic capture or $ for single capture",
                        auto_fixable=True,
                    )
                )

            # Check for empty name (unless it's $_)
            if not name and match.group(0) != "$_":
                errors.append(
                    PatternError(
                        type="empty_metavar_name",
                        message=f"Empty metavariable name at position {pos}",
                        severity=ErrorSeverity.WARNING,
                        position=pos,
                        length=len(match.group(0)),
                        suggestion="Add a name after $ or use $_ for wildcard",
                        auto_fixable=False,
                    )
                )

            # Check for invalid name (starting with number)
            if name and name[0].isdigit():
                errors.append(
                    PatternError(
                        type="invalid_metavar_name",
                        message=f"Metavariable name cannot start with number at position {pos}",
                        severity=ErrorSeverity.WARNING,
                        position=pos,
                        length=len(match.group(0)),
                        suggestion="Use a name starting with letter or underscore",
                        auto_fixable=False,
                    )
                )

        return errors

    def _detect_pattern_errors(self, pattern: str) -> List[PatternError]:
        """Apply regex-based error detection."""
        errors = []

        for regex, error_type, suggestion, auto_fixable in self.error_patterns:
            for match in regex.finditer(pattern):
                errors.append(
                    PatternError(
                        type=error_type,
                        message=f"{suggestion} at position {match.start()}",
                        severity=(
                            ErrorSeverity.WARNING
                            if auto_fixable
                            else ErrorSeverity.ERROR
                        ),
                        position=match.start(),
                        length=len(match.group(0)),
                        suggestion=suggestion,
                        auto_fixable=auto_fixable,
                    )
                )

        return errors

    def _language_specific_validation(
        self, pattern: str, language: str
    ) -> List[PatternError]:
        """Perform language-specific validation."""
        errors = []

        if language == "python":
            # Check for missing colons only in complete statements
            # Don't check partial patterns or patterns with metavariables
            if any(
                keyword in pattern
                for keyword in ["if", "for", "while", "def", "class", "try", "except"]
            ):
                # Only check if pattern looks like a complete statement
                if not re.search(r"(if|for|while|def|class|try|except).*(:|\$)", pattern):
                    # Only warn, don't error - pattern might be partial
                    errors.append(
                        PatternError(
                            type="missing_colon",
                            message="Python compound statement might be missing colon",
                            severity=ErrorSeverity.WARNING,
                            suggestion="Add : after the statement if matching complete statements",
                            auto_fixable=True,
                        )
                    )

        elif language in ["javascript", "typescript"]:
            # Check for arrow function syntax - be more lenient
            if "=>" in pattern and not re.search(
                r"(\(.*\)|[a-zA-Z_$]\w*|\$\w*)\s*=>", pattern
            ):
                errors.append(
                    PatternError(
                        type="invalid_arrow_function",
                        message="Arrow function syntax might be invalid",
                        severity=ErrorSeverity.WARNING,
                        suggestion="Use (params) => expr or param => expr",
                        auto_fixable=False,
                    )
                )

        elif language == "rust":
            # For Rust, be very lenient - ast-grep handles Rust syntax well
            # Just provide helpful hints for common patterns
            pass

        return errors

    def _generate_suggestions(
        self, pattern: str, language: str, errors: List[PatternError]
    ) -> List[str]:
        """Generate helpful suggestions based on the pattern and errors."""
        suggestions: List[str] = []

        # Find similar common patterns
        if language in self.common_patterns:
            lang_patterns = self.common_patterns[language]

            # Use difflib to find similar patterns
            close_matches = difflib.get_close_matches(
                pattern, lang_patterns.values(), n=3, cutoff=0.6
            )

            if close_matches:
                suggestions.append("Did you mean one of these patterns?")
                for match in close_matches:
                    # Find the pattern name
                    for name, pat in lang_patterns.items():
                        if pat == match:
                            suggestions.append(f"  {name}: {match}")
                            break

        # Add specific suggestions based on errors
        error_types = {e.type for e in errors}

        if "missing_dollar" in error_types:
            suggestions.append("Remember to prefix metavariables with $")

        if "invalid_variadic" in error_types:
            suggestions.append("Use $$$ for matching multiple elements (variadic)")

        if any(t in error_types for t in ["unclosed_bracket", "mismatched_bracket"]):
            suggestions.append(
                "Check that all brackets, braces, and parentheses are balanced"
            )

        return suggestions

    def _auto_correct_pattern(
        self, pattern: str, errors: List[PatternError]
    ) -> Tuple[str, float]:
        """Attempt to automatically correct the pattern based on errors."""
        corrected = pattern
        confidence = 1.0

        # Sort errors by position (reverse order to avoid position shifts)
        fixable_errors = [e for e in errors if e.auto_fixable]
        fixable_errors.sort(key=lambda e: e.position or 0, reverse=True)

        for error in fixable_errors:
            if error.type == "invalid_variadic" and error.position is not None:
                # Replace $$ with $$$
                if error.position + 2 <= len(corrected):
                    corrected = (
                        corrected[: error.position]
                        + "$$$"
                        + corrected[error.position + 2 :]
                    )
                    confidence *= 0.9

            elif error.type == "space_after_dollar" and error.position is not None:
                # Remove space after $
                match = re.search(r"\$\s+", corrected[error.position :])
                if match:
                    end_pos = error.position + match.end()
                    corrected = corrected[: error.position + 1] + corrected[end_pos:]
                    confidence *= 0.95

            elif error.type == "unclosed_bracket" and error.position is not None:
                # Add closing bracket at the end
                bracket_map = {"(": ")", "[": "]", "{": "}"}
                if error.position < len(corrected):
                    opening = corrected[error.position]
                    if opening in bracket_map:
                        corrected += bracket_map[opening]
                        confidence *= 0.85

            elif error.type == "missing_colon":
                # Add colon for Python statements
                keywords = ["if", "for", "while", "def", "class", "try", "except"]
                for keyword in keywords:
                    if keyword in corrected and not re.search(
                        f"{keyword}.*:", corrected
                    ):
                        corrected = re.sub(f"({keyword}[^:]+)$", r"\1:", corrected)
                        confidence *= 0.9
                        break

        return corrected, confidence


def create_enhanced_diagnostic(
    pattern: str,
    language: str,
    error_message: Optional[str] = None,
    code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an enhanced diagnostic report for a pattern.

    Args:
        pattern: The pattern to diagnose
        language: The programming language
        error_message: Optional error message from ast-grep
        code: Optional code context

    Returns:
        Comprehensive diagnostic information
    """
    analyzer = PatternAnalyzer()
    diagnostic = analyzer.analyze_pattern(pattern, language, code)

    # Convert to dictionary format
    result = {
        "pattern": diagnostic.pattern,
        "language": diagnostic.language,
        "is_valid": diagnostic.is_valid,
        "errors": [
            {
                "type": e.type,
                "message": e.message,
                "severity": e.severity.value,
                "position": e.position,
                "length": e.length,
                "suggestion": e.suggestion,
                "auto_fixable": e.auto_fixable,
            }
            for e in diagnostic.errors
        ],
        "suggestions": diagnostic.suggestions,
    }

    # Add corrected pattern if available
    if diagnostic.corrected_pattern and diagnostic.confidence_score > 0.7:
        result["corrected_pattern"] = diagnostic.corrected_pattern
        result["correction_confidence"] = diagnostic.confidence_score

    # Add the original error message if provided
    if error_message:
        result["original_error"] = error_message

    # Add a formatted help message with enhanced information
    if not diagnostic.is_valid or error_message:
        help_msg = "❌ Pattern Analysis Results\n" + "=" * 50 + "\n"
        
        # Show what was provided vs what's expected
        help_msg += f"\n📥 Your Pattern: {pattern}\n"
        
        if diagnostic.corrected_pattern:
            help_msg += f"✅ Suggested Fix: {diagnostic.corrected_pattern}\n"
        
        # Add specific error details
        if diagnostic.errors:
            # Only show critical errors in help message
            critical_errors = [e for e in diagnostic.errors if e.severity == ErrorSeverity.CRITICAL]
            if critical_errors:
                help_msg += "\n🔍 Critical Issues Found:\n"
                for i, error in enumerate(critical_errors, 1):
                    help_msg += f"\n{i}. {error.message}"
                    if error.position is not None:
                        # Show the problematic part with context
                        start = max(0, error.position - 10)
                        end = min(len(pattern), error.position + (error.length or 1) + 10)
                        context = pattern[start:end]
                        pointer_pos = error.position - start
                        pointer = " " * pointer_pos + "^" * (error.length or 1)
                        help_msg += f"\n   Pattern: ...{context}...\n   Error:   ...{pointer}...\n"
                    if error.suggestion:
                        help_msg += f"   Fix: {error.suggestion}\n"

        # Add pattern syntax examples
        if diagnostic.suggestions:
            help_msg += "\n💡 Pattern Examples:\n"
            for suggestion in diagnostic.suggestions[:3]:  # Show top 3 suggestions
                help_msg += f"  • {suggestion}\n"
                
        # Add a note about common patterns
        help_msg += f"\n📚 Common {language.title()} Patterns:\n"
        lang_patterns = analyzer.common_patterns.get(language, {})
        # Show relevant patterns based on the input
        shown = 0
        for name, example in lang_patterns.items():
            # Try to match based on keywords in the pattern
            if shown < 3 and any(keyword in pattern.lower() for keyword in name.split("_")):
                help_msg += f"  • {name.replace('_', ' ').title()}: {example}\n"
                shown += 1
        
        # If no relevant patterns found, show the most common ones
        if shown == 0:
            for name, example in list(lang_patterns.items())[:3]:
                help_msg += f"  • {name.replace('_', ' ').title()}: {example}\n"

        result["help_message"] = help_msg

    return result
