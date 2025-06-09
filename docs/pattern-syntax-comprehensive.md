# Comprehensive AST-grep Pattern Syntax Guide

## Overview

AST-grep uses a pattern syntax that matches code based on its Abstract Syntax Tree (AST) structure rather than text. This guide explains the pattern syntax with clear examples and common pitfalls.

## Metavariable Syntax

### Single Metavariables (`$NAME`)
- Captures a single AST node
- Must start with `$` followed by uppercase letters, numbers, or underscores
- Examples:
  ```
  $VAR        # Captures a variable name
  $FUNC       # Captures a function name
  $EXPR       # Captures an expression
  ```

### Variadic Metavariables (`$$$NAME`)
- Captures zero or more AST nodes
- Must use exactly three dollar signs: `$$$`
- Commonly used for parameters, arguments, body statements
- Examples:
  ```
  $$$PARAMS   # Captures function parameters
  $$$ARGS     # Captures function arguments
  $$$BODY     # Captures statement blocks
  ```

### Anonymous Metavariables
- `$_` - Matches any single node (wildcard)
- `$$$` - Matches any sequence of nodes

### Common Mistakes
```
# WRONG - Double dollar is invalid
$$PARAMS

# RIGHT - Use triple dollar for multiple items
$$$PARAMS

# WRONG - Space after dollar
$ NAME

# RIGHT - No space after dollar
$NAME
```

## Language-Specific Patterns

### Rust

#### Functions
```rust
# Match any function
fn $NAME

# Match function with parameters and body
fn $NAME($$$PARAMS) { $$$BODY }

# Match async function
async fn $NAME($$$PARAMS) { $$$BODY }

# Match function with return type
fn $NAME($$$PARAMS) -> $RET_TYPE { $$$BODY }

# Match public function
pub fn $NAME($$$PARAMS) { $$$BODY }
```

#### Common Rust Patterns
```rust
# Match unwrap() calls
$EXPR.unwrap()

# Match Result handling
match $EXPR {
    Ok($VAL) => $$$OK_BODY,
    Err($ERR) => $$$ERR_BODY,
}

# Match struct definition
struct $NAME {
    $$$FIELDS
}

# Match impl block
impl $TYPE {
    $$$METHODS
}

# Match trait implementation
impl $TRAIT for $TYPE {
    $$$METHODS
}

# Match use statements
use $$$PATH

# Match tokio::spawn calls
tokio::spawn($$$ARGS)
```

### Python

#### Functions
```python
# Match function definition
def $NAME($$$PARAMS):
    $$$BODY

# Match method with self
def $NAME(self, $$$PARAMS):
    $$$BODY

# Match async function
async def $NAME($$$PARAMS):
    $$$BODY
```

#### Common Python Patterns
```python
# Match class definition
class $NAME:
    $$$BODY

# Match class with inheritance
class $NAME($$$BASES):
    $$$BODY

# Match if statement
if $COND:
    $$$BODY

# Match list comprehension
[$EXPR for $VAR in $ITER]

# Match exception handling
try:
    $$$TRY_BODY
except $EXCEPTION:
    $$$EXCEPT_BODY

# Match imports
import $MODULE
from $MODULE import $NAME
```

### JavaScript/TypeScript

#### Functions
```javascript
# Match function declaration
function $NAME($$$PARAMS) {
    $$$BODY
}

# Match arrow function
($$$PARAMS) => $EXPR

# Match arrow function with block
($$$PARAMS) => {
    $$$BODY
}

# Match async function
async function $NAME($$$PARAMS) {
    $$$BODY
}

# Match method in object/class
$NAME($$$PARAMS) {
    $$$BODY
}
```

#### Common JavaScript Patterns
```javascript
# Match variable declarations
const $NAME = $VALUE
let $NAME = $VALUE
var $NAME = $VALUE

# Match class definition
class $NAME {
    $$$BODY
}

# Match React component (JSX)
<$COMPONENT $$$PROPS />
<$COMPONENT $$$PROPS>
    $$$CHILDREN
</$COMPONENT>

# Match import statements
import $NAME from '$MODULE'
import { $$$NAMES } from '$MODULE'

# Match promise chains
$PROMISE.then($CALLBACK).catch($ERROR_HANDLER)

# Match async/await
await $EXPR
```

### Go

