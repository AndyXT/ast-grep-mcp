# Building an AST-Powered Code Surgery Tool

A Python MCP server using ast-grep enables powerful code analysis and transformation across multiple languages with minimal setup. This guide walks through creating a server that can search, analyze, and refactor codebases with precision.

## What you need to know first

ast-grep is a powerful AST-based code search and manipulation tool that works across multiple programming languages. When integrated with Python through the Model-Check-Path (MCP) server architecture, it lets AI assistants analyze code with structure awareness rather than just text. The core benefit? **Finding and transforming code based on its syntactic meaning**, not just string patterns.

Using Tree-sitter for parsing, ast-grep supports Python, Lua, C, Rust, Go, and many other languages. It lets you search for code patterns using intuitive syntax like `print($VAR)` to match any print statement regardless of what's being printed.

## Setting up your project

Start by creating a clean Python project structure:

```
mcp-ast-grep/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── ast_analyzer.py    # ast-grep integration layer
│   ├── cli.py             # CLI interface code
│   └── language_handlers/ # Language-specific modules
├── tests/                 # Test suite
├── pyproject.toml         # Project metadata and dependencies
└── README.md
```

Install the required dependencies:

```python
# pyproject.toml
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mcp-ast-grep"
version = "0.1.0"
description = "MCP server using ast-grep for code analysis and refactoring"
requires-python = ">=3.8"
dependencies = [
    "ast_grep_py>=0.37.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "fastmcp>=0.1.0"
]
```

## Integrating ast-grep with Python

The core of your implementation will use ast-grep's Python bindings (`ast_grep_py`):

```python
# src/ast_analyzer.py
from ast_grep_py import SgRoot
from typing import List, Dict, Any, Optional

class AstAnalyzer:
    """AST-based code analyzer using ast-grep"""
    
    def __init__(self):
        self.supported_languages = {
            "python": [".py"],
            "lua": [".lua"],
            "c": [".c", ".h"],
            "rust": [".rs"],
            "go": [".go"]
        }
    
    def parse_code(self, code: str, language: str) -> Optional[SgRoot]:
        """Parse code into an AST representation"""
        if language not in self.supported_languages:
            return None
        
        return SgRoot(code, language)
    
    def find_patterns(self, code: str, language: str, pattern: str) -> List[Dict[str, Any]]:
        """Find all occurrences of a pattern in the code"""
        root = self.parse_code(code, language)
        if not root:
            return []
        
        node = root.root()
        matches = node.find_all(pattern=pattern)
        
        results = []
        for match in matches:
            results.append({
                "text": match.text(),
                "location": {
                    "start": {
                        "line": match.range().start.line,
                        "column": match.range().start.column
                    },
                    "end": {
                        "line": match.range().end.line,
                        "column": match.range().end.column
                    }
                }
            })
        
        return results
    
    def apply_refactoring(self, code: str, language: str, pattern: str, replacement: str) -> str:
        """Apply a pattern-based refactoring to the code"""
        root = self.parse_code(code, language)
        if not root:
            return code
        
        node = root.root()
        matches = node.find_all(pattern=pattern)
        
        edits = []
        for match in matches:
            edit = match.replace(replacement)
            edits.append(edit)
        
        if not edits:
            return code
        
        return node.commit_edits(edits)
```

## Implementing the MCP server

Next, create the MCP server using FastMCP:

