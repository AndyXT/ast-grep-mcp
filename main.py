import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from src.ast_grep_mcp.core import AstGrepMCP, ServerConfig
from src.ast_grep_mcp.core.config import LOG_LEVELS
from src.ast_grep_mcp.utils.benchmarks import run_benchmarks
from src.ast_grep_mcp.utils.config_generator import (
    generate_and_save_config,
    generate_example_ignore_file,
)
import sys
import logging
import tempfile
import json
import os
import re
from pathlib import Path

# Define a version constant
VERSION = "0.2.0"

# Try to get version from package metadata if possible
try:
    import pkg_resources

    try:
        VERSION = pkg_resources.get_distribution("ast_grep_mcp").version
    except pkg_resources.DistributionNotFound:
        # Keep using the default version if the package is not installed
        pass
except ImportError:
    # Keep using the default version if pkg_resources is not available
    pass

console = Console()
app = typer.Typer(help="AST Grep MCP server CLI")


def validate_log_level(log_level: str) -> int:
    """Validate and convert the log level string to an integer."""
    if log_level.lower() in LOG_LEVELS:
        return LOG_LEVELS[log_level.lower()]
    else:
        log_level_options = ", ".join(LOG_LEVELS.keys())
        raise typer.BadParameter(
            f"Invalid log level: {log_level}. Valid options are: {log_level_options}"
        )


