"""
Rust language handler for ast-grep.
"""

from typing import Dict, List
from .base import LanguageHandler


class RustHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "rust"

    @property
    def file_extensions(self) -> List[str]:
        return [".rs"]

    def get_default_patterns(self) -> Dict[str, str]:
        """
        Return default AST patterns for Rust.

        Includes patterns for:
        - Common code constructs
        - Anti-patterns and code smells
        - Performance optimizations
        - Security vulnerabilities
        - Refactoring opportunities
        """
        return {
            # Basic code constructs
            # NOTE: ast-grep works best with structural patterns
            # Use simple patterns for broad matching, complex patterns for specific cases
            
            # Function patterns - basic forms work reliably
            "function": "fn $NAME($$$PARAMS) { $$$BODY }",
            "function_simple": "fn $NAME",  # Matches any function declaration
            "async_function": "async fn $NAME($$$PARAMS) { $$$BODY }",
            "async_function_simple": "async fn $NAME",  # Simpler pattern
            "pub_function": "pub fn $NAME($$$PARAMS) { $$$BODY }",
            "pub_async_function": "pub async fn $NAME($$$PARAMS) { $$$BODY }",
            "function_with_return": "fn $NAME($$$PARAMS) -> $RET_TYPE { $$$BODY }",
            "async_fn_with_return": "async fn $NAME($$$PARAMS) -> $RET_TYPE { $$$BODY }",
            
            # Async patterns
            "async_block": "async { $$$BODY }",
            "async_block_simple": "async",  # Matches any async block
            "await_expr": "$EXPR.await",
            "tokio_spawn": "tokio::spawn($$$ARGS)",
            "tokio_spawn_simple": "tokio::spawn",  # Simple version
            "spawn_call": "spawn($$$ARGS)",  # Generic spawn
            "async_move": "async move { $$$BODY }",
            "future_poll": "$FUTURE.poll($CTX)",
            "stream_next": "$STREAM.next()",
            
            # Trait patterns
            "trait_def": "trait $NAME { $$$BODY }",
            "trait_simple": "trait $NAME",  # Matches trait declaration
            "impl_trait": "impl $TRAIT for $TYPE { $$$BODY }",
            "impl_trait_simple": "impl $TRAIT for $TYPE",
            "impl_generic_trait": "impl<$$$GENERICS> $TRAIT for $TYPE { $$$BODY }",
            "derive_trait": "#[derive($$$TRAITS)]",
            "trait_bound": "where $T: $BOUND",
            "associated_type": "type $NAME = $TYPE;",
            
            # Struct and enum patterns
            "struct_def": "struct $NAME { $$$FIELDS }",
            "struct_simple": "struct $NAME",
            "tuple_struct": "struct $NAME($$$FIELDS);",
            "enum_def": "enum $NAME { $$$VARIANTS }",
            "enum_simple": "enum $NAME",
            "impl_block": "impl $TYPE { $$$BODY }",
            "impl_simple": "impl $TYPE",
            "impl_generic": "impl<$$$GENERICS> $TYPE { $$$BODY }",
            
            # Variables and constants
            "variable": "let $NAME = $VALUE",
            "mutable_variable": "let mut $NAME = $VALUE",
            "const": "const $NAME: $TYPE = $VALUE",
            "static": "static $NAME: $TYPE = $VALUE",
            
            # Module and use patterns
            "use_statement": "use $PATH",
            "mod_declaration": "mod $NAME",
            "pub_mod": "pub mod $NAME",
            "match_expr": "match $EXPR { $$$ARMS }",
            "macro_call": "$MACRO!($$$ARGS)",
            "macro_call_brackets": "$MACRO![$$$ARGS]",
            "macro_call_braces": "$MACRO!{$$$ARGS}",
            # Anti-patterns and code smells (working patterns)
            "unwrap_call": "$EXPR.unwrap()",
            "expect_call": "$EXPR.expect($MSG)",
            "panic_call": "panic!($$$ARGS)",
            "todo_macro": "todo!($$$ARGS)",
            "unimplemented_macro": "unimplemented!($$$ARGS)",
            "clone_call": "$EXPR.clone()",
            "explicit_return": "return $EXPR;",
            "explicit_return_simple": "return $EXPR",
            # Performance optimizations
            "box_vec_new": "Box::new(vec![$$$ITEMS])",
            "string_add_push_str": "$STRING = $STRING + $OTHER",
            "redundant_clone": "$VAR.clone()",
            "unnecessary_sort_by": "$VEC.sort_by(|a, b| a.cmp(b))",
            "inefficient_iterator_chain": "$ITER.collect::<Vec<_>>().$$$METHOD()",
            # Security vulnerabilities
            "dangerous_transmute": "std::mem::transmute::<$FROM, $TO>($EXPR)",
            "unsafe_code_block": "unsafe { $$$CODE }",
            "raw_pointer_deref": "*$PTR",
            "format_string_injection": "format!($USER_INPUT, $$$ARGS)",
            "regex_dos": 'Regex::new(r"($$$USER_CONTROLLED_PATTERN)")',
            # Refactoring patterns
            "if_let_chain": "if let $PATTERN1 = $EXPR1 { if let $PATTERN2 = $EXPR2 { $$$CODE } }",
            "match_to_if_let": "match $EXPR { $PATTERN => $BLOCK, _ => $DEFAULT }",
            "explicit_deref": "*(&$EXPR)",
            "manual_filter_map": "$ITER.filter($PRED).map($MAPPER)",
            "mutex_guard": "let $GUARD = $MUTEX.lock().unwrap(); $$$CODE",
            "redundant_closure": "$ITER.map(|$X| $FN($X))",
            "bool_comparison": "if $EXPR == true",
            "nested_if": "if $COND1 { if $COND2 { $$$CODE } }",
            "match_single_arm": "match $EXPR { $PATTERN => $BLOCK }",
            "manual_map_err": "$RESULT.and_then(|$VAL| Ok($TRANSFORM))",
        }
