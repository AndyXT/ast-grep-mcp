"""
Smoke tests for the ast-grep-mcp package.
"""
import subprocess
import sys
from pathlib import Path


def test_imports():
    """Test that the package is importable."""
    try:
        import src.ast_grep_mcp
        assert src.ast_grep_mcp is not None
    except ImportError:
        assert False, "Failed to import ast_grep_mcp module"


def test_cli_help():
    """Test that the CLI help command works."""
    main_file = Path(__file__).parent.parent / "main.py"
    result = subprocess.run(
        [sys.executable, str(main_file), "serve", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CLI help command failed with: {result.stderr}"
    assert "Start the AST Grep MCP server" in result.stdout 