def load_config(config_file: str) -> ServerConfig:
    """Load configuration from a file."""
    try:
        return ServerConfig.from_file(config_file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[bold red]Error loading configuration:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def generate_config(
    output_file: str = typer.Option(
        "ast-grep.yml", "--output", "-o", help="Output file path"
    ),
    ignore_file: bool = typer.Option(
        False, "--ignore-file", "-i", help="Also generate example .ast-grepignore file"
    ),
    ignore_output: str = typer.Option(
        ".ast-grepignore", help="Path for the generated ignore file"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
):
    """
    Generate a configuration file with default settings and helpful comments.

    This command creates an ast-grep.yml file that can be customized for your project.
    """
    try:
        # Check if output file already exists
        if os.path.exists(output_file) and not force:
            console.print(f"[bold red]File already exists:[/bold red] {output_file}")
            console.print("Use --force to overwrite")
            raise typer.Exit(code=1)

        # Generate and save the configuration file
        generate_and_save_config(output_file)
        console.print(
            f"[bold green]Generated configuration file:[/bold green] {output_file}"
        )

        # Generate ignore file if requested
        if ignore_file:
            if os.path.exists(ignore_output) and not force:
                console.print(
                    f"[bold red]File already exists:[/bold red] {ignore_output}"
                )
                console.print("Use --force to overwrite")
            else:
                generate_example_ignore_file(ignore_output)
                console.print(
                    f"[bold green]Generated ignore file:[/bold green] {ignore_output}"
                )

        console.print("\n[bold blue]Next steps:[/bold blue]")
        console.print("1. Review and customize the generated configuration")
        console.print(
            "2. Use the configuration with 'ast-grep-mcp start --config ast-grep.yml'"
        )

        return 0

    except Exception as e:
        console.print(f"[bold red]Error generating configuration:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def start(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        "-l",
        help="Log level (debug, info, warning, error, critical)",
    ),
    log_file: str = typer.Option(None, "--log-file", "-f", help="Log file path"),
    log_to_console: bool = typer.Option(
        True, "--log-to-console", "-c", help="Whether to log to console"
    ),
    cache_size: int = typer.Option(
        128, "--cache-size", help="Size of the result cache"
    ),
    config_file: str = typer.Option(
        None, "--config", help="Path to configuration file (JSON or YAML)"
    ),
    safe_roots: str = typer.Option(
        None,
        "--safe-roots",
        "-s",
        help="Comma-separated list of safe root directories for file operations",
    ),
    ignore_file: str = typer.Option(
        None, "--ignore-file", help="Path to .ast-grepignore file"
    ),
    preview_mode: bool = typer.Option(
        False, "--preview-mode", help="Enable refactoring preview mode"
    ),
    validation_strictness: str = typer.Option(
        None,
        "--validation-strictness",
        help="Pattern validation strictness (strict, normal, relaxed)",
    ),
    verbosity: str = typer.Option(
        None,
        "--verbosity",
        help="Diagnostic verbosity level (none, minimal, normal, detailed, diagnostic)",
    ),
    output_format: str = typer.Option(
        None, "--output-format", help="Output format (json, text, sarif, html)"
    ),
    enhanced: bool = typer.Option(
        True, "--enhanced/--no-enhanced", help="Use enhanced server with better token management (default: True)"
    ),
):
    """
    Start the AST Grep MCP server.

    The server will listen for MCP requests and process ast-grep commands.
    """
    try:
        # First try to find and load the nearest config file if none specified
        if config_file is None:
            config = ServerConfig.find_and_load_config()
            console.print(
                f"Using configuration from: {config_file if config_file else 'default settings'}"
            )
        else:
            # Load configuration from file
            config = ServerConfig.from_file(config_file)
            console.print(f"Loaded configuration from: {config_file}")

        # Override config with command line options if provided
        overrides = {}

        if host != "localhost":
            overrides["host"] = host
        if port != 8080:
            overrides["port"] = port
        if log_level != "info":
            overrides["log_level"] = validate_log_level(log_level)
        if log_file is not None:
            overrides["log_file"] = log_file
        if not log_to_console:
            overrides["log_to_console"] = False
        if cache_size != 128:
            overrides["cache_size"] = cache_size
        if safe_roots is not None:
            overrides["safe_roots"] = [
                root.strip() for root in safe_roots.split(",") if root.strip()
            ]
        if ignore_file is not None:
            overrides["ignore_file"] = ignore_file

        # Handle nested configurations
        if preview_mode:
            if "refactoring_config" not in overrides:
                overrides["refactoring_config"] = {}
            overrides["refactoring_config"]["preview_mode"] = True

        if validation_strictness is not None:
            if "pattern_config" not in overrides:
                overrides["pattern_config"] = {}
            overrides["pattern_config"]["validation_strictness"] = validation_strictness

        if verbosity is not None:
            if "diagnostic_config" not in overrides:
                overrides["diagnostic_config"] = {}
            overrides["diagnostic_config"]["verbosity"] = verbosity

        if output_format is not None:
            if "output_config" not in overrides:
                overrides["output_config"] = {}
            overrides["output_config"]["format"] = output_format

        # Apply overrides if any were specified
        if overrides:
            updated_config = ServerConfig.from_dict({**config.to_dict(), **overrides})
            config = updated_config

        # Set up logging
        logger = config.setup_logging("ast_grep_mcp.main")
        logger.info(f"Starting AST Grep MCP server on {config.host}:{config.port}")
        logger.info(f"Cache size set to {config.cache_size}")

        # Create and start the server
        if enhanced:
            logger.info("Using enhanced server with better token management")
            from src.ast_grep_mcp.core.ast_grep_mcp_enhanced import create_enhanced_server
            server = create_enhanced_server(config)
        else:
            server = AstGrepMCP(config)
        server.start()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


# Keep serve command for backward compatibility
@app.command()
def serve(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        "-l",
        help="Log level (debug, info, warning, error, critical)",
    ),
    log_file: str = typer.Option(None, "--log-file", "-f", help="Log file path"),
    log_to_console: bool = typer.Option(
        True, "--log-to-console", "-c", help="Whether to log to console"
    ),
    cache_size: int = typer.Option(
        128, "--cache-size", help="Size of the result cache"
    ),
    config_file: str = typer.Option(
        None, "--config", help="Path to configuration file (JSON or YAML)"
    ),
    safe_roots: str = typer.Option(
        None,
        "--safe-roots",
        "-s",
        help="Comma-separated list of safe root directories for file operations",
    ),
    ignore_file: str = typer.Option(
        None, "--ignore-file", help="Path to .ast-grepignore file"
    ),
    preview_mode: bool = typer.Option(
        False, "--preview-mode", help="Enable refactoring preview mode"
    ),
    validation_strictness: str = typer.Option(
        None,
        "--validation-strictness",
        help="Pattern validation strictness (strict, normal, relaxed)",
    ),
    verbosity: str = typer.Option(
        None,
        "--verbosity",
        help="Diagnostic verbosity level (none, minimal, normal, detailed, diagnostic)",
    ),
    output_format: str = typer.Option(
        None, "--output-format", help="Output format (json, text, sarif, html)"
    ),
    enhanced: bool = typer.Option(
        True, "--enhanced/--no-enhanced", help="Use enhanced server with better token management (default: True)"
    ),
):
    """
    Start the AST Grep MCP server (alias for 'start').
    """
    return start(
        host,
        port,
        log_level,
        log_file,
        log_to_console,
        cache_size,
        config_file,
        safe_roots,
        ignore_file,
        preview_mode,
        validation_strictness,
        verbosity,
        output_format,
        enhanced,
    )


@app.command()
def version():
    """
    Show the current version of the AST Grep MCP server.
    """
    console.print(f"[bold green]AST Grep MCP Server v{VERSION}[/bold green]")

    # Show additional configuration info
    console.print("\n[bold blue]Configuration:[/bold blue]")
    console.print("- Default host: localhost")
    console.print("- Default port: 8080")
    console.print("- Default cache size: 128")
    console.print("- Default log level: INFO")

    # Show security features
    console.print("\n[bold blue]Security Features:[/bold blue]")
    console.print("- Pattern sanitization to prevent command injection")
    console.print("- Path access controls via --safe-roots option")
    console.print("- View docs/security-guide.md for more information")


