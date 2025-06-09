"""
Pattern guide and documentation tools for the AST-grep MCP server.

This module provides tools to help users understand pattern syntax and usage.
"""

import logging
from typing import Dict, Any, Optional, List
from ..language_handlers import get_handler

logger = logging.getLogger("ast_grep_mcp.pattern_guide")


class PatternGuideTools:
    """Tools for providing pattern syntax guidance and documentation."""
    
    def __init__(self):
        self.logger = logger
        self.guide_cache = {}
        self._load_guides()
    
    def _load_guides(self):
        """Load pattern syntax guides from documentation."""
        # Basic metavariable syntax guide
        self.guide_cache["metavariables"] = {
            "title": "Metavariable Syntax Guide",
            "description": "How to use metavariables in AST-grep patterns",
            "content": {
                "single_capture": {
                    "syntax": "$NAME",
                    "description": "Captures a single AST node",
                    "examples": [
                        {"pattern": "$VAR", "matches": "x, myVariable, count"},
                        {"pattern": "$FUNC", "matches": "doSomething, calculate, main"},
                        {"pattern": "$EXPR", "matches": "x + 1, obj.method(), true"}
                    ],
                    "rules": [
                        "Must start with $ followed by uppercase letters",
                        "Can contain uppercase letters, numbers, and underscores",
                        "Captures exactly one AST node"
                    ]
                },
                "variadic_capture": {
                    "syntax": "$$$NAME",
                    "description": "Captures zero or more AST nodes",
                    "examples": [
                        {"pattern": "$$$PARAMS", "matches": "(), (a), (a, b, c)"},
                        {"pattern": "$$$ARGS", "matches": "no args, single arg, multiple args"},
                        {"pattern": "$$$BODY", "matches": "empty body, single statement, multiple statements"}
                    ],
                    "rules": [
                        "Must use exactly three dollar signs: $$$",
                        "Commonly used for parameters, arguments, body statements",
                        "Can match zero nodes (empty)"
                    ]
                },
                "wildcards": {
                    "syntax": "$_ and $$$",
                    "description": "Match without capturing",
                    "examples": [
                        {"pattern": "$_", "description": "Matches any single node"},
                        {"pattern": "$$$", "description": "Matches any sequence of nodes"}
                    ]
                },
                "common_mistakes": [
                    {
                        "wrong": "$$PARAMS",
                        "correct": "$$$PARAMS",
                        "explanation": "Double dollar is invalid, use triple for variadic"
                    },
                    {
                        "wrong": "$ NAME",
                        "correct": "$NAME",
                        "explanation": "No space after dollar sign"
                    },
                    {
                        "wrong": "NAME",
                        "correct": "$NAME",
                        "explanation": "Metavariables must start with $"
                    }
                ]
            }
        }
        
        # Pattern matching principles
        self.guide_cache["principles"] = {
            "title": "Pattern Matching Principles",
            "description": "Key concepts for understanding AST-grep patterns",
            "content": {
                "structural_matching": {
                    "description": "AST-grep matches code structure, not text",
                    "examples": [
                        {
                            "pattern": "function $NAME($$$PARAMS) { $$$BODY }",
                            "matches_all": [
                                "function foo(a, b) { return a + b; }",
                                "function foo(a,b){return a+b;}",
                                "function foo(\n  a,\n  b\n) {\n  return a + b;\n}"
                            ],
                            "explanation": "Whitespace and formatting don't affect matching"
                        }
                    ]
                },
                "pattern_simplicity": {
                    "description": "Start with simple patterns and build complexity",
                    "progression": [
                        {"level": "Basic", "pattern": "fn $NAME", "description": "Matches any Rust function"},
                        {"level": "Intermediate", "pattern": "async fn $NAME", "description": "Matches async functions"},
                        {"level": "Advanced", "pattern": "async fn $NAME($$$PARAMS) -> $RET { $$$BODY }", "description": "Full function structure"}
                    ]
                },
                "language_awareness": {
                    "description": "Patterns must follow language syntax rules",
                    "examples": {
                        "python": "Functions need colons: def $NAME($$$PARAMS):",
                        "javascript": "Blocks need braces: function $NAME() { $$$BODY }",
                        "rust": "Return types use arrows: fn $NAME() -> $TYPE"
                    }
                }
            }
        }
        
        # Quick reference
        self.guide_cache["quick_reference"] = {
            "title": "Quick Pattern Reference",
            "description": "Common patterns for quick lookup",
            "content": {
                "metavariables": {
                    "$NAME": "Single capture",
                    "$$$NAME": "Multiple capture (variadic)",
                    "$_": "Single wildcard",
                    "$$$": "Multiple wildcard"
                },
                "common_names": {
                    "$FUNC, $METHOD": "Function/method names",
                    "$VAR, $NAME": "Variable names",
                    "$TYPE": "Type names",
                    "$EXPR": "Expressions",
                    "$$$PARAMS": "Parameter lists",
                    "$$$ARGS": "Argument lists",
                    "$$$BODY": "Statement blocks"
                },
                "tips": [
                    "Use simple patterns for broad matching",
                    "Test patterns incrementally",
                    "Check language-specific syntax requirements",
                    "Validate patterns before using in production"
                ]
            }
        }
    
    def get_pattern_syntax_guide(
        self,
        topic: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get pattern syntax guide for a specific topic or language.
        
        Args:
            topic: Optional specific topic (metavariables, principles, quick_reference)
            language: Optional programming language for language-specific guidance
            
        Returns:
            Dictionary with pattern syntax guidance
        """
        result = {
            "success": True,
            "guides": {}
        }
        
        # If specific topic requested
        if topic and topic in self.guide_cache:
            result["guides"][topic] = self.guide_cache[topic]
        elif topic:
            # Topic not found
            result["success"] = False
            result["error"] = f"Unknown topic: {topic}"
            result["available_topics"] = list(self.guide_cache.keys())
            return result
        else:
            # Return all guides
            result["guides"] = self.guide_cache
        
        # Add language-specific patterns if requested
        if language:
            handler = get_handler(language)
            if handler:
                patterns = handler.get_default_patterns()
                # Group patterns by category
                categorized = self._categorize_patterns(patterns)
                result["language_patterns"] = {
                    "language": language,
                    "categories": categorized
                }
            else:
                result["warning"] = f"No handler found for language: {language}"
        
        # Add helpful links
        result["resources"] = {
            "documentation": "/docs/pattern-syntax-comprehensive.md",
            "examples": "Use 'get_language_patterns' for language-specific examples",
            "validation": "Use 'validate_pattern' to check pattern syntax"
        }
        
        return result
    
    def _categorize_patterns(self, patterns: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
        """Categorize patterns by type."""
        categories = {
            "functions": [],
            "classes": [],
            "variables": [],
            "control_flow": [],
            "imports": [],
            "errors": [],
            "async": [],
            "other": []
        }
        
        for name, pattern in patterns.items():
            item = {"name": name, "pattern": pattern}
            
            # Categorize based on name
            if any(keyword in name for keyword in ["function", "func", "method", "fn"]):
                categories["functions"].append(item)
            elif any(keyword in name for keyword in ["class", "struct", "trait", "interface", "type"]):
                categories["classes"].append(item)
            elif any(keyword in name for keyword in ["var", "variable", "let", "const", "static"]):
                categories["variables"].append(item)
            elif any(keyword in name for keyword in ["if", "for", "while", "match", "switch", "loop"]):
                categories["control_flow"].append(item)
            elif any(keyword in name for keyword in ["import", "use", "require", "include"]):
                categories["imports"].append(item)
            elif any(keyword in name for keyword in ["error", "unwrap", "panic", "throw", "catch"]):
                categories["errors"].append(item)
            elif any(keyword in name for keyword in ["async", "await", "spawn", "future"]):
                categories["async"].append(item)
            else:
                categories["other"].append(item)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def get_pattern_examples(
        self,
        pattern_type: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Get specific pattern examples for a pattern type and language.
        
        Args:
            pattern_type: Type of pattern (function, class, async, etc.)
            language: Programming language
            
        Returns:
            Dictionary with pattern examples and explanations
        """
        examples = {
            "success": True,
            "pattern_type": pattern_type,
            "language": language,
            "examples": []
        }
        
        # Language-specific examples
        language_examples = {
            "rust": {
                "function": [
                    {
                        "description": "Simple function",
                        "pattern": "fn $NAME",
                        "example_code": "fn calculate() {}",
                        "explanation": "Matches any function declaration"
                    },
                    {
                        "description": "Function with parameters",
                        "pattern": "fn $NAME($$$PARAMS) { $$$BODY }",
                        "example_code": "fn add(a: i32, b: i32) { a + b }",
                        "explanation": "Captures function name, parameters, and body"
                    },
                    {
                        "description": "Async function",
                        "pattern": "async fn $NAME($$$PARAMS) { $$$BODY }",
                        "example_code": "async fn fetch_data(url: &str) { ... }",
                        "explanation": "Matches async functions"
                    }
                ],
                "error_handling": [
                    {
                        "description": "Unwrap call",
                        "pattern": "$EXPR.unwrap()",
                        "example_code": "file.read_to_string(&mut contents).unwrap()",
                        "explanation": "Finds potentially dangerous unwrap() calls"
                    },
                    {
                        "description": "Match on Result",
                        "pattern": "match $EXPR { Ok($VAL) => $$$OK, Err($ERR) => $$$ERR }",
                        "example_code": "match result { Ok(v) => v, Err(e) => panic!(e) }",
                        "explanation": "Matches Result pattern matching"
                    }
                ],
                "async": [
                    {
                        "description": "Tokio spawn",
                        "pattern": "tokio::spawn($$$ARGS)",
                        "example_code": "tokio::spawn(async move { ... })",
                        "explanation": "Matches tokio task spawning"
                    },
                    {
                        "description": "Await expression",
                        "pattern": "$EXPR.await",
                        "example_code": "client.get(url).send().await",
                        "explanation": "Matches any await expression"
                    }
                ]
            },
            "python": {
                "function": [
                    {
                        "description": "Function definition",
                        "pattern": "def $NAME($$$PARAMS):",
                        "example_code": "def calculate(x, y):",
                        "explanation": "Note the colon - required in Python patterns"
                    },
                    {
                        "description": "Method with self",
                        "pattern": "def $NAME(self, $$$PARAMS):",
                        "example_code": "def __init__(self, name, age):",
                        "explanation": "Matches class methods"
                    }
                ],
                "class": [
                    {
                        "description": "Class definition",
                        "pattern": "class $NAME:",
                        "example_code": "class Person:",
                        "explanation": "Simple class pattern"
                    },
                    {
                        "description": "Class with inheritance",
                        "pattern": "class $NAME($$$BASES):",
                        "example_code": "class Employee(Person, Serializable):",
                        "explanation": "Captures base classes"
                    }
                ]
            },
            "javascript": {
                "function": [
                    {
                        "description": "Function declaration",
                        "pattern": "function $NAME($$$PARAMS) { $$$BODY }",
                        "example_code": "function calculate(a, b) { return a + b; }",
                        "explanation": "Traditional function syntax"
                    },
                    {
                        "description": "Arrow function",
                        "pattern": "($$$PARAMS) => { $$$BODY }",
                        "example_code": "(x, y) => { return x * y; }",
                        "explanation": "Arrow function with block body"
                    },
                    {
                        "description": "Short arrow function",
                        "pattern": "($$$PARAMS) => $EXPR",
                        "example_code": "(x, y) => x + y",
                        "explanation": "Arrow function with expression body"
                    }
                ],
                "react": [
                    {
                        "description": "JSX element",
                        "pattern": "<$COMPONENT $$$PROPS />",
                        "example_code": "<Button onClick={handleClick} disabled />",
                        "explanation": "Self-closing JSX element"
                    },
                    {
                        "description": "JSX with children",
                        "pattern": "<$COMPONENT $$$PROPS>$$$CHILDREN</$COMPONENT>",
                        "example_code": "<Container className=\"main\">Content</Container>",
                        "explanation": "JSX element with children"
                    }
                ]
            }
        }
        
        # Get examples for the requested language and type
        if language in language_examples:
            if pattern_type in language_examples[language]:
                examples["examples"] = language_examples[language][pattern_type]
            else:
                # Try to find in all categories
                for category, items in language_examples[language].items():
                    if pattern_type.lower() in category.lower():
                        examples["examples"] = items
                        break
                
                if not examples["examples"]:
                    examples["success"] = False
                    examples["error"] = f"No examples found for pattern type '{pattern_type}' in {language}"
                    examples["available_types"] = list(language_examples[language].keys())
        else:
            examples["success"] = False
            examples["error"] = f"No examples available for language: {language}"
            examples["available_languages"] = list(language_examples.keys())
        
        return examples
    
    def explain_pattern(
        self,
        pattern: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Explain what a pattern does and how it matches.
        
        Args:
            pattern: The pattern to explain
            language: Programming language
            
        Returns:
            Dictionary with pattern explanation
        """
        import re
        
        explanation = {
            "pattern": pattern,
            "language": language,
            "components": [],
            "metavariables": [],
            "explanation": ""
        }
        
        # Extract metavariables
        single_vars = re.findall(r'(?<!\$)\$([A-Z][A-Z0-9_]*)(?!\$)', pattern)
        multi_vars = re.findall(r'\$\$\$([A-Z][A-Z0-9_]*)', pattern)
        
        for var in single_vars:
            explanation["metavariables"].append({
                "name": f"${var}",
                "type": "single",
                "description": f"Captures a single {self._describe_metavar(var)}"
            })
        
        for var in multi_vars:
            explanation["metavariables"].append({
                "name": f"$$${var}",
                "type": "variadic",
                "description": f"Captures zero or more {self._describe_metavar(var)}"
            })
        
        # Analyze pattern structure
        if language == "rust":
            if pattern.startswith("fn "):
                explanation["explanation"] = "Matches Rust function declarations"
                if "async" in pattern:
                    explanation["explanation"] = "Matches async Rust function declarations"
            elif "impl" in pattern:
                explanation["explanation"] = "Matches Rust impl blocks"
            elif "struct" in pattern:
                explanation["explanation"] = "Matches Rust struct definitions"
        elif language == "python":
            if pattern.startswith("def "):
                explanation["explanation"] = "Matches Python function definitions"
            elif pattern.startswith("class "):
                explanation["explanation"] = "Matches Python class definitions"
        elif language in ["javascript", "typescript"]:
            if "function" in pattern:
                explanation["explanation"] = "Matches JavaScript function declarations"
            elif "=>" in pattern:
                explanation["explanation"] = "Matches arrow functions"
            elif pattern.startswith("<") and pattern.endswith(">"):
                explanation["explanation"] = "Matches JSX/React components"
        
        # Add pattern complexity assessment
        complexity = "simple"
        if len(explanation["metavariables"]) > 3:
            complexity = "complex"
        elif len(explanation["metavariables"]) > 1:
            complexity = "moderate"
        
        explanation["complexity"] = complexity
        explanation["recommendation"] = self._get_complexity_recommendation(complexity)
        
        return explanation
    
    def _describe_metavar(self, var_name: str) -> str:
        """Get a description for a metavariable based on its name."""
        descriptions = {
            "NAME": "identifier or name",
            "FUNC": "function name",
            "METHOD": "method name",
            "VAR": "variable",
            "TYPE": "type name",
            "EXPR": "expression",
            "PARAMS": "parameters",
            "ARGS": "arguments",
            "BODY": "body statements",
            "VALUE": "value",
            "COND": "condition",
            "PATTERN": "pattern",
            "PATH": "import path",
            "MODULE": "module name"
        }
        return descriptions.get(var_name, "AST node")
    
    def _get_complexity_recommendation(self, complexity: str) -> str:
        """Get recommendation based on pattern complexity."""
        recommendations = {
            "simple": "Good starting pattern - simple patterns are more reliable",
            "moderate": "Reasonable complexity - test thoroughly with sample code",
            "complex": "Consider simplifying - complex patterns may miss edge cases"
        }
        return recommendations.get(complexity, "")


def create_pattern_guide_tools() -> PatternGuideTools:
    """Create a pattern guide tools instance."""
    return PatternGuideTools()