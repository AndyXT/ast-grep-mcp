# Testing Strategy for ast-grep-mcp

This document outlines our testing strategy and the recent improvements made to reduce excessive mocking and increase test reliability.

## Testing Philosophy

Our testing approach follows these principles:

1. **Test real code paths whenever possible**
   - Avoid mocking unless absolutely necessary
   - Test the actual behavior of the code, not just the interfaces

2. **Mock only when needed**
   - Only mock external dependencies or problematic areas
   - Keep mocks focused and minimal
   - Mock at the appropriate level (e.g., function rather than entire module)

3. **Balance integration and unit tests**
   - Use unit tests for core logic
   - Use integration tests to verify components work together
   - Minimize interactions with external systems in fast tests

## Recent Improvements

We identified and fixed several issues with our test suite:

### 1. Language Handler Registration Fix

**Problem:** Language handlers were registered with property objects as keys instead of actual string values.

**Fix:** Changed the handler registration to explicitly create instances and extract string values for keys:
```python
# Before - problematic implementation
handlers = {
    handler.language_name: handler()
    for handler in [PythonHandler, JavaScriptHandler, ...]
}

# After - fixed implementation
handlers = {}
for handler_class in handler_classes:
    handler_instance = handler_class()
    language_name = handler_instance.language_name
    handlers[language_name] = handler_instance
```

### 2. Pattern Sanitization Enhancement

**Problem:** The security sanitization was removing legitimate AST pattern elements like `eval($EXPR)`.

**Fix:** Added special handling for AST pattern keywords that might be mistaken for security issues:
```python
# Protect patterns that look like security issues but are legitimate AST patterns
ast_pattern_placeholders = {}

# List of AST pattern keywords that might be mistaken for security issues
ast_pattern_keywords = [
    r'eval\(\$[A-Za-z_]+\)',  # e.g., eval($EXPR)
    r'exec\(\$[A-Za-z_]+\)',  # e.g., exec($CODE)
    r'Function\(\$[A-Za-z_]+\)',  # e.g., Function($ARGS)
]

# Replace with placeholders before sanitization, then restore after
```

### 3. Improved Metavariable Extraction

**Problem:** The regex-based metavariable extraction wasn't handling all pattern cases correctly.

**Fix:** Enhanced the extraction function with:
- Better logging for debugging
- Special case handling for common patterns 
- Improved extraction of function names, parameters, and expressions

### 4. Strategic Mocking Approach

**Problem:** Some tests used excessive mocking, making them brittle and not testing real behavior.

**Fix:** Adopted a more strategic approach to mocking:
- Created a comprehensive test suite that combines real testing with minimal mocking
- Used mocking only for specific problematic patterns where the underlying ast-grep engine has limitations
- Made mocks more specific and focused on just the problematic parts
- Kept access to original methods to allow normal functionality for other tests

### 5. Test Organization

We organized our tests into several categories:

1. **Pure Integration Tests** - Tests that use real implementations with no mocking
2. **Strategic Mocking Tests** - Tests that use minimal, focused mocking for problematic areas
3. **Comprehensive Tests** - A balanced suite combining both approaches

## Best Practices for Future Tests

When adding new tests, follow these guidelines:

1. **Default to real implementation** - Start by testing the real code without mocking
2. **Identify actual limitations** - Only add mocks when you encounter actual limitations
3. **Mock at the right level** - Mock at the lowest level needed to fix the issue
4. **Document mocking decisions** - Comment why mocking is needed when you use it
5. **Try to fix the underlying code** - If something needs to be mocked, consider if the code can be improved
6. **Use comprehensive tests** - Add tests to the comprehensive suite for critical functionality

## Running Tests

```bash
# Run all tests
uv run pytest

# Run just the comprehensive tests
uv run pytest tests/comprehensive_tests.py

# Run tests with coverage report
uv run pytest --cov=src/ast_grep_mcp
```

## Test Coverage

Our current test coverage is around 35%, which needs significant improvement. Here's the breakdown from our comprehensive tests:

```
Name                                         Stmts   Miss  Cover
------------------------------------------------------------------
src/ast_grep_mcp/ast_analyzer.py              481    344    28%
src/ast_grep_mcp/core/ast_grep_mcp.py         365    206    44%
src/ast_grep_mcp/core/config.py               244    147    40%
src/ast_grep_mcp/language_handlers/*           86     15    83%
src/ast_grep_mcp/utils/security.py             83     14    83%
src/ast_grep_mcp/utils/result_cache.py         42      3    93%
```

### Coverage Improvement Plan

1. **Core Modules (Priority: High)**
   - Target: Increase coverage of `ast_analyzer.py` and `ast_grep_mcp.py` to 70%+
   - Add tests for specific pattern matching capabilities
   - Add tests for different language support features
   - Test error handling paths

2. **Configuration (Priority: Medium)**
   - Target: Increase coverage of `config.py` to 75%+
   - Test configuration loading from different sources
   - Add tests for configuration validation
   - Test environment variable overrides

3. **Utility Modules (Priority: Medium)**
   - Target: Increase coverage of all utility modules to 80%+
   - Add tests for error handling utilities
   - Test pattern suggestion generation
   - Add tests for benchmarking utilities

4. **Server Module (Priority: Low)**
   - Target: Add basic tests for the server module
   - Test API endpoint functionality

### Implementation Strategy

For each module, we'll follow these steps:

1. Identify uncovered code areas using `pytest --cov-report=html`
2. Prioritize functional areas based on importance and risk
3. Add targeted tests following our comprehensive testing approach
4. Measure improvement in coverage
5. Repeat until targets are met

The coverage improvements will be implemented gradually over the next phases of development, with high-priority modules addressed first.

## Future Improvements

1. Investigate ways to improve the underlying pattern matching to reduce the need for mocking
2. Build better error reporting in the pattern matching engine
3. Consider a more robust solution for metavariable extraction
4. Implement property-based testing for pattern matching 
5. Add fuzzing tests to find edge cases in pattern handling
6. Create a visual test report dashboard to track coverage progress
7. Implement CI workflow that fails if coverage drops below thresholds 