@app.command()
def interactive():
    """
    Start an interactive AST Grep session.

    This mode allows you to test patterns and explore AST Grep functionality
    without starting a full server.
    """
    from src.ast_grep_mcp.ast_analyzer import AstAnalyzer
    from src.ast_grep_mcp.language_handlers import get_handler

    console.print("[bold green]AST Grep Interactive Mode[/bold green]")
    console.print("Type 'help' for available commands, 'exit' to quit")

    analyzer = AstAnalyzer()
    current_language = "python"
    current_code = ""

    def get_pattern_help():
        handler = get_handler(current_language)
        if not handler:
            return "No pattern examples available for this language"

        patterns = handler.get_default_patterns()
        result = f"[bold]Pattern examples for {current_language}:[/bold]\n"
        for name, pattern in patterns.items():
            result += f"- {name}: {pattern}\n"
        return result

    commands = {
        "help": "Show this help message",
        "exit": "Exit interactive mode",
        "languages": "List supported languages",
        "language <name>": "Set current language",
        "patterns": "Show example patterns for current language",
        "code <file_path>": "Load code from file",
        "analyze <pattern>": "Analyze current code with pattern",
        "refactor <pattern> <replacement>": "Refactor code with pattern and replacement",
    }

    while True:
        try:
            user_input = input(f"{current_language}> ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                break

            if user_input.lower() == "help":
                console.print("[bold]Available commands:[/bold]")
                for cmd, desc in commands.items():
                    console.print(f"- {cmd}: {desc}")
                continue

            if user_input.lower() == "languages":
                langs = analyzer.get_supported_languages()
                console.print("[bold]Supported languages:[/bold]")
                for lang, exts in langs.items():
                    console.print(f"- {lang}: {', '.join(exts)}")
                continue

            if user_input.lower().startswith("language "):
                lang = user_input[9:].strip()
                if lang in analyzer.get_supported_languages():
                    current_language = lang
                    console.print(f"Language set to [bold]{lang}[/bold]")
                else:
                    console.print(f"[bold red]Unsupported language:[/bold red] {lang}")
                continue

            if user_input.lower() == "patterns":
                console.print(get_pattern_help())
                continue

            if user_input.lower().startswith("code "):
                file_path = user_input[5:].strip()
                try:
                    with open(file_path, "r") as f:
                        current_code = f.read()
                    console.print(f"Loaded code from [bold]{file_path}[/bold]")
                    console.print(f"Code length: {len(current_code)} characters")
                except Exception as e:
                    console.print(f"[bold red]Error loading file:[/bold red] {str(e)}")
                continue

            if user_input.lower().startswith("analyze "):
                if not current_code:
                    console.print(
                        "[bold yellow]No code loaded. Use 'code <file_path>' to load code.[/bold yellow]"
                    )
                    continue

                pattern = user_input[8:].strip()
                try:
                    result = analyzer.analyze_code(
                        current_code, current_language, pattern
                    )
                    if "error" in result:
                        console.print(f"[bold red]Error:[/bold red] {result['error']}")
                    else:
                        console.print(
                            f"[bold green]Found {len(result['matches'])} matches[/bold green]"
                        )
                        for i, match in enumerate(result["matches"]):
                            console.print(f"Match {i+1}:")
                            console.print(
                                f"  Line: {match['range']['start']['line']} - {match['range']['end']['line']}"
                            )
                            console.print(f"  Text: {match['text']}")
                except Exception as e:
                    console.print(
                        f"[bold red]Error analyzing code:[/bold red] {str(e)}"
                    )
                continue

            if user_input.lower().startswith("refactor "):
                if not current_code:
                    console.print(
                        "[bold yellow]No code loaded. Use 'code <file_path>' to load code.[/bold yellow]"
                    )
                    continue

                parts = user_input[9:].strip().split(" ", 1)
                if len(parts) != 2:
                    console.print(
                        "[bold yellow]Usage: refactor <pattern> <replacement>[/bold yellow]"
                    )
                    continue

                pattern, replacement = parts
                try:
                    result = analyzer.refactor_code(
                        current_code, current_language, pattern, replacement
                    )
                    if "error" in result:
                        console.print(f"[bold red]Error:[/bold red] {result['error']}")
                    else:
                        console.print(
                            f"[bold green]Refactored {result['stats']['matches']} matches[/bold green]"
                        )
                        console.print("New code:")
                        console.print(
                            result["refactored_code"][:200] + "..."
                            if len(result["refactored_code"]) > 200
                            else result["refactored_code"]
                        )
                except Exception as e:
                    console.print(
                        f"[bold red]Error refactoring code:[/bold red] {str(e)}"
                    )
                continue

            console.print(f"[bold yellow]Unknown command:[/bold yellow] {user_input}")
            console.print("Type 'help' for available commands")

        except KeyboardInterrupt:
            break
        except EOFError:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

    console.print("[bold green]Exiting interactive mode[/bold green]")


@app.command()
def benchmark(
    output_dir: str = typer.Option(
        None, "--output-dir", "-o", help="Directory to output benchmark results"
    ),
    num_files: int = typer.Option(
        200, "--num-files", "-n", help="Number of synthetic files to create"
    ),
    iterations: int = typer.Option(
        3, "--iterations", "-i", help="Number of iterations for each benchmark"
    ),
    log_level: str = typer.Option(
        "info", "--log-level", "-l", help="Log level for benchmark output"
    ),
    save_json: bool = typer.Option(
        True, "--save-json", help="Save benchmark results as JSON"
    ),
    batch_sizes: str = typer.Option(
        "auto,5,10,20",
        "--batch-sizes",
        help="Comma-separated list of batch sizes to test (use 'auto' for automatic batch sizing)",
    ),
    complexity: str = typer.Option(
        "medium",
        "--complexity",
        help="Complexity of synthetic files (simple, medium, complex)",
    ),
):
    """
    Run performance benchmarks and report results.

    This command creates synthetic files, runs both sequential and parallel
    pattern searches, and reports the speedup achieved.
    """
    try:
        # Convert log_level string to integer
        log_level_int = validate_log_level(log_level)

        # Create a temporary directory if not provided
        if not output_dir:
            output_dir = tempfile.mkdtemp(prefix="ast_grep_benchmark_")
        else:
            os.makedirs(output_dir, exist_ok=True)

        # Configure logging
        config = ServerConfig(log_level=log_level_int, log_to_console=True)
        logger = config.setup_logging("ast_grep_mcp.benchmark")

        # Parse batch sizes
        parsed_batch_sizes = []
        for size in batch_sizes.split(","):
            if size.strip().lower() == "auto":
                parsed_batch_sizes.append(None)
            else:
                try:
                    parsed_batch_sizes.append(int(size.strip()))
                except ValueError:
                    console.print(
                        f"[yellow]Warning: Invalid batch size '{size}', skipping.[/yellow]"
                    )

        if not parsed_batch_sizes:
            parsed_batch_sizes = [None, 5, 10, 20]  # Default if none are valid

        # Show progress spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Running benchmarks with {num_files} files, {iterations} iterations...",
                total=None,
            )

            # Run benchmarks
            logger.info(
                f"Running benchmarks with {num_files} files, {iterations} iterations"
            )
            logger.info(f"Testing batch sizes: {parsed_batch_sizes}")
            logger.info(f"Output directory: {output_dir}")

            result = run_benchmarks(
                output_dir=output_dir,
                num_files=num_files,
                batch_sizes=parsed_batch_sizes,
            )

            # Mark task as completed
            progress.update(task, completed=True)

        # Display results in a table
        table = Table(title="AST Grep Performance Benchmark Results")
        table.add_column("Pattern", style="cyan")
        table.add_column("Best Config", style="green")
        table.add_column("Speedup", style="magenta")
        table.add_column("Improvement", style="yellow")

        for pattern, stats in result["pattern_results"].items():
            speedup = f"{stats['best_speedup']:.2f}x"
            improvement = f"{stats['best_speedup_percentage']:.2f}%"
            table.add_row(pattern, stats["best_config"], speedup, improvement)

        console.print(table)

        # Display overall result
        if result["success"]:
            console.print("[bold green]✓ Target speedup achieved![/bold green]")
        else:
            console.print("[bold yellow]✗ Target speedup not achieved.[/bold yellow]")

        console.print(
            f"Best configuration: [bold green]{result['best_config']}[/bold green]"
        )
        console.print(
            f"Average speedup: [bold]{result['best_avg_speedup']:.2f}x[/bold] ({result['best_avg_speedup_percentage']:.2f}%)"
        )

        # Save results as JSON if requested
        if save_json:
            json_path = os.path.join(output_dir, "benchmark_results.json")
            with open(json_path, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {json_path}")
            console.print(f"Results saved to [bold]{json_path}[/bold]")

        console.print(f"Temporary files located at: {output_dir}")

        # Performance recommendations
        console.print("\n[bold blue]Recommendations:[/bold blue]")

        if result["best_avg_speedup"] < 1:
            console.print(
                "- Consider using sequential processing for your workload size"
            )
            console.print(
                "- The overhead of parallel processing exceeds benefits for small workloads"
            )
        else:
            console.print(
                f"- Use batch size from best configuration ({result['best_config']})"
            )
            console.print("- Adjust cache size based on your typical workload")

        # Add configuration example
        console.print("\n[bold blue]Example Configuration:[/bold blue]")
        console.print(
            """
# Add to your MCP configuration:
"mcpServers": {
  "ast-grep": {
    "command": "uv",
    "args": [
      "--directory", "/path/to/ast-grep-mcp",
      "run", "python", "main.py", "server",
      "--cache-size", "128"
    ],
    "env": {}
  }
}
        """
        )

        return 0 if result["success"] else 1

    except Exception as e:
        console.print(f"[bold red]Error running benchmarks:[/bold red] {str(e)}")
        import traceback

        console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def pattern_builder():
    """
    Interactive pattern builder tool.

    This mode helps you create and test ast-grep patterns step by step,
    showing matches in real-time and providing suggestions.
    """
    from src.ast_grep_mcp.ast_analyzer import AstAnalyzer
    from src.ast_grep_mcp.language_handlers import get_handler

    console.print("[bold green]AST Grep Interactive Pattern Builder[/bold green]")
    console.print("This tool will help you build and test patterns interactively.")

    analyzer = AstAnalyzer()
    current_language = "python"  # Default language
    current_code = ""
    pattern_history = []

    def show_language_selection():
        """Show language selection menu"""
        languages = list(analyzer.get_supported_languages().keys())

        console.print("\n[bold blue]Available languages:[/bold blue]")
        for i, lang in enumerate(languages, 1):
            console.print(f"  {i}. {lang}")

        while True:
            try:
                choice = input(
                    "Select language number (or press Enter to keep current): "
                )
                if not choice.strip():
                    return current_language

                index = int(choice) - 1
                if 0 <= index < len(languages):
                    return languages[index]
                else:
                    console.print("[bold red]Invalid selection. Try again.[/bold red]")
            except ValueError:
                console.print("[bold red]Please enter a number.[/bold red]")

    def load_code():
        """Load code from file or direct input"""
        nonlocal current_code

        console.print("\n[bold blue]Load code to match against:[/bold blue]")
        console.print("  1. Load from file")
        console.print("  2. Enter code directly")
        console.print("  3. Use example code")

        choice = input("Select option: ")

        if choice == "1":
            file_path = input("Enter file path: ")
            try:
                with open(file_path, "r") as f:
                    current_code = f.read()
                console.print(f"Loaded code from [bold]{file_path}[/bold]")
            except Exception as e:
                console.print(f"[bold red]Error loading file:[/bold red] {str(e)}")
                return False

        elif choice == "2":
            console.print("Enter code (end with a line containing only 'END'):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            current_code = "\n".join(lines)

        elif choice == "3":
            # Provide example code based on language
            handler = get_handler(current_language)
            if handler:
                examples = {
                    "python": """def example_function(param1, param2=None):
    \"\"\"Example docstring\"\"\"
    result = []
    for i in range(10):
        if i % 2 == 0:
            result.append(i)
    return result

class ExampleClass:
    def __init__(self, value):
        self.value = value
        
    def method(self):
        return self.value * 2
""",
                    "javascript": """function exampleFunction(param1, param2) {
    const result = [];
    for (let i = 0; i < 10; i++) {
        if (i % 2 === 0) {
            result.push(i);
        }
    }
    return result;
}

class ExampleClass {
    constructor(value) {
        this.value = value;
    }
    
    method() {
        return this.value * 2;
    }
}
""",
                    "typescript": """function exampleFunction(param1: string, param2?: number): number[] {
    const result: number[] = [];
    for (let i = 0; i < 10; i++) {
        if (i % 2 === 0) {
            result.push(i);
        }
    }
    return result;
}

class ExampleClass {
    private value: number;
    
    constructor(value: number) {
        this.value = value;
    }
    
    method(): number {
        return this.value * 2;
    }
}
""",
                    "c": """#include <stdio.h>

int example_function(int param1, int param2) {
    int result[10];
    int count = 0;
    
    for (int i = 0; i < 10; i++) {
        if (i % 2 == 0) {
            result[count++] = i;
        }
    }
    
    return count;
}

typedef struct {
    int value;
} ExampleStruct;

int method(ExampleStruct* obj) {
    return obj->value * 2;
}
""",
                    "rust": """fn example_function(param1: i32, param2: Option<i32>) -> Vec<i32> {
    let mut result = Vec::new();
    for i in 0..10 {
        if i % 2 == 0 {
            result.push(i);
        }
    }
    return result;
}

struct ExampleStruct {
    value: i32,
}

impl ExampleStruct {
    fn new(value: i32) -> Self {
        Self { value }
    }
    
    fn method(&self) -> i32 {
        self.value * 2
    }
}
""",
                    "go": """package main

import "fmt"

func exampleFunction(param1 int, param2 int) []int {
    result := make([]int, 0)
    for i := 0; i < 10; i++ {
        if i % 2 == 0 {
            result = append(result, i)
        }
    }
    return result
}

type ExampleStruct struct {
    value int
}

func (e *ExampleStruct) Method() int {
    return e.value * 2
}
""",
                }

                current_code = examples.get(
                    current_language, "// No example available for this language"
                )
            else:
                current_code = "// No example available"

        else:
            console.print("[bold red]Invalid choice[/bold red]")
            return False

        return True

    def show_pattern_help():
        """Show pattern help for current language"""
        handler = get_handler(current_language)
        if not handler:
            console.print(
                "[bold yellow]No pattern examples available for this language[/bold yellow]"
            )
            return

        patterns = handler.get_default_patterns()
        console.print(
            f"\n[bold blue]Pattern examples for {current_language}:[/bold blue]"
        )
        categories = {}

        # Group patterns by category based on comments in the code
        current_category = "General"
        for name, pattern in patterns.items():
            # Try to infer category from pattern name
            if name.startswith("function_"):
                category = "Functions"
            elif name.startswith("class_"):
                category = "Classes"
            elif (
                name.startswith("if_")
                or name.startswith("for_")
                or name.startswith("while_")
            ):
                category = "Control Flow"
            elif "security" in name or "vulnerability" in name:
                category = "Security Vulnerabilities"
            elif "performance" in name or "inefficient" in name:
                category = "Performance"
            elif "anti_pattern" in name or "smell" in name:
                category = "Anti-Patterns"
            else:
                category = current_category

            if category not in categories:
                categories[category] = []

            categories[category].append((name, pattern))

        # Display patterns by category
        for category, pattern_list in categories.items():
            console.print(f"\n[bold]{category}:[/bold]")
            for name, pattern in pattern_list[:5]:  # Show only 5 examples per category
                console.print(f"  [cyan]{name}[/cyan]: {pattern}")

            if len(pattern_list) > 5:
                console.print(f"  ... and {len(pattern_list) - 5} more")

        console.print("\n[bold]Pattern Syntax Help:[/bold]")
        console.print("  - $VAR: Match a single expression or identifier")
        console.print("  - $$$VAR: Match multiple expressions or statements")
        console.print("  - $: Match anything")
        console.print("  - $_: Match anything (unnamed)")
        console.print("  - Use pattern library with the 'library' command")

    def show_common_patterns():
        """Show commonly used patterns"""
        common_patterns = {
            "Function definition": "def $NAME($$$PARAMS):",
            "Function call": "$NAME($$$ARGS)",
            "Class definition": "class $NAME:",
            "For loop": "for $VAR in $ITER:",
            "If statement": "if $CONDITION:",
            "Variable assignment": "$NAME = $VALUE",
        }

        console.print("\n[bold blue]Common patterns:[/bold blue]")
        for name, pattern in common_patterns.items():
            console.print(f"  [cyan]{name}[/cyan]: {pattern}")

    def test_pattern(pattern, show_results=True):
        """Test a pattern against the current code"""
        if not current_code:
            console.print(
                "[bold yellow]No code loaded. Use 'load' to load code first.[/bold yellow]"
            )
            return None

        result = analyzer.analyze_code(current_code, current_language, pattern)

        if "error" in result:
            console.print(f"[bold red]Error:[/bold red] {result['error']}")
            if "suggestion_message" in result:
                console.print(result["suggestion_message"])
            return None

        matches = result.get("matches", [])

        if not matches:
            console.print("[bold yellow]No matches found.[/bold yellow]")
            if "suggestion_message" in result:
                console.print(result["suggestion_message"])
            return None

        if show_results:
            console.print(f"\n[bold green]Found {len(matches)} matches:[/bold green]")
            for i, match in enumerate(matches[:5], 1):  # Show at most 5 matches
                console.print(f"Match {i}:")
                console.print(
                    f"  Line: {match['location']['start']['line']} - {match['location']['end']['line']}"
                )

                # Truncate very long matches
                match_text = match["text"]
                if len(match_text) > 80:
                    match_text = match_text[:77] + "..."

                console.print(f"  Text: {match_text}")

            if len(matches) > 5:
                console.print(f"... and {len(matches) - 5} more matches")

        return matches

    def save_pattern(pattern, description=None):
        """Save pattern to user library"""
        if not description:
            description = input("Enter a brief description for this pattern: ")

        # Create user pattern library directory if it doesn't exist
        user_lib_dir = Path.home() / ".ast-grep-mcp" / "patterns"
        user_lib_dir.mkdir(parents=True, exist_ok=True)

        # Save to language-specific file
        pattern_file = user_lib_dir / f"{current_language}_patterns.txt"

        with open(pattern_file, "a") as f:
            f.write(f"{pattern} # {description}\n")

        console.print(f"[bold green]✓ Pattern saved to {pattern_file}[/bold green]")

    def load_user_patterns():
        """Load patterns from user library"""
        user_lib_dir = Path.home() / ".ast-grep-mcp" / "patterns"
        pattern_file = user_lib_dir / f"{current_language}_patterns.txt"

        if not pattern_file.exists():
            console.print(
                f"[bold yellow]No saved patterns found for {current_language}[/bold yellow]"
            )
            return []

        patterns = []
        with open(pattern_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(" # ", 1)
                    pattern = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ""
                    patterns.append((pattern, description))

        return patterns

    def show_library():
        """Show pattern library"""
        patterns = load_user_patterns()

        if not patterns:
            console.print(
                f"[bold yellow]No saved patterns found for {current_language}[/bold yellow]"
            )
            return

        console.print(
            f"\n[bold blue]Your {current_language} pattern library:[/bold blue]"
        )
        for i, (pattern, description) in enumerate(patterns, 1):
            console.print(f"{i}. [cyan]{description}[/cyan]: {pattern}")

        console.print("\nEnter pattern number to use, or press Enter to cancel:")
        choice = input("> ")

        if not choice.strip():
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(patterns):
                return patterns[index][0]
            else:
                console.print("[bold red]Invalid selection[/bold red]")
        except ValueError:
            console.print("[bold red]Please enter a number[/bold red]")

    def interactive_builder():
        """Interactive pattern builder"""
        if not current_code:
            console.print(
                "[bold yellow]No code loaded. Use 'load' to load code first.[/bold yellow]"
            )
            return

        console.print("\n[bold blue]Interactive Pattern Builder[/bold blue]")
        console.print("This will help you build a pattern step by step.")

        # Show a small sample of the code
        code_preview = (
            current_code[:200] + "..." if len(current_code) > 200 else current_code
        )
        console.print(f"\nCode preview:\n{code_preview}")

        # Start with a simple pattern
        current_pattern = input(
            "\nEnter a starting pattern (or press Enter for empty): "
        )

        # Interactive refinement loop
        while True:
            console.print(
                f"\nCurrent pattern: [bold cyan]{current_pattern}[/bold cyan]"
            )

            # Test the current pattern
            matches = test_pattern(current_pattern)

            # Ask for refinement
            console.print("\n[bold]What would you like to do?[/bold]")
            console.print("  1. Refine the pattern")
            console.print("  2. Save this pattern")
            console.print("  3. Start over")
            console.print("  4. Exit builder")

            choice = input("> ")

            if choice == "1":
                print("\n[bold]Pattern Refinement Options:[/bold]")
                print(
                    "  1. Make a variable more specific (e.g., $VAR → $SPECIFIC_NAME)"
                )
                print("  2. Make a variable more general (e.g., $SPECIFIC_NAME → $VAR)")
                print("  3. Add more context (e.g., add surrounding code)")
                print("  4. Remove some context")
                print("  5. Edit the pattern directly")

                refine_choice = input("> ")

                if refine_choice == "1":
                    var_pattern = re.compile(r"\$([A-Z_][A-Z0-9_]*)")
                    var_matches = list(var_pattern.finditer(current_pattern))

                    if not var_matches:
                        console.print(
                            "[bold yellow]No variables found in pattern[/bold yellow]"
                        )
                        continue

                    console.print("Variables in pattern:")
                    for i, match in enumerate(var_matches, 1):
                        console.print(f"  {i}. ${match.group(1)}")

                    var_choice = input("Select variable to make more specific: ")
                    try:
                        index = int(var_choice) - 1
                        if 0 <= index < len(var_matches):
                            var_match = var_matches[index]
                            var_name = var_match.group(1)
                            new_name = input(f"Enter new name for ${var_name}: $")
                            if new_name:
                                current_pattern = (
                                    current_pattern[: var_match.start()]
                                    + "$"
                                    + new_name
                                    + current_pattern[var_match.end() :]
                                )
                        else:
                            console.print("[bold red]Invalid selection[/bold red]")
                    except ValueError:
                        console.print("[bold red]Please enter a number[/bold red]")

                elif refine_choice == "2":
                    var_pattern = re.compile(r"\$([A-Z_][A-Z0-9_]*)")
                    var_matches = list(var_pattern.finditer(current_pattern))

                    if not var_matches:
                        console.print(
                            "[bold yellow]No variables found in pattern[/bold yellow]"
                        )
                        continue

                    console.print("Variables in pattern:")
                    for i, match in enumerate(var_matches, 1):
                        console.print(f"  {i}. ${match.group(1)}")

                    var_choice = input("Select variable to make more general: ")
                    try:
                        index = int(var_choice) - 1
                        if 0 <= index < len(var_matches):
                            var_match = var_matches[index]
                            generic_options = ["VAR", "EXPR", "STMT", "NAME", "_"]

                            console.print("Generic variable options:")
                            for i, name in enumerate(generic_options, 1):
                                console.print(f"  {i}. ${name}")

                            generic_choice = input("Select generic variable: ")
                            try:
                                gen_index = int(generic_choice) - 1
                                if 0 <= gen_index < len(generic_options):
                                    current_pattern = (
                                        current_pattern[: var_match.start()]
                                        + "$"
                                        + generic_options[gen_index]
                                        + current_pattern[var_match.end() :]
                                    )
                                else:
                                    console.print(
                                        "[bold red]Invalid selection[/bold red]"
                                    )
                            except ValueError:
                                console.print(
                                    "[bold red]Please enter a number[/bold red]"
                                )
                        else:
                            console.print("[bold red]Invalid selection[/bold red]")
                    except ValueError:
                        console.print("[bold red]Please enter a number[/bold red]")

                elif refine_choice == "3":
                    # Try to find a match to add context around
                    matches = test_pattern(current_pattern, show_results=False)
                    if not matches:
                        console.print(
                            "[bold yellow]No matches to add context around[/bold yellow]"
                        )
                        continue

                    # Get the matched code and some context
                    match = matches[0]
                    lines = current_code.split("\n")

                    start_line = max(0, match["location"]["start"]["line"] - 2)
                    end_line = min(len(lines), match["location"]["end"]["line"] + 2)

                    context_lines = lines[start_line:end_line]
                    console.print("Code context:")
                    for i, line in enumerate(context_lines, start_line + 1):
                        console.print(f"  {i}: {line}")

                    # Ask which lines to include
                    include_lines = input(
                        "Enter line numbers to include (e.g., 10-12): "
                    )
                    try:
                        if "-" in include_lines:
                            start, end = map(int, include_lines.split("-"))
                            context_code = "\n".join(lines[start - 1 : end])
                        else:
                            line_nums = list(map(int, include_lines.split(",")))
                            context_code = "\n".join(lines[ln - 1] for ln in line_nums)

                        # Replace variables in the new context
                        context_code = context_code.replace(
                            match["text"], current_pattern
                        )
                        current_pattern = context_code
                    except ValueError:
                        console.print("[bold red]Invalid line numbers[/bold red]")

                elif refine_choice == "4":
                    if "\n" in current_pattern:
                        lines = current_pattern.split("\n")
                        console.print("Current pattern lines:")
                        for i, line in enumerate(lines, 1):
                            console.print(f"  {i}: {line}")

                        remove_lines = input(
                            "Enter line numbers to remove (e.g., 1,3): "
                        )
                        try:
                            line_nums = list(map(int, remove_lines.split(",")))
                            kept_lines = [
                                line
                                for i, line in enumerate(lines, 1)
                                if i not in line_nums
                            ]
                            current_pattern = "\n".join(kept_lines)
                        except ValueError:
                            console.print("[bold red]Invalid line numbers[/bold red]")
                    else:
                        console.print(
                            "[bold yellow]Pattern is a single line, can't remove context[/bold yellow]"
                        )

                elif refine_choice == "5":
                    new_pattern = input("Enter new pattern: ")
                    if new_pattern:
                        current_pattern = new_pattern

            elif choice == "2":
                if matches:
                    save_pattern(current_pattern)
                    pattern_history.append(current_pattern)
                else:
                    console.print(
                        "[bold yellow]Pattern has no matches, save anyway? (y/n)[/bold yellow]"
                    )
                    if input().lower() == "y":
                        save_pattern(current_pattern)
                        pattern_history.append(current_pattern)
                break

            elif choice == "3":
                current_pattern = input("\nEnter a starting pattern: ")

            elif choice == "4":
                break

            else:
                console.print("[bold red]Invalid choice[/bold red]")

    # Main command loop
    commands = {
        "help": "Show this help message",
        "language": "Select a language",
        "load": "Load code to match against",
        "pattern": "Test a pattern",
        "builder": "Start interactive pattern builder",
        "library": "View and use saved patterns",
        "examples": "Show example patterns",
        "history": "Show pattern history",
        "save": "Save current pattern",
        "clear": "Clear current code",
        "exit": "Exit pattern builder",
    }

    current_pattern = ""

    # Initial setup
    console.print(
        "\n[bold blue]First, select a language and load some code:[/bold blue]"
    )
    current_language = show_language_selection()
    load_code()

    # If no code was loaded, suggest examples
    if not current_code:
        console.print(
            "[bold yellow]No code loaded. You can load code later with the 'load' command.[/bold yellow]"
        )

    console.print("\n[bold]Available commands:[/bold]")
    for cmd, desc in commands.items():
        console.print(f"  - {cmd}: {desc}")

    while True:
        try:
            command = input(f"\n{current_language}> ").strip().lower()

            if not command:
                continue

            if command == "exit":
                break

            if command == "help":
                console.print("\n[bold]Available commands:[/bold]")
                for cmd, desc in commands.items():
                    console.print(f"  - {cmd}: {desc}")
                continue

            if command == "language":
                current_language = show_language_selection()
                console.print(f"Language set to [bold]{current_language}[/bold]")
                continue

            if command == "load":
                load_code()
                continue

            if command.startswith("pattern "):
                current_pattern = command[8:].strip()
                test_pattern(current_pattern)
                if current_pattern:
                    pattern_history.append(current_pattern)
                continue

            if command == "pattern":
                current_pattern = input("Enter pattern to test: ")
                test_pattern(current_pattern)
                if current_pattern:
                    pattern_history.append(current_pattern)
                continue

            if command == "builder":
                interactive_builder()
                continue

            if command == "library":
                pattern = show_library()
                if pattern:
                    current_pattern = pattern
                    test_pattern(current_pattern)
                continue

            if command == "examples":
                show_pattern_help()
                show_common_patterns()
                continue

            if command == "history":
                if not pattern_history:
                    console.print("[bold yellow]No pattern history yet[/bold yellow]")
                    continue

                console.print("\n[bold blue]Pattern history:[/bold blue]")
                for i, pattern in enumerate(pattern_history, 1):
                    console.print(f"{i}. {pattern}")

                console.print(
                    "\nEnter pattern number to use, or press Enter to cancel:"
                )
                choice = input("> ")

                if not choice.strip():
                    continue

                try:
                    index = int(choice) - 1
                    if 0 <= index < len(pattern_history):
                        current_pattern = pattern_history[index]
                        test_pattern(current_pattern)
                    else:
                        console.print("[bold red]Invalid selection[/bold red]")
                except ValueError:
                    console.print("[bold red]Please enter a number[/bold red]")

                continue

            if command == "save":
                if not current_pattern:
                    console.print(
                        "[bold yellow]No current pattern to save[/bold yellow]"
                    )
                    continue

                save_pattern(current_pattern)
                continue

            if command == "clear":
                current_code = ""
                console.print("[bold]Code cleared[/bold]")
                continue

            console.print(f"[bold yellow]Unknown command:[/bold yellow] {command}")
            console.print("Type 'help' for available commands")

        except KeyboardInterrupt:
            break
        except EOFError:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

    console.print("[bold green]Exiting pattern builder[/bold green]")


def main():
    """Main entry point for the AST Grep MCP CLI."""
    try:
        app()
    except Exception as e:
        # Create a basic logger for errors
        logger = logging.getLogger("ast_grep_mcp.main")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)

        logger.error(f"Error: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
