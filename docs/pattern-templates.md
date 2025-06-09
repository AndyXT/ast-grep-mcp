# AST-Grep Pattern Templates

This document provides working pattern templates for common use cases across different programming languages.

## Python Patterns

### Function Definitions
```yaml
# Match any function
pattern: "def $NAME($$$PARAMS): $$$BODY"

# Match async function
pattern: "async def $NAME($$$PARAMS): $$$BODY"

# Match function with specific decorator
pattern: |
  @decorator_name
  def $NAME($$$PARAMS): $$$BODY

# Match function with type hints
pattern: "def $NAME($$$PARAMS) -> $RETURN_TYPE: $$$BODY"
```

### Class Definitions
```yaml
# Match any class
pattern: "class $NAME: $$$BODY"

# Match class with inheritance
pattern: "class $NAME($PARENT): $$$BODY"

# Match class with multiple inheritance
pattern: "class $NAME($$$PARENTS): $$$BODY"
```

### Control Flow
```yaml
# Match if statements
pattern: "if $CONDITION: $$$BODY"

# Match if-elif-else
pattern: |
  if $COND1:
      $$$BODY1
  elif $COND2:
      $$$BODY2
  else:
      $$$BODY3

# Match for loops
pattern: "for $VAR in $ITERABLE: $$$BODY"

# Match while loops
pattern: "while $CONDITION: $$$BODY"

# Match try-except blocks
pattern: |
  try:
      $$$TRY_BODY
  except $EXCEPTION:
      $$$EXCEPT_BODY
```

### Common Patterns
```yaml
# Match imports
pattern: "import $MODULE"
pattern: "from $MODULE import $NAME"
pattern: "from $MODULE import $$$NAMES"

# Match assignments
pattern: "$VAR = $VALUE"

# Match method calls
pattern: "$OBJ.$METHOD($$$ARGS)"

# Match list comprehensions
pattern: "[$EXPR for $VAR in $ITER]"

# Match dict comprehensions
pattern: "{$KEY: $VALUE for $ITEM in $ITER}"

# Match with statements
pattern: "with $EXPR as $VAR: $$$BODY"
```

## JavaScript/TypeScript Patterns

### Function Definitions
```yaml
# Match function declaration
pattern: "function $NAME($$$PARAMS) { $$$BODY }"

# Match arrow function
pattern: "($$$PARAMS) => $EXPR"
pattern: "($$$PARAMS) => { $$$BODY }"

# Match async function
pattern: "async function $NAME($$$PARAMS) { $$$BODY }"

# Match async arrow function
pattern: "async ($$$PARAMS) => { $$$BODY }"
```

### Class Definitions
```yaml
# Match class
pattern: "class $NAME { $$$BODY }"

# Match class with extends
pattern: "class $NAME extends $PARENT { $$$BODY }"

# Match class method
pattern: "$METHOD_NAME($$$PARAMS) { $$$BODY }"
```

### Variable Declarations
```yaml
# Match const declaration
pattern: "const $NAME = $VALUE"

# Match let declaration
pattern: "let $NAME = $VALUE"

# Match var declaration
pattern: "var $NAME = $VALUE"

# Match destructuring
pattern: "const { $$$PROPS } = $OBJ"
pattern: "const [$$$ITEMS] = $ARR"
```

### Control Flow
```yaml
# Match if statements
pattern: "if ($CONDITION) { $$$BODY }"

# Match if-else
pattern: |
  if ($CONDITION) {
      $$$THEN_BODY
  } else {
      $$$ELSE_BODY
  }

# Match for loops
pattern: "for ($INIT; $CONDITION; $UPDATE) { $$$BODY }"

# Match for-of loops
pattern: "for (const $VAR of $ITERABLE) { $$$BODY }"

# Match for-in loops
pattern: "for (const $VAR in $OBJECT) { $$$BODY }"

# Match while loops
pattern: "while ($CONDITION) { $$$BODY }"

# Match try-catch
pattern: |
  try {
      $$$TRY_BODY
  } catch ($ERROR) {
      $$$CATCH_BODY
  }
```

