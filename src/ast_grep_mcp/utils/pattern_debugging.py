"""
Pattern debugging tools to help users understand why patterns fail.
"""
from typing import Dict, Any, List
import re
from dataclasses import dataclass

from ..utils.error_handling import handle_errors


@dataclass
class PartialMatch:
    """Represents a partial match during pattern debugging."""
    location: Dict[str, int]
    matched_text: str
    expected_pattern: str
    failure_reason: str
    confidence: float  # 0.0 to 1.0


@dataclass
class PatternDiagnostic:
    """Diagnostic information about a pattern."""
    pattern: str
    language: str
    is_valid: bool
    complexity_score: int  # 1-10
    expected_matches: List[str]
    common_failures: List[str]
    suggestions: List[str]


class PatternDebugger:
    """Advanced pattern debugging and analysis tool."""
    
    def __init__(self, analyzer=None, logger=None):
        self.analyzer = analyzer
        self.logger = logger
        
        # Common pattern issues by language
        self.common_issues = {
            "rust": {
                "metavar_confusion": {
                    "description": "Confusion between $ and $$$ metavariables",
                    "examples": {
                        "wrong": "async fn $$NAME",
                        "right": "async fn $NAME",
                        "explanation": "Use $ for single tokens, $$$ for multiple tokens"
                    }
                },
                "visibility_modifiers": {
                    "description": "Missing or incorrect visibility modifiers",
                    "examples": {
                        "wrong": "fn $NAME",
                        "right": "pub fn $NAME",
                        "explanation": "Add 'pub' for public functions, omit for private"
                    }
                },
                "generic_parameters": {
                    "description": "Generic parameters not captured",
                    "examples": {
                        "wrong": "fn $NAME($$$ARGS) -> $RET",
                        "right": "fn $NAME<$$$GENERICS>($$$ARGS) -> $RET",
                        "explanation": "Include <$$$GENERICS> to match generic functions"
                    }
                },
                "async_return_types": {
                    "description": "Async function return types",
                    "examples": {
                        "wrong": "async fn $NAME($$$ARGS) -> $RET",
                        "right": "async fn $NAME($$$ARGS) -> Result<$OK, $ERR>",
                        "explanation": "Async functions often return specific types like Result"
                    }
                }
            },
            "python": {
                "indentation_sensitive": {
                    "description": "Python is indentation-sensitive",
                    "examples": {
                        "wrong": "def $NAME($$$ARGS):\n$BODY",
                        "right": "def $NAME($$$ARGS):\n    $$$BODY",
                        "explanation": "Include proper indentation in multi-line patterns"
                    }
                },
                "decorators": {
                    "description": "Missing decorator patterns",
                    "examples": {
                        "wrong": "def $NAME($$$ARGS)",
                        "right": "@$DECORATOR\ndef $NAME($$$ARGS)",
                        "explanation": "Include decorators if targeting decorated functions"
                    }
                }
            },
            "javascript": {
                "function_variants": {
                    "description": "Multiple function syntax variants",
                    "examples": {
                        "alternatives": [
                            "function $NAME($$$ARGS) { $$$BODY }",
                            "const $NAME = ($$$ARGS) => $$$BODY",
                            "const $NAME = function($$$ARGS) { $$$BODY }"
                        ],
                        "explanation": "JavaScript has multiple function syntaxes"
                    }
                },
                "async_variants": {
                    "description": "Async function variants",
                    "examples": {
                        "alternatives": [
                            "async function $NAME($$$ARGS) { $$$BODY }",
                            "const $NAME = async ($$$ARGS) => $$$BODY"
                        ],
                        "explanation": "Async functions have different syntaxes"
                    }
                }
            }
        }
        
        # Pattern complexity scoring
        self.complexity_factors = {
            "metavariables": 1,      # Each metavariable adds complexity
            "nested_structures": 3,   # Nested {} or () structures
            "multiple_lines": 2,      # Multi-line patterns
            "special_characters": 1,  # $, {, }, etc.
            "language_keywords": 1,   # Language-specific keywords
        }
    
    @handle_errors
    def debug_pattern_matching(
        self,
        code: str,
        pattern: str,
        language: str,
        max_partial_matches: int = 5
    ) -> Dict[str, Any]:
        """
        Debug why a pattern doesn't match and provide suggestions.
        
        Args:
            code: Source code to match against
            pattern: AST pattern to debug
            language: Programming language
            max_partial_matches: Maximum partial matches to analyze
            
        Returns:
            Detailed debugging information
        """
        # Basic pattern validation
        pattern_diagnostic = self._analyze_pattern(pattern, language)
        
        # Try to find actual matches first
        actual_matches = []
        if self.analyzer:
            try:
                result = self.analyzer.analyze_code(code, language, pattern)
                if result and result.get("matches"):
                    actual_matches = result["matches"]
            except Exception as e:
                pattern_diagnostic.common_failures.append(f"Analyzer error: {str(e)}")
        
        # If we have matches, provide analysis of successful matches
        if actual_matches:
            return {
                "pattern": pattern,
                "language": language,
                "status": "success",
                "matches_found": len(actual_matches),
                "sample_matches": actual_matches[:3],
                "pattern_analysis": pattern_diagnostic.__dict__,
                "suggestions": ["Pattern is working correctly"],
            }
        
        # No matches - start debugging
        partial_matches = self._find_partial_matches(code, pattern, language, max_partial_matches)
        failure_analysis = self._analyze_failures(code, pattern, language)
        suggestions = self._generate_suggestions(pattern, language, failure_analysis, partial_matches)
        
        return {
            "pattern": pattern,
            "language": language,
            "status": "no_matches",
            "matches_found": 0,
            "partial_matches": [match.__dict__ for match in partial_matches],
            "failure_analysis": failure_analysis,
            "pattern_analysis": pattern_diagnostic.__dict__,
            "suggestions": suggestions,
            "alternative_patterns": self._suggest_alternative_patterns(pattern, language),
            "debugging_steps": self._get_debugging_steps(pattern, language),
        }
    
    def _analyze_pattern(self, pattern: str, language: str) -> PatternDiagnostic:
        """Analyze a pattern for complexity and validity."""
        complexity_score = self._calculate_complexity(pattern)
        
        # Check for common issues
        common_failures = []
        suggestions = []
        
        # Language-specific analysis
        if language in self.common_issues:
            for issue_type, issue_info in self.common_issues[language].items():
                if self._check_pattern_issue(pattern, issue_type, language):
                    common_failures.append(issue_info["description"])
                    if "examples" in issue_info:
                        suggestions.append(
                            f"Try: {issue_info['examples'].get('right', '')} - "
                            f"{issue_info['examples'].get('explanation', '')}"
                        )
        
        # Basic syntax validation
        is_valid = self._validate_pattern_syntax(pattern)
        if not is_valid:
            common_failures.append("Invalid pattern syntax")
        
        # Generate expected matches based on pattern
        expected_matches = self._generate_expected_matches(pattern, language)
        
        return PatternDiagnostic(
            pattern=pattern,
            language=language,
            is_valid=is_valid,
            complexity_score=complexity_score,
            expected_matches=expected_matches,
            common_failures=common_failures,
            suggestions=suggestions
        )
    
    def _find_partial_matches(
        self,
        code: str,
        pattern: str,
        language: str,
        max_matches: int
    ) -> List[PartialMatch]:
        """Find partial matches to understand why full pattern fails."""
        partial_matches = []
        
        # Break pattern into components
        pattern_components = self._decompose_pattern(pattern)
        
        for component in pattern_components:
            # Try matching each component separately
            if self.analyzer:
                try:
                    result = self.analyzer.analyze_code(code, language, component)
                    if result and result.get("matches"):
                        for match in result["matches"][:2]:  # Limit to 2 per component
                            partial_match = PartialMatch(
                                location=match.get("location", {}),
                                matched_text=match.get("text", ""),
                                expected_pattern=component,
                                failure_reason=f"Component '{component}' matches, but full pattern doesn't",
                                confidence=0.7
                            )
                            partial_matches.append(partial_match)
                except Exception:
                    pass
        
        # Try simpler versions of the pattern
        simplified_patterns = self._simplify_pattern(pattern)
        for simple_pattern in simplified_patterns:
            if self.analyzer:
                try:
                    result = self.analyzer.analyze_code(code, language, simple_pattern)
                    if result and result.get("matches"):
                        for match in result["matches"][:1]:  # Limit to 1 per simplified pattern
                            partial_match = PartialMatch(
                                location=match.get("location", {}),
                                matched_text=match.get("text", ""),
                                expected_pattern=simple_pattern,
                                failure_reason=f"Simplified pattern '{simple_pattern}' works, original may be too specific",
                                confidence=0.8
                            )
                            partial_matches.append(partial_match)
                except Exception:
                    pass
        
        return partial_matches[:max_matches]
    
    def _analyze_failures(self, code: str, pattern: str, language: str) -> Dict[str, Any]:
        """Analyze potential reasons for pattern failure."""
        analysis = {
            "pattern_complexity": self._calculate_complexity(pattern),
            "code_structure_mismatch": False,
            "language_feature_mismatch": False,
            "metavariable_issues": [],
            "syntax_issues": [],
        }
        
        # Check for metavariable issues
        metavars = re.findall(r'\$+\w+', pattern)
        for metavar in metavars:
            if metavar.startswith('$$') and not metavar.startswith('$$$'):
                analysis["metavariable_issues"].append(
                    f"Invalid metavariable '{metavar}' - use $ or $$$ not $$"
                )
        
        # Language-specific analysis
        if language == "rust":
            if "async fn" in pattern and "-> Result" not in pattern:
                analysis["language_feature_mismatch"] = True
                analysis["syntax_issues"].append(
                    "Async functions often return Result types"
                )
        
        elif language == "python":
            if "def " in pattern and ":" not in pattern:
                analysis["syntax_issues"].append(
                    "Python function definitions require ':'"
                )
        
        return analysis
    
    def _generate_suggestions(
        self,
        pattern: str,
        language: str,
        failure_analysis: Dict[str, Any],
        partial_matches: List[PartialMatch]
    ) -> List[str]:
        """Generate actionable suggestions for fixing the pattern."""
        suggestions = []
        
        # Based on failure analysis
        if failure_analysis["metavariable_issues"]:
            suggestions.extend([
                "Fix metavariable syntax: use $ for single tokens, $$$ for multiple",
                "Example: 'fn $NAME($$$ARGS)' not 'fn $$NAME($$ARGS)'"
            ])
        
        if failure_analysis["pattern_complexity"] > 7:
            suggestions.append(
                "Pattern is complex - try breaking it into simpler parts first"
            )
        
        # Based on partial matches
        if partial_matches:
            best_partial = max(partial_matches, key=lambda x: x.confidence)
            suggestions.append(
                f"Try starting with simpler pattern: '{best_partial.expected_pattern}'"
            )
        
        # Language-specific suggestions
        if language == "rust":
            suggestions.extend([
                "For public functions, include 'pub' keyword",
                "For generic functions, include '<$$$GENERICS>' parameter",
                "For async functions, consider return type patterns",
            ])
        elif language == "python":
            suggestions.extend([
                "Include proper indentation for multi-line patterns",
                "Consider decorator patterns like '@$DECORATOR'",
            ])
        elif language == "javascript":
            suggestions.extend([
                "Try multiple function syntax variants (function, arrow, const)",
                "Consider async variants if targeting async code",
            ])
        
        # Generic suggestions
        suggestions.extend([
            "Use validate_pattern() to check syntax",
            "Use pattern_wizard() for guided pattern creation",
            "Test with simpler code samples first",
        ])
        
        return suggestions[:8]  # Limit to 8 suggestions for token management
    
    def _suggest_alternative_patterns(self, pattern: str, language: str) -> List[Dict[str, str]]:
        """Suggest alternative patterns that might work better."""
        alternatives = []
        
        # Language-specific alternatives
        if language == "rust":
            if "fn $NAME" in pattern:
                alternatives.extend([
                    {
                        "pattern": pattern.replace("fn $NAME", "pub fn $NAME"),
                        "description": "Try with public visibility"
                    },
                    {
                        "pattern": pattern.replace("fn $NAME($$$ARGS)", "fn $NAME<$$$GENERICS>($$$ARGS)"),
                        "description": "Try with generic parameters"
                    }
                ])
            
            if "async fn" in pattern and "Result" not in pattern:
                alternatives.append({
                    "pattern": pattern.replace("-> $RET", "-> Result<$OK, $ERR>"),
                    "description": "Try with Result return type"
                })
        
        elif language == "javascript":
            if "function $NAME" in pattern:
                alternatives.extend([
                    {
                        "pattern": "const $NAME = ($$$ARGS) => { $$$BODY }",
                        "description": "Try arrow function syntax"
                    },
                    {
                        "pattern": "const $NAME = function($$$ARGS) { $$$BODY }",
                        "description": "Try function expression syntax"
                    }
                ])
        
        return alternatives[:5]  # Limit for token management
    
    def _get_debugging_steps(self, pattern: str, language: str) -> List[str]:
        """Get step-by-step debugging instructions."""
        steps = [
            "1. Validate pattern syntax with validate_pattern()",
            "2. Test pattern on simple, known-good code sample",
            "3. Break complex pattern into smaller components",
            "4. Check language-specific syntax requirements",
            "5. Use pattern_wizard() for guided pattern creation",
        ]
        
        if language == "rust":
            steps.extend([
                "6. Verify visibility modifiers (pub/private)",
                "7. Check for async/await patterns",
                "8. Consider generic parameter requirements",
            ])
        elif language == "python":
            steps.extend([
                "6. Check indentation and colons",
                "7. Consider decorator patterns",
                "8. Verify Python-specific syntax",
            ])
        
        return steps
    
    def _calculate_complexity(self, pattern: str) -> int:
        """Calculate pattern complexity score (1-10)."""
        score = 1
        
        # Count metavariables
        metavars = len(re.findall(r'\$+\w+', pattern))
        score += min(metavars * self.complexity_factors["metavariables"], 4)
        
        # Count nested structures
        nested = len(re.findall(r'[{}\(\)\[\]]', pattern))
        score += min(nested * self.complexity_factors["nested_structures"] // 2, 3)
        
        # Multi-line patterns
        if '\n' in pattern:
            score += self.complexity_factors["multiple_lines"]
        
        return min(score, 10)
    
    def _validate_pattern_syntax(self, pattern: str) -> bool:
        """Basic pattern syntax validation."""
        # Check for basic syntax issues
        if '$$' in pattern and not pattern.startswith('$$$'):
            # Check for invalid $$ patterns
            invalid_metavars = re.findall(r'\$\$(?!\$)\w+', pattern)
            if invalid_metavars:
                return False
        
        # Check for balanced brackets
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        for char in pattern:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    return False
        
        return len(stack) == 0
    
    def _decompose_pattern(self, pattern: str) -> List[str]:
        """Break pattern into components for partial matching."""
        components = []
        
        # Split by common delimiters but keep meaningful parts
        parts = re.split(r'(\s+|\{|\}|\(|\))', pattern)
        
        # Rebuild meaningful components
        current_component = ""
        for part in parts:
            if part.strip():
                current_component += part
                # If we have a complete component, add it
                if any(keyword in current_component for keyword in ['fn ', 'def ', 'class ', 'function ']):
                    components.append(current_component.strip())
                    current_component = ""
        
        if current_component.strip():
            components.append(current_component.strip())
        
        return components
    
    def _simplify_pattern(self, pattern: str) -> List[str]:
        """Generate simpler versions of the pattern."""
        simplified = []
        
        # Remove metavariables and replace with wildcards
        simple = re.sub(r'\$+\w+', '_', pattern)
        simplified.append(simple)
        
        # Remove generic parameters
        simple = re.sub(r'<[^>]*>', '', pattern)
        if simple != pattern:
            simplified.append(simple)
        
        # Remove function bodies
        simple = re.sub(r'\{[^}]*\}', '{ }', pattern)
        if simple != pattern:
            simplified.append(simple)
        
        return simplified
    
    def _generate_expected_matches(self, pattern: str, language: str) -> List[str]:
        """Generate examples of what the pattern should match."""
        examples = []
        
        # This is a simplified implementation
        if language == "rust" and "fn $NAME" in pattern:
            examples.extend([
                "fn example_function()",
                "pub fn public_function()",
                "async fn async_function()",
            ])
        elif language == "python" and "def $NAME" in pattern:
            examples.extend([
                "def example_function():",
                "def function_with_args(a, b):",
                "async def async_function():",
            ])
        
        return examples
    
    def _check_pattern_issue(self, pattern: str, issue_type: str, language: str) -> bool:
        """Check if pattern has a specific issue."""
        if issue_type == "metavar_confusion" and "$$" in pattern and "$$$" not in pattern:
            return True
        if issue_type == "visibility_modifiers" and language == "rust" and "fn $" in pattern and "pub fn" not in pattern:
            return True
        return False