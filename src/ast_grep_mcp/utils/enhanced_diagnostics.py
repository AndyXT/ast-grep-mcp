"""
Enhanced diagnostics for pattern matching errors.

This module provides detailed error messages with examples and suggestions
when patterns fail to match.
"""

from typing import Dict, List, Optional, Any
import re
from .common_patterns import CommonPatternLibrary


class EnhancedDiagnostics:
    """Provides enhanced diagnostic information for pattern matching errors."""
    
    @classmethod
    def diagnose_pattern_failure(
        cls,
        pattern: str,
        language: str,
        code_snippet: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Diagnose why a pattern failed and provide helpful suggestions.
        
        Args:
            pattern: The pattern that failed
            language: Programming language
            code_snippet: Optional code that was searched
            error_message: Optional error message from ast-grep
            
        Returns:
            Diagnostic information with examples and suggestions
        """
        diagnosis = {
            "pattern": pattern,
            "language": language,
            "likely_issues": [],
            "examples_that_would_match": [],
            "suggested_patterns": [],
            "common_mistakes": [],
            "documentation_links": []
        }
        
        # Analyze the pattern for common issues
        issues = cls._identify_pattern_issues(pattern, language)
        diagnosis["likely_issues"] = issues
        
        # Generate examples of code that would match
        examples = cls._generate_matching_examples(pattern, language)
        diagnosis["examples_that_would_match"] = examples
        
        # Suggest alternative patterns
        suggestions = cls._suggest_alternative_patterns(pattern, language, code_snippet)
        diagnosis["suggested_patterns"] = suggestions
        
        # Identify common mistakes
        mistakes = cls._identify_common_mistakes(pattern, language)
        diagnosis["common_mistakes"] = mistakes
        
        # Add metavariable usage guide
        diagnosis["metavariable_guide"] = {
            "$VAR": "Matches a single node (identifier, expression, etc.)",
            "$$$VAR": "Matches multiple nodes (variadic - use for parameters, arguments, statements)",
            "$_": "Matches any single node without capturing it",
            "$$$_": "Matches any sequence of nodes without capturing",
            "$$VAR": "INCORRECT - use $$$ for multiple items, not $$"
        }
        
        # Add helpful documentation links
        diagnosis["documentation_links"] = [
            "https://ast-grep.github.io/reference/pattern-syntax.html",
            f"https://ast-grep.github.io/guide/pattern-syntax.html#{language}"
        ]
        
        # Create a helpful error message
        diagnosis["helpful_message"] = cls._create_helpful_message(diagnosis)
        
        return diagnosis
    
    @classmethod
    def _identify_pattern_issues(cls, pattern: str, language: str) -> List[Dict[str, str]]:
        """Identify likely issues with the pattern."""
        issues = []
        
        # Check for overly specific patterns
        if len(pattern) > 100 and pattern.count("$") < 3:
            issues.append({
                "issue": "Pattern too specific",
                "explanation": "Long patterns with few metavariables are unlikely to match",
                "suggestion": "Use more metavariables ($VAR, $$$ARGS) to make the pattern flexible"
            })
        
        # Check for problematic metavariable usage
        if "$EXPR" in pattern and "." in pattern:
            issues.append({
                "issue": "Problematic $EXPR usage",
                "explanation": "$EXPR before method calls often fails to match",
                "suggestion": "Try removing $EXPR or using a more specific metavariable like $VAR"
            })
        
        # Check for missing metavariable indicators
        if language == "rust":
            if re.search(r'\b(unwrap|expect|await)\b', pattern) and "$" not in pattern:
                issues.append({
                    "issue": "No metavariables in pattern",
                    "explanation": "Patterns without metavariables must match exactly",
                    "suggestion": "Add metavariables to match variations (e.g., $VAR.unwrap())"
                })
        
        # Check for incorrect syntax
        if "$$" in pattern and "$$$" not in pattern:
            issues.append({
                "issue": "Incorrect variadic syntax",
                "explanation": "Use $$$ for matching multiple items, not $$",
                "suggestion": "Replace $$ with $$$ for variadic matching"
            })
        
        return issues
    
    @classmethod
    def _generate_matching_examples(cls, pattern: str, language: str) -> List[Dict[str, str]]:
        """Generate examples of code that would match the pattern."""
        examples = []
        
        # Simple pattern matching
        if language == "rust":
            if pattern == "unwrap()":
                examples.append({
                    "code": "let value = result.unwrap();",
                    "explanation": "Method call on any expression"
                })
                examples.append({
                    "code": "data.get(key).unwrap()",
                    "explanation": "Chained method calls ending with unwrap()"
                })
            
            elif pattern == "async fn $NAME":
                examples.append({
                    "code": "async fn process_data() {\n    // function body\n}",
                    "explanation": "Async function without visibility modifier"
                })
                examples.append({
                    "code": "async fn fetch_user(id: u64) -> Result<User> {\n    // ...\n}",
                    "explanation": "Async function with parameters and return type"
                })
            
            elif pattern == "spawn($$$ARGS)":
                examples.append({
                    "code": "spawn(async { process().await });",
                    "explanation": "Spawn with async block"
                })
                examples.append({
                    "code": "tokio::spawn(async move { handle_request(req).await });",
                    "explanation": "Tokio spawn with async move block"
                })
            
            # Generic pattern for any Rust pattern with $EXPR
            elif "$EXPR" in pattern:
                examples.append({
                    "code": "// Replace $EXPR with any expression",
                    "explanation": "$EXPR matches any expression in the code"
                })
                if ".unwrap()" in pattern:
                    examples.append({
                        "code": "result.unwrap()",
                        "explanation": "Any expression followed by .unwrap()"
                    })
        
        elif language == "javascript":
            if pattern == "console.log($$$ARGS)":
                examples.append({
                    "code": 'console.log("Hello, world!");',
                    "explanation": "Simple console.log with string"
                })
                examples.append({
                    "code": "console.log('User:', user, 'Data:', data);",
                    "explanation": "Console.log with multiple arguments"
                })
            
            elif pattern == "async function $NAME":
                examples.append({
                    "code": "async function fetchData() {\n    return await api.get('/data');\n}",
                    "explanation": "Async function declaration"
                })
        
        return examples
    
    @classmethod
    def _suggest_alternative_patterns(
        cls, 
        pattern: str, 
        language: str,
        code_snippet: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Suggest alternative patterns that might work better."""
        suggestions = []
        
        # Get suggestions from common pattern library
        library = CommonPatternLibrary()
        
        # Try to find similar patterns
        if language == "rust":
            if "unwrap" in pattern.lower():
                unwrap_pattern = library.find_pattern_by_name("rust", "unwrap_calls")
                if unwrap_pattern:
                    for variant in unwrap_pattern.variations or []:
                        suggestions.append({
                            "pattern": variant,
                            "reason": "Common variation for unwrap patterns",
                            "confidence": 0.8
                        })
            
            if "async" in pattern and "fn" in pattern:
                async_pattern = library.find_pattern_by_name("rust", "async_functions")
                if async_pattern:
                    suggestions.append({
                        "pattern": async_pattern.pattern,
                        "reason": "Simplified async function pattern",
                        "confidence": 0.9
                    })
        
        # Add general simplification suggestions
        if len(pattern) > 50:
            # Suggest simpler version
            simplified = cls._simplify_pattern(pattern)
            if simplified != pattern:
                suggestions.append({
                    "pattern": simplified,
                    "reason": "Simplified version of your pattern",
                    "confidence": 0.7
                })
        
        return suggestions
    
    @classmethod
    def _simplify_pattern(cls, pattern: str) -> str:
        """Simplify a complex pattern."""
        # Remove complex parts but keep structure
        simplified = pattern
        
        # Replace complex parameter lists with metavariables
        simplified = re.sub(r'\([^)]+\)', '($$$PARAMS)', simplified)
        
        # Replace complex bodies with metavariables
        simplified = re.sub(r'\{[^}]+\}', '{ $$$BODY }', simplified)
        
        # Replace specific names with metavariables
        simplified = re.sub(r'\b[a-z_][a-z0-9_]*\b', '$NAME', simplified, count=1)
        
        return simplified
    
    @classmethod
    def _identify_common_mistakes(cls, pattern: str, language: str) -> List[str]:
        """Identify common mistakes in the pattern."""
        mistakes = []
        
        # Language-agnostic mistakes
        if pattern.count("(") != pattern.count(")"):
            mistakes.append("Unbalanced parentheses")
        
        if pattern.count("{") != pattern.count("}"):
            mistakes.append("Unbalanced braces")
        
        if pattern.count("[") != pattern.count("]"):
            mistakes.append("Unbalanced brackets")
        
        # Language-specific mistakes
        if language == "rust":
            if "fn" in pattern and "(" not in pattern:
                mistakes.append("Function pattern missing parentheses")
            
            if ".unwrap" in pattern and "()" not in pattern:
                mistakes.append("Method call missing parentheses")
            
            if pattern.startswith("async") and "fn" not in pattern:
                mistakes.append("Async keyword without fn")
        
        elif language == "python":
            if "def" in pattern and ":" not in pattern:
                mistakes.append("Function definition missing colon")
            
            if "if" in pattern and ":" not in pattern:
                mistakes.append("If statement missing colon")
        
        elif language in ["javascript", "typescript"]:
            if "function" in pattern and "{" not in pattern and "=>" not in pattern:
                mistakes.append("Function missing body or arrow")
        
        return mistakes
    
    @classmethod
    def _create_helpful_message(cls, diagnosis: Dict[str, Any]) -> str:
        """Create a helpful error message from the diagnosis."""
        lines = []
        
        lines.append(f"❌ Pattern failed to match: {diagnosis['pattern']}")
        lines.append("")
        
        if diagnosis["likely_issues"]:
            lines.append("🔍 Likely issues:")
            for issue in diagnosis["likely_issues"]:
                lines.append(f"  • {issue['issue']}: {issue['explanation']}")
                lines.append(f"    → {issue['suggestion']}")
            lines.append("")
        
        if diagnosis["common_mistakes"]:
            lines.append("⚠️  Common mistakes found:")
            for mistake in diagnosis["common_mistakes"]:
                lines.append(f"  • {mistake}")
            lines.append("")
        
        if diagnosis["suggested_patterns"]:
            lines.append("💡 Try these patterns instead:")
            for suggestion in diagnosis["suggested_patterns"][:3]:
                lines.append(f"  • {suggestion['pattern']}")
                lines.append(f"    ({suggestion['reason']})")
            lines.append("")
        
        if diagnosis["examples_that_would_match"]:
            lines.append("📝 Examples of code that would match your pattern:")
            for example in diagnosis["examples_that_would_match"][:2]:
                lines.append(f"  {example['code']}")
                lines.append(f"  ^ {example['explanation']}")
                lines.append("")
        
        lines.append("📚 For more help, see the pattern syntax documentation")
        
        return "\n".join(lines)


def create_pattern_example_catalog() -> Dict[str, Dict[str, List[str]]]:
    """
    Create a catalog of pattern examples for quick reference.
    
    Returns:
        Dictionary mapping language -> pattern type -> example codes
    """
    return {
        "rust": {
            "unwrap_patterns": [
                "result.unwrap()",
                "option.unwrap_or(default)",
                "data.get(key).unwrap()",
                "parse::<i32>().unwrap()"
            ],
            "async_functions": [
                "async fn handle_request() { }",
                "pub async fn process(data: &str) -> Result<()> { }",
                "async fn fetch_data() -> impl Future<Output = Data> { }"
            ],
            "spawn_patterns": [
                "tokio::spawn(async { })",
                "spawn(async move { process().await })",
                "runtime.spawn(future)"
            ],
            "error_handling": [
                "result?",
                "file.read_to_string(&mut contents)?",
                "match result { Ok(v) => v, Err(e) => return Err(e) }"
            ]
        },
        "javascript": {
            "async_patterns": [
                "async function getData() { }",
                "const fetchUser = async (id) => { }",
                "await fetchData()",
                "Promise.all([p1, p2])"
            ],
            "console_patterns": [
                "console.log('Debug:', value)",
                "console.error(error)",
                "console.warn('Warning!')"
            ],
            "arrow_functions": [
                "(x) => x * 2",
                "const add = (a, b) => a + b",
                "users.map(user => user.name)"
            ]
        },
        "python": {
            "function_patterns": [
                "def process_data(data):",
                "async def fetch_user(user_id):",
                "@decorator\ndef method():"
            ],
            "error_patterns": [
                "try:\n    risky_operation()\nexcept ValueError as e:\n    handle_error(e)",
                "raise ValueError('Invalid input')",
                "assert condition, 'Error message'"
            ]
        }
    }