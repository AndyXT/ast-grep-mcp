"""
Pattern builder for constructing complex AST patterns.

This module provides a fluent API for building AST patterns programmatically.
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """Types of pattern components."""
    LITERAL = "literal"
    METAVAR = "metavar"
    MULTI_METAVAR = "multi_metavar"
    ANY = "any"
    ALL = "all"
    NOT = "not"
    INSIDE = "inside"
    HAS = "has"
    FOLLOWS = "follows"
    PRECEDES = "precedes"


@dataclass
class PatternComponent:
    """Represents a component of a pattern."""
    type: PatternType
    value: Union[str, List['PatternComponent'], 'PatternComponent']
    name: Optional[str] = None
    

class PatternBuilder:
    """
    Fluent API for building AST patterns.
    
    Example:
        pattern = (PatternBuilder()
                  .function()
                  .with_name("test_*")
                  .with_decorator("pytest.mark.parametrize")
                  .build())
    """
    
    def __init__(self, language: Optional[str] = None):
        """
        Initialize the pattern builder.
        
        Args:
            language: Optional language context for language-specific patterns
        """
        self.language = language
        self.components: List[PatternComponent] = []
        self._current_context: Optional[PatternComponent] = None
        self._constraints: Dict[str, Any] = {}
        self._modifiers: List[str] = []
        
    def literal(self, text: str) -> 'PatternBuilder':
        """Add a literal text component."""
        component = PatternComponent(PatternType.LITERAL, text)
        self._add_component(component)
        return self
        
    def metavar(self, name: str) -> 'PatternBuilder':
        """Add a single metavariable."""
        component = PatternComponent(PatternType.METAVAR, f"${name}", name)
        self._add_component(component)
        return self
        
    def multi_metavar(self, name: str) -> 'PatternBuilder':
        """Add a multi-metavariable (captures multiple nodes)."""
        component = PatternComponent(PatternType.MULTI_METAVAR, f"$$${name}", name)
        self._add_component(component)
        return self
        
    def any(self, *patterns: Union[str, 'PatternBuilder']) -> 'PatternBuilder':
        """Match any of the given patterns."""
        sub_patterns = self._normalize_patterns(patterns)
        component = PatternComponent(PatternType.ANY, sub_patterns)
        self._add_component(component)
        return self
        
    def all(self, *patterns: Union[str, 'PatternBuilder']) -> 'PatternBuilder':
        """Match all of the given patterns."""
        sub_patterns = self._normalize_patterns(patterns)
        component = PatternComponent(PatternType.ALL, sub_patterns)
        self._add_component(component)
        return self
        
    def not_pattern(self, pattern: Union[str, 'PatternBuilder']) -> 'PatternBuilder':
        """Negate a pattern."""
        sub_pattern = self._normalize_pattern(pattern)
        component = PatternComponent(PatternType.NOT, sub_pattern)
        self._add_component(component)
        return self
        
    def inside(self, pattern: Union[str, 'PatternBuilder']) -> 'PatternBuilder':
        """Match only inside the given pattern."""
        sub_pattern = self._normalize_pattern(pattern)
        component = PatternComponent(PatternType.INSIDE, sub_pattern)
        self._current_context = component
        return self
        
    def has(self, pattern: Union[str, 'PatternBuilder']) -> 'PatternBuilder':
        """Match nodes that contain the given pattern."""
        sub_pattern = self._normalize_pattern(pattern)
        component = PatternComponent(PatternType.HAS, sub_pattern)
        self._add_component(component)
        return self
        
    # Language-specific helpers
    
    def function(self, name: Optional[str] = None) -> 'PatternBuilder':
        """Match a function definition."""
        if self.language == "python":
            if name:
                return self.literal(f"def {name}($$$PARAMS): $$$BODY")
            return self.literal("def $NAME($$$PARAMS): $$$BODY")
        elif self.language in ["javascript", "typescript"]:
            if name:
                return self.literal(f"function {name}($$$PARAMS) {{ $$$BODY }}")
            return self.literal("function $NAME($$$PARAMS) { $$$BODY }")
        elif self.language == "rust":
            if name:
                return self.literal(f"fn {name}($$$PARAMS) {{ $$$BODY }}")
            return self.literal("fn $NAME($$$PARAMS) { $$$BODY }")
        else:
            # Generic function pattern
            if name:
                return self.literal(f"{name}($$$PARAMS)")
            return self.literal("$NAME($$$PARAMS)")
            
    def class_definition(self, name: Optional[str] = None) -> 'PatternBuilder':
        """Match a class definition."""
        if self.language == "python":
            if name:
                return self.literal(f"class {name}: $$$BODY")
            return self.literal("class $NAME: $$$BODY")
        elif self.language in ["javascript", "typescript"]:
            if name:
                return self.literal(f"class {name} {{ $$$BODY }}")
            return self.literal("class $NAME { $$$BODY }")
        elif self.language == "rust":
            if name:
                return self.literal(f"struct {name} {{ $$$FIELDS }}")
            return self.literal("struct $NAME { $$$FIELDS }")
        else:
            if name:
                return self.literal(f"class {name}")
            return self.literal("class $NAME")
            
    def method_call(self, object_name: Optional[str] = None, 
                    method_name: Optional[str] = None) -> 'PatternBuilder':
        """Match a method call."""
        obj = object_name or "$OBJ"
        method = method_name or "$METHOD"
        return self.literal(f"{obj}.{method}($$$ARGS)")
        
    def import_statement(self, module: Optional[str] = None) -> 'PatternBuilder':
        """Match an import statement."""
        if self.language == "python":
            if module:
                return self.literal(f"import {module}")
            return self.literal("import $MODULE")
        elif self.language in ["javascript", "typescript"]:
            if module:
                return self.literal(f"import $$$IMPORTS from '{module}'")
            return self.literal("import $$$IMPORTS from '$MODULE'")
        elif self.language == "rust":
            if module:
                return self.literal(f"use {module}")
            return self.literal("use $MODULE")
        else:
            return self.literal("import $MODULE")
            
    def if_statement(self, condition: Optional[str] = None) -> 'PatternBuilder':
        """Match an if statement."""
        cond = condition or "$CONDITION"
        if self.language == "python":
            return self.literal(f"if {cond}: $$$BODY")
        elif self.language in ["javascript", "typescript", "rust", "c"]:
            return self.literal(f"if ({cond}) {{ $$$BODY }}")
        else:
            return self.literal(f"if {cond}")
            
    def loop(self, loop_type: str = "for") -> 'PatternBuilder':
        """Match a loop construct."""
        if loop_type == "for":
            if self.language == "python":
                return self.literal("for $VAR in $ITERABLE: $$$BODY")
            elif self.language in ["javascript", "typescript"]:
                return self.literal("for ($$$INIT; $CONDITION; $$$UPDATE) { $$$BODY }")
            elif self.language == "rust":
                return self.literal("for $VAR in $ITERABLE { $$$BODY }")
        elif loop_type == "while":
            if self.language == "python":
                return self.literal("while $CONDITION: $$$BODY")
            else:
                return self.literal("while ($CONDITION) { $$$BODY }")
        return self
        
    def try_catch(self) -> 'PatternBuilder':
        """Match a try-catch/except block."""
        if self.language == "python":
            return self.literal("try: $$$TRY_BODY except $$$EXCEPTIONS: $$$EXCEPT_BODY")
        elif self.language in ["javascript", "typescript"]:
            return self.literal("try { $$$TRY_BODY } catch ($ERR) { $$$CATCH_BODY }")
        elif self.language == "rust":
            return self.literal("match $EXPR { Ok($VAL) => $$$OK_BODY, Err($ERR) => $$$ERR_BODY }")
        return self
        
    # Python-specific helpers
    
    def with_decorator(self, decorator: str) -> 'PatternBuilder':
        """Match a function/class with a specific decorator (Python)."""
        if self.language != "python":
            raise ValueError("Decorators are Python-specific")
        return self.literal(f"@{decorator}\n$$$DEFINITION")
        
    def with_type_hint(self, param: str, type_hint: str) -> 'PatternBuilder':
        """Match a parameter with type hint (Python/TypeScript)."""
        if self.language == "python":
            return self.literal(f"{param}: {type_hint}")
        elif self.language == "typescript":
            return self.literal(f"{param}: {type_hint}")
        return self
        
    # JavaScript/TypeScript-specific helpers
    
    def arrow_function(self) -> 'PatternBuilder':
        """Match an arrow function (JavaScript/TypeScript)."""
        if self.language not in ["javascript", "typescript"]:
            raise ValueError("Arrow functions are JavaScript/TypeScript-specific")
        return self.literal("($$$PARAMS) => $$$BODY")
        
    def async_function(self, name: Optional[str] = None, simple: bool = True) -> 'PatternBuilder':
        """Match an async function.
        
        Args:
            name: Optional function name
            simple: Use simple patterns (recommended for Rust)
        """
        if self.language in ["javascript", "typescript"]:
            if simple:
                if name:
                    return self.literal(f"async function {name}")
                return self.literal("async function $NAME")
            else:
                if name:
                    return self.literal(f"async function {name}($$$PARAMS) {{ $$$BODY }}")
                return self.literal("async function $NAME($$$PARAMS) { $$$BODY }")
        elif self.language == "python":
            if simple:
                if name:
                    return self.literal(f"async def {name}")
                return self.literal("async def $NAME")
            else:
                if name:
                    return self.literal(f"async def {name}($$$PARAMS): $$$BODY")
                return self.literal("async def $NAME($$$PARAMS): $$$BODY")
        elif self.language == "rust":
            # For Rust, always use simple patterns as complex ones often fail
            if name:
                return self.literal(f"async fn {name}")
            return self.literal("async fn $NAME")
        return self
        
    # Rust-specific helpers
    
    def await_expr(self, expr: Optional[str] = None) -> 'PatternBuilder':
        """Match an await expression (Rust/JS)."""
        if self.language == "rust":
            if expr:
                return self.literal(f"{expr}.await")
            return self.literal("$EXPR.await")
        elif self.language in ["javascript", "typescript"]:
            if expr:
                return self.literal(f"await {expr}")
            return self.literal("await $EXPR")
        return self
    
    def tokio_spawn(self) -> 'PatternBuilder':
        """Match tokio::spawn (Rust)."""
        if self.language != "rust":
            raise ValueError("tokio::spawn is Rust-specific")
        return self.literal("tokio::spawn($$$ARGS)")
    
    def async_block(self, is_move: bool = False) -> 'PatternBuilder':
        """Match an async block (Rust)."""
        if self.language != "rust":
            raise ValueError("async blocks are Rust-specific")
        if is_move:
            return self.literal("async move { $$$BODY }")
        return self.literal("async { $$$BODY }")
    
    def impl_block(self, trait_name: Optional[str] = None, 
                   type_name: Optional[str] = None) -> 'PatternBuilder':
        """Match an impl block (Rust)."""
        if self.language != "rust":
            raise ValueError("impl blocks are Rust-specific")
        
        if trait_name and type_name:
            return self.literal(f"impl {trait_name} for {type_name} {{ $$$BODY }}")
        elif type_name:
            return self.literal(f"impl {type_name} {{ $$$BODY }}")
        else:
            return self.literal("impl $TYPE { $$$BODY }")
            
    def match_expression(self) -> 'PatternBuilder':
        """Match a match expression (Rust)."""
        if self.language != "rust":
            raise ValueError("match expressions are Rust-specific")
        return self.literal("match $EXPR { $$$ARMS }")
        
    def unsafe_block(self) -> 'PatternBuilder':
        """Match an unsafe block (Rust)."""
        if self.language != "rust":
            raise ValueError("unsafe blocks are Rust-specific")
        return self.literal("unsafe { $$$BODY }")
        
    # Attribute/modifier helpers
    
    def with_attribute(self, attribute: str) -> 'PatternBuilder':
        """Add an attribute/annotation requirement."""
        if self.language == "rust":
            return self.literal(f"#[{attribute}]\n$$$ITEM")
        elif self.language == "python":
            return self.with_decorator(attribute)
        return self
        
    def with_visibility(self, visibility: str) -> 'PatternBuilder':
        """Add visibility modifier (public/private/protected)."""
        if self.language == "rust":
            return self.literal(f"{visibility} $$$ITEM")
        elif self.language in ["javascript", "typescript"]:
            return self.literal(f"{visibility} $$$ITEM")
        return self
        
    # Building methods
    
    def build(self) -> str:
        """Build the final pattern string."""
        if not self.components:
            return ""
            
        # If we only have one component and it's a literal, return it directly
        if len(self.components) == 1 and self.components[0].type == PatternType.LITERAL:
            return self.components[0].value
            
        # Otherwise, build a complex pattern
        return self._build_complex_pattern()
        
    def to_rule(self) -> Dict[str, Any]:
        """Convert the pattern to a rule structure."""
        pattern = self.build()
        rule = {"pattern": pattern}
        
        if self._current_context:
            if self._current_context.type == PatternType.INSIDE:
                rule = {
                    "inside": {"pattern": self._current_context.value},
                    "pattern": pattern
                }
                
        return rule
        
    def _add_component(self, component: PatternComponent) -> None:
        """Add a component to the pattern."""
        self.components.append(component)
        
    def _normalize_pattern(self, pattern: Union[str, 'PatternBuilder']) -> str:
        """Normalize a pattern to string."""
        if isinstance(pattern, PatternBuilder):
            return pattern.build()
        return pattern
        
    def _normalize_patterns(self, patterns: tuple) -> List[str]:
        """Normalize a list of patterns to strings."""
        return [self._normalize_pattern(p) for p in patterns]
        
    def _build_complex_pattern(self) -> str:
        """Build a complex pattern from components."""
        # Build pattern based on component types
        if len(self.components) == 1:
            return self._component_to_string(self.components[0])
            
        # Handle multiple components
        pattern_parts = []
        for component in self.components:
            pattern_parts.append(self._component_to_string(component))
            
        # Apply any constraints or modifiers
        result = " ".join(pattern_parts)
        
        # Apply constraints if any
        if self._constraints:
            if "has" in self._constraints:
                result = f"{result} has {self._constraints['has']}"
            if "inside" in self._constraints:
                result = f"{result} inside {self._constraints['inside']}"
            if "not" in self._constraints:
                result = f"not {result}"
                
        return result
        
    def _component_to_string(self, component: PatternComponent) -> str:
        """Convert a component to its string representation."""
        if component.type == PatternType.LITERAL:
            return component.value
        elif component.type == PatternType.METAVAR:
            return component.value
        elif component.type == PatternType.MULTI_METAVAR:
            return component.value
        elif component.type == PatternType.ANY:
            # Handle any() patterns
            sub_patterns = [self._normalize_pattern(p) for p in component.value]
            return f"any({', '.join(sub_patterns)})"
        elif component.type == PatternType.ALL:
            # Handle all() patterns
            sub_patterns = [self._normalize_pattern(p) for p in component.value]
            return f"all({', '.join(sub_patterns)})"
        elif component.type == PatternType.NOT:
            # Handle not patterns
            return f"not({self._normalize_pattern(component.value)})"
        elif component.type == PatternType.INSIDE:
            # Handle inside patterns
            self._constraints["inside"] = self._normalize_pattern(component.value)
            return ""  # Don't add to main pattern
        elif component.type == PatternType.HAS:
            # Handle has patterns
            self._constraints["has"] = self._normalize_pattern(component.value)
            return ""  # Don't add to main pattern
        else:
            return str(component.value)
        

class PatternLibrary:
    """Library of common patterns for different languages."""
    
    @staticmethod
    def get_common_patterns(language: str) -> Dict[str, PatternBuilder]:
        """Get common patterns for a language."""
        patterns = {}
        
        if language == "python":
            patterns.update({
                "empty_except": PatternBuilder(language).literal("except: pass"),
                "print_statement": PatternBuilder(language).literal("print($$$ARGS)"),
                "list_comprehension": PatternBuilder(language).literal("[$EXPR for $VAR in $ITER]"),
                "dict_comprehension": PatternBuilder(language).literal("{$KEY: $VALUE for $VAR in $ITER}"),
                "lambda": PatternBuilder(language).literal("lambda $$$PARAMS: $EXPR"),
                "assert": PatternBuilder(language).literal("assert $CONDITION"),
            })
        elif language == "javascript":
            patterns.update({
                "console_log": PatternBuilder(language).literal("console.log($$$ARGS)"),
                "var_declaration": PatternBuilder(language).literal("var $NAME = $VALUE"),
                "let_declaration": PatternBuilder(language).literal("let $NAME = $VALUE"),
                "const_declaration": PatternBuilder(language).literal("const $NAME = $VALUE"),
                "promise": PatternBuilder(language).literal("new Promise(($RESOLVE, $REJECT) => { $$$BODY })"),
                "async_await": PatternBuilder(language).literal("await $EXPR"),
            })
        elif language == "rust":
            patterns.update({
                "unwrap": PatternBuilder(language).literal("$EXPR.unwrap()"),
                "expect": PatternBuilder(language).literal("$EXPR.expect($MSG)"),
                "println": PatternBuilder(language).literal("println!($$$ARGS)"),
                "vec_macro": PatternBuilder(language).literal("vec![$$$ITEMS]"),
                "derive": PatternBuilder(language).literal("#[derive($$$TRAITS)]"),
                "test_fn": PatternBuilder(language).literal("#[test]\nfn $NAME() { $$$BODY }"),
            })
            
        return patterns