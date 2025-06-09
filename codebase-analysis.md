# AST-Grep MCP Codebase Analysis

## Overview
This is a comprehensive analysis of the ast-grep-mcp codebase structure, architectural patterns, and code organization.

## Project Structure

### Core Architecture
The project follows a modular architecture with clear separation of concerns:

1. **Main Entry Point**: `main.py` - CLI interface using Typer
2. **Core Module**: `src/ast_grep_mcp/core/` - Central MCP server implementation
3. **Language Handlers**: `src/ast_grep_mcp/language_handlers/` - Language-specific pattern implementations
4. **Utilities**: `src/ast_grep_mcp/utils/` - Shared utility functions and helpers
5. **Server**: `src/ast_grep_mcp/server.py` - FastMCP server implementation

### Key Architectural Patterns

#### 1. **Plugin Architecture for Language Support**
- Abstract base class: `LanguageHandler` in `language_handlers/base.py`
- Concrete implementations for each language (Python, JavaScript, TypeScript, Rust, C, Go)
- Self-registering handler pattern in `language_handlers/__init__.py`
- Found 6 language handler classes inheriting from `LanguageHandler`

#### 2. **Configuration Pattern**
- Dataclass-based configuration using Python 3.10+ features
- Found 5 dataclass definitions in `core/config.py`
- Hierarchical configuration structure:
  - `ServerConfig` - Main server configuration
  - `PatternConfig` - Pattern matching configuration
  - `RefactoringConfig` - Code refactoring settings
  - `OutputConfig` - Output formatting options
  - `DiagnosticConfig` - Diagnostic and error reporting settings

#### 3. **Decorator Patterns**
- Error handling decorator: `@handle_errors` in `utils/error_handling.py`
- Caching decorator: `@cached` in `utils/result_cache.py`
- MCP tool registration: `@mcp.tool()` in server modules
- Found 5 tool decorators in `server.py` and 7 in `main.py`

#### 4. **Singleton Pattern**
- `AstGrepMCPSingleton` in `server.py` for maintaining a single MCP instance
- Ensures consistent state across tool invocations

#### 5. **Factory Pattern**
- Language handler factory: `get_handler()` function
- Rule engine factory for creating different rule types

## Code Organization Patterns

### Module Structure
- **Relative imports**: Found 22 relative imports, indicating good module cohesion
- **Package initialization**: Proper `__init__.py` files with `__all__` exports
- **Clear module boundaries**: Each module has a specific responsibility

### Class Distribution
- **Total classes**: ~67 class definitions across the codebase
- **Test classes**: ~37 test classes
- **Core classes**: ~30 production classes

### Function Distribution
- **Tool functions**: 21 registered MCP tools
- **Utility functions**: ~50 helper functions
- **Test functions**: Extensive test coverage with pytest

### Design Patterns Used

#### 1. **Strategy Pattern**
- Language handlers implement different strategies for pattern matching
- Each handler provides language-specific pattern templates

#### 2. **Template Method Pattern**
- Base `LanguageHandler` defines the interface
- Concrete handlers implement specific behavior

#### 3. **Observer Pattern**
- Logging system acts as an observer for events
- Error handling propagates through decorators

#### 4. **Builder Pattern**
- Configuration builders (e.g., `ServerConfig.from_dict()`, `ServerConfig.from_file()`)
- Pattern suggestion builders in utils

## Key Components Analysis

### 1. **AST Analyzer**
- Two versions: `AstAnalyzer` and `AstAnalyzerV2`
- Uses `ast-grep-py` for pattern matching
- Supports parallel processing with `ProcessPoolExecutor`

### 2. **Pattern System**
- Pattern validation with auto-correction
- Pattern diagnostics for better error messages
- Pattern suggestion system for common mistakes
- Metavariable support ($VAR, $$$VAR patterns)

### 3. **Security Features**
- Path validation and sandboxing
- Pattern sanitization
- Safe root directory restrictions

### 4. **Performance Optimizations**
- Result caching with configurable size
- Subprocess pooling for parallel execution
- Streaming support for large result sets

### 5. **Error Handling**
- Comprehensive error handling with context
- Pattern-specific error messages
- Language-aware error suggestions

## Testing Architecture
- **Test framework**: pytest
- **Test organization**: Mirrors source structure
- **Test types**:
  - Unit tests for individual components
  - Integration tests for MCP server
  - Performance benchmarks
  - Security tests

## Dependencies and Integration
- **FastMCP**: MCP server framework
- **ast-grep-py**: Core pattern matching engine
- **Typer**: CLI framework
- **Rich**: Terminal formatting
- **PyYAML**: Configuration file support

## Code Quality Patterns
1. **Type hints**: Extensive use of Python type hints
2. **Docstrings**: Comprehensive documentation
3. **Error messages**: Context-aware, helpful error messages
4. **Logging**: Structured logging throughout
5. **Configuration**: Flexible, file-based configuration

## Notable Features
1. **Pattern Library**: Pre-defined patterns for each language
2. **Interactive Mode**: CLI pattern builder
3. **Benchmarking**: Performance testing capabilities
4. **Rule Engine**: Complex rule composition
5. **Streaming**: Handle large codebases efficiently

This analysis reveals a well-structured, modular codebase with clear architectural patterns, extensive error handling, and a focus on extensibility and performance.