"""
Pattern fixer for handling common pattern issues.

This module fixes common pattern problems like metavariables that don't work
as expected (e.g., $EXPR.unwrap()).
"""

import re
from typing import List, Optional
from ..utils.common_patterns import CommonPatternLibrary


class PatternFixer:
    """Fixes common pattern issues to make them work with ast-grep."""
    
    # Known problematic patterns and their fixes
    PATTERN_FIXES = {
        # Rust patterns
        r'\$EXPR\.unwrap\(\)': ['unwrap()', '.unwrap()', '$VAR.unwrap()'],
        r'\$\.unwrap\(\)': ['unwrap()', '.unwrap()'],
        r'\$_\.unwrap\(\)': ['unwrap()', '.unwrap()'],
        r'\$EXPR\.expect\(\$MSG\)': ['expect($MSG)', '.expect($MSG)', '$VAR.expect($MSG)'],
        r'\$EXPR\.await': ['.await', '$VAR.await'],
        r'\$EXPR\?': ['$VAR?', '?'],
        
        # JavaScript/TypeScript patterns
        r'\$EXPR\.then\(\$\$\$ARGS\)': ['.then($$$ARGS)', '$VAR.then($$$ARGS)'],
        r'\$EXPR\.catch\(\$\$\$ARGS\)': ['.catch($$$ARGS)', '$VAR.catch($$$ARGS)'],
        r'await \$EXPR': ['await $VAR', 'await'],
        
        # Python patterns
        r'\$EXPR\.append\(\$ITEM\)': ['.append($ITEM)', '$VAR.append($ITEM)'],
        r'\$EXPR\[\$KEY\]': ['$VAR[$KEY]'],
    }
    
    @classmethod
    def fix_pattern(cls, pattern: str, language: str) -> List[str]:
        """
        Fix a potentially problematic pattern by generating alternatives.
        
        Args:
            pattern: The original pattern
            language: Programming language
            
        Returns:
            List of alternative patterns to try (including the original)
        """
        alternatives = [pattern]  # Always include the original
        
        # Check if it's a known problematic pattern
        for problematic, fixes in cls.PATTERN_FIXES.items():
            if re.match(problematic, pattern):
                alternatives.extend(fixes)
                break
        
        # Additional heuristics for common issues
        
        # Issue: $EXPR in method calls often doesn't work
        if language == "rust" and "." in pattern:
            # Try without the $EXPR prefix
            if pattern.startswith("$EXPR."):
                simplified = pattern[6:]  # Remove "$EXPR."
                alternatives.append(simplified)
                alternatives.append("." + simplified)
            elif pattern.startswith("$VAR."):
                simplified = pattern[5:]  # Remove "$VAR."
                alternatives.append(simplified)
                alternatives.append("." + simplified)
        
        # Issue: Complex metavariable patterns
        if "$$" in pattern and "$$$" not in pattern:
            # Convert $$ to $$$ for variadic
            alternatives.append(pattern.replace("$$", "$$$"))
        
        # Issue: Specific function names might need metavariables
        if language == "rust":
            # For patterns like "spawn(async move { ... })"
            if "spawn" in pattern and ("async" in pattern or "{" in pattern):
                # Handle various spawn patterns with nested blocks
                alternatives.extend([
                    "spawn($$$ARGS)",  # Most general - catches everything
                    "spawn(async { $$$BODY })",
                    "spawn(async move { $$$BODY })",
                    "tokio::spawn($$$ARGS)",
                    "tokio::spawn(async { $$$BODY })",
                    "tokio::spawn(async move { $$$BODY })",
                ])
                
                # Also add pattern without the block for simpler matching
                if "async move {" in pattern and "$$BODY" in pattern:
                    # User tried nested pattern, suggest simpler alternatives
                    alternatives.extend([
                        "spawn(async move { $_ })",  # Match any single expression
                        "spawn(async move { $$$_ })",  # Match any statements
                        pattern.replace("$$BODY", "$$$BODY"),  # Fix variadic
                    ])
            
            # For patterns like "fn name(...) { ... }"
            if re.match(r'^fn \w+\(', pattern):
                # Extract function name
                match = re.match(r'^fn (\w+)', pattern)
                if match:
                    func_name = match.group(1)
                    alternatives.extend([
                        f"fn {func_name}",
                        f"fn {func_name}($$$PARAMS)",
                        f"fn {func_name}($$$PARAMS) {{ $$$BODY }}",
                        "fn $NAME",
                    ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_alternatives = []
        for alt in alternatives:
            if alt not in seen:
                seen.add(alt)
                unique_alternatives.append(alt)
        
        return unique_alternatives
    
    @classmethod
    def suggest_working_pattern(cls, pattern: str, language: str) -> Optional[str]:
        """
        Suggest a pattern that's known to work for the intended search.
        
        Args:
            pattern: The problematic pattern
            language: Programming language
            
        Returns:
            A suggested pattern that should work, or None
        """
        # Look for common patterns in our library that might match the intent
        library = CommonPatternLibrary()
        
        # Try to understand the intent
        intent_keywords = []
        
        if language == "rust":
            if "unwrap" in pattern:
                intent_keywords.append("unwrap")
            if "expect" in pattern:
                intent_keywords.append("expect")
            if "await" in pattern:
                intent_keywords.append("await")
            if "spawn" in pattern:
                intent_keywords.append("spawn")
            if "?" in pattern:
                intent_keywords.append("error handling")
                
        elif language in ["javascript", "typescript"]:
            if "await" in pattern:
                intent_keywords.append("await")
            if "then" in pattern or "catch" in pattern:
                intent_keywords.append("promise")
            if "=>" in pattern:
                intent_keywords.append("arrow")
                
        elif language == "python":
            if "async def" in pattern:
                intent_keywords.append("async")
            if "try" in pattern or "except" in pattern:
                intent_keywords.append("except")
        
        # Find matching patterns from library
        for keyword in intent_keywords:
            patterns = library.search_patterns(language, keyword)
            if patterns:
                # Return the first matching pattern
                return patterns[0].pattern
        
        return None
    
    @classmethod
    def explain_pattern_issue(cls, pattern: str, language: str) -> str:
        """
        Explain why a pattern might not be working.
        
        Args:
            pattern: The problematic pattern
            language: Programming language
            
        Returns:
            Explanation of the issue
        """
        explanations = []
        
        # Check for common issues
        if "$EXPR" in pattern:
            explanations.append(
                "- $EXPR is often too generic. Try using $VAR or removing the metavariable entirely"
            )
        
        if pattern.startswith("$") and "." in pattern:
            explanations.append(
                "- Metavariables at the start of method chains often fail. Try starting with the method call (e.g., '.unwrap()' instead of '$EXPR.unwrap()')"
            )
        
        if "$$" in pattern and "$$$" not in pattern:
            explanations.append(
                "- Use $$$ for capturing multiple items (variadic), not $$"
            )
        
        if language == "rust":
            if pattern == "fn $FUNC($$PARAMS) { $$BODY }":
                explanations.append(
                    "- Complex function patterns often fail. Try simpler patterns like 'fn $NAME' or 'fn $NAME($$$PARAMS)'"
                )
            
            if "async move {" in pattern and "$" not in pattern:
                explanations.append(
                    "- Literal block patterns are too specific. Try 'spawn($$$ARGS)' or 'async move { $$$BODY }'"
                )
        
        if not explanations:
            explanations.append(
                "- The pattern syntax might be too specific. Try simpler patterns or use our common pattern library"
            )
        
        return "\n".join(explanations)


class FuzzyPatternMatcher:
    """Provides fuzzy pattern matching capabilities."""
    
    @classmethod
    def make_pattern_fuzzy(cls, pattern: str, language: str) -> List[str]:
        """
        Make a pattern more fuzzy/forgiving by generating variations.
        
        Args:
            pattern: The original pattern
            language: Programming language
            
        Returns:
            List of fuzzy pattern variations
        """
        variations = [pattern]
        
        # For Rust
        if language == "rust":
            # Handle async variations
            if "async fn" in pattern:
                # Add with/without visibility modifiers
                if not pattern.startswith("pub "):
                    variations.append(f"pub {pattern}")
                if "pub " in pattern:
                    variations.append(pattern.replace("pub ", ""))
                    
            # Handle spawn variations
            if pattern == "spawn(async)":
                variations.extend([
                    "spawn($$$ARGS)",
                    "spawn(async { $$$BODY })",
                    "spawn(async move { $$$BODY })",
                    "tokio::spawn($$$ARGS)",
                    "tokio::spawn(async { $$$BODY })",
                    "tokio::spawn(async move { $$$BODY })",
                ])
                
            # Handle method calls
            if "." in pattern and not pattern.startswith("."):
                # Add version starting with dot
                variations.append("." + pattern.split(".", 1)[1])
        
        # For JavaScript/TypeScript
        elif language in ["javascript", "typescript"]:
            # Handle function variations
            if "function" in pattern:
                # Add arrow function equivalent
                if "async function" in pattern:
                    name_match = re.search(r'async function (\w+)', pattern)
                    if name_match:
                        name = name_match.group(1)
                        variations.append(f"const {name} = async ($$$PARAMS) => $$$BODY")
                else:
                    name_match = re.search(r'function (\w+)', pattern)
                    if name_match:
                        name = name_match.group(1)
                        variations.append(f"const {name} = ($$$PARAMS) => $$$BODY")
        
        # Remove duplicates
        return list(dict.fromkeys(variations))
    
    @classmethod
    def expand_pattern(cls, pattern: str, language: str) -> List[str]:
        """
        Expand a pattern to match more variations.
        
        For example, 'unwrap' could expand to match unwrap(), unwrap_or(), etc.
        
        Args:
            pattern: The original pattern
            language: Programming language
            
        Returns:
            List of expanded patterns
        """
        expansions = [pattern]
        
        if language == "rust":
            # Expand unwrap to related methods
            if pattern == "unwrap":
                expansions.extend([
                    "unwrap()",
                    "unwrap_or($DEFAULT)",
                    "unwrap_or_else($CLOSURE)",
                    "unwrap_or_default()",
                ])
            
            # Expand error handling
            elif pattern == "error handling":
                expansions.extend([
                    "unwrap()",
                    "expect($MSG)",
                    "$EXPR?",
                    "match $RESULT { Ok($VAL) => $OK, Err($ERR) => $ERR_BODY }",
                ])
                
        return expansions