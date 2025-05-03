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
            "function_definition": "def $NAME($$$PARAMS)",
            "class_definition": "class $NAME",
            "import_statement": "import $MODULE",
            "from_import": "from $MODULE import $NAME",
            "for_loop": "for $VAR in $ITER",
            "with_statement": "with $EXPR as $VAR",
            "try_except": "try: $$$BODY except $EXC: $$$HANDLER",
            "lambda": "lambda $$$PARAMS: $EXPR",
            "list_comprehension": "[$EXPR for $VAR in $ITER]",
            "decorator": "@$NAME",
            "f_string": "f\"$$$EXPR\"",
            "print_statement": "print($$$ARGS)",
            "return_statement": "return $EXPR",
            "if_statement": "if $COND: $$$BODY",
            "dict_comprehension": "{$KEY: $VALUE for $VAR in $ITER}",
            "async_function": "async def $NAME($$$PARAMS)",
            "async_for": "async for $VAR in $ITER",
            "async_with": "async with $EXPR as $VAR",
            "match_case": "match $EXPR: case $PATTERN: $$$BODY",
        }