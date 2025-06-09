"""
Go language handler for ast-grep.
"""

from typing import Dict, List
from .base import LanguageHandler


class GoHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "go"

    @property
    def file_extensions(self) -> List[str]:
        return [".go"]

    def get_default_patterns(self) -> Dict[str, str]:
        """
        Return default AST patterns for Go.

        Includes patterns for:
        - Common code constructs
        - Anti-patterns and code smells
        - Performance optimizations
        - Security vulnerabilities
        - Refactoring opportunities
        """
        return {
            # Basic code constructs
            "function": "func $NAME($$$PARAMS) $$$RETURN_TYPE",
            "struct": "type $NAME struct { $$$FIELDS }",
            "variable": "$NAME := $VALUE",
            "comment": "// $$$COMMENT",
            "interface": "type $NAME interface { $$$METHODS }",
            "method": "func ($RECEIVER $TYPE) $NAME($$$PARAMS) $$$RETURN_TYPE",
            "import": "import ($$$IMPORTS)",
            "for_loop": "for $INIT; $CONDITION; $POST { $$$BODY }",
            "range_loop": "for $KEY, $VALUE := range $COLLECTION { $$$BODY }",
            "switch": "switch $EXPR { $$$CASES }",
            # Anti-patterns and code smells
            "naked_return": "return",
            "empty_interface_param": "func $NAME($PARAM interface{}) $$$RETURN_TYPE",
            "panic_call": "panic($MESSAGE)",
            "goroutine_without_sync": "go func() { $$$BODY }()",
            "bool_param_leading": "func $NAME($FLAG bool, $$$OTHER_PARAMS)",
            "large_struct": "type $NAME struct { $$$MANY_FIELDS }",
            # Performance optimizations
            "string_concat_plus": "$STR = $STR + $OTHER",
            "inefficient_slice_append": "for $_, $ELEM := range $SOURCE { $DEST = append($DEST, $ELEM) }",
            "unnecessary_allocation": "make([]$TYPE, 0)",
            "map_without_capacity": "make(map[$KEY]$VALUE)",
            "mutex_copy": "var $NEW_MUT $MUT",
            # Security vulnerabilities
            "sql_injection": "db.Exec($QUERY + $USER_INPUT)",
            "command_injection": 'exec.Command("sh", "-c", $USER_INPUT)',
            "weak_rand": "rand.Intn($NUM)",
            "insecure_temp_file": 'ioutil.TempFile("", $PREFIX)',
            "http_redirect_open": "http.Redirect($W, $R, $LOCATION, http.StatusFound)",
            # Refactoring patterns
            "nil_check": "if $VAR == nil { $$$ERROR_HANDLING }",
            "error_check": "if err != nil { $$$ERROR_HANDLING }",
            "nested_if": "if $COND1 { if $COND2 { $$$BODY } }",
            "explicit_type_conversion": "$TYPE($VAR)",
            "repeated_condition": "if $COND { $$$BODY1 } else if $COND { $$$BODY2 }",
            "switch_two_cases": "switch $EXPR { case $CASE1: $$$BODY1; case $CASE2: $$$BODY2; }",
            "map_value_check": "if $VAL, $OK := $MAP[$KEY]; $OK { $$$BODY }",
            "defer_in_loop": "for $$$LOOP_HEADER { defer $FUNC() }",
            "fmt_sprint_simple": 'fmt.Sprintf("%s", $VAR)',
            "redundant_type": "$NAME := $TYPE{$$$FIELDS}",
        }
