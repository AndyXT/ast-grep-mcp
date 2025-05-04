# AST Grep MCP Configuration Guide

This guide explains how to configure AST Grep MCP using the new configuration system.

## Table of Contents
- [Overview](#overview)
- [Configuration Files](#configuration-files)
- [Generating Configuration Files](#generating-configuration-files)
- [Configuration Options](#configuration-options)
- [Environment Variables](#environment-variables)
- [Ignore Files](#ignore-files)
- [Pattern Templates](#pattern-templates)
- [Examples](#examples)

## Overview

AST Grep MCP provides a flexible configuration system that allows you to customize its behavior through:

1. Configuration files (YAML or JSON)
2. Command-line arguments
3. Environment variables
4. Project-specific configuration files

The configuration is applied in the following order, with later sources overriding earlier ones:

1. Default configuration
2. Project configuration file (ast-grep.yml)
3. User-specified configuration file (--config option)
4. Environment variables
5. Command-line arguments

## Configuration Files

AST Grep MCP supports two types of configuration files:

- **YAML** files (recommended, with `.yml` or `.yaml` extension)
- **JSON** files (with `.json` extension)

Configuration files can be placed in your project directory or any parent directory. AST Grep MCP will automatically look for the following files in order:

1. `ast-grep.yml`
2. `ast-grep.yaml`
3. `ast-grep.json`

You can also specify a configuration file explicitly using the `--config` option:

```bash
ast-grep-mcp start --config path/to/config.yml
```

## Generating Configuration Files

You can generate a default configuration file with helpful comments using the `generate-config` command:

```bash
ast-grep-mcp generate-config
```

This will create an `ast-grep.yml` file in the current directory. You can specify a different output path:

```bash
ast-grep-mcp generate-config --output my-config.yml
```

You can also generate an example `.ast-grepignore` file:

```bash
ast-grep-mcp generate-config --ignore-file
```

## Configuration Options

The configuration is organized into sections:

### Server Configuration

```yaml
# Hostname to bind the server to
host: localhost
# Port number to listen on
port: 8080
```

### Logging Configuration

```yaml
# Logging level (debug, info, warning, error, critical)
log_level: info
# Format string for log messages
log_format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# Path to log file (optional)
log_file: null
# Whether to log to console
log_to_console: true
```

### Cache Configuration

```yaml
# Whether to enable caching
enable_cache: true
# Maximum number of items to store in the cache
cache_size: 100
```

### Security Configuration

```yaml
# List of directories that are safe to access
safe_roots:
  # Add directories that are safe to access, e.g.:
  # - /path/to/project
```

### Ignore Files Configuration

```yaml
# Path to .ast-grepignore file (optional)
ignore_file: null
# Whether to use default ignore patterns
use_default_ignores: true
# List of ignore patterns
ignore_patterns:
  # - '*.tmp'  # Example: ignore temporary files
```

### Pattern Configuration

```yaml
pattern_config:
  # Directory containing pattern templates
  template_dir: null
  # Dictionary mapping languages to template directories
  language_templates:
    # python: /path/to/python/templates
  # Pattern validation strictness (strict, normal, relaxed)
  validation_strictness: normal
  # Custom patterns defined in the configuration
  custom_patterns:
    # python:
    #   for_loop: 'for $VAR in $ITER:'
```

### Refactoring Configuration

```yaml
refactoring_config:
  # Whether to preview refactorings before applying them
  preview_mode: false
  # Whether to validate replacement patterns
  validate_replacements: true
  # Maximum number of replacements to perform (optional)
  max_replacements: null
  # Whether to attempt fixing malformed outputs
  fix_malformed_output: true
  # Whether to enhance partial match handling
  enhance_partial_matches: true
```

### Output Configuration

```yaml
output_config:
  # Output format (json, text, sarif, html)
  format: json
  # Whether to colorize output
  colorize: true
  # Whether to show line numbers
  show_line_numbers: true
  # Whether to show match context
  show_context: true
  # Number of context lines to show
  context_lines: 2
```

### Diagnostic Configuration

```yaml
diagnostic_config:
  # Diagnostic verbosity level (none, minimal, normal, detailed, diagnostic)
  verbosity: normal
  # Whether to show diagnostic information for pattern errors
  pattern_diagnostics: true
  # Whether to show suggestions for pattern errors
  show_suggestions: true
  # Whether to show example patterns
  show_examples: true
  # Whether to show stack traces for errors
  show_stack_traces: false
```

### Custom Options

```yaml
options:
  # Add any custom options here
```

## Environment Variables

You can also configure AST Grep MCP using environment variables. The following environment variables are supported:

| Environment Variable                | Configuration Option                                 |
|------------------------------------|----------------------------------------------------|
| `AST_GREP_HOST`                    | host                                               |
| `AST_GREP_PORT`                    | port                                               |
| `AST_GREP_LOG_LEVEL`               | log_level                                          |
| `AST_GREP_LOG_FILE`                | log_file                                           |
| `AST_GREP_LOG_TO_CONSOLE`          | log_to_console                                     |
| `AST_GREP_ENABLE_CACHE`            | enable_cache                                       |
| `AST_GREP_CACHE_SIZE`              | cache_size                                         |
| `AST_GREP_SAFE_ROOTS`              | safe_roots (comma-separated)                       |
| `AST_GREP_IGNORE_FILE`             | ignore_file                                        |
| `AST_GREP_USE_DEFAULT_IGNORES`     | use_default_ignores                                |
| `AST_GREP_TEMPLATE_DIR`            | pattern_config.template_dir                        |
| `AST_GREP_VALIDATION_STRICTNESS`   | pattern_config.validation_strictness               |
| `AST_GREP_PREVIEW_MODE`            | refactoring_config.preview_mode                    |
| `AST_GREP_VALIDATE_REPLACEMENTS`   | refactoring_config.validate_replacements           |
| `AST_GREP_MAX_REPLACEMENTS`        | refactoring_config.max_replacements                |
| `AST_GREP_FIX_MALFORMED_OUTPUT`    | refactoring_config.fix_malformed_output            |
| `AST_GREP_OUTPUT_FORMAT`           | output_config.format                               |
| `AST_GREP_COLORIZE`                | output_config.colorize                             |
| `AST_GREP_SHOW_LINE_NUMBERS`       | output_config.show_line_numbers                    |
| `AST_GREP_SHOW_CONTEXT`            | output_config.show_context                         |
| `AST_GREP_CONTEXT_LINES`           | output_config.context_lines                        |
| `AST_GREP_VERBOSITY`               | diagnostic_config.verbosity                        |
| `AST_GREP_PATTERN_DIAGNOSTICS`     | diagnostic_config.pattern_diagnostics              |
| `AST_GREP_SHOW_SUGGESTIONS`        | diagnostic_config.show_suggestions                 |
| `AST_GREP_SHOW_EXAMPLES`           | diagnostic_config.show_examples                    |
| `AST_GREP_SHOW_STACK_TRACES`       | diagnostic_config.show_stack_traces                |

## Ignore Files

AST Grep MCP supports a `.ast-grepignore` file that works similar to `.gitignore`. This file specifies patterns for files and directories that should be ignored during directory searches.

Example `.ast-grepignore` file:

```
# Version control directories
.git/
.svn/

# Build directories
build/
dist/

# Python cache files
__pycache__/
*.pyc

# JavaScript/Node.js
node_modules/

# IDE files
.idea/
.vscode/
```

You can generate an example `.ast-grepignore` file using:

```bash
ast-grep-mcp generate-config --ignore-file
```

### Ignore Pattern Syntax

Ignore patterns follow these rules:

1. **Basic Patterns**
   - Simple text patterns match files and directories containing that text
   - `*.ext` matches all files with extension `.ext`
   - `dir/file.txt` matches specific files in specific directories

2. **Directory Patterns**
   - Patterns ending with `/` match only directories
   - Matching directories causes all files inside to be ignored
   - Example: `node_modules/` ignores the `node_modules` directory and all files within it

3. **Wildcard Patterns**
   - `*` matches any number of characters (except `/`)
   - `?` matches a single character (except `/`)
   - `**` matches any number of directories (not yet supported)

4. **Negation Patterns**
   - Patterns starting with `!` negate previously matched patterns
   - Example: `*.log` followed by `!important.log` ignores all `.log` files except `important.log`

5. **Anchored Patterns**
   - Patterns starting with `/` match only at the root level
   - Example: `/root-file.txt` matches only `root-file.txt` at the top level, not in subdirectories

### Examples of Pattern Matching

```
# Pattern: *.txt
# Matches: file.txt, path/to/file.txt
# Doesn't match: file.text, file.txt.bak

# Pattern: node_modules/
# Matches: node_modules/, node_modules/file.js, path/to/node_modules/
# Doesn't match: nodemodules, my-node_modules

# Pattern: /root-only.txt
# Matches: root-only.txt
# Doesn't match: path/to/root-only.txt

# Pattern: *.log
# !important.log
# Matches: debug.log, logs/info.log
# Doesn't match: important.log, path/to/important.log

# Pattern: build/
# Matches: build/, build/output.js, src/build/
# Doesn't match: building, rebuilding
```

### How Ignore Patterns Are Applied

1. Patterns are applied in order they appear in the file
2. Later patterns override earlier ones (important for negation)
3. When searching directories, if a directory is ignored, all its contents are automatically ignored
4. Default ignore patterns are applied first (if enabled), then custom patterns
5. Patterns from the configuration file override patterns from the `.ast-grepignore` file

### Default Ignore Patterns

The following patterns are ignored by default (when `use_default_ignores` is true):

```
# Version control
.git/
.svn/
.hg/

# Build directories
build/
dist/
target/

# Virtual environments
venv/
.venv/
env/
.env/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.ruff_cache/

# JavaScript/Node.js
node_modules/
.npm/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Other common files
.DS_Store
Thumbs.db
```

You can disable default ignore patterns in your configuration:

```yaml
use_default_ignores: false
```

## Pattern Templates

AST Grep MCP supports custom pattern templates, which are reusable patterns for common code structures. You can define templates in the configuration file or in separate template files.

### Defining Templates in Configuration

```yaml
pattern_config:
  custom_patterns:
    python:
      for_loop: 'for $VAR in $ITER:'
      while_loop: 'while $CONDITION:'
    javascript:
      arrow_function: '($$$PARAMS) => $$$BODY'
```

### Using Template Directories

You can also store template patterns in separate files organized by language:

```yaml
pattern_config:
  template_dir: path/to/templates
  language_templates:
    python: path/to/python/templates
    javascript: path/to/javascript/templates
```

Template files should be YAML files with a structure like:

```yaml
# python_patterns.yml
for_loop: 'for $VAR in $ITER:'
while_loop: 'while $CONDITION:'
function_def: 'def $NAME($$$PARAMS):'
```

## Examples

### Basic Configuration File

```yaml
# ast-grep.yml
host: localhost
port: 8080
log_level: info

# Security settings
safe_roots:
  - /home/user/projects

# Pattern configuration
pattern_config:
  validation_strictness: normal
  
# Refactoring configuration
refactoring_config:
  preview_mode: true
  validate_replacements: true
  fix_malformed_output: true
  
# Diagnostic configuration
diagnostic_config:
  verbosity: detailed
  show_suggestions: true
  show_examples: true
```

### Project-Specific Configuration

```yaml
# /project/ast-grep.yml
pattern_config:
  template_dir: templates
  validation_strictness: relaxed

refactoring_config:
  preview_mode: true
  
output_config:
  format: text
  colorize: true
  
ignore_file: .ast-grepignore
```

### Command-Line Overrides

```bash
ast-grep-mcp start --config config.yml --verbosity detailed --preview-mode
```

This will use `config.yml` as the base configuration, but override the verbosity level to "detailed" and enable preview mode for refactorings.

## Advanced Usage

### Configuration for CI/CD Environments

For CI/CD environments, you might want to use a dedicated configuration that disables interactive features and focuses on reporting:

```yaml
# ci-config.yml
log_level: warning
log_to_console: true
enable_cache: false

output_config:
  format: sarif
  colorize: false
  
diagnostic_config:
  verbosity: minimal
  show_stack_traces: true
```

### Multi-Language Projects

For projects with multiple languages, you can configure language-specific settings:

```yaml
pattern_config:
  language_templates:
    python: templates/python
    javascript: templates/javascript
    typescript: templates/typescript
  
  custom_patterns:
    python:
      # Python-specific patterns
    javascript:
      # JavaScript-specific patterns
```

### Security-Focused Configuration

For security-sensitive environments:

```yaml
# Restrict file access to specific directories
safe_roots:
  - /path/to/project
  - /path/to/allowed/dir

# Limit replacement operations
refactoring_config:
  validate_replacements: true
  max_replacements: 100
  
# Strict pattern validation
pattern_config:
  validation_strictness: strict
``` 