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
            "function_declaration": "function $NAME($$$PARAMS)",
            "arrow_function": "($$$PARAMS) => $$$BODY",
            "class_declaration": "class $NAME",
            "import_statement": "import $NAME from '$MODULE'",
            "export_statement": "export $$$DECL",
            "for_loop": "for ($INIT; $COND; $UPDATE)",
            "for_of_loop": "for ($VAR of $ITERABLE)",
            "for_in_loop": "for ($VAR in $OBJECT)",
            "try_catch": "try { $$$BODY } catch ($ERR) { $$$HANDLER }",
            "if_statement": "if ($COND) { $$$BODY }",
            "ternary_operator": "$COND ? $THEN : $ELSE",
            "object_literal": "{ $$$PROPS }",
            "array_literal": "[ $$$ELEMENTS ]",
            "destructuring_assignment": "const { $$$PROPS } = $OBJ",
            "template_literal": "`$$$EXPR`",
            "async_function": "async function $NAME($$$PARAMS)",
            "jsx_element": "<$TAG $$$PROPS>$$$CHILDREN</$TAG>",
            "console_log": "console.log($$$ARGS)",
            "spread_operator": "...$EXPR",
        }