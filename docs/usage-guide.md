# AST-Grep MCP Usage Guide

This guide provides detailed instructions for using the AST-Grep MCP server, including common use cases, pattern examples, and troubleshooting.

## MCP Server Installation & Setup

### Prerequisites

Before installing the AST-Grep MCP server, ensure you have:

- Python 3.10 or higher
- [UV](https://astral.sh/uv) package manager (recommended)
- Rust compiler (required for ast-grep-py compilation)

### Installation Steps

1. **Clone the repository**:

```bash
git clone https://github.com/AndyXT/ast-grep-mcp.git
cd ast-grep-mcp
```

2. **Install dependencies using UV**:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

3. **Verify installation**:

```bash
python main.py version
```

If successful, you should see the version information displayed.

## Server Configuration

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host`, `-h` | Host to bind to | `localhost` |
| `--port`, `-p` | Port to listen on | `8080` |
| `--log-level`, `-l` | Log level (debug, info, warning, error, critical) | `info` |
| `--log-file`, `-f` | Log file path | None |
| `--log-to-console`, `-c` | Whether to log to console | `True` |
| `--cache-size` | Size of the result cache | `128` |
| `--config` | Path to configuration file (JSON or YAML) | None |

### Using Configuration Files

You can provide a JSON or YAML configuration file:

**JSON format**:
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

**YAML format**:
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

### Environment Variables

You can also configure the server using environment variables:

| Environment Variable | Description |
|----------------------|-------------|
| `AST_GREP_HOST` | Server host |
| `AST_GREP_PORT` | Server port |
| `AST_GREP_LOG_LEVEL` | Logging level |
| `AST_GREP_LOG_FILE` | Log file path |
| `AST_GREP_LOG_TO_CONSOLE` | Whether to log to console |
| `AST_GREP_ENABLE_CACHE` | Whether to enable caching |
| `AST_GREP_CACHE_SIZE` | Cache size |
| `AST_GREP_SAFE_ROOTS` | Comma-separated list of safe roots |

## Running the Server

### Starting in Normal Mode

```bash
python main.py start
```

### Starting with Custom Configuration

```bash
python main.py start --host 0.0.0.0 --port 9000 --cache-size 256
```

### Using a Configuration File

```bash
python main.py start --config config.json
```

## Using Interactive Mode

Interactive mode allows you to explore AST-Grep functionality without running a server:

```bash
python main.py interactive
```

### Interactive Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `exit` | Exit interactive mode |
| `languages` | List supported languages |
| `language <name>` | Set current language |
| `patterns` | Show example patterns for current language |
| `code <file_path>` | Load code from file |
| `analyze <pattern>` | Analyze current code with pattern |
| `refactor <pattern> <replacement>` | Refactor code with pattern and replacement |

## Performance Tuning

### Running Benchmarks

The benchmark command helps find optimal settings for your workload:

```bash
python main.py benchmark --num-files 300 --batch-sizes auto,5,10,20,50
```

### Recommended Settings

- For small codebases (<200 files): Use sequential processing with caching
- For medium codebases (200-1000 files): Use parallel processing with batch size 10-20
- For large codebases (>1000 files): Use parallel processing with batch size 20-50

## Pattern Writing Guide

### Syntax Elements

| Syntax | Description | Example |
|--------|-------------|---------|
| `$NAME` | Matches a single named node | `def $FUNC_NAME` |
| `$$$PARAMS` | Matches multiple nodes | `def name($$$PARAMS)` |
| `$...X` | Matches a node of specific type | `$...expression` |
| `$_` | Wildcard that matches any single node | `if $_: print()` |

### Common Patterns by Language

#### Python

```
# Function definitions
def $NAME($$$PARAMS):
    $$$BODY

# Class definitions
class $NAME($$$PARENTS):
    $$$BODY

# Imports
import $MODULE
from $MODULE import $NAMES

# Conditionals
if $CONDITION:
    $$$BODY
elif $CONDITION:
    $$$BODY
else:
    $$$BODY
```

#### JavaScript/TypeScript

```
# Function declarations
function $NAME($$$PARAMS) {
    $$$BODY
}

# Arrow functions
($$$PARAMS) => $$$BODY

# Classes
class $NAME extends $PARENT {
    $$$BODY
}

# React components
<$COMPONENT $$$PROPS>$$$CHILDREN</$COMPONENT>
```

## MCP Tool Reference

### analyze_code

Analyzes code using ast-grep pattern matching.

**Parameters**:
- `code`: Source code to analyze
- `language`: Programming language
- `pattern`: Pattern to search for in the code

**Example**:
```python
result = analyze_code(
    code="def hello(): print('world')", 
    language="python", 
    pattern="def $NAME"
)
```

### refactor_code

Refactors code by replacing pattern matches with a replacement.

**Parameters**:
- `code`: Source code to refactor
- `language`: Programming language
- `pattern`: Pattern to search for
- `replacement`: Replacement code

**Example**:
```python
result = refactor_code(
    code="print('hello')", 
    language="python", 
    pattern="print($MSG)", 
    replacement="console.log($MSG)"
)
```

### analyze_file

Analyzes a file using ast-grep pattern matching.

**Parameters**:
- `file_path`: Path to the file to analyze
- `pattern`: Pattern to search for

**Example**:
```python
result = analyze_file(
    file_path="/path/to/file.py",
    pattern="def $NAME"
)
```

### search_directory

Searches for pattern matches in all files in a directory.

**Parameters**:
- `directory`: Directory to search
- `pattern`: Pattern to search for
- `parallel`: Whether to use parallel processing
- `max_workers`: Maximum number of worker processes
- `file_extensions`: List of file extensions to include

**Example**:
```python
result = search_directory(
    directory="/path/to/project",
    pattern="def $NAME",
    parallel=True,
    file_extensions=[".py"]
)
```

### get_language_patterns

Gets common pattern templates for a specific language.

**Parameters**:
- `language`: Programming language

**Example**:
```python
result = get_language_patterns(language="python")
```

### get_supported_languages

Gets a list of supported languages and their file extensions.

**Example**:
```python
result = get_supported_languages()
```

## Troubleshooting

### Common Issues

#### Installation Problems

If you encounter issues installing the package:

```bash
# Run the helper script
./scripts/install_deps.sh

# Or install manually
uv pip install ast-grep-py==0.37.0
uv sync --dev
```

#### Pattern Matching Issues

If patterns aren't matching as expected:

1. Check whitespace and indentation (ast-grep is whitespace-sensitive in some languages)
2. Ensure you're using the correct syntax for the language
3. Use `$$$` for multiple nodes (like function parameters or body)
4. Try simpler patterns first and build up complexity

#### Performance Issues

If you experience performance problems:

1. Check cache size configuration
2. Try different batch sizes for parallel processing
3. For very large directories, consider using file extension filtering
4. Run the benchmarks to find optimal settings for your workload

## Advanced Usage

### Security Configuration

To restrict file operations to specific directories:

```json
{
  "safe_roots": [
    "/path/to/project",
    "/another/safe/directory"
  ]
}
```

### Custom Logging Setup

For detailed logging:

```bash
python main.py start --log-level debug --log-file ast-grep-detailed.log
```

For production environments:

```bash
python main.py start --log-level warning --log-file /var/log/ast-grep.log
```

## Next Steps

- Check out the [Pattern Syntax Guide](./pattern-syntax.md) for more details
- Review the [Architecture Documentation](./architecture.md) to understand the system
- Join the community and contribute to the project 