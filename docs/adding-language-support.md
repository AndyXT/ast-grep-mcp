# Adding Language Support

This guide explains how to add support for new programming languages in the ast-grep-mcp project.

## Prerequisites

Before adding a new language, ensure:

1. The language is supported by [ast-grep](https://ast-grep.github.io/) and its underlying tree-sitter parser
2. You have examples of code in the language to test your patterns
3. You're familiar with the common idioms, anti-patterns, and best practices for the language

## Using the Language Generator Script

The easiest way to add a new language is to use the generator script:

```bash
uv run python scripts/new_language.py <language_name>
```

For example:
```bash
uv run python scripts/new_language.py kotlin
```

The script:
1. Creates a new language handler file in `src/ast_grep_mcp/language_handlers/`
2. Registers the handler in `__init__.py`
3. Sets up the boilerplate for pattern development

## Manual Setup Process

If the script doesn't support your language yet, follow these steps:

### 1. Create a Language Handler

Create a new file in `src/ast_grep_mcp/language_handlers/` named `your_language_handler.py`:

```python
from typing import Dict, List
from .base import LanguageHandler

class YourLanguageHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        """Return the language name as recognized by ast-grep."""
        return "your_language_name"  # e.g., "kotlin"
        
    @property
    def file_extensions(self) -> List[str]:
        """Return a list of file extensions for this language."""
        return [".ext"]  # e.g., [".kt", ".kts"] for Kotlin
        
    def get_default_patterns(self) -> Dict[str, str]:
        """Return default AST patterns for this language."""
        return {
            # Basic constructs
            "function": "...",
            "class": "...",
            
            # Anti-patterns and code smells
            "antipattern1": "...",
            "antipattern2": "...",
            
            # Performance optimizations
            "optimization1": "...",
            "optimization2": "...",
            
            # Security vulnerabilities
            "security1": "...",
            "security2": "...",
            
            # Refactoring patterns
            "refactoring1": "...",
            "refactoring2": "...",
        }
```

### 2. Register the Handler

Add your handler to `src/ast_grep_mcp/language_handlers/__init__.py`:

```python
from .your_language_handler import YourLanguageHandler

# Register all language handlers
handlers = {
    handler.language_name: handler()
    for handler in [
        PythonHandler,
        JavaScriptHandler,
        # ... other handlers ...
        YourLanguageHandler  # Add your handler here
    ]
}
```

## Building the Pattern Library

For a production-quality language handler, follow these steps:

### 1. Basic Constructs (5-10 patterns)

Start with patterns for the basic constructs:
- Functions/methods
- Classes/structs/interfaces
- Variables/constants
- Control flow structures (if, loops, etc.)
- Comments
- Module/package/namespace declarations

### 2. Anti-patterns and Code Smells (5-10 patterns)

Include patterns for common anti-patterns:
- Unused variables or imports
- Deep nesting
- Overly long functions or classes
- Language-specific bad practices
- Common logical errors

### 3. Performance Optimizations (5-10 patterns)

Add patterns for performance issues:
- Inefficient data structures
- Repeated expensive operations
- Unnecessary object creation
- Loop inefficiencies
- Resource leaks

### 4. Security Vulnerabilities (5-10 patterns)

Identify security problems:
- Input validation issues
- Potential injection attacks
- Unsafe data handling
- Insecure cryptography
- Authentication/authorization weaknesses

### 5. Refactoring Opportunities (5-10 patterns)

Create patterns for code that could be refactored:
- Duplicate code
- Complex conditions that could be simplified
- Outdated APIs or patterns
- Opportunities for modern language features
- Architecture improvements

## Testing Your Language Handler

Create unit tests for your language handler in `tests/language_handlers/test_your_language_handler.py`:

```python
from src.ast_grep_mcp.language_handlers.your_language_handler import YourLanguageHandler

class TestYourLanguageHandler:
    def test_language_name(self):
        handler = YourLanguageHandler()
        assert handler.language_name == "your_language_name"
    
    def test_file_extensions(self):
        handler = YourLanguageHandler()
        assert handler.file_extensions == [".ext"]
    
    def test_get_default_patterns(self):
        handler = YourLanguageHandler()
        patterns = handler.get_default_patterns()
        
        # Verify we have at least 25 patterns
        assert len(patterns) >= 25
        
        # Verify key patterns are present
        basic_constructs = ["function", "class", ...]
        for pattern in basic_constructs:
            assert pattern in patterns
        
        # Verify anti-patterns are present
        anti_patterns = ["antipattern1", "antipattern2", ...]
        for pattern in anti_patterns:
            assert pattern in patterns
            
        # Continue for other pattern categories...
```

## Testing the Patterns

To ensure your patterns work correctly, use the interactive mode to test them:

```bash
# Run interactive mode with UV
uv run ast-grep-mcp interactive

# Or run directly from source
uv run python main.py interactive
```

Within the interactive mode, you can:
1. Set your language: `language your_language_name`
2. Load test code: `code path/to/example.ext`
3. Try patterns: `analyze "your pattern here"`

## Documentation

Update the following documentation:

1. Add pattern examples to `docs/pattern-library.md`
2. Update language table in `README.md`
3. Create example patterns in your PR description

## Pattern Development Tips

1. **Start simple** - Begin with the most basic constructs and build complexity
2. **Test patterns** - Use the interactive mode to test patterns on real code
3. **Metavariables** - Use descriptive names for metavariables ($EXPR, $NAME, etc.)
4. **Wildcard matching** - Use $$$_ for "anything" within a match context
5. **Specificity** - Balance making patterns specific enough to be useful but general enough to match variations

## Example: Building a "function" Pattern

Let's take Kotlin as an example:

1. Find a basic function: `fun name(params): ReturnType { body }`
2. Extract the structure: `fun $NAME($$$PARAMS): $RETURN_TYPE { $$$BODY }`
3. Test with variations:
   - Functions with/without parameters
   - Functions with/without return type
   - Functions with/without visibility modifiers
4. Refine as needed: `$$$VISIBILITY fun $NAME($$$PARAMS)$$$RETURN { $$$BODY }`

## Submitting Your Language Handler

1. Create a branch: `git checkout -b add-language-support/your-language`
2. Add all files: handler, tests, documentation updates
3. Ensure tests pass: `uv run pytest tests/language_handlers/test_your_language_handler.py -v`
4. Submit a PR with detailed description of the patterns you've added 