```python
# src/server.py
from fastmcp import FastMCP, Context
from .ast_analyzer import AstAnalyzer
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Initialize the analyzer
analyzer = AstAnalyzer()

# Create an MCP server
mcp = FastMCP("CodeAnalysisServer")

@mcp.tool()
def analyze_code(code: str, language: str, pattern: str) -> Dict[str, Any]:
    """
    Analyze code using ast-grep pattern matching
    
    Args:
        code: Source code to analyze
        language: Programming language (python, lua, c, rust, go)
        pattern: Pattern to search for in the code
        
    Returns:
        Dictionary with pattern matches and their locations
    """
    if language not in analyzer.supported_languages:
        return {"error": f"Language '{language}' is not supported", "matches": []}
    
    matches = analyzer.find_patterns(code, language, pattern)
    
    return {
        "matches": matches,
        "count": len(matches),
        "language": language
    }

@mcp.tool()
def refactor_code(code: str, language: str, pattern: str, replacement: str) -> Dict[str, Any]:
    """
    Refactor code by replacing pattern matches with a replacement
    
    Args:
        code: Source code to refactor
        language: Programming language (python, lua, c, rust, go)
        pattern: Pattern to search for in the code
        replacement: Replacement code
        
    Returns:
        Dictionary with refactored code and statistics
    """
    if language not in analyzer.supported_languages:
        return {"error": f"Language '{language}' is not supported", "success": False}
    
    original_code = code
    refactored_code = analyzer.apply_refactoring(code, language, pattern, replacement)
    
    # Count matches (by comparing refactored code with original)
    changes_made = original_code != refactored_code
    
    return {
        "original_code": original_code,
        "refactored_code": refactored_code,
        "success": changes_made,
        "language": language
    }

@mcp.tool()
def analyze_file(file_path: str, pattern: str) -> Dict[str, Any]:
    """
    Analyze a file using ast-grep pattern matching
    
    Args:
        file_path: Path to the file to analyze
        pattern: Pattern to search for in the file
        
    Returns:
        Dictionary with pattern matches and their locations
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return {"error": f"File '{file_path}' does not exist or is not a file", "matches": []}
    
    # Determine language from file extension
    extension = path.suffix.lower()
    language = None
    
    for lang, exts in analyzer.supported_languages.items():
        if extension in exts:
            language = lang
            break
    
    if not language:
        return {"error": f"Unsupported file type: {extension}", "matches": []}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        
        matches = analyzer.find_patterns(code, language, pattern)
        
        return {
            "file": str(path),
            "language": language,
            "matches": matches,
            "count": len(matches)
        }
    
    except Exception as e:
        return {"error": str(e), "matches": []}

if __name__ == "__main__":
    mcp.run()
```

## Building the CLI interface

Create a powerful CLI interface using Typer:

```python
# src/cli.py
import typer
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress
from rich.syntax import Syntax
import os
import json
import subprocess
from .ast_analyzer import AstAnalyzer

# Initialize the analyzer
analyzer = AstAnalyzer()

# Create Typer app with rich formatting
app = typer.Typer(
    name="mcp-ast-grep",
    help="Python MCP server with ast-grep for code analysis and refactoring",
    add_completion=True,
)

# Create console for rich output
console = Console()

# Create command groups
search_app = typer.Typer(help="Search for code patterns")
analyze_app = typer.Typer(help="Analyze code")
refactor_app = typer.Typer(help="Refactor code")
serve_app = typer.Typer(help="Start MCP server")

# Add command groups to main app
app.add_typer(search_app, name="search")
app.add_typer(analyze_app, name="analyze")
app.add_typer(refactor_app, name="refactor")
app.add_typer(serve_app, name="serve")

@search_app.command("pattern")
def search_pattern(
    pattern: str = typer.Argument(..., help="Pattern to search for"),
    paths: List[str] = typer.Argument(None, help="Paths to search in"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language to use"),
    output_format: str = typer.Option("text", "--format", "-f", help="Output format (text, json)"),
    context_lines: int = typer.Option(2, "--context", "-c", help="Number of context lines"),
):
    """
    Search for code patterns using ast-grep pattern syntax
    
    EXAMPLES:
        # Search for function calls in Python files
        mcp-ast-grep search pattern "print($A)" --language python
        
        # Search in specific directory with JSON output
        mcp-ast-grep search pattern "if ($COND)" src/ --format json
    """
    # Default to current directory if no paths provided
    if not paths:
        paths = ["."]
    
    results = []
    
    with Progress() as progress:
        task = progress.add_task("Searching...", total=len(paths))
        
        for path in paths:
            path_obj = Path(path)
            
            if path_obj.is_file():
                # Process single file
                extension = path_obj.suffix.lower()
                file_language = language
                
                # Try to detect language from extension if not specified
                if not file_language:
                    for lang, exts in analyzer.supported_languages.items():
                        if extension in exts:
                            file_language = lang
                            break
                
                if file_language:
                    with open(path_obj, "r", encoding="utf-8") as f:
                        code = f.read()
                    
                    matches = analyzer.find_patterns(code, file_language, pattern)
                    
                    if matches:
                        results.append({
                            "file": str(path_obj),
                            "language": file_language,
                            "matches": matches
                        })
            
            elif path_obj.is_dir():
                # Process directory recursively
                for lang, extensions in analyzer.supported_languages.items():
                    # Skip if language is specified and doesn't match
                    if language and language != lang:
                        continue
                    
                    for ext in extensions:
                        for file_path in path_obj.glob(f"**/*{ext}"):
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    code = f.read()
                                
                                matches = analyzer.find_patterns(code, lang, pattern)
                                
                                if matches:
                                    results.append({
                                        "file": str(file_path),
                                        "language": lang,
                                        "matches": matches
                                    })
                            except Exception as e:
                                console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")
            
            progress.update(task, advance=1)
    
    # Output results
    if output_format == "json":
        console.print_json(json.dumps(results))
    else:
        for result in results:
            console.print(f"[bold blue]{result['file']}[/bold blue] ([italic]{result['language']}[/italic]):")
            
            for match in result["matches"]:
                location = match["location"]
                start_line = location["start"]["line"]
                end_line = location["end"]["line"]
                
                console.print(f"  [bold green]Line {start_line+1}-{end_line+1}:[/bold green]")
                
                # Show code with syntax highlighting
                try:
                    with open(result["file"], "r", encoding="utf-8") as f:
                        code_lines = f.readlines()
                    
                    # Extract context lines
                    start_ctx = max(0, start_line - context_lines)
                    end_ctx = min(len(code_lines), end_line + context_lines + 1)
                    
                    context_code = "".join(code_lines[start_ctx:end_ctx])
                    
                    syntax = Syntax(
                        context_code, 
                        result["language"],
                        line_numbers=True,
                        start_line=start_ctx + 1,
                        highlight_lines=set(range(start_line + 1, end_line + 2))
                    )
                    console.print(syntax)
                except Exception as e:
                    console.print(f"    [red]Error displaying code: {str(e)}[/red]")
                    console.print(f"    {match['text']}")
            
            console.print()

@serve_app.command("start")
def start_server(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
):
    """
    Start the MCP server with ast-grep integration
    
    EXAMPLES:
        # Start server with default settings
        mcp-ast-grep serve start
        
        # Start on specific host and port
        mcp-ast-grep serve start --host 0.0.0.0 --port 9000
    """
    from .server import mcp
    
    console.print(f"[bold green]Starting MCP server on {host}:{port}[/bold green]")
    mcp.run(host=host, port=port)

def main():
    app()

if __name__ == "__main__":
    main()
```

