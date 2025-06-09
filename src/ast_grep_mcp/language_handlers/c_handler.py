"""
C language handler for ast-grep.
"""

from typing import Dict, List
from .base import LanguageHandler


class CHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "c"

    @property
    def file_extensions(self) -> List[str]:
        return [".c", ".h"]

    def get_default_patterns(self) -> Dict[str, str]:
        """
        Return default AST patterns for C.

        Includes patterns for:
        - Common code constructs
        - Anti-patterns and code smells
        - Performance optimizations
        - Security vulnerabilities
        - Refactoring opportunities
        """
        return {
            # Basic code constructs
            "function": "$RET_TYPE $NAME($$$PARAMS)",
            "struct": "struct $NAME { $$$FIELDS }",
            "variable": "$TYPE $NAME = $VALUE;",
            "comment": "/* $$$COMMENT */",
            "enum": "enum $NAME { $$$VALUES }",
            "typedef": "typedef $OLD_TYPE $NEW_TYPE;",
            "function_pointer": "$RET_TYPE (*$NAME)($$$PARAMS)",
            "macro": "#define $NAME($$$PARAMS) $BODY",
            "include": "#include $HEADER",
            "switch": "switch ($EXPR) { $$$CASES }",
            # Anti-patterns and code smells
            "goto": "goto $LABEL;",
            "magic_number": "$EXPR $OP $NUMBER",
            "nested_conditional": "if ($COND1) { if ($COND2) { $$$BODY } }",
            "large_function": "$RET_TYPE $NAME($$$PARAMS) { $$$LOTS_OF_CODE }",
            "global_var": "$TYPE $NAME = $VALUE;",
            "deeply_nested_loop": "for ($INIT1; $COND1; $POST1) { for ($INIT2; $COND2; $POST2) { $$$BODY } }",
            # Performance optimizations
            "unnecessary_copy": "memcpy($DEST, $SRC, sizeof($TYPE))",
            "inefficient_string_concat": "strcat($DEST, $SRC)",
            "malloc_without_check": "$PTR = malloc($SIZE)",
            "repeated_array_element_access": "for ($I = 0; $I < $N; $I++) { $$$_; $ARRAY[$I]; $$$_ }",
            "redundant_condition": "if ($EXPR) { return 1; } else { return 0; }",
            # Security vulnerabilities
            "buffer_overflow": "strcpy($DEST, $SRC)",
            "format_string_vulnerability": "printf($USER_INPUT)",
            "gets_call": "gets($BUFFER)",
            "integer_overflow": "$SMALL_TYPE $VAR = $LARGE_TYPE_EXPR",
            "null_pointer_deref": "*$PTR",
            "use_after_free": "free($PTR); $$$_; *$PTR",
            # Refactoring patterns
            "if_return_pattern": "if ($COND) { return $TRUE_VAL; } return $FALSE_VAL;",
            "void_parameter": "$RET_TYPE $NAME(void)",
            "switch_without_default": "switch ($EXPR) { $$$CASES }",
            "multiple_return_paths": "if ($COND) { return $VAL1; } else { return $VAL2; }",
            "malloc_sizeof_type": "malloc(sizeof($TYPE))",
            "redundant_null_check": "if ($PTR != NULL) { $$$BODY }",
            "loop_counter_size": "for (int $I = 0; $I < $SIZE; $I++)",
            "unused_variable": "$TYPE $VAR = $EXPR; $$$_; return $RET;",
            "literal_constant": "#define $NAME $VALUE",
        }
