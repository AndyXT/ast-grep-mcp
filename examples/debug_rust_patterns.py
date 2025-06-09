#!/usr/bin/env python3
"""
Debug script to test Rust pattern matching with ast-grep MCP.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ast_grep_mcp.ast_analyzer_v2 import AstAnalyzerV2
from ast_grep_mcp.language_handlers.rust_handler import RustHandler

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

def test_rust_patterns():
    """Test various Rust patterns."""
    analyzer = AstAnalyzerV2()
    handler = RustHandler()
    
    # Test code
    rust_code = '''
pub async fn connect_to_barcode_scanner(port: String) -> Result<(), Error> {
    println!("Connecting to port: {}", port);
    Ok(())
}

async fn process_barcode(code: String) {
    let result = decode_barcode(code).unwrap();
    println!("Barcode: {}", result);
}

fn sync_function(x: i32) -> i32 {
    x * 2
}
'''
    
    print("Testing Rust Pattern Matching")
    print("=" * 50)
    print("Test Code:")
    print(rust_code)
    print("=" * 50)
    
    # Test various patterns
    test_patterns = [
        # Basic patterns
        ("async fn $NAME($$$PARAMS) { $$$BODY }", "async function"),
        ("pub async fn $NAME($$$PARAMS) { $$$BODY }", "public async function"),
        ("fn $NAME($$$PARAMS) { $$$BODY }", "any function"),
        ("$EXPR.unwrap()", "unwrap calls"),
        ("println!($$$ARGS)", "println macro"),
        
        # From handler defaults
        ("async_function", handler.get_default_patterns().get("async_function", "N/A")),
        ("pub_async_function", handler.get_default_patterns().get("pub_async_function", "N/A")),
        
        # Common mistakes (should fail but be normalized)
        ("async fn $NAME($$PARAMS) { $$BODY }", "double $$ (should be normalized)"),
    ]
    
    for name, pattern in test_patterns:
        if pattern == "N/A":
            continue
            
        print(f"\nTesting pattern '{name}': {pattern}")
        print("-" * 40)
        
        try:
            # Use the analyzer directly
            matches = analyzer.find_patterns(rust_code, "rust", pattern)
            
            print(f"Found {len(matches)} matches")
            for i, match in enumerate(matches):
                print(f"\nMatch {i + 1}:")
                print(f"  Text: {match['match'][:50]}...")
                print(f"  Location: Line {match['location']['start']['line']}")
                if match.get('metavariables'):
                    print(f"  Metavariables: {match['metavariables']}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Test the language handler patterns
    print("\n\nLanguage Handler Default Patterns:")
    print("=" * 50)
    patterns = handler.get_default_patterns()
    for key, pattern in patterns.items():
        if "async" in key or "function" in key:
            print(f"{key}: {pattern}")


def test_simple_matching():
    """Test with very simple code and patterns."""
    print("\n\nSimple Pattern Test")
    print("=" * 50)
    
    analyzer = AstAnalyzerV2()
    
    simple_code = "async fn test() {}"
    simple_patterns = [
        "async fn test() {}",  # Exact match
        "async fn $NAME() {}",  # With metavar
        "async fn $NAME($$$PARAMS) { $$$BODY }",  # Full pattern
    ]
    
    for pattern in simple_patterns:
        print(f"\nPattern: {pattern}")
        try:
            matches = analyzer.find_patterns(simple_code, "rust", pattern)
            print(f"Result: {len(matches)} matches")
            if matches:
                print(f"Match: {matches[0]['match']}")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    test_rust_patterns()
    test_simple_matching()