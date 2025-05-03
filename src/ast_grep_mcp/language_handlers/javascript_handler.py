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
        return {
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
        }


class TypeScriptHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "typescript"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".ts", ".tsx"]
    
    def get_default_patterns(self) -> Dict[str, str]:
        # Include all JavaScript patterns and add TypeScript-specific ones
        js_patterns = JavaScriptHandler().get_default_patterns()
        ts_patterns = {
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
        }
        return {**js_patterns, **ts_patterns}