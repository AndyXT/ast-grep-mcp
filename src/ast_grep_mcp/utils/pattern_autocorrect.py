"""
Automatic pattern correction and suggestion system for ast-grep patterns.

This module provides intelligent pattern correction suggestions based on
common mistakes and language-specific patterns.
"""

import re
import difflib
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("ast_grep_mcp.pattern_autocorrect")


@dataclass
class PatternSuggestion:
    """Represents a pattern correction suggestion."""

    original: str
    suggested: str
    confidence: float
    reason: str
    applied_fixes: List[str]


class PatternAutoCorrector:
    """Provides automatic pattern correction and suggestions."""

    def __init__(self):
        self.correction_rules = self._load_correction_rules()
        self.pattern_templates = self._load_pattern_templates()

    def _load_correction_rules(self) -> List[Tuple[re.Pattern, str, str]]:
        """Load pattern correction rules."""
        return [
            # Fix double dollar to triple dollar (but not if already triple)
            (
                re.compile(r"(?<!\$)\$\$(\w+)"),
                r"$$$\1",
                "Convert $$ to $$$ for variadic capture",
            ),
            # Remove space after dollar
            (re.compile(r"\$\s+(\w+)"), r"$\1", "Remove space after $"),
            # Add dollar to uppercase identifiers (not already preceded by $)
            (
                re.compile(r"(?<!\$)\b([A-Z][A-Za-z0-9_]*)\b"),
                r"$\1",
                "Add $ to metavariable",
            ),
            # Fix common typos
            (re.compile(r"\bfucntion\b"), "function", "Fix typo: fucntion → function"),
            (re.compile(r"\bfuntcion\b"), "function", "Fix typo: funtcion → function"),
            (re.compile(r"\bclss\b"), "class", "Fix typo: clss → class"),
            (re.compile(r"\bimprot\b"), "import", "Fix typo: improt → import"),
            (re.compile(r"\bdefien\b"), "define", "Fix typo: defien → define"),
            (re.compile(r"\bretrun\b"), "return", "Fix typo: retrun → return"),
            # Fix missing spaces
            (
                re.compile(r"(\w)(if|for|while|def|class)(\s|$)"),
                r"\1 \2\3",
                "Add space before keyword",
            ),
            # Fix template literal syntax
            (
                re.compile(r"'([^']*)\$\{([^}]+)\}([^']*)'"),
                r"`\1${\2}\3`",
                "Use backticks for template literals",
            ),
            (
                re.compile(r'"([^"]*)\$\{([^}]+)\}([^"]*)"'),
                r"`\1${\2}\3`",
                "Use backticks for template literals",
            ),
        ]

    def _load_pattern_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load common pattern templates by language."""
        return {
            "python": {
                "function": [
                    "def $NAME($$$PARAMS):",
                    "def $NAME($$$PARAMS) -> $RETURN:",
                    "async def $NAME($$$PARAMS):",
                    "def $NAME(self, $$$PARAMS):",
                ],
                "class": [
                    "class $NAME:", 
                    "class $NAME($BASE):",
                    "class $NAME($$$BASES):",
                ],
                "if": [
                    "if $COND:", 
                    "if $COND:\n    $$$BODY",
                    "if $COND:\n    $$$BODY\nelse:\n    $$$ELSE",
                ],
                "for": [
                    "for $VAR in $ITER:", 
                    "for $IDX, $VAR in enumerate($ITER):",
                    "for $KEY, $VALUE in $DICT.items():",
                ],
                "while": ["while $COND:", "while $COND:\n    $$$BODY"],
                "with": [
                    "with $EXPR as $VAR:", 
                    "with $EXPR:\n    $$$BODY",
                    "with $EXPR as $VAR, $EXPR2 as $VAR2:",
                ],
                "try": [
                    "try:\n    $$$BODY\nexcept $EXCEPTION:",
                    "try:\n    $$$BODY\nexcept $EXCEPTION as $VAR:",
                    "try:\n    $$$BODY\nfinally:",
                    "try:\n    $$$BODY\nexcept:\n    $$$EXCEPT\nfinally:\n    $$$FINALLY",
                ],
                "import": [
                    "import $MODULE", 
                    "from $MODULE import $NAME",
                    "from $MODULE import $NAME as $ALIAS",
                    "from $PACKAGE.$MODULE import $NAME",
                ],
                "comprehension": [
                    "[$EXPR for $VAR in $ITER]",
                    "[$EXPR for $VAR in $ITER if $COND]",
                    "{$KEY: $VALUE for $ITEM in $ITER}",
                    "{$EXPR for $VAR in $ITER}",
                ],
                "decorator": [
                    "@$DECORATOR",
                    "@$DECORATOR($$$ARGS)",
                    "@$MODULE.$DECORATOR",
                ],
                "lambda": [
                    "lambda $VAR: $EXPR",
                    "lambda $$$PARAMS: $EXPR",
                ],
            },
            "javascript": {
                "function": [
                    "function $NAME($$$PARAMS) { $$$BODY }",
                    "function $NAME($$$PARAMS) {}",
                    "async function $NAME($$$PARAMS) { $$$BODY }",
                    "function* $NAME($$$PARAMS) { $$$BODY }",
                ],
                "arrow": [
                    "($$$PARAMS) => $EXPR", 
                    "($$$PARAMS) => { $$$BODY }",
                    "$PARAM => $EXPR",
                    "async ($$$PARAMS) => { $$$BODY }",
                ],
                "class": [
                    "class $NAME { $$$BODY }",
                    "class $NAME extends $BASE { $$$BODY }",
                    "class $NAME { constructor($$$PARAMS) { $$$BODY } }",
                ],
                "if": [
                    "if ($COND) { $$$BODY }", 
                    "if ($COND) $STMT",
                    "if ($COND) { $$$BODY } else { $$$ELSE }",
                    "if ($COND) { $$$BODY } else if ($COND2) { $$$BODY2 }",
                ],
                "for": [
                    "for ($INIT; $COND; $UPDATE) { $$$BODY }",
                    "for (const $VAR of $ITER) { $$$BODY }",
                    "for (const $VAR in $OBJ) { $$$BODY }",
                    "for (let $VAR = 0; $VAR < $LIMIT; $VAR++) { $$$BODY }",
                ],
                "while": [
                    "while ($COND) { $$$BODY }", 
                    "do { $$$BODY } while ($COND)",
                ],
                "const": [
                    "const $NAME = $VALUE", 
                    "const { $$$PROPS } = $OBJ",
                    "const [$$$ITEMS] = $ARR",
                    "const { $PROP: $ALIAS } = $OBJ",
                ],
                "let": [
                    "let $NAME = $VALUE", 
                    "let $NAME",
                    "let { $$$PROPS } = $OBJ",
                ],
                "import": [
                    "import $NAME from '$MODULE'",
                    "import { $$$NAMES } from '$MODULE'",
                    "import * as $NAME from '$MODULE'",
                    "import { $NAME as $ALIAS } from '$MODULE'",
                    "import $DEFAULT, { $$$NAMES } from '$MODULE'",
                ],
                "export": [
                    "export default $EXPR",
                    "export { $$$NAMES }",
                    "export const $NAME = $VALUE",
                    "export function $NAME($$$PARAMS) { $$$BODY }",
                ],
                "jsx": [
                    "<$TAG $$$PROPS>$$$CHILDREN</$TAG>", 
                    "<$TAG $$$PROPS />",
                    "<$TAG {...$PROPS}>$$$CHILDREN</$TAG>",
                    "<$TAG $PROP={$VALUE}>$$$CHILDREN</$TAG>",
                ],
                "promise": [
                    "$PROMISE.then($CALLBACK)",
                    "$PROMISE.then($SUCCESS).catch($ERROR)",
                    "await $PROMISE",
                ],
                "template": [
                    "`$$$TEXT`",
                    "`${$EXPR}`",
                    "`$TEXT ${$EXPR} $MORE_TEXT`",
                ],
            },
            "typescript": {
                "function": [
                    "function $NAME($$$PARAMS): $RETURN { $$$BODY }",
                    "function $NAME<$T>($$$PARAMS): $RETURN { $$$BODY }",
                ],
                "arrow": [
                    "($$$PARAMS): $RETURN => $EXPR",
                    "($$$PARAMS): $RETURN => { $$$BODY }",
                ],
                "interface": [
                    "interface $NAME { $$$PROPS }",
                    "interface $NAME extends $BASE { $$$PROPS }",
                ],
                "type": ["type $NAME = $TYPE", "type $NAME<$T> = $TYPE"],
                "class": [
                    "class $NAME { $$$BODY }",
                    "class $NAME<$T> implements $INTERFACE { $$$BODY }",
                ],
                "enum": ["enum $NAME { $$$VALUES }", "const enum $NAME { $$$VALUES }"],
            },
            "rust": {
                "function": [
                    "fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }",
                    "fn $NAME($$$PARAMS) { $$$BODY }",
                    "fn $NAME() { $$$BODY }",
                    "async fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }",
                    "pub fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }",
                    "pub async fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }",
                    "fn $NAME",  # Simple pattern that often works better
                    "async fn $NAME",  # Simple async pattern
                ],
                "struct": [
                    "struct $NAME { $$$FIELDS }", 
                    "struct $NAME($$$FIELDS);",
                    "struct $NAME;",
                    "pub struct $NAME { $$$FIELDS }",
                    "#[derive($$$DERIVES)]\nstruct $NAME { $$$FIELDS }",
                ],
                "enum": [
                    "enum $NAME { $$$VARIANTS }",
                    "enum $NAME<$T> { $$$VARIANTS }",
                    "pub enum $NAME { $$$VARIANTS }",
                    "#[derive($$$DERIVES)]\nenum $NAME { $$$VARIANTS }",
                ],
                "impl": [
                    "impl $TYPE { $$$METHODS }",
                    "impl<$T> $TYPE<$T> { $$$METHODS }",
                    "impl $TRAIT for $TYPE { $$$METHODS }",
                    "impl<$T> $TRAIT for $TYPE<$T> { $$$METHODS }",
                    "impl $TYPE",  # Simple pattern
                ],
                "trait": [
                    "trait $NAME { $$$METHODS }",
                    "trait $NAME<$T> { $$$METHODS }",
                    "pub trait $NAME { $$$METHODS }",
                    "trait $NAME: $BOUND { $$$METHODS }",
                ],
                "match": [
                    "match $EXPR { $$$ARMS }",
                    "match $EXPR { $PATTERN => $EXPR, _ => $DEFAULT }",
                    "match $EXPR { Some($VAR) => $EXPR, None => $DEFAULT }",
                    "match $EXPR { Ok($VAR) => $EXPR, Err($ERR) => $HANDLER }",
                ],
                "if_let": [
                    "if let $PATTERN = $EXPR { $$$BODY }",
                    "if let Some($VAR) = $EXPR { $$$BODY }",
                    "if let Ok($VAR) = $EXPR { $$$BODY }",
                    "if let $PATTERN = $EXPR { $$$BODY } else { $$$ELSE }",
                ],
                "use": [
                    "use $PATH;",
                    "use $PATH::$ITEM;",
                    "use $PATH::{$$$ITEMS};",
                    "use $PATH as $ALIAS;",
                    "use $PATH::*;",
                ],
                "let": [
                    "let $VAR = $EXPR;",
                    "let mut $VAR = $EXPR;",
                    "let $VAR: $TYPE = $EXPR;",
                    "let $PATTERN = $EXPR;",
                ],
                "loop": [
                    "loop { $$$BODY }",
                    "while $COND { $$$BODY }",
                    "while let $PATTERN = $EXPR { $$$BODY }",
                    "for $VAR in $ITER { $$$BODY }",
                ],
                "macro": [
                    "$MACRO!($$$ARGS)",
                    "$MACRO![$$$ARGS]",
                    "$MACRO!{$$$ARGS}",
                    "println!($$$ARGS)",
                    "vec![$$$ITEMS]",
                ],
            },
            "go": {
                "function": [
                    "func $NAME($$$PARAMS) $RETURN { $$$BODY }",
                    "func $NAME($$$PARAMS) { $$$BODY }",
                    "func $NAME() { $$$BODY }",
                    "func $NAME() {}",
                ],
                "method": [
                    "func ($RECV $TYPE) $NAME($$$PARAMS) $RETURN { $$$BODY }",
                    "func ($RECV *$TYPE) $NAME($$$PARAMS) { $$$BODY }",
                ],
                "struct": ["type $NAME struct { $$$FIELDS }", "type $NAME struct {}"],
                "interface": [
                    "type $NAME interface { $$$METHODS }",
                    "type $NAME interface {}",
                ],
                "if": ["if $COND { $$$BODY }", "if $VAR := $EXPR; $COND { $$$BODY }"],
                "for": [
                    "for $COND { $$$BODY }",
                    "for $KEY, $VALUE := range $ITER { $$$BODY }",
                ],
                "switch": ["switch $EXPR { $$$CASES }", "switch { $$$CASES }"],
            },
            "c": {
                "function": [
                    "$RETURN $NAME($$$PARAMS) { $$$BODY }",
                    "static $RETURN $NAME($$$PARAMS) { $$$BODY }",
                ],
                "struct": [
                    "struct $NAME { $$$FIELDS };",
                    "typedef struct { $$$FIELDS } $NAME;",
                ],
                "if": ["if ($COND) { $$$BODY }", "if ($COND) $STMT;"],
                "for": [
                    "for ($INIT; $COND; $UPDATE) { $$$BODY }",
                    "for (;;) { $$$BODY }",
                ],
                "while": ["while ($COND) { $$$BODY }", "do { $$$BODY } while ($COND);"],
                "switch": [
                    "switch ($EXPR) { $$$CASES }",
                    "switch ($EXPR) { case $VAL: $$$BODY }",
                ],
            },
        }

    def suggest_corrections(
        self, pattern: str, language: str
    ) -> List[PatternSuggestion]:
        """
        Generate correction suggestions for a pattern.

        Args:
            pattern: The pattern to correct
            language: The programming language

        Returns:
            List of correction suggestions
        """
        suggestions: List[PatternSuggestion] = []

        # Apply rule-based corrections
        rule_suggestions = self._apply_correction_rules(pattern)
        suggestions.extend(rule_suggestions)

        # Find similar templates
        template_suggestions = self._find_similar_templates(pattern, language)
        suggestions.extend(template_suggestions)

        # Apply language-specific corrections
        lang_suggestions = self._apply_language_specific_corrections(pattern, language)
        suggestions.extend(lang_suggestions)

        # Sort by confidence and remove duplicates
        seen = set()
        unique_suggestions = []
        for suggestion in sorted(suggestions, key=lambda s: s.confidence, reverse=True):
            if suggestion.suggested not in seen:
                seen.add(suggestion.suggested)
                unique_suggestions.append(suggestion)

        return unique_suggestions[:5]  # Return top 5 suggestions

    def _apply_correction_rules(self, pattern: str) -> List[PatternSuggestion]:
        """Apply regex-based correction rules."""
        suggestions: List[PatternSuggestion] = []
        current_pattern = pattern
        applied_fixes = []
        total_confidence = 1.0

        for regex, replacement, reason in self.correction_rules:
            if regex.search(current_pattern):
                new_pattern = regex.sub(replacement, current_pattern)
                if new_pattern != current_pattern:
                    applied_fixes.append(reason)
                    current_pattern = new_pattern
                    total_confidence *= 0.9

        if current_pattern != pattern and applied_fixes:
            suggestions.append(
                PatternSuggestion(
                    original=pattern,
                    suggested=current_pattern,
                    confidence=total_confidence,
                    reason="Applied automatic fixes",
                    applied_fixes=applied_fixes,
                )
            )

        return suggestions

    def _find_similar_templates(
        self, pattern: str, language: str
    ) -> List[PatternSuggestion]:
        """Find similar pattern templates."""
        suggestions: List[PatternSuggestion] = []

        if language not in self.pattern_templates:
            return suggestions

        templates = self.pattern_templates[language]

        # Flatten all templates
        all_templates = []
        for category, patterns in templates.items():
            for template in patterns:
                all_templates.append((category, template))

        # Find similar patterns using difflib
        pattern_lower = pattern.lower()
        for category, template in all_templates:
            # Calculate similarity
            similarity = difflib.SequenceMatcher(
                None, pattern_lower, template.lower()
            ).ratio()

            # Also check if pattern contains keywords from the category
            category_match = any(
                keyword in pattern_lower for keyword in category.split("_")
            )

            if similarity > 0.6 or (category_match and similarity > 0.4):
                suggestions.append(
                    PatternSuggestion(
                        original=pattern,
                        suggested=template,
                        confidence=similarity,
                        reason=f"Similar to {category} pattern",
                        applied_fixes=[f"Matched {category} template"],
                    )
                )

        return suggestions

    def _apply_language_specific_corrections(
        self, pattern: str, language: str
    ) -> List[PatternSuggestion]:
        """Apply language-specific corrections."""
        suggestions: List[PatternSuggestion] = []

        if language == "python":
            # Check for missing colons
            if any(
                kw in pattern
                for kw in [
                    "if",
                    "for",
                    "while",
                    "def",
                    "class",
                    "try",
                    "except",
                    "with",
                ]
            ):
                if not pattern.rstrip().endswith(":"):
                    suggestions.append(
                        PatternSuggestion(
                            original=pattern,
                            suggested=pattern.rstrip() + ":",
                            confidence=0.9,
                            reason="Python statements need colons",
                            applied_fixes=["Added missing colon"],
                        )
                    )

            # Check for incorrect indentation markers
            if "\\t" in pattern:
                suggestions.append(
                    PatternSuggestion(
                        original=pattern,
                        suggested=pattern.replace("\\t", "    "),
                        confidence=0.8,
                        reason="Python prefers spaces over tabs",
                        applied_fixes=["Replaced tabs with spaces"],
                    )
                )

        elif language in ["javascript", "typescript"]:
            # Fix arrow function syntax
            if "=>" in pattern and not re.search(
                r"(\(.*\)|[a-zA-Z_$]\w*)\s*=>", pattern
            ):
                # Try to fix it
                fixed = re.sub(r"(\s*)=>", r"() =>", pattern)
                suggestions.append(
                    PatternSuggestion(
                        original=pattern,
                        suggested=fixed,
                        confidence=0.7,
                        reason="Arrow functions need parameters",
                        applied_fixes=["Added empty parameter list"],
                    )
                )

            # Fix template literal syntax
            if "${" in pattern and not (pattern.count("`") >= 2):
                # Find the string containing ${} and convert to template literal
                fixed = re.sub(
                    r'(["\'])([^"\']*\$\{[^}]+\}[^"\']*)(["\'])', r"`\2`", pattern
                )
                if fixed != pattern:
                    suggestions.append(
                        PatternSuggestion(
                            original=pattern,
                            suggested=fixed,
                            confidence=0.85,
                            reason="Template literals need backticks",
                            applied_fixes=["Converted to template literal"],
                        )
                    )

        elif language == "rust":
            # Fix missing semicolons
            if pattern.strip() and not pattern.rstrip().endswith((";", "}", ")")):
                if any(kw in pattern for kw in ["let", "use", "type", "const"]):
                    suggestions.append(
                        PatternSuggestion(
                            original=pattern,
                            suggested=pattern.rstrip() + ";",
                            confidence=0.8,
                            reason="Rust statements need semicolons",
                            applied_fixes=["Added missing semicolon"],
                        )
                    )

        return suggestions

    def auto_correct_pattern(self, pattern: str, language: str) -> Optional[str]:
        """
        Attempt to automatically correct a pattern.

        Args:
            pattern: The pattern to correct
            language: The programming language

        Returns:
            The corrected pattern if confident, None otherwise
        """
        suggestions = self.suggest_corrections(pattern, language)

        if suggestions and suggestions[0].confidence > 0.8:
            return suggestions[0].suggested

        return None

    def get_quick_fixes(
        self, pattern: str, language: str, error_type: str
    ) -> List[str]:
        """
        Get quick fixes for specific error types.

        Args:
            pattern: The pattern with errors
            language: The programming language
            error_type: The type of error detected

        Returns:
            List of quick fix suggestions
        """
        fixes = []

        if error_type == "unclosed_bracket":
            # Add closing brackets
            bracket_map = {"(": ")", "[": "]", "{": "}"}
            for opening, closing in bracket_map.items():
                if pattern.count(opening) > pattern.count(closing):
                    fixes.append(pattern + closing)

        elif error_type == "missing_dollar":
            # Add dollar signs to uppercase identifiers (not already preceded by $)
            fixed = re.sub(r"(?<!\$)\b([A-Z][A-Za-z0-9_]*)\b", r"$\1", pattern)
            if fixed != pattern:
                fixes.append(fixed)

        elif error_type == "invalid_variadic":
            # Convert $$ to $$$
            fixed = re.sub(r"\$\$(\w+)(?!\$)", r"$$$\1", pattern)
            if fixed != pattern:
                fixes.append(fixed)

        elif error_type == "missing_colon" and language == "python":
            # Add colon at the end
            if not pattern.rstrip().endswith(":"):
                fixes.append(pattern.rstrip() + ":")

        return fixes


def create_pattern_suggestion_message(suggestions: List[PatternSuggestion]) -> str:
    """
    Create a formatted message from pattern suggestions.

    Args:
        suggestions: List of pattern suggestions

    Returns:
        Formatted suggestion message
    """
    if not suggestions:
        return "No suggestions available."

    message = "Pattern correction suggestions:\n\n"

    for i, suggestion in enumerate(suggestions[:3], 1):
        message += f"{i}. {suggestion.suggested}\n"
        message += f"   Confidence: {suggestion.confidence:.0%}\n"
        message += f"   Reason: {suggestion.reason}\n"
        if suggestion.applied_fixes:
            message += f"   Fixes: {', '.join(suggestion.applied_fixes)}\n"
        message += "\n"

    return message.strip()
