# AST-Grep Pattern Quick Reference

## Universal Patterns (All Languages)

| Pattern | Description | Example Match |
|---------|-------------|---------------|
| `$VAR` | Single variable/identifier | `x`, `userName`, `MAX_SIZE` |
| `$VALUE` | Any value/expression | `42`, `"hello"`, `obj.method()` |
| `$EXPR` | Any expression | `a + b`, `func()`, `x > 5` |
| `$TYPE` | Type name | `String`, `int`, `MyClass` |
| `$NAME` | Any identifier | `myFunc`, `ClassName`, `var_name` |

## Rust Patterns

### Functions
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `fn $NAME` | Any function | Find all functions |
| `async fn $NAME` | Async functions | Find async functions |
| `pub fn $NAME` | Public functions | Find public API |
| `pub async fn $NAME` | Public async functions | Find public async API |
| `fn main()` | Main function | Find entry point |
| `#[test]` | Test functions | Find tests |

### Traits & Implementations
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `impl $TYPE` | Type implementations | Find impls |
| `impl $TRAIT for $TYPE` | Trait implementations | Find trait impls |
| `trait $NAME` | Trait definitions | Find traits |
| `#[derive($TRAIT)]` | Derive macros | Find derived traits |

### Async/Await
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `$EXPR.await` | Await expressions | Find await points |
| `async` | Async blocks | Find async contexts |
| `tokio::spawn` | Tokio spawns | Find task spawning |
| `async move` | Async move blocks | Find async closures |

### Error Handling
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `$EXPR?` | Question mark operator | Find error propagation |
| `$EXPR.unwrap()` | Unwrap calls | Find panic points |
| `$EXPR.expect($MSG)` | Expect calls | Find panic points |
| `Result<$OK, $ERR>` | Result types | Find Result usage |

## JavaScript/TypeScript Patterns

### Functions
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `function $NAME` | Function declarations | Find functions |
| `async function $NAME` | Async functions | Find async functions |
| `const $NAME = function` | Function expressions | Find function vars |
| `const $NAME = () =>` | Arrow functions | Find arrow functions |
| `$OBJ.$METHOD` | Method calls | Find method usage |

### Classes & Objects
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `class $NAME` | Class declarations | Find classes |
| `new $CLASS` | Constructor calls | Find instantiations |
| `extends $BASE` | Class inheritance | Find subclasses |
| `super` | Super calls | Find parent calls |

### Async/Promises
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `await $EXPR` | Await expressions | Find await usage |
| `$PROMISE.then` | Promise then | Find promise chains |
| `$PROMISE.catch` | Promise catch | Find error handlers |
| `Promise.all` | Promise.all calls | Find parallel ops |

### Imports/Exports
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `import $NAME` | Default imports | Find imports |
| `import { $NAME }` | Named imports | Find named imports |
| `require($MODULE)` | CommonJS imports | Find requires |
| `export default` | Default exports | Find exports |

## Python Patterns

### Functions & Classes
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `def $NAME` | Function definitions | Find functions |
| `async def $NAME` | Async functions | Find async functions |
| `class $NAME:` | Class definitions | Find classes |
| `@$DECORATOR` | Decorators | Find decorated items |
| `__init__` | Constructors | Find initializers |

### Control Flow
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `if $COND:` | If statements | Find conditionals |
| `for $VAR in $ITER:` | For loops | Find iterations |
| `while $COND:` | While loops | Find loops |
| `try:` | Try blocks | Find error handling |
| `except $TYPE` | Except clauses | Find error types |

### Imports
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `import $MODULE` | Simple imports | Find imports |
| `from $MODULE import $NAME` | From imports | Find specific imports |
| `import $MODULE as $ALIAS` | Aliased imports | Find aliases |

## Go Patterns

### Functions
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `func $NAME` | Functions | Find functions |
| `func ($RECV) $NAME` | Methods | Find methods |
| `defer $FUNC` | Defer statements | Find defers |
| `go $FUNC` | Goroutines | Find concurrency |

### Types
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `type $NAME struct` | Struct types | Find structs |
| `type $NAME interface` | Interfaces | Find interfaces |
| `chan $TYPE` | Channel types | Find channels |
| `make($TYPE)` | Make calls | Find allocations |

### Error Handling
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `if err != nil` | Error checks | Find error handling |
| `return err` | Error returns | Find error propagation |
| `panic($MSG)` | Panic calls | Find panics |

## C Patterns

### Functions & Types
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `void $NAME` | Void functions | Find void functions |
| `int $NAME` | Int functions | Find int functions |
| `struct $NAME` | Struct declarations | Find structs |
| `typedef $TYPE $NAME` | Typedefs | Find type aliases |
| `#define $NAME` | Macros | Find macros |

### Memory Management
| Pattern | Matches | Use Case |
|---------|---------|----------|
| `malloc($SIZE)` | Malloc calls | Find allocations |
| `free($PTR)` | Free calls | Find deallocations |
| `NULL` | NULL references | Find null checks |
| `*$PTR` | Pointer derefs | Find pointer usage |

## Tips for Success

1. **Start Simple**: `fn $NAME` is better than `fn $NAME($$$PARAMS) { $$$BODY }`
2. **Language Syntax Matters**: Python needs colons, Rust doesn't need semicolons in patterns
3. **Test First**: Try patterns on small code samples before large codebases
4. **Use Exact Strings**: For specific API calls like `console.log` or `tokio::spawn`
5. **Avoid $$$**: Multiple-capture rarely works as expected

## Common Mistakes to Avoid

❌ **Don't use complex parameter lists**: `fn foo($$$PARAMS)`
✅ **Do use simple patterns**: `fn foo`

❌ **Don't nest metavariables**: `match $EXPR { $PATTERN => $$$BODY }`
✅ **Do use flat patterns**: `match $EXPR`

❌ **Don't forget language syntax**: `def foo` (Python)
✅ **Do include required syntax**: `def foo:` (Python)

❌ **Don't over-specify**: `let x: i32 = 42;`
✅ **Do capture what varies**: `let $VAR = $VALUE`