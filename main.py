import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from src.ast_grep_mcp.core import AstGrepMCP, ServerConfig
from src.ast_grep_mcp.core.config import LOG_LEVELS
from src.ast_grep_mcp.utils.benchmarks import run_benchmarks
import sys
import logging
import tempfile
import json
import os

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
        raise typer.BadParameter(f"Invalid log level: {log_level}. Valid options are: {log_level_options}")

def load_config(config_file: str) -> ServerConfig:
    """Load configuration from a file."""
    try:
        return ServerConfig.from_file(config_file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[bold red]Error loading configuration:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

@app.command()
def start(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    log_level: str = typer.Option("info", "--log-level", "-l", 
                               help="Log level (debug, info, warning, error, critical)"),
    log_file: str = typer.Option(None, "--log-file", "-f", help="Log file path"),
    log_to_console: bool = typer.Option(True, "--log-to-console", "-c", 
                                      help="Whether to log to console"),
    cache_size: int = typer.Option(128, "--cache-size", help="Size of the result cache"),
    config_file: str = typer.Option(None, "--config", help="Path to configuration file (JSON or YAML)"),
    safe_roots: str = typer.Option(None, "--safe-roots", "-s", 
                                  help="Comma-separated list of safe root directories for file operations"),
):
    """
    Start the AST Grep MCP server.
    
    The server will listen for MCP requests and process ast-grep commands.
    """
    try:
        if config_file:
            # Load configuration from file
            config = load_config(config_file)
            
            # Override config with command line options if provided
            if host != "localhost":
                config.host = host
            if port != 8080:
                config.port = port
            if log_level != "info":
                config.log_level = validate_log_level(log_level)
            if log_file is not None:
                config.log_file = log_file
            if not log_to_console:
                config.log_to_console = False
            if cache_size != 128:
                config.cache_size = cache_size
            if safe_roots is not None:
                config.safe_roots = [root.strip() for root in safe_roots.split(",") if root.strip()]
        else:
            # Convert log_level string to integer
            log_level_int = validate_log_level(log_level)
            
            # Parse safe roots if provided
            safe_roots_list = []
            if safe_roots is not None:
                safe_roots_list = [root.strip() for root in safe_roots.split(",") if root.strip()]
            
            # Create a server configuration
            config = ServerConfig(
                host=host, 
                port=port,
                log_level=log_level_int,
                log_file=log_file,
                log_to_console=log_to_console,
                cache_size=cache_size,
                safe_roots=safe_roots_list
            )
        
        # Set up logging
        logger = config.setup_logging("ast_grep_mcp.main")
        logger.info(f"Starting AST Grep MCP server on {host}:{port}")
        logger.info(f"Cache size set to {config.cache_size}")
        
        # Create and start the server
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
    log_level: str = typer.Option("info", "--log-level", "-l", 
                               help="Log level (debug, info, warning, error, critical)"),
    log_file: str = typer.Option(None, "--log-file", "-f", help="Log file path"),
    log_to_console: bool = typer.Option(True, "--log-to-console", "-c", 
                                      help="Whether to log to console"),
    cache_size: int = typer.Option(128, "--cache-size", help="Size of the result cache"),
    config_file: str = typer.Option(None, "--config", help="Path to configuration file (JSON or YAML)"),
    safe_roots: str = typer.Option(None, "--safe-roots", "-s", 
                                  help="Comma-separated list of safe root directories for file operations"),
):
    """
    Start the AST Grep MCP server (alias for 'start').
    """
    return start(host, port, log_level, log_file, log_to_console, cache_size, config_file, safe_roots)

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
                    console.print("[bold yellow]No code loaded. Use 'code <file_path>' to load code.[/bold yellow]")
                    continue
                
                pattern = user_input[8:].strip()
                try:
                    result = analyzer.analyze_code(current_code, current_language, pattern)
                    if "error" in result:
                        console.print(f"[bold red]Error:[/bold red] {result['error']}")
                    else:
                        console.print(f"[bold green]Found {len(result['matches'])} matches[/bold green]")
                        for i, match in enumerate(result['matches']):
                            console.print(f"Match {i+1}:")
                            console.print(f"  Line: {match['range']['start']['line']} - {match['range']['end']['line']}")
                            console.print(f"  Text: {match['text']}")
                except Exception as e:
                    console.print(f"[bold red]Error analyzing code:[/bold red] {str(e)}")
                continue
            
            if user_input.lower().startswith("refactor "):
                if not current_code:
                    console.print("[bold yellow]No code loaded. Use 'code <file_path>' to load code.[/bold yellow]")
                    continue
                
                parts = user_input[9:].strip().split(" ", 1)
                if len(parts) != 2:
                    console.print("[bold yellow]Usage: refactor <pattern> <replacement>[/bold yellow]")
                    continue
                
                pattern, replacement = parts
                try:
                    result = analyzer.refactor_code(current_code, current_language, pattern, replacement)
                    if "error" in result:
                        console.print(f"[bold red]Error:[/bold red] {result['error']}")
                    else:
                        console.print(f"[bold green]Refactored {result['stats']['matches']} matches[/bold green]")
                        console.print("New code:")
                        console.print(result['refactored_code'][:200] + "..." if len(result['refactored_code']) > 200 else result['refactored_code'])
                except Exception as e:
                    console.print(f"[bold red]Error refactoring code:[/bold red] {str(e)}")
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
    output_dir: str = typer.Option(None, "--output-dir", "-o", help="Directory to output benchmark results"),
    num_files: int = typer.Option(200, "--num-files", "-n", help="Number of synthetic files to create"),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Number of iterations for each benchmark"),
    log_level: str = typer.Option("info", "--log-level", "-l", help="Log level for benchmark output"),
    save_json: bool = typer.Option(True, "--save-json", help="Save benchmark results as JSON"),
    batch_sizes: str = typer.Option("auto,5,10,20", "--batch-sizes", help="Comma-separated list of batch sizes to test (use 'auto' for automatic batch sizing)"),
    complexity: str = typer.Option("medium", "--complexity", help="Complexity of synthetic files (simple, medium, complex)"),
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
                    console.print(f"[yellow]Warning: Invalid batch size '{size}', skipping.[/yellow]")
        
        if not parsed_batch_sizes:
            parsed_batch_sizes = [None, 5, 10, 20]  # Default if none are valid
        
        # Show progress spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Running benchmarks with {num_files} files, {iterations} iterations...", 
                total=None
            )
            
            # Run benchmarks
            logger.info(f"Running benchmarks with {num_files} files, {iterations} iterations")
            logger.info(f"Testing batch sizes: {parsed_batch_sizes}")
            logger.info(f"Output directory: {output_dir}")
            
            result = run_benchmarks(
                output_dir=output_dir, 
                num_files=num_files,
                batch_sizes=parsed_batch_sizes
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
            table.add_row(pattern, stats['best_config'], speedup, improvement)
        
        console.print(table)
        
        # Display overall result
        if result["success"]:
            console.print("[bold green]✓ Target speedup achieved![/bold green]")
        else:
            console.print("[bold yellow]✗ Target speedup not achieved.[/bold yellow]")
        
        console.print(f"Best configuration: [bold green]{result['best_config']}[/bold green]")
        console.print(f"Average speedup: [bold]{result['best_avg_speedup']:.2f}x[/bold] ({result['best_avg_speedup_percentage']:.2f}%)")
        
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
            console.print("- Consider using sequential processing for your workload size")
            console.print("- The overhead of parallel processing exceeds benefits for small workloads")
        else:
            console.print(f"- Use batch size from best configuration ({result['best_config']})")
            console.print("- Adjust cache size based on your typical workload")
            
        # Add configuration example
        console.print("\n[bold blue]Example Configuration:[/bold blue]")
        console.print("""
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
        """)
        
        return 0 if result["success"] else 1
    
    except Exception as e:
        console.print(f"[bold red]Error running benchmarks:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
        raise typer.Exit(code=1)

def main():
    """Main entry point for the AST Grep MCP CLI."""
    try:
        app()
    except Exception as e:
        # Create a basic logger for errors
        logger = logging.getLogger("ast_grep_mcp.main")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
        
        logger.error(f"Error: {str(e)}")
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
