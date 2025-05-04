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
        """
        Return default AST patterns for Python.
        
        Includes patterns for:
        - Common code constructs
        - Anti-patterns and code smells
        - Performance optimizations
        - Security vulnerabilities
        - Refactoring opportunities
        """
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
            
            # Anti-patterns and code smells
            "bare_except": "try:\n    $$$BODY\nexcept:\n    $$$HANDLER",
            "except_pass": "try:\n    $$$BODY\nexcept $EXCEPTION:\n    pass",
            "mutable_default_arg": "def $NAME($PARAM=$MUTABLE_VALUE):",
            "global_statement": "global $NAME",
            "nested_function": "def $OUTER($$$OUTER_PARAMS):\n    $$$OUTER_BODY\n    def $INNER($$$INNER_PARAMS):\n        $$$INNER_BODY",
            "nested_loops": "for $OUTER_VAR in $OUTER_ITER:\n    for $INNER_VAR in $INNER_ITER:\n        $$$BODY",
            "long_function": "def $NAME($$$PARAMS):\n    $$$LONG_BODY",
            
            # Performance optimizations
            "list_in_loop": "for $VAR in $ITER:\n    $$$BODY\n    $LIST.append($ITEM)",
            "string_concat_in_loop": "for $VAR in $ITER:\n    $STR += $SOMETHING",
            "inefficient_dict_lookup": "$DICT[$KEY] if $KEY in $DICT else $DEFAULT",
            "repeated_calculation": "for $VAR in $ITER:\n    $$$BODY\n    $EXPENSIVE_FUNC($ARGS)",
            "inefficient_list_creation": "[x for x in range($N)]",
            "unnecessary_list": "list($GENERATOR)",
            
            # Security vulnerabilities
            "eval_call": "eval($EXPR)",
            "exec_call": "exec($CODE)",
            "shell_true": "subprocess.run($CMD, shell=True)",
            "pickle_load": "pickle.load($FILE)",
            "yaml_load": "yaml.load($DATA)",
            "sql_format": "cursor.execute(f\"$$$SQL {$USER_INPUT}\")",
            "open_file_without_close": "f = open($FILENAME, 'r')",
            "tempfile_insecure": "tempfile.mktemp($$$ARGS)",
            
            # Refactoring patterns
            "if_return_early": "if $COND:\n    return $EARLY\n$$$MORE_CODE\nreturn $LATE",
            "multiple_if_returns": "if $COND1:\n    return $VAL1\nelif $COND2:\n    return $VAL2\nelse:\n    return $VAL3",
            "dict_get_with_default": "if $KEY in $DICT:\n    $VAR = $DICT[$KEY]\nelse:\n    $VAR = $DEFAULT",
            "try_except_else": "try:\n    $$$BODY\nexcept $EXCEPTION:\n    $$$HANDLER\nelse:\n    $$$SUCCESS",
            "repeated_condition": "if $COND:\n    $$$BODY1\n$$$OTHER_CODE\nif $COND:\n    $$$BODY2",
            "explicit_none_compare": "if $VAR == None:",
            "redundant_with_open": "with open($FILE, $MODE) as $F:\n    $CONTENT = $F.read()\n    $$$OPERATIONS_ON_CONTENT",
        }