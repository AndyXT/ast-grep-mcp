"""
Interactive pattern building wizard for ast-grep.
"""
from typing import Dict, Any, List, Optional
import re
from dataclasses import dataclass

from ..utils.error_handling import handle_errors


@dataclass
class PatternExample:
    """Example showing pattern usage."""
    code: str
    matches: List[str]
    explanation: str


class PatternWizard:
    """Interactive pattern building assistant."""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.pattern_templates = self._load_pattern_templates()
    
    def _load_pattern_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load common pattern templates."""
        return {
            "python": {
                "function": {
                    "simple": "def $NAME($$$ARGS)",
                    "async": "async def $NAME($$$ARGS)",
                    "with_return": "def $NAME($$$ARGS) -> $RETURN_TYPE",
                    "with_decorator": "@$DECORATOR\ndef $NAME($$$ARGS)",
                    "class_method": "def $NAME(self, $$$ARGS)",
                },
                "class": {
                    "simple": "class $NAME",
                    "with_base": "class $NAME($BASE)",
                    "with_decorator": "@$DECORATOR\nclass $NAME",
                },
                "import": {
                    "simple": "import $MODULE",
                    "from": "from $MODULE import $NAME",
                    "alias": "import $MODULE as $ALIAS",
                },
                "exception": {
                    "try_except": "try:\n    $$$BODY\nexcept $EXCEPTION",
                    "raise": "raise $EXCEPTION",
                },
                "assignment": {
                    "simple": "$VAR = $VALUE",
                    "multiple": "$VAR1, $VAR2 = $VALUE",
                    "augmented": "$VAR += $VALUE",
                },
            },
            "javascript": {
                "function": {
                    "simple": "function $NAME($$$ARGS) { $$$BODY }",
                    "arrow": "const $NAME = ($$$ARGS) => $BODY",
                    "async": "async function $NAME($$$ARGS) { $$$BODY }",
                    "async_arrow": "const $NAME = async ($$$ARGS) => $BODY",
                },
                "class": {
                    "simple": "class $NAME { $$$BODY }",
                    "extends": "class $NAME extends $BASE { $$$BODY }",
                    "method": "$NAME($$$ARGS) { $$$BODY }",
                },
                "import": {
                    "named": "import { $NAME } from '$MODULE'",
                    "default": "import $NAME from '$MODULE'",
                    "namespace": "import * as $NAME from '$MODULE'",
                },
                "variable": {
                    "const": "const $NAME = $VALUE",
                    "let": "let $NAME = $VALUE",
                    "destructure": "const { $$$PROPS } = $OBJECT",
                },
            },
            "rust": {
                "function": {
                    "simple": "fn $NAME($$$ARGS)",
                    "with_return": "fn $NAME($$$ARGS) -> $RETURN_TYPE",
                    "async": "async fn $NAME($$$ARGS)",
                    "public": "pub fn $NAME($$$ARGS)",
                    "pub_async": "pub async fn $NAME($$$ARGS)",
                },
                "struct": {
                    "simple": "struct $NAME",
                    "with_fields": "struct $NAME { $$$FIELDS }",
                    "tuple": "struct $NAME($$$TYPES)",
                },
                "impl": {
                    "simple": "impl $TYPE { $$$BODY }",
                    "trait": "impl $TRAIT for $TYPE { $$$BODY }",
                },
                "match": {
                    "simple": "match $EXPR { $$$ARMS }",
                    "result": "match $EXPR { Ok($OK) => $OK_BODY, Err($ERR) => $ERR_BODY }",
                },
                "error_handling": {
                    "unwrap": "$EXPR.unwrap()",
                    "expect": "$EXPR.expect($MSG)",
                    "question_mark": "$EXPR?",
                },
            },
            "go": {
                "function": {
                    "simple": "func $NAME($$$ARGS)",
                    "with_return": "func $NAME($$$ARGS) $RETURN_TYPE",
                    "method": "func ($RECEIVER $TYPE) $NAME($$$ARGS)",
                },
                "struct": {
                    "simple": "type $NAME struct { $$$FIELDS }",
                },
                "interface": {
                    "simple": "type $NAME interface { $$$METHODS }",
                },
                "error_handling": {
                    "check": "if err != nil { $$$BODY }",
                    "return": "return $VALUE, err",
                },
            },
        }
    
    @handle_errors
    def pattern_wizard(
        self,
        description: str,
        language: str,
        examples: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate pattern suggestions based on natural language description.
        
        Args:
            description: What you want to find
            language: Programming language
            examples: Optional code examples
            
        Returns:
            Dictionary with pattern suggestions and explanations
        """
        suggestions = []
        
        # Normalize description
        desc_lower = description.lower()
        
        # Get language templates
        lang_templates = self.pattern_templates.get(language, {})
        
        # Analyze description for keywords
        keywords = self._extract_keywords(desc_lower)
        
        # Generate suggestions based on keywords
        for category, templates in lang_templates.items():
            for template_name, pattern in templates.items():
                score = self._score_template(keywords, category, template_name)
                if score > 0:
                    suggestions.append({
                        "pattern": pattern,
                        "score": score,
                        "category": category,
                        "name": template_name,
                        "explanation": self._explain_pattern(pattern, language),
                        "examples": self._generate_examples(pattern, language, category),
                    })
        
        # Sort by score
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        
        # If examples provided, try to infer pattern
        if examples:
            inferred = self._infer_from_examples(examples, language)
            if inferred:
                suggestions.insert(0, inferred)
        
        # Limit to top 5 suggestions
        top_suggestions = suggestions[:5]
        
        return {
            "description": description,
            "language": language,
            "suggestions": top_suggestions,
            "tips": self._get_pattern_tips(language),
            "metavariables": self._get_metavar_reference(),
            "next_steps": [
                "Test patterns with validate_pattern()",
                "Use explain_pattern() for detailed breakdown",
                "Refine with pattern_builder() for complex patterns",
            ],
        }
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extract relevant keywords from description."""
        # Common programming concepts
        keywords = []
        
        # Function-related
        if any(word in description for word in ["function", "method", "func", "def"]):
            keywords.append("function")
        if "async" in description or "await" in description:
            keywords.append("async")
        if "public" in description or "pub" in description:
            keywords.append("public")
        
        # Class-related
        if any(word in description for word in ["class", "struct", "type"]):
            keywords.append("class")
        if "inherit" in description or "extend" in description:
            keywords.append("extends")
        
        # Import-related
        if "import" in description or "require" in description or "use" in description:
            keywords.append("import")
        
        # Error handling
        if any(word in description for word in ["error", "exception", "try", "catch", "unwrap"]):
            keywords.append("error")
        
        # Pattern matching
        if "match" in description or "switch" in description:
            keywords.append("match")
        
        # Variable/assignment
        if any(word in description for word in ["variable", "const", "let", "assign"]):
            keywords.append("variable")
        
        return keywords
    
    def _score_template(self, keywords: List[str], category: str, template_name: str) -> int:
        """Score how well a template matches the keywords."""
        score = 0
        
        # Category matching
        for keyword in keywords:
            if keyword in category:
                score += 2
            if keyword in template_name:
                score += 3
        
        # Specific matches
        if "async" in keywords and "async" in template_name:
            score += 5
        if "public" in keywords and ("pub" in template_name or "public" in template_name):
            score += 4
        if "error" in keywords and category == "error_handling":
            score += 5
        
        return score
    
    def _explain_pattern(self, pattern: str, language: str) -> str:
        """Generate explanation for a pattern."""
        explanation = "This pattern matches "
        
        # Identify metavariables
        metavars = re.findall(r'\$+\w+', pattern)
        
        if "$NAME" in metavars:
            explanation += "an identifier "
        if "$$$ARGS" in metavars:
            explanation += "with any arguments "
        if "$$$BODY" in metavars:
            explanation += "containing any code block "
        if "$RETURN_TYPE" in metavars:
            explanation += "with a return type "
        
        # Add language-specific notes
        if language == "rust" and "pub" in pattern:
            explanation += "(public visibility) "
        if "async" in pattern:
            explanation += "(asynchronous) "
        
        return explanation.strip()
    
    def _generate_examples(self, pattern: str, language: str, category: str) -> List[Dict[str, str]]:
        """Generate example code that would match the pattern."""
        examples = []
        
        # Generate based on category and language
        if category == "function":
            if language == "python":
                if "async" in pattern:
                    examples.append({
                        "code": "async def fetch_data(url: str) -> dict:",
                        "matches": ["fetch_data", "url: str", "dict"],
                    })
                else:
                    examples.append({
                        "code": "def calculate_sum(a, b):",
                        "matches": ["calculate_sum", "a, b"],
                    })
            elif language == "rust":
                if "pub async" in pattern:
                    examples.append({
                        "code": "pub async fn handle_request(req: Request) -> Result<Response, Error>",
                        "matches": ["handle_request", "req: Request", "Result<Response, Error>"],
                    })
        
        return examples
    
    def _infer_from_examples(self, examples: List[str], language: str) -> Optional[Dict[str, Any]]:
        """Try to infer pattern from provided examples."""
        # This would use more sophisticated analysis in a real implementation
        # For now, return None
        return None
    
    def _get_pattern_tips(self, language: str) -> List[str]:
        """Get language-specific pattern tips."""
        tips = [
            "Use $ for single token capture (e.g., $VAR)",
            "Use $$$ for multiple tokens capture (e.g., $$$ARGS)",
            "Metavariables can be reused to ensure consistency",
            "Use ... for any code sequence",
        ]
        
        if language == "python":
            tips.extend([
                "Python patterns are whitespace-sensitive",
                "Use proper indentation in multi-line patterns",
            ])
        elif language == "rust":
            tips.extend([
                "Match lifetime annotations with $LIFETIME",
                "Generic types can be matched with $T",
            ])
        
        return tips
    
    def _get_metavar_reference(self) -> Dict[str, str]:
        """Get metavariable reference guide."""
        return {
            "$VAR": "Matches single identifier",
            "$$$VAR": "Matches zero or more tokens",
            "$_": "Matches any single token (wildcard)",
            "...": "Matches any sequence of code",
            "$VAR1, $VAR2": "Multiple captures with different names",
            "$$VAR": "Invalid - use either $ or $$$",
        }
    
    @handle_errors
    def explain_pattern(self, pattern: str, language: str) -> Dict[str, Any]:
        """
        Provide detailed explanation of what a pattern does.
        
        Args:
            pattern: The pattern to explain
            language: Programming language
            
        Returns:
            Detailed breakdown of the pattern
        """
        # Parse pattern components
        components = self._parse_pattern_components(pattern)
        
        # Generate explanation
        explanation = {
            "pattern": pattern,
            "language": language,
            "components": components,
            "matches": self._describe_matches(pattern, language),
            "examples": {
                "will_match": self._generate_positive_examples(pattern, language),
                "wont_match": self._generate_negative_examples(pattern, language),
            },
            "common_uses": self._get_common_uses(pattern, language),
            "tips": [
                "Test with actual code using analyze_code()",
                "Use validate_pattern() to check syntax",
                "Combine with other patterns using compose_rule()",
            ],
        }
        
        return explanation
    
    def _parse_pattern_components(self, pattern: str) -> List[Dict[str, str]]:
        """Parse pattern into components."""
        components = []
        
        # Find metavariables
        for match in re.finditer(r'(\$+)(\w+)', pattern):
            prefix = match.group(1)
            name = match.group(2)
            
            component_type = "single" if len(prefix) == 1 else "multiple"
            components.append({
                "metavar": f"{prefix}{name}",
                "type": component_type,
                "name": name,
                "description": f"Captures {component_type} token(s) as '{name}'"
            })
        
        # Find ellipsis
        if "..." in pattern:
            components.append({
                "metavar": "...",
                "type": "ellipsis",
                "name": "any",
                "description": "Matches any sequence of code"
            })
        
        return components
    
    def _describe_matches(self, pattern: str, language: str) -> str:
        """Describe what the pattern matches in plain language."""
        # This would be more sophisticated in a real implementation
        description = f"This {language} pattern matches code that "
        
        # Add specific descriptions based on pattern content
        if "function" in pattern or "fn" in pattern or "def" in pattern:
            description += "defines a function "
        if "class" in pattern:
            description += "defines a class "
        if "async" in pattern:
            description += "is asynchronous "
        
        return description
    
    def _generate_positive_examples(self, pattern: str, language: str) -> List[str]:
        """Generate examples that will match the pattern."""
        # Simplified implementation
        return ["# Example code that matches the pattern"]
    
    def _generate_negative_examples(self, pattern: str, language: str) -> List[str]:
        """Generate examples that won't match the pattern."""
        # Simplified implementation
        return ["# Example code that doesn't match the pattern"]
    
    def _get_common_uses(self, pattern: str, language: str) -> List[str]:
        """Get common use cases for the pattern."""
        uses = []
        
        if "$NAME" in pattern:
            uses.append("Finding all occurrences of specific identifiers")
        if "$$$ARGS" in pattern:
            uses.append("Matching functions regardless of parameter count")
        if "async" in pattern:
            uses.append("Identifying asynchronous code for refactoring")
        
        return uses