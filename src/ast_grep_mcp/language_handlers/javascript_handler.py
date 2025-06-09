from .base import LanguageHandler
from typing import List, Dict


class JavaScriptHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "javascript"

    @property
    def file_extensions(self) -> List[str]:
        return [".js", ".jsx"]

    def get_default_patterns(self) -> Dict[str, str]:
        """
        Return default AST patterns for JavaScript.

        Includes patterns for:
        - Common code constructs
        - Anti-patterns and code smells
        - Performance optimizations
        - Security vulnerabilities
        - Refactoring opportunities
        """
        return {
            # Basic code constructs
            "function_declaration": "function $NAME($$$PARAMS) { $$$BODY }",
            "arrow_function": "($$$PARAMS) => $$$BODY",
            "class_declaration": "class $NAME { $$$BODY }",
            "method_definition": "$NAME($$$PARAMS) { $$$BODY }",
            "import_statement": "import $NAME from '$MODULE'",
            "export_statement": "export $$$DECL",
            "for_loop": "for ($INIT; $COND; $UPDATE) { $$$BODY }",
            "for_of_loop": "for (const $VAR of $ITERABLE) { $$$BODY }",
            "for_in_loop": "for (const $VAR in $OBJECT) { $$$BODY }",
            "try_catch": "try { $$$BODY } catch ($ERR) { $$$HANDLER }",
            "if_statement": "if ($COND) { $$$BODY }",
            "else_statement": "else { $$$BODY }",
            "if_else_statement": "if ($COND) { $$$THEN_BODY } else { $$$ELSE_BODY }",
            "ternary_operator": "$COND ? $THEN : $ELSE",
            "object_literal": "{ $$$PROPS }",
            "array_literal": "[ $$$ELEMENTS ]",
            "destructuring_assignment": "const { $$$PROPS } = $OBJ",
            "template_literal": "`$$$EXPR`",
            "async_function": "async function $NAME($$$PARAMS) { $$$BODY }",
            "jsx_element": "<$TAG $$$PROPS>$$$CHILDREN</$TAG>",
            "self_closing_jsx": "<$TAG $$$PROPS />",
            "console_log": "console.log($$$ARGS)",
            "spread_operator": "...$EXPR",
            "variable_declaration": "const $NAME = $VALUE",
            "arrow_function_simple": "$$$PARAMS => $EXPR",
            # Anti-patterns and code smells
            "var_declaration": "var $NAME = $VALUE",
            "setTimeout_zero": "setTimeout($FUNC, 0)",
            "with_statement": "with ($OBJ) { $$$BODY }",
            "alert": "alert($MESSAGE)",
            "document_write": "document.write($CONTENT)",
            "nested_callbacks": "$FUNC($$$ARGS, function($$$PARAMS) { $$$BODY })",
            "global_variable": "$NAME = $VALUE",
            "multiple_var_declarators": "var $NAME1 = $VAL1, $NAME2 = $VAL2",
            "double_equal": "$A == $B",
            "long_function": "function $NAME($$$PARAMS) { $$$LONG_BODY }",
            # Performance optimizations
            "array_push_in_loop": "for ($$$INIT) { $ARR.push($ITEM) }",
            "inefficient_dom_query": "document.querySelectorAll($SELECTOR)",
            "redundant_jquery_selector": "$($SELECTOR).find($SUBSELECTOR)",
            "innerHTML_in_loop": "for ($$$INIT) { $ELEM.innerHTML += $CONTENT }",
            "blocking_event_handler": "$ELEM.addEventListener('$EVENT', function() { $$$HEAVY_COMPUTATION })",
            "string_concat_plus": "$STR = $STR + $OTHER",
            # Security vulnerabilities
            "eval_call": "eval($CODE)",
            "innerHTML_user_input": "$ELEM.innerHTML = $USER_INPUT",
            "document_location_href": "document.location.href = $USER_INPUT",
            "insecure_cookie": "document.cookie = $COOKIE_STRING",
            "dangerouslySetInnerHTML": "dangerouslySetInnerHTML={{ __html: $USER_INPUT }}",
            "sql_string_concatenation": "db.query('SELECT * FROM users WHERE id = ' + $USER_INPUT)",
            "dom_clobbering": "$ELEM.id = $USER_CONTROLLED_ID",
            # Refactoring patterns
            "nested_if": "if ($COND1) { if ($COND2) { $$$BODY } }",
            "callback_to_promise": "$FUNC($$$ARGS, function($$$PARAMS) { $$$BODY })",
            "repeated_condition": "if ($COND) { $$$BODY1 } else if ($COND) { $$$BODY2 }",
            "boolean_literal_compare": "$EXPR === true",
            "unnecessary_return": "return $EXPR; }",
            "promise_then_catch": "$PROMISE.then($SUCCESS).catch($ERROR)",
            "json_parse_try_catch": "try { JSON.parse($STRING) } catch ($ERR) { $$$HANDLER }",
            "manual_promise_chain": "$PROMISE.then(function($RESULT) { return $NEXT_PROMISE; })",
            "try_catch_finally": "try { $$$TRY_BODY } catch ($ERR) { $$$CATCH_BODY } finally { $$$FINALLY_BODY }",
        }


class TypeScriptHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "typescript"

    @property
    def file_extensions(self) -> List[str]:
        return [".ts", ".tsx"]

    def get_default_patterns(self) -> Dict[str, str]:
        """
        Return default AST patterns for TypeScript.

        Includes all JavaScript patterns plus TypeScript-specific patterns.
        """
        # Include all JavaScript patterns and add TypeScript-specific ones
        js_patterns = JavaScriptHandler().get_default_patterns()
        ts_patterns = {
            # Basic TypeScript patterns
            "interface_declaration": "interface $NAME { $$$BODY }",
            "type_declaration": "type $NAME = $TYPE",
            "enum_declaration": "enum $NAME { $$$MEMBERS }",
            "typed_function": "function $NAME($$$PARAMS): $RETURN_TYPE { $$$BODY }",
            "typed_arrow_function": "($$$PARAMS): $RETURN_TYPE => $$$BODY",
            "typed_method": "$NAME($$$PARAMS): $RETURN_TYPE { $$$BODY }",
            "type_annotation": ": $TYPE",
            "type_assertion": "<$TYPE>$EXPR",
            "typed_property": "$NAME: $TYPE",
            "generic_type": "$NAME<$$$TYPE_PARAMS>",
            "import_type": "import type { $$$TYPES } from '$MODULE'",
            "export_type": "export type $NAME = $TYPE",
            "namespace": "namespace $NAME { $$$BODY }",
            "decorated_class": "@$DECORATOR class $NAME { $$$BODY }",
            # Anti-patterns and code smells
            "any_type": ": any",
            "non_null_assertion": "$EXPR!",
            "type_assertion_any": "$EXPR as any",
            "nested_type_assertion": "($EXPR as $TYPE1) as $TYPE2",
            "complex_intersection": "$TYPE1 & $TYPE2 & $TYPE3",
            "complex_union": "$TYPE1 | $TYPE2 | $TYPE3 | $TYPE4",
            "large_interface": "interface $NAME { $$$MANY_PROPS }",
            # Performance optimizations
            "untyped_object_literal": "{ $$$PROPS } as $TYPE",
            "excessive_generics": "<$T1, $T2, $T3, $T4>",
            "redundant_casting": "$EXPR as $ITS_ACTUAL_TYPE",
            # Security vulnerabilities
            "unsafe_any": "$FUNC($PARAM as any)",
            "definite_assignment": "$PROP!: $TYPE",
            "loose_object_literal": "const $OBJ: $TYPE = {}",
            # Refactoring patterns
            "optional_chain": "$OBJ?.$PROP",
            "nullish_coalescing": "$EXPR ?? $DEFAULT",
            "type_guard": "function is$TYPE($PARAM: any): $PARAM is $TYPE { $$$BODY }",
            "type_predicate": "$PARAM is $TYPE",
            "keyof_operator": "keyof $TYPE",
            "mapped_type": "{ [P in keyof $TYPE]: $MAPPED_TYPE }",
            "conditional_type": "$TYPE extends $CONDITION ? $TRUE_TYPE : $FALSE_TYPE",
            "infer_type": "infer $TYPE_VAR",
            "template_literal_type": "`$$$TEMPLATE`",
            "readonly_modifier": "readonly $PROP: $TYPE",
        }
        return {**js_patterns, **ts_patterns}
