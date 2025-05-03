from .base import LanguageHandler
from typing import List, Dict

class PythonHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "python"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".py"]
    
    def get_default_patterns(self) -> Dict[str, str]:
        return {
            # Function patterns
            "function_definition": "def $NAME($$$PARAMS):",
            "function_with_body": "def $NAME($$$PARAMS):\n    $$$BODY",
            "function_call": "$NAME($$$ARGS)",
            "function_with_decorator": "@$DECORATOR\ndef $NAME($$$PARAMS):",
            "function_with_type_hints": "def $NAME($$$PARAMS) -> $RETURN_TYPE:",
            
            # Class patterns
            "class_definition": "class $NAME:",
            "class_with_bases": "class $NAME($$$BASES):",
            "class_with_body": "class $NAME:\n    $$$BODY",
            "method_definition": "def $NAME(self, $$$PARAMS):",
            "class_variable": "$NAME = $VALUE",
            
            # Flow control
            "if_statement": "if $CONDITION:",
            "if_else_statement": "if $CONDITION:\n    $$$THEN_BODY\nelse:\n    $$$ELSE_BODY",
            "for_loop": "for $VAR in $ITERABLE:",
            "for_loop_with_body": "for $VAR in $ITERABLE:\n    $$$BODY",
            "while_loop": "while $CONDITION:",
            "try_except": "try:\n    $$$BODY\nexcept $EXCEPTION:\n    $$$HANDLER",
            "with_statement": "with $CONTEXT as $VAR:",
            
            # Imports
            "import_statement": "import $MODULE",
            "from_import": "from $MODULE import $NAME",
            "from_import_multiple": "from $MODULE import $$$NAMES",
            "import_as": "import $MODULE as $ALIAS",
            "from_import_as": "from $MODULE import $NAME as $ALIAS",
            
            # Expressions
            "lambda": "lambda $$$PARAMS: $EXPR",
            "list_comprehension": "[$EXPR for $VAR in $ITER]",
            "dict_comprehension": "{$KEY: $VALUE for $VAR in $ITER}",
            "f_string": "f\"$$$EXPR\"",
            "string_literal": "\"$$$TEXT\"",
            
            # Statements
            "print_statement": "print($$$ARGS)",
            "return_statement": "return $EXPR",
            "assignment": "$NAME = $VALUE",
            "multiple_assignment": "$$$NAMES = $$$VALUES",
            "augmented_assignment": "$NAME += $VALUE",
            
            # Modern Python
            "async_function": "async def $NAME($$$PARAMS):",
            "async_for": "async for $VAR in $ITER:",
            "async_with": "async with $EXPR as $VAR:",
            "match_case": "match $EXPR:\n    case $PATTERN:\n        $$$BODY",
            "walrus_operator": "$NAME := $EXPR",
            "type_hint": "($$$PARAMS) -> $RETURN_TYPE",
            "dataclass": "@dataclass\nclass $NAME:",
        }