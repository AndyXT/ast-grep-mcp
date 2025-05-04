"""
Pattern suggestion system for ast-grep-mcp.

This module provides functionality to suggest alternative patterns
when a pattern doesn't match or yields unexpected results.
"""

from typing import Dict, List, Tuple
import re
import logging
from ..language_handlers import get_handler

logger = logging.getLogger("ast_grep_mcp.pattern_suggestions")

def get_pattern_variants(pattern: str) -> List[str]:
    """
    Generate simpler variants of a pattern by:
    - Removing nested structures
    - Replacing specific identifiers with wildcards
    - Relaxing type constraints
    - Simplifying complex patterns
    
    Args:
        pattern: The original pattern that didn't match
        
    Returns:
        List of alternative patterns to try
    """
    variants = []
    
    # Replace specific identifiers with wildcards
    var_pattern = re.compile(r'\$([A-Z_][A-Z0-9_]*)')
    var_matches = list(var_pattern.finditer(pattern))
    
    # If pattern has variables, create variants with wildcards
    if var_matches:
        for match in var_matches:
            # Replace specific variables with generic wildcards
            variant = pattern[:match.start()] + "$_" + pattern[match.end():]
            variants.append(variant)
    
    # Remove specific variable names in triple-$ patterns
    triple_var_pattern = re.compile(r'\$\$\$([A-Z_][A-Z0-9_]*)')
    if triple_var_pattern.search(pattern):
        variant = triple_var_pattern.sub("$$$_", pattern)
        variants.append(variant)
    
    # Simplify nested structures (remove content inside {})
    brace_pattern = re.compile(r'(\{[^{}]*\})')
    if brace_pattern.search(pattern):
        variant = brace_pattern.sub("{$$$_}", pattern)
        variants.append(variant)
    
    # Remove optional parts (parts that can be absent in some cases)
    optional_pattern = re.compile(r'\?[^:]*:')
    if optional_pattern.search(pattern):
        variant = optional_pattern.sub("", pattern)
        variants.append(variant)
    
    # Handle parentheses structures (function calls, etc.)
    paren_pattern = re.compile(r'\([^()]*\)')
    if paren_pattern.search(pattern):
        variant = paren_pattern.sub("($$$_)", pattern)
        variants.append(variant)
    
    # For function definitions, try with any params
    if pattern.startswith("def ") and "(" in pattern:
        variant = re.sub(r'\([^)]*\)', "($$$_)", pattern)
        variants.append(variant)
    
    # For class definitions, try without base classes
    if pattern.startswith("class ") and "(" in pattern:
        variant = re.sub(r'\([^)]*\)', "", pattern)
        variants.append(variant)
    
    # For multi-line patterns, extract just the first line
    if "\n" in pattern:
        first_line = pattern.split("\n")[0]
        variants.append(first_line)
    
    # Convert JavaScript-style syntax to Python-style
    js_function_pattern = re.compile(r'(function\s+\w+\s*\([^)]*\))\s*\{')
    js_func_match = js_function_pattern.search(pattern)
    if js_func_match:
        # Convert "function name() {" to "function name():"
        python_variant = js_func_match.group(1) + ":"
        variants.append(python_variant)
    
    # Convert JavaScript-style method/function to Python-style
    js_method_pattern = re.compile(r'(\w+\s*\([^)]*\))\s*\{')
    js_method_match = js_method_pattern.search(pattern)
    if js_method_match:
        # Convert "name() {" to "name():"
        python_variant = js_method_match.group(1) + ":"
        variants.append(python_variant)
    
    # Convert brace to colon (generic case)
    if "{" in pattern and ":" not in pattern:
        variant = pattern.replace("{", ":")
        variants.append(variant)
        # Also try removing the closing brace if it exists
        if "}" in variant:
            variant = variant.replace("}", "")
            variants.append(variant)
    
    # Direct conversion from JavaScript/C-style to Python-style
    if "def " in pattern and "{" in pattern:
        variant = pattern.replace("{", ":")
        if "}" in variant:
            variant = variant.replace("}", "")
        variants.append(variant)
    
    # If we have no variants yet, try a more generic approach
    if not variants:
        # Try to extract just the core structure
        if ":" in pattern and not pattern.endswith(":"):
            # For complex patterns with colons, keep everything before the colon + colon
            variant = pattern.split(":", 1)[0] + ":"
            variants.append(variant)
    
    # Remove duplicates and the original pattern
    unique_variants = [v for v in variants if v != pattern]
    
    return unique_variants

