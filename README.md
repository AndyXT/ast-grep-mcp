# AST-Grep MCP Server

An MCP (Model-Check-Path) server that uses ast-grep for advanced code analysis and refactoring across multiple programming languages.

## Features

- AST-powered code analysis and search
- Structural pattern matching on code
- Support for multiple languages (Python, JavaScript, TypeScript, Lua, C, Rust, Go)
- Comprehensive pattern libraries with 25+ patterns per language
- Detection of anti-patterns, code smells, and security vulnerabilities
- Code refactoring capabilities
- LRU caching for improved performance
- Parallel directory search with batching for large codebases
- Built with UV for blazing fast dependency management

## Prerequisites

- Python 3.10 or higher
- [UV](https://astral.sh/uv) package manager (strongly recommended)
- Rust (required for ast-grep-py compilation)

## Installation

### Option 1: From Source (Recommended)
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

### Option 2: Install as a Package

```bash
# Install using UV (recommended)
uv pip install ast-grep-mcp

# Or install from the repository
uv pip install git+https://github.com/yourorg/ast-grep-mcp.git
```

### Option 3: Development Installation

```bash
# Clone repository
git clone https://github.com/yourorg/ast-grep-mcp.git
cd ast-grep-mcp

# Install in development mode with UV
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Helper Script

Alternatively, use the helper script for a clean installation:

```bash
./scripts/install_deps.sh
```

## Usage

### Starting the MCP Server

After installing the package, you can use the provided commands:

```bash
# Using the console script
ast-grep-mcp start

# Using the Python module with UV
uv run python -m ast-grep-mcp start
```

Or run directly from source with UV:

```bash
uv run python main.py start
```

Customize host, port and cache size:

```bash
uv run ast-grep-mcp start --host 0.0.0.0 --port 9000 --cache-size 256
```

Configure logging:

```bash
uv run ast-grep-mcp start --log-level debug --log-file ast-grep.log
```

Use a configuration file (JSON or YAML):

```bash
uv run ast-grep-mcp start --config config.json
```

### Interactive Mode

Test patterns and explore AST Grep functionality without starting a server:

```bash
uv run ast-grep-mcp interactive
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
uv run ast-grep-mcp version
```

### Performance Optimization

The server includes several performance optimizations:

1. **LRU Cache**: Results are cached to avoid redundant pattern matching operations
2. **Parallel Processing**: For large directories (>200 files), search can be parallelized
3. **Batch Processing**: Files are processed in batches to optimize parallel execution
4. **UV Execution**: Using UV for running Python commands provides additional performance benefits

#### Running Benchmarks

To find the optimal configuration for your workload and system, use the benchmark command:

```bash
uv run ast-grep-mcp benchmark --num-files 300 --batch-sizes auto,5,10,20,50
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

This configuration uses UV to run the server, which offers:
- Faster initialization time compared to directly running Python
- Consistent dependency resolution
- Isolated environment management

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

For a comprehensive list of patterns for all supported languages, see the [Pattern Library](docs/pattern-library.md) documentation.

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

### Rust Pattern Examples

```
# Find function definitions
fn $NAME($$$PARAMS) -> $RET_TYPE

# Find struct definitions
struct $NAME { $$$FIELDS }

# Find unsafe blocks
unsafe { $$$CODE }

# Find unwrap calls (potential issues)
$EXPR.unwrap()

# Find match expressions
match $EXPR { $$$ARMS }
```

### Go Pattern Examples

```
# Find function definitions
func $NAME($$$PARAMS) $$$RETURN_TYPE

# Find interface definitions
type $NAME interface { $$$METHODS }

# Find goroutine launches
go func() { $$$BODY }()

# Find error checks
if err != nil { $$$ERROR_HANDLING }

# Find range loops
for $KEY, $VALUE := range $COLLECTION { $$$BODY }
```

### C Pattern Examples

```
# Find function definitions
$RET_TYPE $NAME($$$PARAMS)

# Find struct definitions
struct $NAME { $$$FIELDS }

# Find potential buffer overflows
strcpy($DEST, $SRC)

# Find memory allocation without checks
$PTR = malloc($SIZE)

# Find switch statements
switch ($EXPR) { $$$CASES }
```

## Language Support

AST-grep-mcp supports the following languages with comprehensive pattern libraries:

| Language | Patterns | File Extensions |
|----------|----------|-----------------|
| Python | 67 | .py |
| JavaScript | 57 | .js, .jsx |
| TypeScript | 94 | .ts, .tsx |
| Rust | 36 | .rs |
| Go | 36 | .go |
| C | 36 | .c, .h |
| Lua | Basic | .lua |

Each language includes patterns for:
- Basic code constructs
- Anti-patterns and code smells
- Performance optimization opportunities
- Security vulnerabilities
- Refactoring suggestions

## Adding New Language Support

The project includes a language handler generator script to easily add support for new languages:

```bash
uv run python scripts/new_language.py <language_name>
```

For example:
```bash
uv run python scripts/new_language.py kotlin
```

This will:
1. Create a new language handler file
2. Register it in the handlers registry
3. Set up the basic pattern structure

After generating the boilerplate, you'll need to:
1. Complete the pattern library with language-specific patterns
2. Add unit tests for the handler
3. Add documentation examples

For more details, see the [Adding Language Support](docs/adding-language-support.md) guide.

## Development

### Project Structure

```
ast-grep-mcp/
   docs/
      implementation-plan.md  # Project roadmap and progress
      pattern-library.md      # Comprehensive pattern documentation
   scripts/
      new_language.py         # New language handler generator
   src/
      ast_grep_mcp/
          __init__.py
          __main__.py         # Module entry point
          ast_analyzer.py     # Core AST analysis functionality
          server.py           # MCP server implementation
          language_handlers/  # Language-specific modules
              base.py         # Base handler class
              python_handler.py
              javascript_handler.py
              c_handler.py
              go_handler.py
              rust_handler.py
          core/               # Core server functionality
              __init__.py     # AstGrepMCP class
              config.py       # Server configuration
          utils/              # Utility modules
              error_handling.py # Error handling utilities
              result_cache.py   # Caching implementation
              benchmarks.py     # Performance benchmarking
   tests/
      language_handlers/      # Tests for language handlers
      core/                   # Tests for core functionality
   main.py                    # CLI entry point
   pyproject.toml             # Project configuration
   README.md                  # This file
```

### Why UV?

We use UV for all package management and Python execution for several key benefits:

1. **Speed**: UV is significantly faster than pip and conda for dependency resolution and installation
2. **Reproducibility**: Precisely tracks dependencies for consistent environments
3. **Integration**: Works seamlessly with Python's packaging ecosystem
4. **Caching**: Efficient caching of dependencies and build artifacts
5. **Performance**: Faster Python execution through optimized environment management

### Development Commands

```bash
# Create and activate environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install all dependencies
uv sync

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

# Update all dependencies
uv pip sync --upgrade

# Generate lock file
uv pip freeze > requirements.lock
```

### Troubleshooting

If you encounter issues with dependencies or installation:

1. Make sure Rust is installed (required for ast-grep-py compilation)
2. Try the helper script: `./scripts/install_deps.sh`
3. See the detailed [Troubleshooting Guide](TROUBLESHOOTING.md) for common issues and solutions

## License

[MIT License](LICENSE)

