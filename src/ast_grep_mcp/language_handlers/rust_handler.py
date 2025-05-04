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
            "function": "fn $NAME($$$PARAMS) -> $RET_TYPE",
            "struct": "struct $NAME { $$$FIELDS }",
            "variable": "let $NAME = $VALUE;",
            "comment": "// $$$COMMENT",
            "enum": "enum $NAME { $$$VARIANTS }",
            "impl": "impl $NAME { $$$METHODS }",
            "trait": "trait $NAME { $$$METHODS }",
            "impl_trait": "impl $TRAIT for $TYPE { $$$METHODS }",
            "match": "match $EXPR { $$$ARMS }",
            "macro_invocation": "$NAME!($$$ARGS)",
            
            # Anti-patterns and code smells
            "unwrap": "$EXPR.unwrap()",
            "expect": "$EXPR.expect($MESSAGE)",
            "clone_in_loop": "for $VAR in $ITER { $$$_; $EXPR.clone(); $$$_ }",
            "nested_match": "match $EXPR { $$$_; match $INNER_EXPR { $$$_ } $$$_ }",
            "needless_return": "return $EXPR;",
            "large_enum_variant": "enum $NAME { $$$VARIANTS, $LARGE_VARIANT($$$MANY_FIELDS) }",
            
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
            "regex_dos": "Regex::new(r\"($$$USER_CONTROLLED_PATTERN)\")",
            
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
