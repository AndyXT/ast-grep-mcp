"""
Simplified pattern builder for common AST patterns.

This module provides a fluent API for building AST patterns without
needing to know the exact syntax.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class SimplePatternBuilder:
    """A simplified, fluent API for building AST patterns."""
    
    language: str
    _pattern_parts: List[str] = field(default_factory=list)
    _current_context: str = ""
    
    def function(self, name: Optional[str] = None) -> "SimplePatternBuilder":
        """Start building a function pattern."""
        self._current_context = "function"
        if self.language == "rust":
            name_part = name if name else "$NAME"
            self._pattern_parts = [f"fn {name_part}"]
        elif self.language == "python":
            name_part = name if name else "$NAME"
            self._pattern_parts = [f"def {name_part}"]
        elif self.language in ["javascript", "typescript"]:
            name_part = name if name else "$NAME"
            self._pattern_parts = [f"function {name_part}"]
        return self
    
    def async_function(self, name: Optional[str] = None) -> "SimplePatternBuilder":
        """Start building an async function pattern."""
        self._current_context = "async_function"
        if self.language == "rust":
            name_part = name if name else "$NAME"
            self._pattern_parts = [f"async fn {name_part}"]
        elif self.language == "python":
            name_part = name if name else "$NAME"
            self._pattern_parts = [f"async def {name_part}"]
        elif self.language in ["javascript", "typescript"]:
            name_part = name if name else "$NAME"
            self._pattern_parts = [f"async function {name_part}"]
        return self
    
    def with_params(self, params: Optional[str] = None) -> "SimplePatternBuilder":
        """Add parameters to a function."""
        if self._current_context not in ["function", "async_function", "method"]:
            raise ValueError("with_params() can only be used after function() or method()")
        
        param_part = params if params else "$$$PARAMS"
        self._pattern_parts.append(f"({param_part})")
        return self
    
    def with_body(self, body: Optional[str] = None) -> "SimplePatternBuilder":
        """Add body to a function or block."""
        body_part = body if body else "$$$BODY"
        
        if self.language == "python":
            self._pattern_parts.append(f":\n    {body_part}")
        else:
            self._pattern_parts.append(f" {{ {body_part} }}")
        return self
    
    def returns(self, return_type: str) -> "SimplePatternBuilder":
        """Add return type (for typed languages)."""
        if self.language == "rust":
            # Insert before body if exists
            if self._pattern_parts and "{" in self._pattern_parts[-1]:
                body = self._pattern_parts.pop()
                self._pattern_parts.append(f" -> {return_type}")
                self._pattern_parts.append(body)
            else:
                self._pattern_parts.append(f" -> {return_type}")
        elif self.language == "typescript":
            # Insert after params
            for i, part in enumerate(self._pattern_parts):
                if ")" in part and i < len(self._pattern_parts) - 1:
                    self._pattern_parts.insert(i + 1, f": {return_type}")
                    break
        elif self.language == "python":
            # Python type hints
            for i, part in enumerate(self._pattern_parts):
                if ")" in part:
                    self._pattern_parts[i] = part.rstrip(")") + f") -> {return_type}"
                    break
        return self
    
    def method_call(self, object_name: Optional[str] = None, 
                   method: Optional[str] = None) -> "SimplePatternBuilder":
        """Build a method call pattern."""
        obj = object_name if object_name else "$OBJ"
        meth = method if method else "$METHOD"
        self._pattern_parts = [f"{obj}.{meth}($$$ARGS)"]
        self._current_context = "method_call"
        return self
    
    def unwrap_call(self) -> "SimplePatternBuilder":
        """Build an unwrap call pattern (Rust)."""
        if self.language == "rust":
            # Use the simplest pattern that works
            self._pattern_parts = ["unwrap()"]
        return self
    
    def spawn_call(self, with_block: bool = False) -> "SimplePatternBuilder":
        """Build a spawn call pattern (Rust)."""
        if self.language == "rust":
            if with_block:
                self._pattern_parts = ["spawn(async move { $$$BODY })"]
            else:
                # Use the general pattern that actually works
                self._pattern_parts = ["spawn($$$ARGS)"]
        return self
    
    def if_statement(self, condition: Optional[str] = None) -> "SimplePatternBuilder":
        """Build an if statement pattern."""
        cond = condition if condition else "$COND"
        
        if self.language == "python":
            self._pattern_parts = [f"if {cond}:"]
        elif self.language in ["rust", "javascript", "typescript", "c", "go"]:
            self._pattern_parts = [f"if {cond} {{"]
        
        self._current_context = "if_statement"
        return self
    
    def match_expr(self, expr: Optional[str] = None) -> "SimplePatternBuilder":
        """Build a match expression pattern (Rust)."""
        if self.language == "rust":
            match_expr = expr if expr else "$EXPR"
            self._pattern_parts = [f"match {match_expr} {{ $$$ARMS }}"]
        return self
    
    def try_block(self) -> "SimplePatternBuilder":
        """Build a try block pattern."""
        if self.language == "python":
            self._pattern_parts = ["try:\n    $$$TRY\nexcept $EXCEPTION:\n    $$$EXCEPT"]
        elif self.language in ["javascript", "typescript"]:
            self._pattern_parts = ["try { $$$TRY } catch ($ERR) { $$$CATCH }"]
        return self
    
    def import_statement(self, module: Optional[str] = None) -> "SimplePatternBuilder":
        """Build an import statement pattern."""
        if self.language == "python":
            mod = module if module else "$MODULE"
            self._pattern_parts = [f"import {mod}"]
        elif self.language in ["javascript", "typescript"]:
            mod = module if module else "$MODULE"
            self._pattern_parts = [f"import $$$IMPORTS from '{mod}'"]
        elif self.language == "rust":
            mod = module if module else "$MODULE"
            self._pattern_parts = [f"use {mod}"]
        return self
    
    def any_of(self, *patterns: str) -> "SimplePatternBuilder":
        """Match any of the given patterns."""
        # This would need special handling in ast-grep
        # For now, return the first pattern as a fallback
        if patterns:
            self._pattern_parts = [patterns[0]]
        return self
    
    def build(self) -> str:
        """Build the final pattern string."""
        return "".join(self._pattern_parts)
    
    def build_with_alternatives(self) -> List[str]:
        """Build pattern with common alternatives."""
        base_pattern = self.build()
        alternatives = [base_pattern]
        
        # Add common alternatives based on pattern type
        if self._current_context == "function" and self.language == "rust":
            # Add public variant
            if not base_pattern.startswith("pub "):
                alternatives.append(f"pub {base_pattern}")
        
        elif self._current_context == "async_function" and self.language == "rust":
            # Add public variant
            if not base_pattern.startswith("pub "):
                alternatives.append(f"pub {base_pattern}")
        
        return alternatives
    
    @classmethod
    def from_example(cls, example: str, language: str) -> str:
        """
        Create a pattern from an example code snippet.
        
        This is a simple implementation that replaces literals with metavariables.
        """
        import re
        
        pattern = example
        
        # Replace string literals
        pattern = re.sub(r'"[^"]*"', '$STRING', pattern)
        pattern = re.sub(r"'[^']*'", '$STRING', pattern)
        
        # Replace numbers
        pattern = re.sub(r'\b\d+\b', '$NUMBER', pattern)
        
        # Replace identifiers in common positions
        if language == "rust":
            # Function names
            pattern = re.sub(r'\bfn\s+(\w+)', 'fn $NAME', pattern)
            # Variable names in let statements
            pattern = re.sub(r'\blet\s+(\w+)', 'let $VAR', pattern)
            pattern = re.sub(r'\blet\s+mut\s+(\w+)', 'let mut $VAR', pattern)
        
        elif language == "python":
            # Function names
            pattern = re.sub(r'\bdef\s+(\w+)', 'def $NAME', pattern)
            # Variable assignments
            pattern = re.sub(r'^(\w+)\s*=', '$VAR =', pattern, flags=re.MULTILINE)
        
        elif language in ["javascript", "typescript"]:
            # Function names
            pattern = re.sub(r'\bfunction\s+(\w+)', 'function $NAME', pattern)
            # Variable declarations
            pattern = re.sub(r'\b(let|const|var)\s+(\w+)', r'\1 $VAR', pattern)
        
        return pattern


def create_pattern_for_concept(concept: str, language: str) -> Dict[str, Any]:
    """
    Create patterns for high-level concepts.
    
    Args:
        concept: High-level concept like "error handling", "async code", etc.
        language: Programming language
        
    Returns:
        Dictionary with pattern info and alternatives
    """
    builder = SimplePatternBuilder(language)
    
    concept_lower = concept.lower()
    patterns = []
    confidence = 0.8
    
    # CRITICAL FIX: Add much more comprehensive pattern matching
    
    # Generic function patterns
    if any(word in concept_lower for word in ["function", "fn", "def", "method"]):
        if language == "rust":
            patterns.extend([
                "fn $NAME($$$ARGS)",
                "pub fn $NAME($$$ARGS)",
                "async fn $NAME($$$ARGS)",
                "pub async fn $NAME($$$ARGS)"
            ])
        elif language == "python":
            patterns.extend([
                "def $NAME($$$ARGS)",
                "async def $NAME($$$ARGS)"
            ])
        elif language in ["javascript", "typescript"]:
            patterns.extend([
                "function $NAME($$$ARGS)",
                "async function $NAME($$$ARGS)",
                "const $NAME = ($$$ARGS) => $$$BODY",
                "const $NAME = async ($$$ARGS) => $$$BODY"
            ])
    
    # Database/connection patterns
    elif any(word in concept_lower for word in ["database", "connection", "connect", "db"]):
        if language == "rust":
            patterns.extend([
                "$VAR.connect($$$ARGS)",
                "async fn connect($$$ARGS)",
                "Connection::new($$$ARGS)",
                "$DB::connect($$$ARGS)",
                ".execute($$$ARGS)",
                ".query($$$ARGS)"
            ])
        elif language == "python":
            patterns.extend([
                "connect($$$ARGS)",
                "async def connect($$$ARGS)",
                ".connect($$$ARGS)",
                ".execute($$$ARGS)",
                ".query($$$ARGS)"
            ])
        elif language in ["javascript", "typescript"]:
            patterns.extend([
                "connect($$$ARGS)",
                "async function connect($$$ARGS)",
                ".connect($$$ARGS)",
                "new Connection($$$ARGS)",
                ".query($$$ARGS)"
            ])
    
    # Error handling patterns
    elif any(word in concept_lower for word in ["error", "exception", "try", "catch"]):
        if language == "rust":
            patterns.extend([
                "unwrap()",
                "expect($MSG)",
                "$EXPR?",
                "match $RESULT { Ok($VAL) => $OK, Err($ERR) => $ERR_BODY }",
                "Result<$OK, $ERR>"
            ])
        elif language == "python":
            patterns.extend([
                "try:\n    $$$TRY\nexcept $EXCEPTION:\n    $$$EXCEPT",
                "except $EXCEPTION:",
                "raise $EXCEPTION"
            ])
        elif language in ["javascript", "typescript"]:
            patterns.extend([
                "try { $$$TRY } catch ($ERR) { $$$CATCH }",
                "catch ($ERR)",
                "throw new Error($MSG)"
            ])
    
    # Async patterns
    elif any(word in concept_lower for word in ["async", "await", "promise"]):
        if language == "rust":
            patterns.extend([
                "async fn $NAME($$$ARGS)",
                "$EXPR.await",
                "spawn($$$ARGS)",
                "async move { $$$BODY }"
            ])
        elif language == "python":
            patterns.extend([
                "async def $NAME($$$ARGS)",
                "await $EXPR",
                "asyncio.$METHOD($$$ARGS)"
            ])
        elif language in ["javascript", "typescript"]:
            patterns.extend([
                "async function $NAME($$$ARGS)",
                "await $EXPR",
                "$PROMISE.then($$$ARGS)",
                "new Promise(($RESOLVE, $REJECT) => { $$$BODY })"
            ])
    
    # Specific language patterns based on concept
    if language == "rust":
        if "spawn" in concept_lower:
            patterns.extend([
                builder.spawn_call(with_block=False).build(),
                builder.spawn_call(with_block=True).build(),
            ])
        
        elif "unwrap" in concept_lower:
            patterns.append(builder.unwrap_call().build())
    
    # If no specific patterns found, provide generic search patterns
    if not patterns:
        # Extract key words from concept and create simple patterns
        words = [word.strip() for word in concept_lower.split() if len(word.strip()) > 2]
        for word in words[:3]:  # Use first 3 meaningful words
            patterns.extend([
                f"$OBJ.{word}($$$ARGS)",  # Method call
                f"{word}($$$ARGS)",        # Function call
                f"fn {word}($$$ARGS)" if language == "rust" else f"def {word}($$$ARGS)" if language == "python" else f"function {word}($$$ARGS)"
            ])
        confidence = 0.5  # Lower confidence for generic patterns
    
    return {
        "concept": concept,
        "language": language,
        "patterns": patterns,
        "confidence": confidence,
        "usage": f"Use these patterns to find {concept} in {language} code",
        "total_patterns": len(patterns)
    }