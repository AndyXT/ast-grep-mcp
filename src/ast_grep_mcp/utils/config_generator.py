"""
Configuration generator for ast-grep-mcp.

This module provides utilities to generate default configuration files
with comments explaining each option.
"""

import os
from ..core.config import ServerConfig, OUTPUT_FORMATS, VERBOSITY_LEVELS, VALIDATION_STRICTNESS


def generate_commented_config() -> str:
    """
    Generate a configuration file with comments explaining each option.
    
    Returns:
        YAML-formatted configuration with comments
    """
    # Create a default configuration
    config = ServerConfig()
    
    # Convert the configuration to a dictionary
    config_dict = config.to_dict()
    
    # Define comments for each section and option
    comments = {
        "# AST Grep MCP Configuration File": "",
        "# Server Configuration": "",
        "host": "# Hostname to bind the server to",
        "port": "# Port number to listen on",
        
        "# Logging Configuration": "",
        "log_level": "# Logging level (debug, info, warning, error, critical)",
        "log_format": "# Format string for log messages",
        "log_file": "# Path to log file (optional)",
        "log_to_console": "# Whether to log to console",
        
        "# Cache Configuration": "",
        "enable_cache": "# Whether to enable caching",
        "cache_size": "# Maximum number of items to store in the cache",
        
        "# Security Configuration": "",
        "safe_roots": "# List of directories that are safe to access",
        
        "# Ignore Files Configuration": "",
        "ignore_file": "# Path to .ast-grepignore file (optional)",
        "use_default_ignores": "# Whether to use default ignore patterns",
        "ignore_patterns": "# List of ignore patterns",
        
        "# Pattern Configuration": "",
        "pattern_config": "",
        "template_dir": "# Directory containing pattern templates",
        "language_templates": "# Dictionary mapping languages to template directories",
        "validation_strictness": f"# Pattern validation strictness ({', '.join(VALIDATION_STRICTNESS)})",
        "custom_patterns": "# Custom patterns defined in the configuration",
        
        "# Refactoring Configuration": "",
        "refactoring_config": "",
        "preview_mode": "# Whether to preview refactorings before applying them",
        "validate_replacements": "# Whether to validate replacement patterns",
        "max_replacements": "# Maximum number of replacements to perform (optional)",
        "fix_malformed_output": "# Whether to attempt fixing malformed outputs",
        "enhance_partial_matches": "# Whether to enhance partial match handling",
        
        "# Output Configuration": "",
        "output_config": "",
        "format": f"# Output format ({', '.join(OUTPUT_FORMATS)})",
        "colorize": "# Whether to colorize output",
        "show_line_numbers": "# Whether to show line numbers",
        "show_context": "# Whether to show match context",
        "context_lines": "# Number of context lines to show",
        
        "# Diagnostic Configuration": "",
        "diagnostic_config": "",
        "verbosity": f"# Diagnostic verbosity level ({', '.join(VERBOSITY_LEVELS)})",
        "pattern_diagnostics": "# Whether to show diagnostic information for pattern errors",
        "show_suggestions": "# Whether to show suggestions for pattern errors",
        "show_examples": "# Whether to show example patterns",
        "show_stack_traces": "# Whether to show stack traces for errors",
        
        "# Custom Options": "",
        "options": "# Additional custom configuration options"
    }
    
    # Generate YAML with comments
    lines = []
    lines.append(comments["# AST Grep MCP Configuration File"])
    
    # Add server configuration
    lines.append(comments["# Server Configuration"])
    lines.append(f"{comments['host']}")
    lines.append(f"host: {config_dict['host']}")
    lines.append(f"{comments['port']}")
    lines.append(f"port: {config_dict['port']}")
    lines.append("")
    
    # Add logging configuration
    lines.append(comments["# Logging Configuration"])
    lines.append(f"{comments['log_level']}")
    lines.append(f"log_level: {config_dict['log_level']}")
    lines.append(f"{comments['log_format']}")
    lines.append(f"log_format: '{config_dict['log_format']}'")
    lines.append(f"{comments['log_file']}")
    lines.append(f"log_file: {config_dict['log_file'] or 'null'}")
    lines.append(f"{comments['log_to_console']}")
    lines.append(f"log_to_console: {str(config_dict['log_to_console']).lower()}")
    lines.append("")
    
    # Add cache configuration
    lines.append(comments["# Cache Configuration"])
    lines.append(f"{comments['enable_cache']}")
    lines.append(f"enable_cache: {str(config_dict['enable_cache']).lower()}")
    lines.append(f"{comments['cache_size']}")
    lines.append(f"cache_size: {config_dict['cache_size']}")
    lines.append("")
    
    # Add security configuration
    lines.append(comments["# Security Configuration"])
    lines.append(f"{comments['safe_roots']}")
    lines.append("safe_roots:")
    for root in config_dict['safe_roots']:
        lines.append(f"  - {root}")
    if not config_dict['safe_roots']:
        lines.append("  # Add directories that are safe to access, e.g.:")
        lines.append("  # - /path/to/project")
    lines.append("")
    
    # Add ignore files configuration
    lines.append(comments["# Ignore Files Configuration"])
    lines.append(f"{comments['ignore_file']}")
    lines.append(f"ignore_file: {config_dict['ignore_file'] or 'null'}")
    lines.append(f"{comments['use_default_ignores']}")
    lines.append(f"use_default_ignores: {str(config_dict['use_default_ignores']).lower()}")
    lines.append(f"{comments['ignore_patterns']}")
    lines.append("ignore_patterns:")
    for pattern in config_dict['ignore_patterns']:
        lines.append(f"  - {pattern}")
    if not config_dict['ignore_patterns']:
        lines.append("  # - '*.tmp'  # Example: ignore temporary files")
    lines.append("")
    
    # Add pattern configuration
    lines.append(comments["# Pattern Configuration"])
    pattern_config = config_dict['pattern_config']
    lines.append("pattern_config:")
    lines.append(f"  {comments['template_dir']}")
    lines.append(f"  template_dir: {pattern_config['template_dir'] or 'null'}")
    lines.append(f"  {comments['language_templates']}")
    lines.append("  language_templates:")
    if pattern_config['language_templates']:
        for lang, template_dir in pattern_config['language_templates'].items():
            lines.append(f"    {lang}: {template_dir}")
    else:
        lines.append("    # python: /path/to/python/templates")
    lines.append(f"  {comments['validation_strictness']}")
    lines.append(f"  validation_strictness: {pattern_config['validation_strictness']}")
    lines.append(f"  {comments['custom_patterns']}")
    lines.append("  custom_patterns:")
    if pattern_config['custom_patterns']:
        for lang, patterns in pattern_config['custom_patterns'].items():
            lines.append(f"    {lang}:")
            for name, pattern in patterns.items():
                lines.append(f"      {name}: '{pattern}'")
    else:
        lines.append("    # python:")
        lines.append("    #   for_loop: 'for $VAR in $ITER:'")
    lines.append("")
    
    # Add refactoring configuration
    lines.append(comments["# Refactoring Configuration"])
    refactoring_config = config_dict['refactoring_config']
    lines.append("refactoring_config:")
    lines.append(f"  {comments['preview_mode']}")
    lines.append(f"  preview_mode: {str(refactoring_config['preview_mode']).lower()}")
    lines.append(f"  {comments['validate_replacements']}")
    lines.append(f"  validate_replacements: {str(refactoring_config['validate_replacements']).lower()}")
    lines.append(f"  {comments['max_replacements']}")
    lines.append(f"  max_replacements: {refactoring_config['max_replacements'] or 'null'}")
    lines.append(f"  {comments['fix_malformed_output']}")
    lines.append(f"  fix_malformed_output: {str(refactoring_config['fix_malformed_output']).lower()}")
    lines.append(f"  {comments['enhance_partial_matches']}")
    lines.append(f"  enhance_partial_matches: {str(refactoring_config['enhance_partial_matches']).lower()}")
    lines.append("")
    
    # Add output configuration
    lines.append(comments["# Output Configuration"])
    output_config = config_dict['output_config']
    lines.append("output_config:")
    lines.append(f"  {comments['format']}")
    lines.append(f"  format: {output_config['format']}")
    lines.append(f"  {comments['colorize']}")
    lines.append(f"  colorize: {str(output_config['colorize']).lower()}")
    lines.append(f"  {comments['show_line_numbers']}")
    lines.append(f"  show_line_numbers: {str(output_config['show_line_numbers']).lower()}")
    lines.append(f"  {comments['show_context']}")
    lines.append(f"  show_context: {str(output_config['show_context']).lower()}")
    lines.append(f"  {comments['context_lines']}")
    lines.append(f"  context_lines: {output_config['context_lines']}")
    lines.append("")
    
    # Add diagnostic configuration
    lines.append(comments["# Diagnostic Configuration"])
    diagnostic_config = config_dict['diagnostic_config']
    lines.append("diagnostic_config:")
    lines.append(f"  {comments['verbosity']}")
    lines.append(f"  verbosity: {diagnostic_config['verbosity']}")
    lines.append(f"  {comments['pattern_diagnostics']}")
    lines.append(f"  pattern_diagnostics: {str(diagnostic_config['pattern_diagnostics']).lower()}")
    lines.append(f"  {comments['show_suggestions']}")
    lines.append(f"  show_suggestions: {str(diagnostic_config['show_suggestions']).lower()}")
    lines.append(f"  {comments['show_examples']}")
    lines.append(f"  show_examples: {str(diagnostic_config['show_examples']).lower()}")
    lines.append(f"  {comments['show_stack_traces']}")
    lines.append(f"  show_stack_traces: {str(diagnostic_config['show_stack_traces']).lower()}")
    lines.append("")
    
    # Add custom options
    lines.append(comments["# Custom Options"])
    lines.append(f"{comments['options']}")
    lines.append("options:")
    if config_dict['options']:
        for name, value in config_dict['options'].items():
            lines.append(f"  {name}: {value}")
    else:
        lines.append("  # Add any custom options here")
    
    return "\n".join(lines)


