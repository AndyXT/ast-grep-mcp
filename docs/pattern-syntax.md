# AST-Grep Pattern Syntax Guide

This guide explains the pattern syntax for AST-Grep in detail, with examples for different programming languages.

## Introduction to AST Pattern Matching

AST-Grep uses a pattern language specifically designed for Abstract Syntax Tree (AST) matching. This allows for more precise and semantically meaningful searches compared to traditional text-based approaches.

When writing patterns, you're not matching text, but rather the structure of the code. This means your patterns can ignore whitespace, comments, and specific formatting variations while focusing on the code's meaning.

## Core Syntax Elements

### Metavariables

Metavariables are placeholders that match code elements. They always start with `$`.

| Syntax | Description | Example | Matches |
|--------|-------------|---------|---------|
| `$NAME` | Named metavariable | `def $FUNC_NAME():` | `def hello():`, `def process_data():` |
| `$_` | Wildcard (matches any single node) | `if $_:` | `if x > 5:`, `if True:` |
| `$$$` | Ellipsis (matches zero or more nodes) | `def func($$$PARAMS):` | `def func():`, `def func(a, b=5):` |
| `$...TYPE` | Typed metavariable | `$...expression` | Any expression node |

### Literal Matching

To match literals, simply write the code as it appears:

| Syntax | Example | Matches |
|--------|---------|---------|
| Identifiers | `print` | The identifier `print` |
| Keywords | `if` | The keyword `if` |
| Operators | `+`, `==` | The specific operators |
| Literals | `"string"`, `42` | String or number literals |

## Advanced Pattern Features

### Nested Patterns

Patterns can be nested to match complex structures:

```
if $CONDITION:
    $$$BODY
```

This matches any `if` statement, capturing the condition and the body.

### Pattern Modifiers

Some nodes can use modifiers to refine matches:

| Modifier | Description | Example |
|----------|-------------|---------|
| `?` | Optional match | `$PARAM?` matches an optional parameter |
| `*` | Zero or more | `$ITEM*` matches zero or more items |
| `+` | One or more | `$ITEM+` matches one or more items |

## Language-Specific Patterns

### Python

#### Function Definitions

```
def $NAME($$$PARAMS):
    $$$BODY
```

Matches any function definition, capturing the name, parameters, and body.

#### Class Definitions

```
class $CLASS_NAME($$$PARENTS):
    $$$BODY
```

Matches class definitions with optional inheritance.

#### Decorators

```
@$DECORATOR
def $FUNC_NAME($$$PARAMS):
    $$$BODY
```

Matches decorated functions.

#### Context Managers

```
with $EXPR as $VAR:
    $$$BODY
```

Matches with statements.

### JavaScript/TypeScript

#### Function Declarations

```
function $NAME($$$PARAMS) {
    $$$BODY
}
```

Matches function declarations.

#### Arrow Functions

```
($$$PARAMS) => $$$BODY
```

Matches arrow functions.

#### Class Definitions

```
class $NAME {
    $$$METHODS
}
```

Matches class definitions.

#### JSX/React Components

```
<$COMPONENT $$$PROPS>$$$CHILDREN</$COMPONENT>
```

Matches JSX components.

### Other Languages

AST-Grep supports multiple languages including:
- C/C++
- Go
- Rust
- Lua
- And more

Patterns for these languages follow similar principles, but with syntax adjusted to the target language.

## Pattern Writing Best Practices

### Start Simple

Begin with simple patterns and incrementally add complexity:

1. **Start with structure**: `if $CONDITION: $$$BODY`
2. **Add constraints**: `if $CONDITION == True: $$$BODY`
3. **Refine as needed**: `if $CONDITION == True and $X: $$$BODY`

### Handle Whitespace Carefully

AST-Grep is generally whitespace-insensitive for matching, but whitespace is important for:

1. Indentation in Python
2. Distinguishing between statements in languages without semicolons

### Use Named Metavariables Meaningfully

Choose meaningful names for your metavariables to make patterns more readable:

- Good: `def $FUNC_NAME($$$PARAMS):`
- Less Clear: `def $X($$$Y):`

### Use Ellipsis Appropriately

Use `$$$` when you need to match multiple nodes or don't care about specific parts:

- Function parameters: `function name($$$PARAMS)`
- Function bodies: `function name() { $$$BODY }`
- List items: `[$$$ITEMS]`

## Refactoring Patterns

When performing refactoring, the replacement pattern must use the same metavariables that were matched in the search pattern.

### Example:

**Search pattern**:
```
print($$$ARGS)
```

**Replacement pattern**:
```
console.log($$$ARGS)
```

This would convert Python's `print()` calls to JavaScript's `console.log()` calls, preserving all arguments.

## Common Patterns by Use Case

### Finding Function Calls

```
$FUNC_NAME($$$ARGS)
```

### Finding API Usage

```
requests.get($URL)
```

### Finding Error Handling

Python:
```
try:
    $$$TRY_BODY
except $EXCEPTION:
    $$$EXCEPT_BODY
```

JavaScript:
```
try {
    $$$TRY_BODY
} catch ($ERROR) {
    $$$CATCH_BODY
}
```

### Finding Import Statements

Python:
```
import $MODULE
```
or
```
from $MODULE import $NAMES
```

JavaScript:
```
import $WHAT from $SOURCE
```
or
```
const $NAME = require($SOURCE)
```

## Debugging Pattern Matches

When a pattern isn't matching as expected:

1. **Simplify**: Reduce the pattern to a simpler form and verify it matches
2. **Check syntax**: Ensure your pattern is valid for the target language
3. **Use interactive mode**: Test patterns in the interactive mode
4. **Verify AST structure**: The structure might be different than expected

## Working with AST Structure

Different languages represent the same constructs with different AST structures. For example:

- In Python, a `for` loop has a different structure than in JavaScript
- Class declarations vary between languages
- Function calls may have different representations

The best approach is to write a small example in the target language and test your pattern in interactive mode to understand the structure.

## Further Resources

- [AST-Grep GitHub Repository](https://github.com/ast-grep/ast-grep)
- [Tree-Sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Tree-Sitter Playground](https://tree-sitter.github.io/tree-sitter/playground) 