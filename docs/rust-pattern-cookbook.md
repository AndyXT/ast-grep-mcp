# Rust Pattern Cookbook for AST-GREP

## Important Notes

1. **Rust patterns in ast-grep have limitations with function parameters**
   - You cannot use `$$$PARAMS` for function parameters
   - Use simpler patterns that match function signatures

2. **Always test patterns on simple code first**

## Working Patterns

### Function Definitions

```yaml
# Match any function by name
pattern: fn $NAME

# Match async functions
pattern: async fn $NAME

# Match public async functions  
pattern: pub async fn $NAME

# Match functions with specific names
pattern: fn connect
pattern: async fn process_barcode

# Match function with return type (no params)
pattern: fn $NAME() -> $TYPE

# Match function body (only works for parameterless functions)
pattern: fn $NAME() { $$$BODY }
```

### Working with Specific Signatures

```yaml
# Match exact function signature
pattern: pub async fn connect(port: String) -> Result<(), Error>

# Match with one metavariable
pattern: pub async fn $NAME(port: String) -> Result<(), Error>

# Match with parameter name as metavar
pattern: async fn process($PARAM: String)
```

### Method Calls and Expressions

```yaml
# Match unwrap calls
pattern: $EXPR.unwrap()

# Match expect calls
pattern: $EXPR.expect($MSG)

# Match Result types
pattern: Result<$OK, $ERR>

# Match Option types
pattern: Option<$TYPE>
```

### Macros

```yaml
# Match println! macro
pattern: println!($$$ARGS)

# Match any macro invocation
pattern: $MACRO!($$$ARGS)

# Match format! macro
pattern: format!($$$ARGS)
```

### Structs and Enums

```yaml
# Match struct definition
pattern: struct $NAME

# Match struct with body
pattern: struct $NAME { $$$FIELDS }

# Match enum
pattern: enum $NAME { $$$VARIANTS }

# Match impl block
pattern: impl $TYPE

# Match trait impl
pattern: impl $TRAIT for $TYPE
```

### Pattern Matching

```yaml
# Match match expressions
pattern: match $EXPR

# Match if let
pattern: if let $PATTERN = $EXPR

# Match specific match arm
pattern: Ok($VALUE) => $EXPR
```

### Common Anti-patterns

```yaml
# Unwrap without error handling
pattern: $EXPR.unwrap()

# Cloning in loops (partial match)
pattern: $EXPR.clone()

# Unsafe blocks
pattern: unsafe { $$$BODY }

# Raw pointer dereference
pattern: *$PTR
```

## Examples of What DOESN'T Work

```yaml
# ❌ WRONG - $$$ doesn't work for parameters
pattern: fn $NAME($$$PARAMS)

# ❌ WRONG - Double $$ is invalid
pattern: fn $NAME($$PARAMS)

# ❌ WRONG - Complex parameter patterns
pattern: fn $NAME($PARAM1: $TYPE1, $PARAM2: $TYPE2)
```

## Recommended Approach

1. **For finding all async functions:**
   ```yaml
   pattern: async fn $NAME
   ```

2. **For finding specific function calls:**
   ```yaml
   # Search for the function name directly
   pattern: connect_to_scanner
   
   # Or search for method calls
   pattern: $EXPR.connect()
   ```

3. **For security audits:**
   ```yaml
   # Find all unwraps
   pattern: $EXPR.unwrap()
   
   # Find unsafe blocks
   pattern: unsafe
   
   # Find format strings (potential injection)
   pattern: format!($$$ARGS)
   ```

## Debugging Tips

1. Start with exact string matches
2. Add one metavariable at a time
3. Use `fn $NAME` instead of trying to match parameters
4. For complex searches, search for the function name and filter results