# AST-Grep MCP Server

An MCP (Model-Check-Path) server that uses ast-grep for advanced code analysis and refactoring across multiple programming languages.

## Features

- AST-powered code analysis and search
- Structural pattern matching on code
- Support for multiple languages (Python, JavaScript, TypeScript, Lua, C, Rust, Go)
- Code refactoring capabilities
- LRU caching for improved performance
- Parallel directory search with batching for large codebases
- Built with UV for blazing fast dependency management

## Prerequisites

- Python 3.10 or higher
- [UV](https://astral.sh/uv) package manager (recommended)
- Rust (required for ast-grep-py compilation)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/AndyXT/ast-grep-mcp.git
cd ast-grep-mcp
```

2. Install dependencies with UV:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

3. Or install with pip (alternative):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

4. Alternatively, use the helper script for a clean installation:

```bash
./scripts/install_deps.sh
```

## Usage

### Starting the MCP Server

Start the server with default settings:

```bash
python main.py start
```

Or use the legacy command:

```bash
python main.py serve
```

Customize host, port and cache size:

```bash
python main.py start --host 0.0.0.0 --port 9000 --cache-size 256
```

Configure logging:

```bash
python main.py start --log-level debug --log-file ast-grep.log
```

Use a configuration file (JSON or YAML):

```bash
python main.py start --config config.json
```

### Interactive Mode

Test patterns and explore AST Grep functionality without starting a server:

```bash
python main.py interactive
```

In interactive mode, you can:
- List supported languages
- Change the current language
- Load code from a file
- Analyze code with patterns
- Refactor code with patterns and replacements
- View example patterns for the current language

### View Version Information

```bash
python main.py version
```

### Performance Optimization

The server includes several performance optimizations:

1. **LRU Cache**: Results are cached to avoid redundant pattern matching operations
2. **Parallel Processing**: For large directories (>200 files), search can be parallelized
3. **Batch Processing**: Files are processed in batches to optimize parallel execution

#### Running Benchmarks

To find the optimal configuration for your workload and system, use the benchmark command:

```bash
python main.py benchmark --num-files 300 --batch-sizes auto,5,10,20,50
```

This will create synthetic test files, run both sequential and parallel searches, and provide recommendations for your specific environment.

**Note**: For small to medium workloads (<200 files), sequential processing is generally faster due to the overhead of parallel processing. The caching mechanism provides significant speedup for repeated operations regardless of processing mode.

### MCP Server Configuration

To configure an AI assistant to use this MCP server, use the following configuration:

```json
{
  "mcpServers": {
    "ast-grep": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/ast-grep-mcp",
        "run", "python", "main.py", "start",
        "--cache-size", "128"
      ],
      "env": {}
    }
  }
}
```

### Configuration File Example

Create a JSON configuration file:

```json
{
  "host": "0.0.0.0",
  "port": 9000,
  "log_level": "info",
  "log_file": "ast-grep.log",
  "log_to_console": true,
  "cache_size": 256,
  "safe_roots": ["/path/to/safe/dir"]
}
```

Or use YAML format:

```yaml
host: 0.0.0.0
port: 9000
log_level: info
log_file: ast-grep.log
log_to_console: true
cache_size: 256
safe_roots:
  - /path/to/safe/dir
```

### Available MCP Tools

This server exposes the following tools:

1. `analyze_code` - Find patterns in code
2. `refactor_code` - Replace patterns in code
3. `analyze_file` - Analyze patterns in a file
4. `search_directory` - Search for patterns across all files in a directory
5. `get_language_patterns` - Get common patterns for a language
6. `get_supported_languages` - List supported languages

## Pattern Syntax Guide

AST-grep uses a specialized syntax for pattern matching. Here are the key elements:

### Pattern Syntax Elements

| Syntax | Description | Example |
|--------|-------------|---------|
| `$NAME` | Matches a single named node (variable, identifier, etc.) | `def $FUNC_NAME` |
| `$$$PARAMS` | Matches multiple nodes (zero or more) | `def name($$$PARAMS)` |
| `$...X` | Matches a node of specific type X | `$...expression` |
| `$_` | Wildcard that matches any single node | `if $_: print()` |

### Common Issues & Solutions

- **Parameters not matching**: For function parameters, always use triple dollar `$$$PARAMS` to match variable number of parameters
- **Compound statements**: For blocks or statements with nested content, use triple dollar for the body: `if $COND: $$$BODY`
- **String literals**: To match strings, use quote characters: `print("$MESSAGE")`
- **Whitespace**: Pattern matching ignores most whitespace differences

### Refactoring Patterns

When refactoring, the replacement pattern must use the same metavariables ($NAME, etc.) that were matched in the search pattern:

```
# Search pattern
print($$$ARGS)

# Replacement pattern
console.log($$$ARGS)
```

## Pattern Examples

### Python Pattern Examples

```
# Find all function definitions
def $NAME($$$PARAMS)

# Find all class definitions
class $NAME

# Find all print statements
print($$$ARGS)

# Find specific function calls
requests.get($URL)

# Find if statements with body
if $CONDITION:
    $$$BODY
```

### JavaScript Pattern Examples

```
# Find all function declarations
function $NAME($$$PARAMS) { $$$BODY }

# Find all arrow functions
($$$PARAMS) => $$$BODY

# Find all console.log statements
console.log($$$ARGS)

# Find all React components
<$COMPONENT $$$PROPS>$$$CHILDREN</$COMPONENT>

# Find if statements
if ($CONDITION) { $$$BODY }
```

## Development

### Project Structure

```
ast-grep-mcp/
   src/
      ast_grep_mcp/
          __init__.py
          ast_analyzer.py     # Core AST analysis functionality
          server.py           # MCP server implementation
          language_handlers/  # Language-specific modules
          core/               # Core server functionality
              ast_grep_mcp.py # Main server class
              config.py       # Server configuration
          utils/              # Utility modules
              error_handling.py # Error handling utilities
              result_cache.py   # Caching implementation
              benchmarks.py     # Performance benchmarking
   main.py                    # CLI entry point
   pyproject.toml             # Project configuration
   README.md                  # This file
```

### Adding Support for New Languages

1. Create a new handler in `src/ast_grep_mcp/language_handlers/`
2. Register the handler in `src/ast_grep_mcp/language_handlers/__init__.py`

### Development Commands

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy .

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/path/to/test.py::test_function_name -v

# Run performance tests
uv run pytest tests/test_performance.py -v

# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name
```

### Troubleshooting

If you encounter issues with dependencies or installation:

1. Make sure Rust is installed (required for ast-grep-py compilation)
2. Try the helper script: `./scripts/install_deps.sh`
3. See the detailed [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues and solutions

## License

[MIT License](LICENSE)

