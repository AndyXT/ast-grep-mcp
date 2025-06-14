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
- Pattern suggestion system for helpful feedback when patterns don't match
- Interactive pattern builder for step-by-step pattern creation
- Comprehensive configuration system with YAML/JSON files, environment variables, and command-line options
- `.ast-grepignore` support for excluding files and directories using gitignore-style patterns
- Built with UV for blazing fast dependency management

### New Features

- **Enhanced Pattern Diagnostics**: Advanced error recovery with position tracking, language-specific validation, and intelligent error detection
- **Automatic Pattern Correction**: Intelligent pattern correction suggestions with confidence scoring and automatic fixes for common mistakes
- **Pattern Validation**: Comprehensive validation with detailed error messages, syntax checking, and language-specific rules
- **Streaming Support**: Async streaming for large-scale operations with progress updates and batch processing
- **Native Metavariable Extraction**: Uses ast-grep's native API for reliable metavariable capture instead of regex-based extraction
- **Rule-Based Analysis**: Define and run complex rules with pattern composition, constraints, and YAML configuration
- **Performance Optimizations**: Connection pooling infrastructure and optimized subprocess management

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

### Interactive Pattern Builder

Create and refine patterns with real-time feedback:

```bash
uv run ast-grep-mcp pattern-builder
```

The pattern builder helps you:
- Build patterns step by step with immediate feedback
- See live matches as you refine your pattern
- Save patterns to your personal library
- Explore pattern variants and alternatives
- Test patterns against your code

See [Pattern Suggestions Guide](docs/pattern-suggestions.md) for more details on these features.

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

#### Configuration Files

AST Grep MCP supports hierarchical configuration files in YAML or JSON format. Create a file named `ast-grep.yml` in your project directory:

```yaml
# Server settings
host: 0.0.0.0
port: 9000
log_level: info
log_file: ast-grep.log

# Performance settings
enable_cache: true
cache_size: 256

# Security settings
safe_roots:
  - /path/to/safe/dir

# Ignore configuration
ignore_file: .ast-grepignore
use_default_ignores: true
ignore_patterns:
  - "*.tmp"
  - "*.bak"

# Pattern configuration
pattern_config:
  template_dir: templates
  validation_strictness: normal

# Refactoring configuration
refactoring_config:
  preview_mode: true
  validate_replacements: true
  max_replacements: 1000
```

Configuration files are discovered in the following order:
1. Default configuration
2. Project configuration file (ast-grep.yml in current or parent directory)
3. User-specified configuration file (--config option)
4. Environment variables
5. Command-line arguments

#### Configuration Using Environment Variables

You can configure AST Grep MCP using environment variables:

```bash
# Set host and port
export AST_GREP_HOST=0.0.0.0
export AST_GREP_PORT=9000

# Configure logging
export AST_GREP_LOG_LEVEL=debug
export AST_GREP_LOG_FILE=ast-grep.log

# Set security restrictions
export AST_GREP_SAFE_ROOTS=/path/to/project,/another/path

# Configure ignore patterns
export AST_GREP_IGNORE_FILE=.my-custom-ignore
export AST_GREP_USE_DEFAULT_IGNORES=true

# Start the server (will use environment variables)
ast-grep-mcp start
```

See [Configuration Guide](docs/configuration.md) for the full list of environment variables.

#### Ignoring Files and Directories

Create a `.ast-grepignore` file in your project directory to exclude files and directories from analysis:

```
# Version control
.git/
.svn/

# Build directories
build/
dist/
target/

# Dependencies
node_modules/
venv/
.venv/

# Cache and temporary files
__pycache__/
*.pyc
*.swp
.DS_Store
```

The ignore system works like `.gitignore` with support for:
- Directory-specific patterns (ending with `/`)
- Wildcard patterns with `*` and `?`
- Negation patterns with `!` to include previously excluded files
- Comments and empty lines

### Available MCP Tools

This server exposes the following tools:

1. `analyze_code` - Find patterns in code
2. `refactor_code` - Replace patterns in code
3. `analyze_file` - Analyze patterns in a file
4. `search_directory` - Search for patterns across all files in a directory
5. `get_language_patterns` - Get common patterns for a language
6. `get_supported_languages` - List supported languages
7. `get_config` - Get current configuration
8. `set_config` - Update configuration dynamically
9. `generate_config` - Generate configuration file
10. `preview_refactoring` - Preview refactoring changes without applying
11. `validate_pattern` - Validate a pattern with detailed diagnostics
12. `suggest_pattern_corrections` - Get automatic pattern correction suggestions
13. `search_directory_stream` - Stream search results for large directories
14. `create_rule` - Create a new analysis rule from a pattern
15. `load_rules` - Load rules from YAML/JSON files
16. `run_rules` - Run loaded rules against code
17. `test_rule` - Test a rule configuration against sample code
18. `compose_rule` - Create composite rules with logical operators
19. `list_rules` - List all loaded rules
20. `remove_rule` - Remove a rule from the engine
21. `export_rules` - Export rules to YAML/JSON format

## Using the New MCP Features

### Rule-Based Analysis

The new rule engine allows you to define and run complex code analysis rules:

#### Loading Rules from Files

```json
{
  "tool": "load_rules",
  "arguments": {
    "file_path": "rules/javascript-best-practices.yaml"
  }
}
```

#### Creating Custom Rules

```json
{
  "tool": "create_rule",
  "arguments": {
    "rule_id": "no-eval",
    "pattern": "eval($$$ARGS)",
    "message": "Avoid using eval() as it can execute arbitrary code",
    "language": "javascript",
    "severity": "error",
    "fix": "// eval($$$ARGS) // SECURITY: Do not use eval"
  }
}
```

#### Running Rules

```json
{
  "tool": "run_rules",
  "arguments": {
    "code": "var x = eval('2 + 2'); console.log(x);",
    "language": "javascript",
    "severities": ["error", "warning"]
  }
}
```

#### Composite Rules

Create complex rules with logical operators:

```json
{
  "tool": "compose_rule",
  "arguments": {
    "rule_id": "unused-async",
    "message": "Async function without await",
    "sub_rules": [
      {"pattern": "async function $NAME($$$PARAMS) { $$$BODY }"},
      {"not": {"pattern": "await $$$"}}
    ],
    "operator": "all",
    "language": "javascript",
    "severity": "warning"
  }
}
```

### Pattern Validation and Diagnostics

The new `validate_pattern` tool provides comprehensive pattern validation with detailed error messages:

```json
{
  "tool": "validate_pattern",
  "arguments": {
    "pattern": "if CONDITION:",
    "language": "python",
    "code": "if x > 0:\n    print(x)"
  }
}
```

Response includes:
- Syntax validation with error positions
- Metavariable detection and suggestions
- Language-specific rule violations
- Automatic correction suggestions

### Automatic Pattern Correction

The `suggest_pattern_corrections` tool provides intelligent pattern corrections:

```json
{
  "tool": "suggest_pattern_corrections",
  "arguments": {
    "pattern": "def NAME(PARAMS):",
    "language": "python"
  }
}
```

Returns ranked suggestions with confidence scores and explanations for each fix.

### Streaming Large Directory Searches

For large codebases, use `search_directory_stream` to get results as they're found:

```json
{
  "tool": "search_directory_stream",
  "arguments": {
    "directory": "/path/to/large/project",
    "pattern": "$FUNC.unwrap()",
    "language": "rust",
    "stream_config": {
      "batch_size": 50,
      "include_progress": true
    }
  }
}
```

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