def get_similar_patterns(pattern: str, language: str) -> List[Tuple[str, str]]:
    """
    Find similar patterns in the pattern library for the given language.
    
    Args:
        pattern: The original pattern
        language: The language to find patterns for
        
    Returns:
        List of (pattern_name, pattern) tuples that are similar to the input pattern
    """
    handler = get_handler(language)
    if not handler:
        return []
    
    patterns = handler.get_default_patterns()
    
    # No patterns available for this language
    if not patterns:
        return []
    
    # Calculate similarity scores using simple heuristics
    similar_patterns = []
    
    # Tokenize the input pattern (split on spaces, newlines, parens, etc.)
    pattern_tokens = re.findall(r'[$\w]+|[^\s\w]', pattern)
    pattern_keywords = [token for token in pattern_tokens if not token.startswith('$')]
    
    for name, lib_pattern in patterns.items():
        # Simple scoring: count common tokens
        lib_tokens = re.findall(r'[$\w]+|[^\s\w]', lib_pattern)
        lib_keywords = [token for token in lib_tokens if not token.startswith('$')]
        
        # Count common non-variable tokens
        common_tokens = set(pattern_keywords).intersection(lib_keywords)
        
        # If they share significant tokens, consider it similar
        if len(common_tokens) >= 1 and len(common_tokens) >= len(pattern_keywords) / 2:
            similar_patterns.append((name, lib_pattern))
    
    # Sort by similarity (currently just by the number of matching tokens)
    similar_patterns.sort(key=lambda x: len(set(re.findall(r'[$\w]+|[^\s\w]', x[1])).intersection(
                                            set(re.findall(r'[$\w]+|[^\s\w]', pattern)))),
                           reverse=True)
    
    # Return top 3 similar patterns
    return similar_patterns[:3]

def suggest_patterns(pattern: str, code: str, language: str) -> Dict[str, List[str]]:
    """
    Suggest alternative patterns when a pattern doesn't match.
    
    Args:
        pattern: The original pattern that didn't match
        code: The code being analyzed
        language: The language of the code
        
    Returns:
        Dictionary with suggestion categories and lists of patterns
    """
    suggestions = {
        "variants": [],
        "similar_patterns": [],
        "examples": []
    }
    
    # Get pattern variants
    variants = get_pattern_variants(pattern)
    suggestions["variants"] = variants
    
    # Get similar patterns from the library
    similar = get_similar_patterns(pattern, language)
    suggestions["similar_patterns"] = [f"{name}: {pattern}" for name, pattern in similar]
    
    # Get example patterns for this language
    handler = get_handler(language)
    if handler:
        # Select a few representative examples
        examples = list(handler.get_default_patterns().items())
        
        # Get at most 3 examples spread across the examples list
        if examples:
            if len(examples) <= 3:
                examples_sample = [item[1] for item in examples]
            else:
                step = max(1, len(examples) // 3)
                indices = [0, min(step, len(examples)-1), min(2*step, len(examples)-1)]
                examples_sample = [examples[i][1] for i in indices]
            
            suggestions["examples"] = examples_sample
    
    return suggestions

def build_suggestion_message(pattern: str, language: str, suggestions: Dict[str, List[str]]) -> str:
    """
    Build a user-friendly message with pattern suggestions.
    
    Args:
        pattern: The original pattern
        language: The language being used
        suggestions: Dictionary of suggestions
        
    Returns:
        Formatted message with suggestions
    """
    message = [f"No matches found for pattern '{pattern}' in {language} code."]
    
    if suggestions["variants"]:
        message.append("\nDid you mean:")
        for i, variant in enumerate(suggestions["variants"][:3], 1):
            message.append(f"  {i}. {variant}")
    
    if suggestions["similar_patterns"]:
        message.append("\nSimilar patterns from library:")
        for i, pattern_desc in enumerate(suggestions["similar_patterns"][:3], 1):
            message.append(f"  {i}. {pattern_desc}")
    
    if suggestions["examples"]:
        message.append("\nExample patterns for this language:")
        for i, example in enumerate(suggestions["examples"][:3], 1):
            message.append(f"  {i}. {example}")
    
    message.append("\nPattern writing tips:")
    message.append("  - Use $VAR to match a single expression/identifier")
    message.append("  - Use $$$VAR to match multiple expressions/statements")
    message.append("  - Make sure your pattern follows the language syntax")
    message.append("  - Try matching smaller code fragments first")
    
    return "\n".join(message) 