def generate_and_save_config(output_path: str) -> None:
    """
    Generate and save a configuration file with comments.
    
    Args:
        output_path: Path to save the configuration file
    """
    config_yaml = generate_commented_config()
    
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write the configuration file
    with open(output_path, "w") as f:
        f.write(config_yaml)


def generate_example_ignore_file(output_path: str) -> None:
    """
    Generate an example .ast-grepignore file.
    
    Args:
        output_path: Path to save the ignore file
    """
    lines = [
        "# AST Grep Ignore File",
        "# This file follows a similar format to .gitignore",
        "# Lines starting with # are comments",
        "# Empty lines are ignored",
        "# Each line specifies a pattern to ignore",
        "# Patterns ending with / match directories only",
        "# Patterns starting with ! negate the pattern (include the file)",
        "",
        "# Common version control directories",
        ".git/",
        ".svn/",
        ".hg/",
        "",
        "# Common build directories",
        "build/",
        "dist/",
        "target/",
        "",
        "# Common virtual environment directories",
        "venv/",
        ".venv/",
        "env/",
        ".env/",
        "",
        "# Python cache files",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache/",
        ".ruff_cache/",
        "",
        "# JavaScript/Node.js",
        "node_modules/",
        ".npm/",
        "",
        "# IDE files",
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "",
        "# Other common files to ignore",
        ".DS_Store",
        "Thumbs.db",
        "",
        "# Example of negating a pattern (include this file even if it matches a previous pattern)",
        "!important.txt"
    ]
    
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write the ignore file
    with open(output_path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    # Generate and save the configuration file
    config_path = "ast-grep.yml"
    generate_and_save_config(config_path)
    print(f"Generated configuration file: {config_path}")
    
    # Generate and save the ignore file
    ignore_path = ".ast-grepignore"
    generate_example_ignore_file(ignore_path)
    print(f"Generated ignore file: {ignore_path}") 