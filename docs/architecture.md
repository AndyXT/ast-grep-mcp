# AST-Grep MCP Architecture

This document provides an overview of the architecture of the AST-Grep MCP server.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastMCP Protocol                        │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                       AstGrepMCP Core                        │
│                                                             │
│  ┌─────────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │   ServerConfig  │◄───┤ Tool Registry │───►│ Cached API │  │
│  └─────────────────┘    └──────────────┘    └────────────┘  │
│           ▲                     ▲                  ▲         │
└───────────┼─────────────────────┼──────────────────┼─────────┘
            │                     │                  │
┌───────────┼─────────────────────┼──────────────────┼─────────┐
│           │                     │                  │         │
│  ┌────────▼────────┐    ┌───────▼───────┐   ┌─────▼──────┐  │
│  │ Config Providers │    │ Tool Handlers │   │ AST Engine │  │
│  │                  │    │               │   │            │  │
│  │ - JSON           │    │ - analyze     │   │ - ast-grep │  │
│  │ - YAML           │    │ - refactor    │   │ - patterning│  │
│  │ - Environment    │    │ - file ops    │   │ - handlers  │  │
│  └──────────────────┘    └───────────────┘   └────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### Core Components

1. **AstGrepMCP**: The main class that handles the MCP server initialization, 
   tool registration, and server lifecycle.

2. **ServerConfig**: Configuration class that manages server settings including:
   - Server host and port
   - Logging configuration
   - Cache settings
   - Security settings
   
3. **Tool Registry**: Registers and manages all available tools that can be invoked
   via the MCP protocol.

### Utility Components

1. **Error Handling**: Centralized error handling with consistent formatting
   for all tools.

2. **Result Cache**: LRU caching mechanism to avoid redundant operations.

3. **Parallel Processing**: Multi-processing capabilities for large directory 
   operations.

4. **Language Handlers**: Specialized modules for different programming languages.

## Data Flow

1. An MCP request comes in from an AI assistant or client.
2. The request is routed to the appropriate tool handler.
3. Error handling decorators catch any exceptions.
4. The tool is executed, potentially using cached results when available.
5. Results are formatted according to MCP protocol and returned.

## Performance Optimizations

1. **LRU Caching**: Frequently used results are cached to avoid redundant analysis.
2. **Parallel Directory Search**: Large directories are processed in parallel.
3. **Batch Processing**: Files are processed in optimal batch sizes.

## Configuration System

The server can be configured in multiple ways:

1. **Command Line Arguments**: Directly via CLI flags.
2. **Configuration Files**: Using JSON or YAML configuration files.
3. **Environment Variables**: Through environment variables for containerized deployments.

## Security Considerations

1. **Path Sanitization**: Prevents directory traversal attacks.
2. **Safe Roots**: Restricts file operations to approved directories.
3. **Pattern Validation**: Ensures patterns are safe before execution.

## Extensibility

The architecture is designed for extensibility:

1. **Language Support**: New languages can be added by creating handler modules.
2. **Tool Addition**: New tools can be registered with the core server.
3. **Custom Configurations**: The configuration system is extensible for future needs. 