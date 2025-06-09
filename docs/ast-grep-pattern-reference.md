# AST-Grep Pattern Reference Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Basic Pattern Syntax](#basic-pattern-syntax)
3. [Metavariables](#metavariables)
4. [Language-Specific Patterns](#language-specific-patterns)
5. [Common Issues and Solutions](#common-issues-and-solutions)
6. [Best Practices](#best-practices)

## Introduction

AST-grep uses pattern matching based on Abstract Syntax Trees (AST) rather than text. This means patterns must follow the syntactic rules of the target language.

### Key Principles
- Patterns must be syntactically valid in the target language
- Simpler patterns are more reliable than complex ones
- Use metavariables to capture varying parts of code

## Basic Pattern Syntax

### Literal Matching
Match exact code snippets:
```
// Matches: console.log("hello")
console.log("hello")

// Matches: return 42;
return 42;
```

### Metavariables

#### Single Element Capture: `$NAME`
Captures a single AST node:
```
// Pattern: let $VAR = $VALUE
// Matches: let x = 5
// Matches: let name = "John"
// Captures: VAR=x, VALUE=5
```

#### Multiple Elements Capture: `$$$NAME`
Captures multiple AST nodes (use sparingly - often causes issues):
```
// Pattern: function($$$ARGS)
// Matches: function(a, b, c)
// Captures: ARGS=[a, b, c]
```

### Important Limitations
- **Complex patterns with `$$$` often fail** - prefer simpler patterns
- **Nested metavariables are unreliable**
- **Pattern must be syntactically complete**

## Language-Specific Patterns

### Rust

#### Functions
```rust
// ✅ GOOD - Simple patterns that work reliably
fn $NAME                     // Any function
async fn $NAME               // Async function
pub fn $NAME                 // Public function
pub async fn $NAME           // Public async function

// ❌ BAD - Complex patterns that often fail
fn $NAME($$$PARAMS) { $$$BODY }     // Too complex
async fn $NAME<$T>($$$PARAMS) -> $RET { $$$BODY }  // Way too complex
```

#### Async Patterns
```rust
// ✅ GOOD
async                        // Async blocks
$EXPR.await                  // Await expressions
tokio::spawn                 // Tokio spawn calls

// ❌ BAD
async { $$$BODY }           // Complex async block
```

#### Trait Implementations
```rust
// ✅ GOOD
impl $TRAIT for $TYPE        // Basic impl
impl<$T> $TRAIT for $TYPE    // Generic impl

// ❌ BAD
impl $TRAIT for $TYPE { $$$METHODS }  // Too complex
```

#### Common Rust Patterns
```rust
// Match expressions
match $EXPR

// Struct declarations
struct $NAME

// Enum declarations
enum $NAME

// Use statements
use $PATH

// Derive macros
#[derive($TRAIT)]

// Result handling
$EXPR?
$EXPR.unwrap()
$EXPR.expect($MSG)
```

### JavaScript/TypeScript

#### Functions
```javascript
// ✅ GOOD
function $NAME               // Function declaration
const $NAME = function       // Function expression
const $NAME = () =>         // Arrow function
async function $NAME        // Async function

// ❌ BAD
function $NAME($$$PARAMS) { $$$BODY }  // Too complex
```

#### Classes and Objects
```javascript
// ✅ GOOD
class $NAME                  // Class declaration
new $CLASS                   // Constructor calls
$OBJ.$METHOD                 // Method calls

// ❌ BAD
class $NAME extends $BASE { $$$BODY }  // Too complex
```

#### Common Patterns
```javascript
// Imports
import $NAME
import { $NAME }
require($MODULE)

// Async/Promise
await $EXPR
$PROMISE.then
$PROMISE.catch

// Console
console.log
console.error
```

### Python

#### Functions and Classes
```python
// ✅ GOOD
def $NAME                    // Function definition
async def $NAME              // Async function
class $NAME:                 // Class definition
@$DECORATOR                  // Decorators

// ❌ BAD
def $NAME($$$PARAMS): $$$BODY  // Too complex
```

#### Control Flow
```python
// ✅ GOOD
if $COND:                    // If statement
for $VAR in $ITER:          // For loop
while $COND:                // While loop
try:                        // Try block

// Note: Python patterns require colons!
```

#### Common Patterns
```python
// Imports
import $MODULE
from $MODULE import $NAME

// Exception handling
raise $EXCEPTION
except $TYPE

// Comprehensions
[$EXPR for $VAR in $ITER]
{$KEY: $VALUE for $VAR in $ITER}
```

### Go

#### Functions and Methods
```go
// ✅ GOOD
func $NAME                   // Function
func ($RECV) $NAME          // Method
defer $FUNC                  // Defer statement
go $FUNC                    // Goroutine

// ❌ BAD
func $NAME($$$PARAMS) $RET { $$$BODY }  // Too complex
```

#### Types and Interfaces
```go
// ✅ GOOD
type $NAME struct           // Struct type
type $NAME interface        // Interface type
chan $TYPE                  // Channel type

// ❌ BAD
type $NAME struct { $$$FIELDS }  // Too complex
```

### C

#### Functions and Types
```c
// ✅ GOOD
void $NAME                   // Void function
int $NAME                    // Int function
struct $NAME                 // Struct declaration
typedef $TYPE $NAME          // Typedef

// ❌ BAD
$TYPE $NAME($$$PARAMS) { $$$BODY }  // Too complex
```

## Common Issues and Solutions

### Issue 1: Pattern Too Complex
**Problem**: `async fn $NAME($$$PARAMS) { $$$BODY }` returns no matches
**Solution**: Simplify to `async fn $NAME`

### Issue 2: Missing Language Syntax
**Problem**: `def $NAME` fails in Python
**Solution**: Use `def $NAME:` (colon required)

### Issue 3: Token Limit Exceeded
**Problem**: Large result sets cause errors
**Solution**: Use pagination parameters or more specific patterns

### Issue 4: Metavariable Not Captured
**Problem**: `$$$PARAMS` not capturing parameters
**Solution**: Avoid `$$$` in complex contexts; use simpler patterns

## Best Practices

### 1. Start Simple
Begin with the simplest pattern that identifies your target:
- Instead of `fn calculate_sum(a: i32, b: i32) -> i32 { a + b }`
- Use `fn calculate_sum`

### 2. Test Incrementally
Build patterns step by step:
1. Start: `fn`
2. Add name: `fn $NAME`
3. Only add more if needed

### 3. Use Language-Specific Features
Each language has unique patterns:
- Rust: `impl $TRAIT for $TYPE`
- JavaScript: `$PROMISE.then`
- Python: `@$DECORATOR`

### 4. Avoid Complex Nesting
Instead of nested patterns:
```
// ❌ Bad
match $EXPR { 
    $PATTERN => { 
        if $COND { $$$BODY } 
    } 
}

// ✅ Good
match $EXPR
// Then search within matches for: if $COND
```

### 5. Use File Extensions
Specify file extensions to improve performance:
```
file_extensions: [".rs"]  // For Rust only
file_extensions: [".js", ".ts"]  // For JavaScript/TypeScript
```

## Pattern Testing

### Quick Test Method
1. Use a simple code sample
2. Start with literal matching
3. Gradually introduce metavariables
4. Check captured variables in results

### Debugging Failed Patterns
1. Check syntax validity in target language
2. Remove `$$$` metavariables
3. Simplify nested structures
4. Verify language detection

## Advanced Features

### Pattern Composition
Combine simple patterns programmatically rather than creating complex single patterns.

### Context Awareness
Use `search_directory_with_context` for surrounding code context.

### Performance Optimization
- Set `max_results_per_file` to limit matches
- Use `max_file_size` to skip large files
- Enable `parallel` processing for large codebases

## Additional Resources

- [AST Explorer](https://astexplorer.net/) - Visualize AST structures
- [Pattern Builder API](./pattern-builder.md) - Programmatic pattern construction
- [Language Handlers](./language-handlers.md) - Language-specific details