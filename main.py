import typer
from rich.console import Console
from src.ast_grep_mcp.server import run_server
import sys

console = Console()
app = typer.Typer()

@app.command()
def serve(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
):
    """
    Start the AST Grep MCP server
    
    Examples:
        # Start server with default settings
        python main.py serve
        
        # Start on specific host and port
        python main.py serve --host 0.0.0.0 --port 9000
    """
    console.print(f"[bold green]Starting AST Grep MCP server on {host}:{port}[/bold green]")
    run_server(host=host, port=port)

def main():
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