### Modern JavaScript
```yaml
# Match imports
pattern: "import $NAME from '$MODULE'"
pattern: "import { $$$NAMES } from '$MODULE'"
pattern: "import * as $NAME from '$MODULE'"

# Match exports
pattern: "export default $EXPR"
pattern: "export { $$$NAMES }"
pattern: "export const $NAME = $VALUE"

# Match template literals
pattern: "`$$$TEMPLATE`"

# Match spread operator
pattern: "...$EXPR"

# Match await expressions
pattern: "await $EXPR"

# Match promises
pattern: "new Promise(($RESOLVE, $REJECT) => { $$$BODY })"
```

## Rust Patterns

### Function Definitions
```yaml
# Match function
pattern: "fn $NAME($$$PARAMS) { $$$BODY }"

# Match function with return type
pattern: "fn $NAME($$$PARAMS) -> $RETURN { $$$BODY }"

# Match public function
pattern: "pub fn $NAME($$$PARAMS) { $$$BODY }"

# Match async function
pattern: "async fn $NAME($$$PARAMS) { $$$BODY }"

# Match generic function
pattern: "fn $NAME<$$$GENERICS>($$$PARAMS) { $$$BODY }"
```

### Struct and Enum
```yaml
# Match struct
pattern: "struct $NAME { $$$FIELDS }"

# Match tuple struct
pattern: "struct $NAME($$$FIELDS);"

# Match enum
pattern: "enum $NAME { $$$VARIANTS }"

# Match impl block
pattern: "impl $TYPE { $$$METHODS }"

# Match trait impl
pattern: "impl $TRAIT for $TYPE { $$$METHODS }"
```

### Pattern Matching
```yaml
# Match match expression
pattern: "match $EXPR { $$$ARMS }"

# Match if let
pattern: "if let $PATTERN = $EXPR { $$$BODY }"

# Match while let
pattern: "while let $PATTERN = $EXPR { $$$BODY }"
```

### Common Patterns
```yaml
# Match use statements
pattern: "use $PATH"
pattern: "use $PATH as $ALIAS"
pattern: "use $PATH::{$$$ITEMS}"

# Match let bindings
pattern: "let $VAR = $VALUE"
pattern: "let mut $VAR = $VALUE"
pattern: "let $VAR: $TYPE = $VALUE"

# Match method calls
pattern: "$EXPR.$METHOD($$$ARGS)"

# Match unwrap/expect
pattern: "$EXPR.unwrap()"
pattern: "$EXPR.expect($MSG)"

# Match Result/Option handling
pattern: "$EXPR?"

# Match macros
pattern: "$MACRO!($$$ARGS)"
pattern: "$MACRO![$$$ARGS]"
pattern: "$MACRO!{$$$ARGS}"

# Match attributes
pattern: "#[$ATTR]"
pattern: "#![$ATTR]"

# Match async/await
pattern: "$EXPR.await"
pattern: "async { $$$BODY }"
pattern: "async move { $$$BODY }"
```

## Go Patterns

### Function Definitions
```yaml
# Match function
pattern: "func $NAME($$$PARAMS) { $$$BODY }"

# Match function with return type
pattern: "func $NAME($$$PARAMS) $RETURN { $$$BODY }"

# Match function with multiple returns
pattern: "func $NAME($$$PARAMS) ($$$RETURNS) { $$$BODY }"

# Match method
pattern: "func ($RECEIVER $TYPE) $NAME($$$PARAMS) { $$$BODY }"
```

### Type Definitions
```yaml
# Match struct
pattern: "type $NAME struct { $$$FIELDS }"

# Match interface
pattern: "type $NAME interface { $$$METHODS }"

# Match type alias
pattern: "type $NAME $TYPE"
```

### Control Flow
```yaml
# Match if statements
pattern: "if $CONDITION { $$$BODY }"

# Match if with initialization
pattern: "if $INIT; $CONDITION { $$$BODY }"

# Match for loops
pattern: "for $CONDITION { $$$BODY }"

# Match for range
pattern: "for $KEY, $VALUE := range $ITERABLE { $$$BODY }"

# Match switch
pattern: "switch $EXPR { $$$CASES }"

# Match select
pattern: "select { $$$CASES }"
```

### Common Patterns
```yaml
# Match imports
pattern: "import \"$PACKAGE\""
pattern: "import $ALIAS \"$PACKAGE\""
pattern: |
  import (
      $$$IMPORTS
  )

# Match variable declarations
pattern: "var $NAME $TYPE"
pattern: "var $NAME = $VALUE"
pattern: "$NAME := $VALUE"

# Match defer
pattern: "defer $EXPR"

# Match go routine
pattern: "go $FUNC($$$ARGS)"

# Match channel operations
pattern: "$CHAN <- $VALUE"
pattern: "$VAR := <-$CHAN"
pattern: "$VAR, $OK := <-$CHAN"
```

