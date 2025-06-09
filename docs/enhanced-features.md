# Enhanced AST-Grep MCP Features

This document describes the enhanced features added to address the pain points in the original ast-grep MCP tool.

## Overview

The enhanced version (now the default) provides:
- **Better token management** to avoid MCP token limit errors
- **Simplified pattern creation** with interactive wizards
- **High-level convenience functions** for common tasks
- **Improved error messages** with actionable suggestions
- **Progressive result loading** for large codebases

## Key Features

### 1. Search Summary (`search_summary`)

**Problem Solved**: Token limit errors when searching large codebases.

**Usage**:
```python
result = mcp.search_summary(
    pattern="async fn $NAME",
    directory="/path/to/project",
    language="rust"
)
```

**Returns**:
- Total files searched
- Files with matches
- Total match count
- Language breakdown
- Top 10 files with most matches
- Search time

**Benefits**:
- Uses ~90% less tokens than full search results
- Provides instant overview of search scope
- Helps identify where to focus detailed searches

### 2. Pattern Wizard (`pattern_wizard`)

**Problem Solved**: Complex and poorly documented pattern syntax.

**Usage**:
```python
result = mcp.pattern_wizard(
    description="find functions that return Result types",
    language="rust",
    examples=["fn example() -> Result<T, E>"]  # optional
)
```

**Returns**:
- Top 5 pattern suggestions with scores
- Explanation for each pattern
- Pattern syntax tips
- Metavariable reference

**Example Output**:
```json
{
  "suggestions": [{
    "pattern": "fn $NAME($$$ARGS) -> Result<$OK, $ERR>",
    "score": 8,
    "explanation": "Matches functions with Result return type",
    "examples": [...]
  }]
}
```

### 3. High-Level Convenience Functions

#### Find Functions (`find_functions`)
```python
functions = mcp.find_functions(
    directory=".",
    async_only=True,
    public_only=True,
    name_pattern=r"handle_.*"
)
```

#### Find TODOs and FIXMEs (`find_todos_and_fixmes`)
```python
todos = mcp.find_todos_and_fixmes(
    directory=".",
    include_patterns=["HACK", "NOTE"],
    case_sensitive=False
)
```

#### Find Potential Bugs (`find_potential_bugs`)
```python
bugs = mcp.find_potential_bugs(
    directory=".",
    language="rust"
)
# Finds: unwrap(), expect(), panic!, etc.
```

#### Find Imports (`find_imports`)
```python
imports = mcp.find_imports(
    directory=".",
    module_name="tokio",
    unused=True  # Try to detect unused imports
)
```

### 4. Enhanced Error Handling

**Problem Solved**: Cryptic error messages without guidance.

**Example**:
```python
# Old error:
"Token limit exceeded"

# New error:
TokenLimitError: Response size (29853 tokens) exceeds search limit (10000 tokens)
Suggestions:
- Use search_summary() for an overview without full match details
- Narrow your search with a specific subdirectory
- Add file_extensions filter (e.g., file_extensions=['.py'])
- Use page_size parameter (try page_size=5)
- Use search_stream() for progressive result loading
Example: search_summary(pattern='async fn', directory='.')
```

### 5. Streaming Search (`search_stream`)

**Problem Solved**: Need to process results incrementally for large codebases.

**Usage**:
```python
# Create stream
stream = mcp.search_stream(
    pattern="TODO",
    directory="/large/codebase",
    page_size=10
)

# Get results in batches
while True:
    batch = mcp.get_stream_results(stream["search_id"], batch_size=10)
    process_batch(batch["batch"])
    if not batch["has_more"]:
        break
```

### 6. Files-Only Search (`search_files_only`)

**Problem Solved**: Sometimes you just need to know which files contain matches.

**Usage**:
```python
result = mcp.search_files_only(
    pattern="unsafe",
    directory=".",
    language="rust"
)
# Returns just file paths and match counts - extremely lightweight
```

## Token Usage Comparison

| Operation | Original | Enhanced | Reduction |
|-----------|----------|----------|-----------|
| Search large directory | 29,853 tokens | 2,450 tokens | 92% |
| Find all functions | 18,234 tokens | 3,120 tokens | 83% |
| Get pattern help | N/A | 1,850 tokens | N/A |

