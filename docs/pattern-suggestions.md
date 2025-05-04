# Pattern Suggestion System and Interactive Builder

This document explains the new features added in Phase 10 of the ast-grep-mcp project:

1. Pattern Suggestion System
2. Interactive Pattern Builder

## Pattern Suggestion System

The Pattern Suggestion System provides helpful feedback when patterns don't match or yield unexpected results. It offers alternatives and contextual examples to help users create effective patterns.

### Features

- **Variant Suggestions**: Simpler or modified versions of your pattern that might match
- **Similar Pattern Lookups**: Finds patterns from the language library that are similar to yours
- **Example Patterns**: Shows relevant examples from the pattern library
- **Context-Aware Tips**: Explains pattern syntax and offers tips based on code being analyzed

### Using Pattern Suggestions

Pattern suggestions are automatically provided whenever:

- Your pattern doesn't match any code
- Your pattern causes an error
- Your pattern works but doesn't match expected code segments

Example output:

```
No matches found for pattern 'def my_function(arg1, arg2) {' in python code.

Did you mean:
  1. def my_function(arg1, arg2):
  2. def $_($$$_):

Similar patterns from library:
  1. function_definition: def $NAME($$$PARAMS):
  2. function_with_body: def $NAME($$$PARAMS):
      $$$BODY

Example patterns for this language:
  1. def $NAME($$$PARAMS):
  2. class $NAME:
  3. for $VAR in $ITER:

Pattern writing tips:
  - Use $VAR to match a single expression/identifier
  - Use $$$VAR to match multiple expressions/statements
  - Make sure your pattern follows the language syntax
  - Try matching smaller code fragments first
```

## Interactive Pattern Builder

The Interactive Pattern Builder is a CLI tool that helps you create and refine patterns interactively. It provides real-time feedback by showing matches as you build your pattern.

### Starting the Pattern Builder

```bash
uv run python main.py pattern-builder
```

### Features

- **Language Selection**: Choose from supported languages
- **Code Loading**: Load code from files, paste directly, or use examples
- **Real-Time Matching**: See matches as you build your pattern
- **Step-by-Step Refinement**: Guided process to improve patterns
- **Pattern Library**: Save and reuse your own patterns
- **Interactive Help**: Access examples and syntax tips

### Commands

| Command    | Description                      |
|------------|----------------------------------|
| `help`     | Show all available commands      |
| `language` | Select a language                |
| `load`     | Load code to match against       |
| `pattern`  | Test a pattern                   |
| `builder`  | Start interactive pattern builder|
| `library`  | View and use saved patterns      |
| `examples` | Show example patterns            |
| `history`  | Show pattern history             |
| `save`     | Save current pattern             |
| `clear`    | Clear current code               |
| `exit`     | Exit pattern builder             |

### Example Workflow

1. Select a language: `language` (choose from menu)
2. Load code: `load` (from file, direct input, or examples)
3. Try a pattern: `pattern def $NAME($$$PARAMS):`
4. Refine interactively: `builder`
5. Save the pattern: `save`
6. View pattern library: `library`

### Pattern Refinement Options

The interactive builder offers multiple ways to refine patterns:

1. Make variables more specific (e.g., `$VAR` → `$SPECIFIC_NAME`)
2. Make variables more general (e.g., `$SPECIFIC_NAME` → `$VAR`)
3. Add more context (surrounding code)
4. Remove context (simplify pattern)
5. Edit the pattern directly

### User Pattern Library

All patterns you save are stored in your user library at `~/.ast-grep-mcp/patterns/`. These patterns are saved by language and can be reused in future sessions.

## Pattern Syntax Quick Reference

| Syntax     | Description                                 | Example                |
|------------|---------------------------------------------|------------------------|
| `$NAME`    | Match single expression or identifier       | `$FUNCTION($ARG)`      |
| `$$$NAME`  | Match multiple expressions or statements    | `def f(): $$$BODY`     |
| `$_`       | Match anything (unnamed)                    | `if $_: $$$_`          |
| `$$$_`     | Match multiple expressions (unnamed)        | `f($$$_)`              |

## Tips for Effective Patterns

1. **Start simple**: Begin with minimal patterns and add complexity
2. **Target unique code**: Focus on distinct syntax elements
3. **Use variables**: Replace specific identifiers with `$NAME` or `$$$ARGS` 
4. **Add context gradually**: Expand patterns with surrounding code only as needed
5. **Test incrementally**: Verify each change matches expected code
6. **Save common patterns**: Build a library of your frequently used patterns 