## C Patterns

### Function Definitions
```yaml
# Match function
pattern: "$RETURN $NAME($$$PARAMS) { $$$BODY }"

# Match function declaration
pattern: "$RETURN $NAME($$$PARAMS);"

# Match static function
pattern: "static $RETURN $NAME($$$PARAMS) { $$$BODY }"
```

### Type Definitions
```yaml
# Match struct
pattern: "struct $NAME { $$$FIELDS };"

# Match typedef
pattern: "typedef $TYPE $NAME;"

# Match typedef struct
pattern: "typedef struct { $$$FIELDS } $NAME;"

# Match enum
pattern: "enum $NAME { $$$VALUES };"
```

### Control Flow
```yaml
# Match if statements
pattern: "if ($CONDITION) { $$$BODY }"

# Match if-else
pattern: |
  if ($CONDITION) {
      $$$THEN_BODY
  } else {
      $$$ELSE_BODY
  }

# Match for loops
pattern: "for ($INIT; $CONDITION; $UPDATE) { $$$BODY }"

# Match while loops
pattern: "while ($CONDITION) { $$$BODY }"

# Match do-while loops
pattern: "do { $$$BODY } while ($CONDITION);"

# Match switch
pattern: "switch ($EXPR) { $$$CASES }"
```

### Common Patterns
```yaml
# Match includes
pattern: "#include <$HEADER>"
pattern: "#include \"$HEADER\""

# Match defines
pattern: "#define $NAME $VALUE"
pattern: "#define $NAME($$$PARAMS) $BODY"

# Match variable declarations
pattern: "$TYPE $NAME;"
pattern: "$TYPE $NAME = $VALUE;"

# Match pointer declarations
pattern: "$TYPE *$NAME"
pattern: "$TYPE **$NAME"

# Match array declarations
pattern: "$TYPE $NAME[$SIZE]"

# Match function calls
pattern: "$FUNC($$$ARGS)"
```

## Advanced Pattern Techniques

### Using Metavariables
- `$NAME` - Matches a single identifier
- `$$$NAME` - Matches zero or more elements (variadic)
- `$_` - Matches any single node (wildcard)

### Pattern Composition
```yaml
# Match functions that call a specific method
pattern: |
  def $FUNC($$$PARAMS):
      $$$BEFORE
      $OBJ.specific_method($$$ARGS)
      $$$AFTER

# Match classes with specific methods
pattern: |
  class $CLASS:
      $$$BEFORE
      def target_method(self, $$$PARAMS):
          $$$BODY
      $$$AFTER
```

### Negative Patterns
```yaml
# Match functions that don't have a return statement
rule:
  pattern: "def $NAME($$$PARAMS): $$$BODY"
  not:
    pattern: "return $$$"
```

### Contextual Patterns
```yaml
# Match only inside specific functions
rule:
  pattern: "$PATTERN"
  inside:
    pattern: "def specific_function($$$): $$$"
```

## Tips for Writing Patterns

1. **Start Simple**: Begin with basic patterns and gradually add complexity
2. **Use Metavariables**: Leverage `$NAME` and `$$$NAME` for flexibility
3. **Test Incrementally**: Test patterns on small code samples first
4. **Language Awareness**: Patterns are language-specific, use appropriate syntax
5. **Escape Special Characters**: Some characters may need escaping in YAML
6. **Use Multi-line Patterns**: For complex structures, use YAML's `|` for readability

## Common Pitfalls

1. **Missing Colons**: Python patterns often need colons after statements
2. **Bracket Matching**: Ensure all brackets/braces are properly balanced
3. **Whitespace Sensitivity**: Some languages are whitespace-sensitive
4. **Metavariable Naming**: Use descriptive names for metavariables
5. **Overly Specific**: Don't make patterns too specific unless needed

## Testing Patterns

Always test your patterns with the validate_pattern tool:

```python
# Example validation
result = validate_pattern(
    pattern="def $NAME($$$PARAMS): $$$BODY",
    language="python",
    code="def example(a, b): return a + b"
)
```