## Migration Guide

### 1. Update Your MCP Configuration

Enhanced features are now enabled by default:

```json
{
  "mcpServers": {
    "ast-grep": {
      "command": "python",
      "args": ["main.py", "serve"],
      "cwd": "/path/to/ast-grep-mcp"
    }
  }
}
```

To use the legacy version (not recommended):
```json
{
  "mcpServers": {
    "ast-grep": {
      "command": "python",
      "args": ["main.py", "serve", "--no-enhanced"],
      "cwd": "/path/to/ast-grep-mcp"
    }
  }
}
```

### 2. Update Your Code

Replace token-heavy operations:

**Before**:
```python
# This often fails with token limit
results = mcp.search_directory(
    directory="/large/project",
    pattern="async fn"
)
```

**After**:
```python
# Get summary first
summary = mcp.search_summary(
    directory="/large/project",
    pattern="async fn"
)

# Then search specific files if needed
for file_info in summary["summary"]["top_files"]:
    details = mcp.search_directory(
        directory=file_info["file"],
        pattern="async fn"
    )
```

### 3. Use Pattern Wizard for Complex Patterns

**Before** (trial and error):
```python
# Try different patterns until one works
patterns = [
    "match $EXPR { Ok($VAR) => $VAR, Err($E) => $BODY }",
    "match $E { Ok($V) => $V, Err($ERR) => { $B } }",
    # ... many attempts
]
```

**After** (guided):
```python
wizard = mcp.pattern_wizard(
    description="match expression with Ok/Err arms",
    language="rust"
)
pattern = wizard["suggestions"][0]["pattern"]
```

## Performance Tips

1. **Always start with `search_summary`** for large codebases
2. **Use language filters** to reduce search scope
3. **Leverage convenience functions** instead of complex patterns
4. **Enable streaming** for real-time processing of results
5. **Cache results** when doing multiple searches

## Common Workflows

### Workflow 1: Find and Fix Security Issues
```python
# 1. Get overview
summary = mcp.search_summary("unwrap()", directory=".", language="rust")

# 2. Find all potential issues
bugs = mcp.find_potential_bugs(directory=".", language="rust")

# 3. Focus on high-severity issues
for bug in bugs["bugs"]:
    if bug["severity"] == "high":
        # Get detailed matches for this file
        details = mcp.analyze_file(
            file_path=bug["file"],
            pattern=bug["pattern"]
        )
```

### Workflow 2: Codebase Analysis
```python
# 1. Get language breakdown
summary = mcp.search_summary("*", directory=".")

# 2. Find all functions
functions = mcp.find_functions(directory=".")

# 3. Find all classes
classes = mcp.find_classes(directory=".")

# 4. Generate report
report = {
    "languages": summary["summary"]["language_breakdown"],
    "total_functions": functions["summary"]["total"],
    "total_classes": classes["summary"]["total"],
}
```

## Troubleshooting

### Still Getting Token Errors?

1. Reduce `page_size` further (try 3-5)
2. Use more specific file extensions
3. Search smaller subdirectories
4. Use `search_files_only` for initial filtering

### Pattern Not Matching?

1. Use `pattern_wizard` with examples
2. Use `explain_pattern` to understand existing patterns
3. Start simple and add complexity gradually

### Performance Issues?

1. Enable result caching
2. Use parallel processing options
3. Filter by file extensions early
4. Consider using traditional grep for simple text searches

## Best Practices

1. **Start broad, then narrow**: Use summaries before detailed searches
2. **Cache strategically**: Save summaries for repeated analysis
3. **Combine tools**: Use ripgrep for simple searches, ast-grep for AST operations
4. **Learn patterns incrementally**: Start with pattern wizard suggestions
5. **Monitor token usage**: Check response sizes in development

## Conclusion

The enhanced ast-grep MCP addresses the major pain points of the original tool while maintaining its powerful AST-based search capabilities. By focusing on progressive disclosure of information and better developer experience, it makes ast-grep accessible for everyday use in large codebases.