## Supporting multiple languages

To handle multiple programming languages, implement language-specific handlers:

```python
# src/language_handlers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LanguageHandler(ABC):
    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name"""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """Return file extensions associated with this language"""
        pass
    
    @abstractmethod
    def get_default_patterns(self) -> Dict[str, str]:
        """Return dictionary of common patterns for this language"""
        pass

# src/language_handlers/python_handler.py
from .base import LanguageHandler
from typing import List, Dict

class PythonHandler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "python"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".py"]
    
    def get_default_patterns(self) -> Dict[str, str]:
        return {
            "function_definition": "def $NAME($$$PARAMS)",
            "class_definition": "class $NAME",
            "import_statement": "import $MODULE",
            "from_import": "from $MODULE import $NAME",
            "for_loop": "for $VAR in $ITER",
            "print_statement": "print($$$ARGS)"
        }

# Create similar handler classes for Lua, C, Rust, and Go
```

## Practical examples for pattern finding and refactoring

Here are examples demonstrating the MCP server capabilities:

### Python pattern finding example:

```python
from ast_grep_py import SgRoot

# Find deprecated API usage
code = """
import requests

def fetch_data(url):
    r = requests.get(url)
    return r.json()

def post_data(url, data):
    r = requests.post(url, json=data)
    return r.status_code
"""

root = SgRoot(code, "python")
node = root.root()

# Find all requests.get calls
get_calls = node.find_all(pattern="requests.get($URL)")
print(f"Found {len(get_calls)} requests.get calls")

# Find all calls with json parameter
json_calls = node.find_all(pattern="$OBJ.post($$$A, json=$DATA)")
print(f"Found {len(json_calls)} POST calls with json parameter")
```

### Rust code refactoring example:

```python
from ast_grep_py import SgRoot

# Update Rust 2018 code to 2021 edition
code = """
extern crate serde;
extern crate reqwest;

use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
struct User {
    name: String,
    email: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();
    let res = client.get("https://api.example.com/users").send()?;
    let users: Vec<User> = res.json()?;
    
    println!("Found {} users", users.len());
    Ok(())
}
"""

root = SgRoot(code, "rust")
node = root.root()

# Replace extern crate with use statements
extern_crate_nodes = node.find_all(pattern="extern crate $CRATE;")

edits = []
for extern_node in extern_crate_nodes:
    edits.append(extern_node.replace(""))

# Apply edits
refactored_code = node.commit_edits(edits)
print(refactored_code)
```

### Multi-language CLI example:

```python
# src/multi_lang.py
import typer
from rich.console import Console
from typing import Optional
import os
from pathlib import Path
from ast_grep_py import SgRoot

app = typer.Typer()
console = Console()

@app.command()
def convert_print_to_logs(
    path: str = typer.Argument(..., help="Path to directory to process"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show changes without applying"),
    log_level: str = typer.Option("info", "--level", help="Logging level to use"),
):
    """Convert print statements to logging calls across Python and Lua files"""
    
    # Pattern and replacement for Python
    py_pattern = "print($$$ARGS)"
    py_replacement = f"logging.{log_level}($$$ARGS)"
    
    # Pattern and replacement for Lua
    lua_pattern = "print($$$ARGS)"
    lua_replacement = f"log.{log_level}($$$ARGS)"
    
    path_obj = Path(path)
    
    if not path_obj.exists():
        console.print(f"[bold red]Path does not exist: {path}[/bold red]")
        return
    
    changes = {
        "python": [],
        "lua": []
    }
    
    # Process Python files
    for file_path in path_obj.glob("**/*.py"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            root = SgRoot(code, "python")
            node = root.root()
            
            matches = node.find_all(pattern=py_pattern)
            
            if matches:
                if dry_run:
                    changes["python"].append((str(file_path), len(matches)))
                else:
                    edits = [match.replace(py_replacement) for match in matches]
                    new_code = node.commit_edits(edits)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    
                    changes["python"].append((str(file_path), len(matches)))
        except Exception as e:
            console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")
    
    # Process Lua files
    for file_path in path_obj.glob("**/*.lua"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            root = SgRoot(code, "lua")
            node = root.root()
            
            matches = node.find_all(pattern=lua_pattern)
            
            if matches:
                if dry_run:
                    changes["lua"].append((str(file_path), len(matches)))
                else:
                    edits = [match.replace(lua_replacement) for match in matches]
                    new_code = node.commit_edits(edits)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    
                    changes["lua"].append((str(file_path), len(matches)))
        except Exception as e:
            console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")
    
    # Report changes
    if dry_run:
        console.print("[bold yellow]Dry run - no changes made[/bold yellow]")
    
    py_count = sum(count for _, count in changes["python"])
    lua_count = sum(count for _, count in changes["lua"])
    
    console.print(f"[bold green]Python files: {len(changes['python'])} files with {py_count} print statements[/bold green]")
    console.print(f"[bold green]Lua files: {len(changes['lua'])} files with {lua_count} print statements[/bold green]")
    
    if dry_run:
        console.print("[bold]Run without --dry-run to apply changes[/bold]")
```

## Complete MCP server configuration

Configure the MCP server in a user's environment:

```json
{
  "mcpServers": {
    "ast-grep": {
      "command": "python",
      "args": ["-m", "mcp_ast_grep.server"],
      "env": {}
    }
  }
}
```

## Implementation strategies and best practices

1. **Performance optimization**: Implement caching for parsed ASTs to avoid reanalyzing the same file multiple times.

2. **Error handling**: Always provide detailed error messages and graceful fallbacks.

```python
try:
    root = SgRoot(code, language)
    # Processing code
except Exception as e:
    # Log detailed error
    logging.error(f"Failed to parse {language} code: {str(e)}")
    # Provide fallback
    return {"error": f"Failed to parse code: {str(e)}", "success": False}
```

3. **Pattern library**: Create a repository of common patterns for each language.

```python
COMMON_PATTERNS = {
    "python": {
        "function_def": "def $NAME($$$PARAMS)",
        "class_def": "class $NAME",
        "import_stmt": "import $MODULE"
    },
    "rust": {
        "function_def": "fn $NAME($$$PARAMS)",
        "struct_def": "struct $NAME",
        "impl_block": "impl $NAME"
    }
}
```

4. **Language detection**: Implement robust language detection based on file extensions.

```python
def detect_language(file_path):
    extension = Path(file_path).suffix.lower()
    extension_map = {
        ".py": "python",
        ".lua": "lua",
        ".c": "c",
        ".h": "c",
        ".rs": "rust", 
        ".go": "go"
    }
    return extension_map.get(extension)
```

## Conclusion

By integrating ast-grep with Python through an MCP server, you've created a powerful tool that can search and refactor code across multiple programming languages with structural awareness. The CLI interface makes it accessible for daily development tasks while the MCP server enables AI assistants to leverage its capabilities.

This approach lets you perform sophisticated code analysis and transformations that would be error-prone or impossible with regex-based tools, while maintaining the ease of use that developers expect from modern development tools.