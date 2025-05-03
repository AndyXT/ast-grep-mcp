from fastmcp import FastMCP
from .ast_analyzer import AstAnalyzer
from .language_handlers import get_handler
from pathlib import Path
from typing import Dict, Any

# Initialize the analyzer
analyzer = AstAnalyzer()

# Create an MCP server
mcp = FastMCP("AstGrepCodeAnalyzer")

@mcp.tool()
def analyze_code(code: str, language: str, pattern: str) -> Dict[str, Any]:
    """
    Analyze code using ast-grep pattern matching
    
    Args:
        code: Source code to analyze
        language: Programming language (python, javascript, lua, c, rust, go, etc.)
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
        language: Programming language (python, javascript, lua, c, rust, go, etc.)
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

@mcp.tool()
def get_language_patterns(language: str) -> Dict[str, Any]:
    """
    Get common pattern templates for a specific language
    
    Args:
        language: Programming language (python, javascript, etc.)
        
    Returns:
        Dictionary with pattern templates for the language
    """
    handler = get_handler(language)
    
    if not handler:
        return {
            "error": f"Language '{language}' is not supported or has no templates",
            "patterns": {}
        }
    
    patterns = handler.get_default_patterns()
    
    return {
        "language": language,
        "patterns": patterns
    }

@mcp.tool()
def get_supported_languages() -> Dict[str, Any]:
    """
    Get a list of supported languages and their file extensions
    
    Returns:
        Dictionary with supported languages and their file extensions
    """
    return {
        "languages": analyzer.get_supported_languages()
    }

def run_server(host: str = "localhost", port: int = 8080):
    """Run the MCP server"""
    if host != "localhost" or port != 8080:
        print("Note: FastMCP currently ignores host and port. Using default settings.")
    mcp.run()