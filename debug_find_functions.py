#!/usr/bin/env python3
"""
Debug script to understand why find_functions() fails while search_summary works.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ast_grep_mcp.core.ast_grep_mcp_enhanced import create_enhanced_server

def debug_find_functions():
    """Debug the find_functions implementation step by step."""
    print("=== Debugging find_functions() failure ===\n")
    
    server = create_enhanced_server()
    
    # Test 1: Basic search_summary that works
    print("1. Testing search_summary (known to work)...")
    try:
        summary = server.search_summary(pattern="fn $NAME", directory="./src", language="rust")
        print(f"   ✓ search_summary found {summary.get('summary', {}).get('total_matches', 0)} matches")
        if summary.get('summary', {}).get('top_files'):
            print(f"   ✓ Top files: {[f['file'] for f in summary['summary']['top_files'][:3]]}")
    except Exception as e:
        print(f"   ✗ search_summary failed: {e}")
    
    # Test 2: find_functions that fails
    print("\n2. Testing find_functions...")
    try:
        functions = server.find_functions(directory="./src", language="rust", async_only=False)
        print(f"   → find_functions returned {functions['summary']['total']} functions")
        print(f"   → Summary: {functions['summary']}")
        if functions['functions']:
            print(f"   → Sample functions: {[f['name'] for f in functions['functions'][:3]]}")
        else:
            print("   ✗ No functions returned")
    except Exception as e:
        print(f"   ✗ find_functions failed with exception: {e}")
        traceback.print_exc()
    
    # Test 3: Let's debug the pattern building
    print("\n3. Debugging pattern building...")
    try:
        # Get the patterns that find_functions would use
        if hasattr(server, '_build_function_patterns'):
            patterns = server._build_function_patterns("rust", False, False, None)
            print(f"   → Patterns for Rust: {patterns}")
            
            # Test each pattern individually
            for lang, lang_patterns in patterns.items():
                for pattern in lang_patterns:
                    print(f"\n   Testing pattern: '{pattern}' for {lang}")
                    try:
                        summary = server.search_summary(
                            pattern=pattern,
                            directory="./src",
                            language=lang
                        )
                        matches = summary.get("summary", {}).get("total_matches", 0)
                        print(f"     → Pattern '{pattern}' found {matches} matches")
                        
                        if matches > 0:
                            # Test the detailed function extraction
                            top_files = summary.get("summary", {}).get("top_files", [])[:1]
                            for file_info in top_files:
                                print(f"     → Testing _get_function_details on {file_info['file']}")
                                if hasattr(server, '_get_function_details'):
                                    details = server._get_function_details(
                                        file_info["file"], pattern, lang, None
                                    )
                                    print(f"       → _get_function_details returned {len(details)} functions")
                                    if details:
                                        print(f"       → Sample: {details[0]}")
                                    else:
                                        print("       ✗ _get_function_details returned empty list")
                    except Exception as e:
                        print(f"     ✗ Pattern test failed: {e}")
        else:
            print("   ✗ _build_function_patterns method not found")
    except Exception as e:
        print(f"   ✗ Pattern debugging failed: {e}")
        traceback.print_exc()
    
    # Test 4: Direct analyzer test
    print("\n4. Testing analyzer directly...")
    try:
        if hasattr(server, 'analyzer'):
            # Try to read a file and analyze it directly
            test_file = Path("./src") / "ast_grep_mcp" / "core" / "ast_grep_mcp.py"
            if test_file.exists():
                with open(test_file, 'r') as f:
                    content = f.read()[:2000]  # First 2000 chars
                
                print(f"   → Testing analyzer on {test_file}")
                result = server.analyzer.analyze_code(content, "python", "def $NAME")
                print(f"   → Direct analyzer found {len(result.get('matches', []))} matches")
                
                if result.get('matches'):
                    print(f"   → Sample match: {result['matches'][0].get('text', '')[:100]}")
            else:
                print(f"   ✗ Test file {test_file} not found")
        else:
            print("   ✗ Analyzer not found on server")
    except Exception as e:
        print(f"   ✗ Direct analyzer test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_find_functions()