#### Functions
```go
# Match function
func $NAME($$$PARAMS) {
    $$$BODY
}

# Match function with return type
func $NAME($$$PARAMS) $RETURN {
    $$$BODY
}

# Match method
func ($RECEIVER $TYPE) $NAME($$$PARAMS) {
    $$$BODY
}
```

#### Common Go Patterns
```go
# Match struct definition
type $NAME struct {
    $$$FIELDS
}

# Match interface
type $NAME interface {
    $$$METHODS
}

# Match error check
if err != nil {
    $$$BODY
}

# Match goroutine
go $FUNC($$$ARGS)

# Match channel operations
$CHAN <- $VALUE
$VAR := <-$CHAN
```

## Pattern Matching Tips

### 1. Start Simple
Instead of writing complex patterns, start with simple ones:
```rust
# Instead of this complex pattern that might fail:
async fn $NAME($$$PARAMS) -> Result<$OK, $ERR> {
    $$$BODY
}

# Start with this:
async fn $NAME
```

### 2. Use Structural Patterns
AST-grep matches structure, not text. These are equivalent:
```javascript
// Both matched by: function $NAME($$$PARAMS) { $$$BODY }
function foo(a, b) { return a + b; }
function foo(a,b){return a+b;}
```

### 3. Pattern Validation
Before using a pattern, validate it:
- Test with simple code samples
- Check for balanced brackets/braces
- Ensure metavariables are properly formed

### 4. Debugging Patterns
When a pattern doesn't match:
1. Simplify it to identify which part fails
2. Check metavariable syntax ($ vs $$$)
3. Verify language-specific syntax requirements
4. Use the tool's pattern validation features

## Common Pitfalls and Solutions

### Pitfall 1: Complex Parameter Patterns
```rust
# This might not match:
fn $NAME($PARAM1: $TYPE1, $PARAM2: $TYPE2)

# Use this instead:
fn $NAME($$$PARAMS)
```

### Pitfall 2: Expecting Text Matching
```python
# This won't match comments or specific formatting:
def $NAME($$$PARAMS):
    # This is a comment
    $$$BODY

# Patterns match AST structure, not comments or whitespace
```

### Pitfall 3: Over-Specific Patterns
```javascript
# Too specific:
const $NAME = async ($PARAM1, $PARAM2) => {
    return await $EXPR;
}

# More flexible:
const $NAME = async ($$$PARAMS) => {
    $$$BODY
}
```

### Pitfall 4: Mixing Metavariable Types
```rust
# Wrong - can't use same name for different captures:
impl $TYPE {
    fn $TYPE() {}  // Error: $TYPE already used
}

# Correct - use different names:
impl $TYPE {
    fn $METHOD() {}
}
```

## Advanced Patterns

### Nested Patterns
```rust
# Match nested function calls
$OUTER($$$ARGS1, $INNER($$$ARGS2), $$$ARGS3)

# Match chained method calls
$EXPR.$METHOD1($$$ARGS1).$METHOD2($$$ARGS2)
```

### Alternative Patterns
When one pattern doesn't work, try alternatives:
```python
# If this doesn't match:
class $NAME($BASE):
    $$$BODY

# Try simpler:
class $NAME
```

### Pattern Context
Some patterns need context:
```rust
# This matches any unwrap(), but in context:
$EXPR.unwrap()

# You might want to capture more:
let $VAR = $EXPR.unwrap();
```

## Best Practices

1. **Use Language-Specific Pattern Libraries**: Each language handler provides tested patterns
2. **Test Patterns Incrementally**: Build complex patterns step by step
3. **Prefer Simple Patterns**: They're more reliable and match more cases
4. **Document Your Patterns**: Explain what each pattern matches and why
5. **Handle Edge Cases**: Consider different ways code can be written
6. **Use Pattern Validation**: Always validate patterns before using in production

## Quick Reference

### Metavariables
- `$NAME` - Single capture
- `$$$NAME` - Multiple capture (variadic)
- `$_` - Single wildcard
- `$$$` - Multiple wildcard

### Common Captures
- `$FUNC`, `$METHOD` - Function/method names
- `$VAR`, `$NAME` - Variable names
- `$TYPE` - Type names
- `$EXPR` - Expressions
- `$$$PARAMS` - Parameter lists
- `$$$ARGS` - Argument lists
- `$$$BODY` - Statement blocks

### Language Keywords
Patterns must use proper language syntax:
- Python: `:` after function/class definitions
- JavaScript: `{}` for blocks
- Rust: `->` for return types
- Go: Uppercase for exported names