import typer
from rich.console import Console
from src.ast_grep_mcp.core import AstGrepMCP, ServerConfig
from src.ast_grep_mcp.core.config import LOG_LEVELS
import sys
import logging

console = Console()
app = typer.Typer(help="AST Grep MCP server CLI")

def validate_log_level(log_level: str) -> int:
    """Validate and convert the log level string to an integer."""
    if log_level.lower() in LOG_LEVELS:
        return LOG_LEVELS[log_level.lower()]
    else:
        log_level_options = ", ".join(LOG_LEVELS.keys())
        raise typer.BadParameter(f"Invalid log level: {log_level}. Valid options are: {log_level_options}")

@app.command()
def start(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    log_level: str = typer.Option("info", "--log-level", "-l", 
                               help="Log level (debug, info, warning, error, critical)"),
    log_file: str = typer.Option(None, "--log-file", "-f", help="Log file path"),
    log_to_console: bool = typer.Option(True, "--log-to-console", "-c", 
                                      help="Whether to log to console"),
):
    """
    Start the AST Grep MCP server.
    
    The server will listen for MCP requests and process ast-grep commands.
    """
    try:
        # Convert log_level string to integer
        log_level_int = validate_log_level(log_level)
        
        # Create a server configuration
        config = ServerConfig(
            host=host, 
            port=port,
            log_level=log_level_int,
            log_file=log_file,
            log_to_console=log_to_console
        )
        
        # Set up logging
        logger = config.setup_logging("ast_grep_mcp.main")
        logger.info(f"Starting AST Grep MCP server on {host}:{port}")
        
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
):
    """
    Start the AST Grep MCP server (alias for 'start').
    """
    return start(host, port, log_level, log_file, log_to_console)

@app.command()
def version():
    """
    Show the current version of the AST Grep MCP server.
    """
    console.print("[bold green]AST Grep MCP Server v0.1.0[/bold green]")

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
