# AST-Grep MCP Coding Standards

This document outlines the coding standards for the AST-Grep MCP project. Following these standards will help maintain code quality, performance, and readability.

## General Guidelines

### Code Organization

1. **Keep files focused**: Each file should have a clear responsibility and purpose.
2. **Use modules**: Group related functionality into modules.
3. **Follow the Single Responsibility Principle**: Each class and function should do one thing and do it well.

### Naming Conventions

1. **Use descriptive names**: Variable and function names should clearly indicate their purpose.
2. **Use snake_case**: For variables, functions, and module names.
3. **Use CamelCase**: For class names.
4. **Use ALL_CAPS**: For constants.

### Documentation

1. **Document modules**: Each module should have a docstring explaining its purpose.
2. **Document functions**: Each function should have a docstring explaining what it does, its parameters, and its return value.
3. **Document classes**: Each class should have a docstring explaining its purpose and behavior.
4. **Use type hints**: Include type hints for function parameters and return values.

## Anti-Patterns to Avoid

### Global Variables

**Don't:**
```python
# Global state is difficult to reason about and test
_instance = None

def get_instance():
    global _instance
    if _instance is None:
        _instance = MyClass()
    return _instance
```

**Do:**
```python
# Class-based singleton pattern
class MySingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

### Long Functions

**Don't:**
```python
def process_data(data):
    # Hundreds of lines of code doing many different things
    # ...
```

**Do:**
```python
def process_data(data):
    validated_data = validate_data(data)
    transformed_data = transform_data(validated_data)
    return store_data(transformed_data)

def validate_data(data):
    # Validation logic
    
def transform_data(data):
    # Transformation logic
    
def store_data(data):
    # Storage logic
```

### Nested Loops

**Don't:**
```python
def search_files(directory, pattern):
    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            with open(os.path.join(root, file)) as f:
                for line in f:
                    if pattern in line:
                        results.append((file, line))
    return results
```

**Do:**
```python
def search_files(directory, pattern):
    files = get_files(directory)
    return [result for file in files for result in search_file(file, pattern)]

def get_files(directory):
    return [os.path.join(root, file) 
            for root, dirs, files in os.walk(directory) 
            for file in files]

def search_file(file, pattern):
    with open(file) as f:
        return [(file, line) for line in f if pattern in line]
```

## Performance Optimizations

### List Building

**Don't:**
```python
def build_list(items):
    result = []
    for item in items:
        result.append(process(item))
    return result
```

**Do:**
```python
def build_list(items):
    return [process(item) for item in items]
```

### Unnecessary Conversions

**Don't:**
```python
def process_items(items):
    # Unnecessary conversion to list
    for item in list(items.keys()):
        process(item)
```

**Do:**
```python
def process_items(items):
    # Iterate directly over the view object
    for item in items.keys():
        process(item)
```

### Repeated Calculations

**Don't:**
```python
def process_data(items):
    for item in items:
        # Expensive calculation repeated in every iteration
        max_value = max(items)
        if item > max_value * 0.8:
            process_high_value(item)
```

**Do:**
```python
def process_data(items):
    # Calculate once outside the loop
    max_value = max(items)
    threshold = max_value * 0.8
    
    for item in items:
        if item > threshold:
            process_high_value(item)
```

## Error Handling

1. **Be specific**: Catch specific exceptions rather than using a broad except clause.
2. **Use context managers**: Use `with` statements for resource management.
3. **Provide useful error messages**: Error messages should be clear and helpful.

```python
# Good
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
    raise
except IOError as e:
    logger.error(f"IO error during processing: {e}")
    raise
```

## Testing

1. **Write unit tests**: For all public functions and methods.
2. **Test edge cases**: Include tests for boundary conditions and error cases.
3. **Use mock objects**: For external dependencies.
4. **Aim for high coverage**: The goal is to have comprehensive test coverage.

## Version Control

1. **Use descriptive commit messages**: Explain what the change does and why.
2. **Keep commits focused**: Each commit should address a single concern.
3. **Use branches**: For new features and bug fixes.
4. **Review code**: Use pull requests for code review.

## Enforcement

The project uses the following tools to enforce these standards:

1. **AST-Grep**: Custom patterns to detect code smells and anti-patterns.
2. **Ruff**: For linting Python code.
3. **CI/CD Pipeline**: Automated checks run on each pull request.

## Conclusion

Following these standards will help maintain a high-quality codebase. Remember that the goal is to write code that is readable, maintainable, and performant. 