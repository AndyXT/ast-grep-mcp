# AST Grep Pattern Documentation

This comprehensive guide explains the AST Grep pattern syntax, providing detailed examples for all supported languages.

## Table of Contents
- [Pattern Syntax Basics](#pattern-syntax-basics)
- [Metavariables](#metavariables)
- [Common Pattern Idioms](#common-pattern-idioms)
- [Edge Cases & Troubleshooting](#edge-cases--troubleshooting)
- [Language-Specific Patterns](#language-specific-patterns)
  - [Python](#python)
  - [JavaScript & TypeScript](#javascript--typescript)
  - [Rust](#rust)
  - [Go](#go)
  - [C](#c)
- [Testing Patterns](#testing-patterns)

## Pattern Syntax Basics

AST Grep patterns are structural code patterns that match against the Abstract Syntax Tree (AST) representation of code, not just the text. This means patterns can match code with different formatting or whitespace.

### Basic Pattern Structure

A pattern is a piece of code with special metavariables that act as wildcards:

```
function $NAME($$$PARAMS) {
    $$$BODY
}
```

This pattern matches any JavaScript function declaration, capturing the name in `$NAME`, parameters in `$$$PARAMS`, and body in `$$$BODY`.

### Pattern Types

- **Literal Patterns**: Match code exactly (except for whitespace)
  ```python
  # Pattern: print("Hello")
  # Matches: print("Hello"), print( "Hello" )
  # Doesn't match: print('Hello'), print("hello")
  ```

- **Variable Patterns**: Match code with metavariables as placeholders
  ```python
  # Pattern: print($MESSAGE)
  # Matches: print("Hello"), print(x), print(func())
  ```

- **Structural Patterns**: Match based on code structure
  ```python
  # Pattern: if $CONDITION: $$$BODY
  # Matches any if statement regardless of condition or body
  ```

## Metavariables

Metavariables are the special placeholders that make patterns flexible:

| Metavariable | Description | Example |
|--------------|-------------|---------|
| `$NAME` | Matches a single AST node | `def $FUNC_NAME():` |
| `$$$NAME` | Matches multiple nodes (variadic) | `function f($$$PARAMS)` |
| `$...TYPE` | Matches node of specific type | `$...expression` |
| `$_` | Anonymous wildcard (single node) | `if $_: print()` |
| `$$$_` | Anonymous wildcard (multiple nodes) | `[$$$_]` |

### Choosing Between $ and $$$

- Use `$VAR` when matching a single node (variable name, expression, etc.)
- Use `$$$VAR` when matching potentially multiple nodes (function parameters, block statements, etc.)

## Common Pattern Idioms

These patterns represent common structures across multiple languages:

### Function Definitions
```python
# Python
def $NAME($$$PARAMS):
    $$$BODY

# JavaScript
function $NAME($$$PARAMS) {
    $$$BODY
}

# Rust
fn $NAME($$$PARAMS) -> $RETURN_TYPE {
    $$$BODY
}
```

### Conditional Statements
```python
# Python
if $CONDITION:
    $$$BODY

# JavaScript/C/Rust/Go
if ($CONDITION) {
    $$$BODY
}
```

### Loop Structures
```python
# Python - for loop
for $VAR in $ITERABLE:
    $$$BODY

# JavaScript - for loop
for ($INIT; $CONDITION; $UPDATE) {
    $$$BODY
}

# Rust - for loop
for $VAR in $ITERABLE {
    $$$BODY
}
```

## Edge Cases & Troubleshooting

### Common Issues

1. **Whitespace Mismatch**
   - AST Grep ignores most whitespace, but indentation in Python matters
   - Solution: Focus on structural elements, not formatting

2. **Nested Structures**
   - Matching nested structures can be tricky
   - Solution: Use `$$$` for inner blocks and be explicit about nesting levels

3. **Parentheses and Brackets**
   - Parentheses often have special meaning in AST structures
   - Solution: Be explicit about parentheses when they're part of an expression

4. **String Literals**
   - String quotes matter in patterns
   - Solution: Match the exact quote style (`"` vs `'`)

### Debugging Patterns

When a pattern doesn't match as expected:

1. Start with a simplified pattern and gradually add complexity
2. Use the pattern validation tool: `ast-grep-mcp validate-pattern`
3. Try interactive mode to see live pattern matches

## Language-Specific Patterns

### Python

Python patterns need to account for significant whitespace and different syntax forms.

#### Function Definitions

```python
# Standard function
def $NAME($$$PARAMS):
    $$$BODY

# Method in class
def $NAME(self, $$$PARAMS):
    $$$BODY

# Function with type hints
def $NAME($$$PARAMS) -> $RETURN_TYPE:
    $$$BODY
```

#### Class Definitions

```python
# Basic class
class $NAME:
    $$$BODY

# Class with inheritance
class $NAME($$$PARENTS):
    $$$BODY
```

#### Comprehensions and Generators

```python
# List comprehension
[$EXPR for $VAR in $ITERABLE]

# Dict comprehension
{$KEY: $VALUE for $VAR in $ITERABLE}

# Generator expression
($EXPR for $VAR in $ITERABLE)
```

#### Context Managers

```python
# With statement
with $CONTEXT as $VAR:
    $$$BODY
```

#### Decorators

```python
@$DECORATOR
def $NAME($$$PARAMS):
    $$$BODY
```

### JavaScript & TypeScript

JavaScript/TypeScript patterns need to handle many syntax variations and TypeScript's type annotations.

#### Function Variations

```javascript
// Function declaration
function $NAME($$$PARAMS) {
    $$$BODY
}

// Arrow function
($$$PARAMS) => $$$BODY

// Method in class/object
$NAME($$$PARAMS) {
    $$$BODY
}

// Async function
async function $NAME($$$PARAMS) {
    $$$BODY
}
```

#### TypeScript Types

```typescript
// Type annotation
const $NAME: $TYPE = $VALUE;

// Interface
interface $NAME {
    $$$BODY
}

// Generic type
$NAME<$TYPE>($$$PARAMS): $RETURN_TYPE {
    $$$BODY
}
```

#### React Components

```jsx
// Function component
function $NAME($$$PROPS) {
    return (
        $$$JSX
    );
}

// Class component
class $NAME extends React.Component {
    render() {
        return (
            $$$JSX
        );
    }
}
```

### Rust

Rust patterns need to consider lifetimes, traits, and macros.

#### Functions and Methods

```rust
// Function
fn $NAME($$$PARAMS) -> $RETURN_TYPE {
    $$$BODY
}

// Method impl
impl $TYPE {
    fn $NAME(&self, $$$PARAMS) -> $RETURN_TYPE {
        $$$BODY
    }
}
```

#### Structs and Enums

```rust
// Struct definition
struct $NAME {
    $$$FIELDS
}

// Enum definition
enum $NAME {
    $$$VARIANTS
}
```

#### Traits and Implementations

```rust
// Trait definition
trait $NAME {
    $$$METHODS
}

// Trait implementation
impl $TRAIT for $TYPE {
    $$$METHODS
}
```

#### Macros

```rust
// Macro invocation
$NAME!($$$ARGS);
```

### Go

Go patterns need to handle its C-like syntax with distinctive features.

#### Functions and Methods

```go
// Function
func $NAME($$$PARAMS) $$$RETURN_TYPES {
    $$$BODY
}

// Method
func ($RECEIVER $TYPE) $NAME($$$PARAMS) $$$RETURN_TYPES {
    $$$BODY
}
```

#### Structs and Interfaces

```go
// Struct
type $NAME struct {
    $$$FIELDS
}

// Interface
type $NAME interface {
    $$$METHODS
}
```

#### Concurrency

```go
// Goroutine
go $FUNCTION($$$ARGS)

// Channel operations
$CHANNEL <- $VALUE
$VAR := <-$CHANNEL
```

### C

C patterns need to handle preprocessor directives and pointer syntax.

#### Functions

```c
// Function definition
$RETURN_TYPE $NAME($$$PARAMS) {
    $$$BODY
}

// Function declaration
$RETURN_TYPE $NAME($$$PARAMS);
```

#### Structs and Typedefs

```c
// Struct definition
struct $NAME {
    $$$FIELDS
};

// Typedef
typedef struct $NAME {
    $$$FIELDS
} $TYPE_NAME;
```

#### Preprocessor Directives

```c
// Include directive
#include <$HEADER>

// Define directive
#define $NAME $VALUE

// Conditional compilation
#ifdef $SYMBOL
    $$$BODY
#endif
```

#### Pointers and Memory Operations

```c
// Pointer declaration
$TYPE *$NAME;

// Memory allocation
$PTR = malloc($SIZE);

// Memory access
*$PTR = $VALUE;
```

## Testing Patterns

To test and refine your patterns:

1. Use the interactive mode:
   ```bash
   ast-grep-mcp interactive
   ```

2. Validate patterns against test code:
   ```bash
   ast-grep-mcp validate-pattern --code "test code" --pattern "your pattern"
   ```

3. Check for pattern syntax errors:
   ```bash
   ast-grep-mcp validate-pattern --pattern "your pattern"
   ```

4. Get suggested corrections when patterns don't match:
   ```bash
   ast-grep-mcp analyze-code --pattern "your pattern" --code "test code" --suggest
   ```

Remember that AST Grep pattern matching is structural, not textual, so focus on the code structure rather than exact formatting. 