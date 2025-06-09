# AST-GREP Pattern Syntax Guide

## Understanding Metavariables

AST-grep uses metavariables to capture parts of the code. The syntax is:

- `$NAME` - Captures a single AST node (identifier, expression, etc.)
- `$$NAME` - **DEPRECATED** - Do not use double dollar signs
- `$$$NAME` - Captures zero or more nodes (variadic)

## Important Rules

1. **Always use single `$` for single captures**
2. **Always use triple `$$$` for multiple captures**
3. **Never use `$$` - it's not valid**

## Language-Specific Patterns

### Rust

```yaml
# Function definitions
- Simple function: fn $NAME($$$PARAMS) { $$$BODY }
- Async function: async fn $NAME($$$PARAMS) { $$$BODY }
- Public async: pub async fn $NAME($$$PARAMS) { $$$BODY }
- Generic function: fn $NAME<$$$GENERICS>($$$PARAMS) { $$$BODY }

# Impl blocks
- Basic impl: impl $TYPE { $$$BODY }
- Trait impl: impl $TRAIT for $TYPE { $$$BODY }
- Generic impl: impl<$$$GENERICS> $TYPE { $$$BODY }

# Match expressions
- Match: match $EXPR { $$$ARMS }
- If let: if let $PATTERN = $EXPR { $$$BODY }

# Common patterns
- Unwrap call: $EXPR.unwrap()
- Option/Result: Result<$OK, $ERR>
- Use statement: use $$$PATH;
```

### Python

```yaml
# Function definitions
- Simple function: def $NAME($$$PARAMS): $$$BODY
- Async function: async def $NAME($$$PARAMS): $$$BODY
- Method: def $NAME(self, $$$PARAMS): $$$BODY

# Class definitions
- Simple class: class $NAME: $$$BODY
- Inheritance: class $NAME($$$BASES): $$$BODY

# Common patterns
- Import: import $MODULE
- From import: from $MODULE import $$$NAMES
- Try/except: try: $$$TRY except $EXCEPTION: $$$EXCEPT
```

### JavaScript/TypeScript

```yaml
# Function definitions
- Function declaration: function $NAME($$$PARAMS) { $$$BODY }
- Arrow function: ($$$PARAMS) => $$$BODY
- Async function: async function $NAME($$$PARAMS) { $$$BODY }
- Method: $NAME($$$PARAMS) { $$$BODY }

# Class definitions
- Class: class $NAME { $$$BODY }
- Extends: class $NAME extends $BASE { $$$BODY }

# Common patterns
- Import: import $$$IMPORTS from '$MODULE'
- Export: export $$$EXPORTS
- Await: await $EXPR
```

## Pattern Testing

Always test your patterns with simple code first:

```rust
// Test code
async fn test() {}

// Pattern that WORKS
async fn $NAME($$$PARAMS) { $$$BODY }

// Pattern that FAILS (double $$)
async fn $NAME($$PARAMS) { $$BODY }
```

## Common Mistakes

1. **Using `$$` instead of `$` or `$$$`**
   - Wrong: `fn $NAME($$PARAMS)`
   - Right: `fn $NAME($$$PARAMS)`

2. **Missing spaces in patterns**
   - Wrong: `asyncfn$NAME`
   - Right: `async fn $NAME`

3. **Over-specific patterns**
   - Wrong: `pub async fn $NAME<T>($$$PARAMS) -> Result<(), Error>`
   - Right: `async fn $NAME($$$PARAMS)`

4. **Not escaping special characters**
   - Use exact syntax as it appears in code

## Debugging Tips

1. Start with the simplest pattern possible
2. Add complexity gradually
3. Use `analyze_code` to test patterns on small snippets
4. Check that your language is correctly specified
5. Ensure file extensions match the language