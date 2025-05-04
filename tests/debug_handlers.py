"""
Debug script to diagnose language handler registration issues.
"""

from ast_grep_mcp.core import AstGrepMCP
from ast_grep_mcp.language_handlers import get_handler, get_all_handlers

def debug_handlers():
    print("Debugging language handler registration...")
    
    # Print all registered handlers
    handlers = get_all_handlers()
    print(f"\nDirectly from get_all_handlers(): {len(handlers)} handlers registered")
    for name, handler in handlers.items():
        print(f"  - {name}: {handler.__class__.__name__}")
    
    # Create AstGrepMCP instance
    mcp = AstGrepMCP()
    
    # Try to get JavaScript handler
    js_result = mcp.get_language_patterns("javascript")
    print("\nResult from mcp.get_language_patterns('javascript'):")
    print(f"  - 'error' in result: {'error' in js_result}")
    if 'error' in js_result:
        print(f"  - Error message: {js_result['error']}")
    
    # Get supported languages
    langs = mcp.get_supported_languages()
    print("\nSupported languages from mcp.get_supported_languages():")
    for lang, exts in langs['languages'].items():
        print(f"  - {lang}: {exts}")
    
    # Try direct handler lookup
    js_handler = get_handler("javascript")
    print("\nDirect handler lookup:")
    print(f"  - get_handler('javascript'): {js_handler}")
    if js_handler:
        print(f"  - Class: {js_handler.__class__.__name__}")
        patterns = js_handler.get_default_patterns()
        print(f"  - Number of patterns: {len(patterns)}")
    else:
        print("  - No JavaScript handler found!")

if __name__ == "__main__":
    debug_handlers() 