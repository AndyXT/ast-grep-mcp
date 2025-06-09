"""
Improved pattern validation with detailed error messages and suggestions.
"""

from typing import Dict, Any, List, Optional
import re
from pathlib import Path


class ImprovedPatternValidator:
    """Enhanced pattern validator with helpful error messages and suggestions."""
    
    def __init__(self, logger: Optional[Any] = None):
        self.logger = logger
        
        # Common pattern mistakes and their fixes
        self.common_fixes = {
            "python": {
                r"def (\w+)\(": "def $NAME(",  # Concrete name -> metavariable
                r"class (\w+):": "class $NAME:",
                r"import (\w+)": "import $MODULE",
                r"from (\w+) import": "from $MODULE import",
            },
            "rust": {
                r"fn (\w+)\(": "fn $NAME(",
                r"struct (\w+)": "struct $NAME",
                r"enum (\w+)": "enum $NAME",
                r"impl (\w+)": "impl $NAME",
                r"pub fn (\w+)": "pub fn $NAME",
            },
            "javascript": {
                r"function (\w+)\(": "function $NAME(",
                r"const (\w+) =": "const $NAME =",
                r"class (\w+)": "class $NAME",
            },
        }
    
    def validate_and_suggest(
        self, 
        pattern: str, 
        language: Optional[str] = None,
        directory: str = "."
    ) -> Dict[str, Any]:
        """
        Validate a pattern and provide helpful suggestions.
        
        Returns:
            Dictionary with validation results and suggestions
        """
        result = {
            "valid": True,
            "suggestions": [],
            "errors": [],
            "warnings": [],
            "auto_fixes": [],
            "examples": []
        }
        
        # Basic pattern validation
        basic_issues = self._check_basic_issues(pattern)
        result["errors"].extend(basic_issues)
        
        # Language-specific validation
        if language:
            lang_issues = self._check_language_specific(pattern, language)
            result["warnings"].extend(lang_issues)
            
            # Generate suggestions based on language
            suggestions = self._generate_language_suggestions(pattern, language)
            result["suggestions"].extend(suggestions)
            
            # Look for auto-fixable patterns
            auto_fixes = self._find_auto_fixes(pattern, language)
            result["auto_fixes"].extend(auto_fixes)
            
            # Provide examples
            examples = self._get_pattern_examples(pattern, language)
            result["examples"].extend(examples)
        
        # Context-aware suggestions
        context_suggestions = self._analyze_directory_context(directory, pattern)
        result["suggestions"].extend(context_suggestions)
        
        # Overall validation status
        result["valid"] = len(result["errors"]) == 0
        
        # Add helpful tips
        if not result["valid"] or result["warnings"]:
            result["help"] = self._generate_help_message(pattern, language, result)
        
        return result
    
    def _check_basic_issues(self, pattern: str) -> List[str]:
        """Check for basic pattern syntax issues."""
        issues = []
        
        if not pattern or not pattern.strip():
            issues.append("Pattern cannot be empty")
            return issues
        
        # Check for unbalanced brackets
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in pattern:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    issues.append(f"Unmatched closing bracket '{char}'")
                else:
                    expected = brackets[stack.pop()]
                    if char != expected:
                        issues.append(f"Mismatched brackets: expected '{expected}', got '{char}'")
        
        if stack:
            issues.append(f"Unmatched opening brackets: {', '.join(stack)}")
        
        # Check for invalid metavariable syntax
        invalid_metavars = re.findall(r'\$[a-z][a-zA-Z0-9_]*', pattern)
        if invalid_metavars:
            issues.append(f"Metavariables should be uppercase: {', '.join(invalid_metavars)}")
        
        # Check for common typos
        if '$$' in pattern and '$$$' not in pattern:
            issues.append("Did you mean '$$$' for multiple matches? '$$' is not valid syntax")
        
        return issues
    
    def _check_language_specific(self, pattern: str, language: str) -> List[str]:
        """Check for language-specific issues."""
        warnings = []
        
        if language == "python":
            if "def " in pattern and "$NAME" not in pattern:
                warnings.append("Python function patterns usually need $NAME metavariable")
            if "class " in pattern and "$NAME" not in pattern:
                warnings.append("Python class patterns usually need $NAME metavariable")
        
        elif language == "rust":
            if "fn " in pattern and "$NAME" not in pattern:
                warnings.append("Rust function patterns usually need $NAME metavariable")
            if pattern.startswith("async ") and "fn" not in pattern:
                warnings.append("'async' keyword usually precedes 'fn' in Rust")
        
        elif language in ["javascript", "typescript"]:
            if "function " in pattern and "$NAME" not in pattern:
                warnings.append("JavaScript function patterns usually need $NAME metavariable")
            if "=>" in pattern and "(" not in pattern:
                warnings.append("Arrow functions usually have parameters in parentheses")
        
        return warnings
    
    def _generate_language_suggestions(self, pattern: str, language: str) -> List[str]:
        """Generate helpful suggestions based on language and pattern."""
        suggestions = []
        
        # Common patterns for each language
        common_patterns = {
            "python": [
                "def $NAME($$$ARGS):",
                "class $NAME($$$BASES):",
                "import $MODULE",
                "from $MODULE import $NAME",
                "async def $NAME($$$ARGS):",
            ],
            "rust": [
                "fn $NAME($$$ARGS)",
                "pub fn $NAME($$$ARGS)",
                "async fn $NAME($$$ARGS)",
                "struct $NAME",
                "enum $NAME",
                "impl $NAME",
            ],
            "javascript": [
                "function $NAME($$$ARGS)",
                "const $NAME = ($$$ARGS) =>",
                "class $NAME",
                "async function $NAME($$$ARGS)",
            ]
        }
        
        if language in common_patterns:
            # Find similar patterns
            pattern_words = set(pattern.lower().split())
            
            for common in common_patterns[language]:
                common_words = set(common.lower().replace("$", "").split())
                
                # If there's overlap, suggest it
                if pattern_words & common_words:
                    suggestions.append(f"Try: {common}")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _find_auto_fixes(self, pattern: str, language: str) -> List[Dict[str, str]]:
        """Find patterns that can be automatically fixed."""
        auto_fixes = []
        
        if language in self.common_fixes:
            for mistake, fix in self.common_fixes[language].items():
                if re.search(mistake, pattern):
                    fixed_pattern = re.sub(mistake, fix, pattern)
                    auto_fixes.append({
                        "original": pattern,
                        "fixed": fixed_pattern,
                        "explanation": "Replace concrete names with metavariables like $NAME"
                    })
        
        return auto_fixes
    
    def _get_pattern_examples(self, pattern: str, language: str) -> List[Dict[str, str]]:
        """Get examples of what the pattern would match."""
        examples = []
        
        # Simple pattern-to-example mapping
        pattern_examples = {
            "python": {
                "def $NAME": "def hello_world():",
                "class $NAME": "class MyClass:",
                "import $MODULE": "import os",
                "async def $NAME": "async def fetch_data():",
            },
            "rust": {
                "fn $NAME": "fn main() {",
                "pub fn $NAME": "pub fn new() -> Self {",
                "struct $NAME": "struct Point {",
                "async fn $NAME": "async fn fetch() -> Result<(), Error> {",
            },
            "javascript": {
                "function $NAME": "function doSomething() {",
                "const $NAME =": "const myVar = 42;",
                "class $NAME": "class Component {",
            }
        }
        
        if language in pattern_examples:
            for pattern_key, example in pattern_examples[language].items():
                if pattern_key.replace("$NAME", "").strip() in pattern:
                    examples.append({
                        "pattern": pattern_key,
                        "example": example,
                        "description": f"This would match code like: {example}"
                    })
        
        return examples[:2]  # Limit examples
    
    def _analyze_directory_context(self, directory: str, pattern: str) -> List[str]:
        """Analyze directory to provide context-aware suggestions."""
        suggestions = []
        
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                return suggestions
            
            # Count file types
            file_counts = {}
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    file_counts[ext] = file_counts.get(ext, 0) + 1
            
            # Suggest language based on files found
            if not any(keyword in pattern.lower() for keyword in ['def', 'fn', 'function', 'class']):
                if file_counts.get('.py', 0) > 0:
                    suggestions.append("Found Python files - try patterns like 'def $NAME' or 'class $NAME'")
                if file_counts.get('.rs', 0) > 0:
                    suggestions.append("Found Rust files - try patterns like 'fn $NAME' or 'struct $NAME'")
                if file_counts.get('.js', 0) > 0 or file_counts.get('.ts', 0) > 0:
                    suggestions.append("Found JavaScript/TypeScript files - try 'function $NAME' or 'const $NAME ='")
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error analyzing directory context: {e}")
        
        return suggestions
    
    def _generate_help_message(self, pattern: str, language: Optional[str], result: Dict[str, Any]) -> str:
        """Generate a helpful error/warning message."""
        help_parts = []
        
        if result["errors"]:
            help_parts.append("Issues found:")
            help_parts.extend([f"  • {error}" for error in result["errors"]])
        
        if result["auto_fixes"]:
            help_parts.append("\nSuggested fixes:")
            for fix in result["auto_fixes"]:
                help_parts.append(f"  • Try: {fix['fixed']}")
                help_parts.append(f"    ({fix['explanation']})")
        
        if result["suggestions"]:
            help_parts.append("\nCommon patterns to try:")
            help_parts.extend([f"  • {suggestion}" for suggestion in result["suggestions"][:3]])
        
        if language:
            help_parts.append(f"\nFor {language} code, metavariables like $NAME, $ARGS are commonly used.")
            help_parts.append("Use $$$ARGS for multiple arguments or statements.")
        
        return "\n".join(help_parts)


def validate_pattern_with_suggestions(
    pattern: str,
    language: Optional[str] = None,
    directory: str = ".",
    logger=None
) -> Dict[str, Any]:
    """
    Convenience function to validate a pattern with suggestions.
    
    Args:
        pattern: The pattern to validate
        language: Programming language (optional)
        directory: Directory context for suggestions
        logger: Logger instance
        
    Returns:
        Dictionary with validation results and suggestions
    """
    validator = ImprovedPatternValidator(logger)
    return validator.validate_and_suggest(pattern, language, directory)