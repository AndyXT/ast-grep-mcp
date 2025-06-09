"""
Pattern simplification utility for handling complex patterns.

This module provides functionality to simplify complex patterns that may fail
and suggest simpler alternatives that are more likely to work.
"""

import re
from typing import List, Dict, Tuple
import logging


class PatternSimplifier:
    """Simplifies complex patterns and provides alternatives."""
    
    def __init__(self):
        self.logger = logging.getLogger("ast_grep_mcp.pattern_simplifier")
        
        # Pattern complexity indicators
        self.complexity_patterns = {
            # Multiple metavariables in one pattern
            r'\$\w+.*\$\$\$\w+.*\$\$\$\w+': 'multiple_complex_metavars',
            # Function with params and body
            r'(fn|function|def)\s+\$\w+\s*\([^)]*\$\$\$\w+[^)]*\)\s*[{:]?\s*\$\$\$\w+': 'function_with_params_and_body',
            # Complex async patterns
            r'async\s+(fn|function)\s+\$\w+\s*\([^)]*\)\s*.*\{.*\}': 'complex_async_function',
            # Nested structures
            r'\{[^}]*\{[^}]*\}[^}]*\}': 'nested_braces',
            # Complex class patterns
            r'(class|struct)\s+\$\w+.*\{.*\$\$\$\w+.*\}': 'class_with_body',
        }
        
        # Simplification strategies by language
        self.simplification_strategies = {
            'rust': {
                'function_with_params_and_body': [
                    ('fn $NAME($$$PARAMS) { $$$BODY }', 'fn $NAME'),
                    ('async fn $NAME($$$PARAMS) { $$$BODY }', 'async fn $NAME'),
                    ('pub fn $NAME($$$PARAMS) { $$$BODY }', 'pub fn $NAME'),
                    ('pub async fn $NAME($$$PARAMS) { $$$BODY }', 'pub async fn $NAME'),
                ],
                'complex_async_function': [
                    ('async fn $NAME($$$) { $$$$ }', 'async fn $NAME'),
                    ('async { $$$$ }', 'async'),
                ],
                'suggestions': [
                    'For Rust functions, try: fn $NAME',
                    'For async functions: async fn $NAME',
                    'For trait implementations: impl $TRAIT for $TYPE',
                    'For match expressions: match $EXPR',
                ]
            },
            'javascript': {
                'function_with_params_and_body': [
                    ('function $NAME($$$PARAMS) { $$$BODY }', 'function $NAME'),
                    ('const $NAME = ($$$PARAMS) => { $$$BODY }', 'const $NAME = '),
                    ('async function $NAME($$$PARAMS) { $$$BODY }', 'async function $NAME'),
                ],
                'suggestions': [
                    'For functions: function $NAME',
                    'For arrow functions: const $NAME =',
                    'For async functions: async function $NAME',
                    'For classes: class $NAME',
                ]
            },
            'python': {
                'function_with_params_and_body': [
                    ('def $NAME($$$PARAMS): $$$BODY', 'def $NAME'),
                    ('async def $NAME($$$PARAMS): $$$BODY', 'async def $NAME'),
                    ('def $NAME($$$PARAMS):', 'def $NAME'),
                ],
                'class_with_body': [
                    ('class $NAME: $$$BODY', 'class $NAME:'),
                    ('class $NAME($BASE): $$$BODY', 'class $NAME'),
                ],
                'suggestions': [
                    'For functions: def $NAME',
                    'For async functions: async def $NAME',
                    'For classes: class $NAME:',
                    'For decorators: @$DECORATOR',
                ]
            },
            'go': {
                'function_with_params_and_body': [
                    ('func $NAME($$$PARAMS) $RETURN { $$$BODY }', 'func $NAME'),
                    ('func ($RECV) $NAME($$$PARAMS) { $$$BODY }', 'func $NAME'),
                ],
                'suggestions': [
                    'For functions: func $NAME',
                    'For methods: func ($RECV) $NAME',
                    'For structs: type $NAME struct',
                    'For interfaces: type $NAME interface',
                ]
            }
        }
    
    def analyze_complexity(self, pattern: str) -> List[str]:
        """
        Analyze pattern complexity and identify issues.
        
        Args:
            pattern: The pattern to analyze
            
        Returns:
            List of complexity issues found
        """
        issues = []
        
        for regex, issue_type in self.complexity_patterns.items():
            if re.search(regex, pattern, re.IGNORECASE):
                issues.append(issue_type)
        
        # Additional checks
        metavar_count = len(re.findall(r'\$+\w+', pattern))
        if metavar_count > 3:
            issues.append('too_many_metavars')
        
        # Check for unbalanced delimiters
        if pattern.count('(') != pattern.count(')'):
            issues.append('unbalanced_parentheses')
        if pattern.count('{') != pattern.count('}'):
            issues.append('unbalanced_braces')
        if pattern.count('[') != pattern.count(']'):
            issues.append('unbalanced_brackets')
        
        return issues
    
    def simplify_pattern(self, pattern: str, language: str) -> List[Tuple[str, str]]:
        """
        Simplify a complex pattern and provide alternatives.
        
        Args:
            pattern: The complex pattern
            language: The programming language
            
        Returns:
            List of (simplified_pattern, description) tuples
        """
        simplified = []
        issues = self.analyze_complexity(pattern)
        
        if not issues:
            return [(pattern, "Pattern appears simple enough")]
        
        # Get language-specific simplifications
        lang_strategies = self.simplification_strategies.get(language, {})
        
        # Apply simplification strategies based on issues
        for issue in issues:
            if issue in lang_strategies:
                for complex_pattern, simple_pattern in lang_strategies[issue]:
                    if self._pattern_matches_template(pattern, complex_pattern):
                        simplified.append((
                            simple_pattern,
                            f"Simplified from: {complex_pattern}"
                        ))
        
        # If no specific simplifications found, try generic ones
        if not simplified:
            simplified.extend(self._generic_simplifications(pattern, language))
        
        # Add language-specific suggestions
        if 'suggestions' in lang_strategies:
            for suggestion in lang_strategies['suggestions']:
                simplified.append((suggestion, "Common pattern suggestion"))
        
        return simplified
    
    def _pattern_matches_template(self, pattern: str, template: str) -> bool:
        """Check if a pattern roughly matches a template."""
        # Convert template to regex pattern
        regex_pattern = re.escape(template)
        regex_pattern = regex_pattern.replace(r'\$NAME', r'\$\w+')
        regex_pattern = regex_pattern.replace(r'\$\$\$PARAMS', r'.*?')
        regex_pattern = regex_pattern.replace(r'\$\$\$BODY', r'.*?')
        regex_pattern = regex_pattern.replace(r'\$\$\$\w+', r'.*?')
        regex_pattern = regex_pattern.replace(r'\$\w+', r'\$\w+')
        
        return bool(re.search(regex_pattern, pattern, re.IGNORECASE | re.DOTALL))
    
    def _generic_simplifications(self, pattern: str, language: str) -> List[Tuple[str, str]]:
        """Apply generic simplification strategies."""
        simplified = []
        
        # Extract the main construct (function, class, etc.)
        main_constructs = {
            'rust': ['fn', 'async fn', 'impl', 'struct', 'trait'],
            'javascript': ['function', 'class', 'const', 'let', 'var'],
            'python': ['def', 'class', 'async def'],
            'go': ['func', 'type', 'interface'],
            'c': ['void', 'int', 'struct', 'typedef'],
        }
        
        constructs = main_constructs.get(language, [])
        
        for construct in constructs:
            if construct in pattern:
                # Try to extract metavariable after construct
                match = re.search(rf'{construct}\s+(\$\w+)', pattern)
                if match:
                    simple = f"{construct} {match.group(1)}"
                    simplified.append((simple, f"Simplified to basic {construct} pattern"))
        
        # If pattern has multiple metavariables, suggest using just the first
        metavars = re.findall(r'\$\w+', pattern)
        if len(metavars) > 1:
            first_metavar = metavars[0]
            simplified.append((first_metavar, "Use just the primary metavariable"))
        
        # Remove complex body/parameter patterns
        if '$$$' in pattern:
            simple = re.sub(r'\([^)]*\$\$\$\w+[^)]*\)', '', pattern)
            simple = re.sub(r'\{[^}]*\$\$\$\w+[^}]*\}', '', simple)
            simple = simple.strip()
            if simple and simple != pattern:
                simplified.append((simple, "Removed complex parameter/body patterns"))
        
        return simplified
    
    def get_pattern_examples(self, language: str) -> Dict[str, List[str]]:
        """
        Get examples of working patterns for a language.
        
        Args:
            language: The programming language
            
        Returns:
            Dictionary of pattern categories to example patterns
        """
        examples = {
            'rust': {
                'functions': [
                    'fn $NAME',
                    'pub fn $NAME',
                    'async fn $NAME',
                    'pub async fn $NAME',
                ],
                'async': [
                    'async',
                    '$EXPR.await',
                    'tokio::spawn',
                ],
                'types': [
                    'struct $NAME',
                    'enum $NAME',
                    'impl $TYPE',
                    'impl $TRAIT for $TYPE',
                ],
                'control_flow': [
                    'match $EXPR',
                    'if let $PATTERN = $EXPR',
                    'loop',
                    'while $COND',
                ],
            },
            'javascript': {
                'functions': [
                    'function $NAME',
                    'const $NAME = function',
                    'const $NAME = () =>',
                    'async function $NAME',
                ],
                'classes': [
                    'class $NAME',
                    'class $NAME extends $BASE',
                ],
                'async': [
                    'await $EXPR',
                    'async',
                    'Promise',
                    '.then',
                ],
                'imports': [
                    'import $NAME',
                    'import { $NAME }',
                    'require($MODULE)',
                ],
            },
            'python': {
                'functions': [
                    'def $NAME',
                    'def $NAME():',
                    'async def $NAME',
                    'lambda',
                ],
                'classes': [
                    'class $NAME:',
                    'class $NAME($BASE):',
                ],
                'control_flow': [
                    'if $COND:',
                    'for $VAR in $ITER:',
                    'while $COND:',
                    'try:',
                ],
                'decorators': [
                    '@$DECORATOR',
                    '@property',
                    '@staticmethod',
                ],
            },
            'go': {
                'functions': [
                    'func $NAME',
                    'func ($RECV) $NAME',
                ],
                'types': [
                    'type $NAME struct',
                    'type $NAME interface',
                ],
                'control_flow': [
                    'if $COND',
                    'for $INIT; $COND; $POST',
                    'switch $EXPR',
                    'select',
                ],
                'concurrency': [
                    'go $FUNC',
                    'chan $TYPE',
                    '<-$CHAN',
                ],
            }
        }
        
        return examples.get(language, {})