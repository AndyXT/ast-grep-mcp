# AST-Grep MCP Security Guide

This document provides information about the security features implemented in AST-Grep MCP and how to configure them for your environment.

## Security Features Overview

AST-Grep MCP includes the following security features:

1. **Pattern Sanitization**: All pattern inputs are sanitized to prevent potentially dangerous shell commands from being executed.

2. **Path Access Controls**: File operations can be restricted to specific directories to prevent unauthorized access to sensitive files.

3. **Error Handling**: Robust error handling ensures that security issues are properly caught and reported without exposing sensitive information.

## Pattern Sanitization

AST-Grep patterns may include special characters that could be interpreted as shell commands by the system. To prevent command injection attacks, all patterns are sanitized before processing.

The sanitization process:

1. Removes backticks (\`command\`) which could be used for command execution
2. Removes command substitution syntax ($(command))
3. Preserves AST-Grep pattern syntax features like metavariables ($NAME, $$$BODY)

This sanitization is automatically applied to all patterns used in:

- Code analysis
- Code refactoring
- File searching
- Directory scanning

## Path Access Controls

To prevent unauthorized access to sensitive files, AST-Grep MCP can be configured to restrict file operations to specific directories using the `safe_roots` configuration option.

### Configuring Safe Roots

Safe roots can be configured in several ways:

#### Via Configuration File (JSON)

```json
{
  "host": "localhost",
  "port": 8080,
  "safe_roots": [
    "/path/to/project",
    "/another/safe/directory"
  ]
}
```

#### Via Environment Variables

```bash
export AST_GREP_SAFE_ROOTS="/path/to/project,/another/safe/directory"
```

#### Via Command Line

```bash
python main.py start --safe-roots "/path/to/project,/another/safe/directory"
```

### How Safe Roots Work

When a file or directory operation is attempted:

1. The path is resolved to its absolute form (resolving symlinks)
2. The path is checked against all configured safe roots
3. Access is only permitted if the path is inside one of the safe roots
4. If access is denied, an error is returned with a generic "Access denied" message

## Security Best Practices

For the most secure deployment of AST-Grep MCP:

1. **Always configure safe roots**: Explicitly set the directories that should be accessible.

2. **Run with minimal privileges**: Run the server with a user account that has minimal system access.

3. **Use network isolation**: When possible, restrict the server to localhost or limit network access.

4. **Monitor logs**: Security events are logged at WARNING level. Configure appropriate log monitoring.

5. **Keep updated**: Regularly update AST-Grep MCP to receive security fixes.

## Security Events Logging

Security-related events are logged with the following levels:

- **WARNING**: Potentially dangerous patterns detected and sanitized
- **WARNING**: Attempted access to paths outside safe roots
- **WARNING**: No safe roots configured (unrestricted file access)
- **ERROR**: Path safety check errors

Example log messages:

```
WARNING  ast_grep_mcp.security:security.py:50 Potentially dangerous pattern detected and sanitized: `ls -la` -> 
WARNING  ast_grep_mcp.security:security.py:98 Attempted access to path outside safe roots: /etc/passwd
WARNING  ast_grep_mcp.security:security.py:83 No safe roots specified, allowing access to: /home/user/code.py
``` 