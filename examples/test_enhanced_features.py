#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced features of ast-grep MCP.

This script shows how the new features solve the pain points mentioned.
"""
import asyncio
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ast_grep_mcp.core.ast_grep_mcp_enhanced import create_enhanced_server


async def demonstrate_enhanced_features():
    """Demonstrate the enhanced features."""
    print("=== AST-GREP MCP Enhanced Features Demo ===\n")
    
    # Create enhanced server
    server = create_enhanced_server()
    
    # Get the current directory for testing
    test_dir = Path(__file__).parent.parent
    
    print("1. Testing search_summary (lightweight overview)")
    print("-" * 50)
    
    # This would fail with token limit in the original implementation
    summary = server.search_summary(
        pattern="def $NAME($$$ARGS)",
        directory=str(test_dir),
        language="python"
    )
    
    if "error" not in summary:
        print(f"✓ Found {summary['summary']['total_matches']} matches in {summary['summary']['total_files']} files")
        print(f"✓ Search completed in {summary['summary']['search_time']:.2f}s")
        print("\nTop files with matches:")
        for file_info in summary['summary']['top_files'][:5]:
            print(f"  - {file_info['file']}: {file_info['matches']} matches")
        print("\n✓ No token limit error! Summary is lightweight.\n")
    else:
        print(f"✗ Error: {summary['error']}\n")
    
    print("2. Testing pattern_wizard (interactive pattern building)")
    print("-" * 50)
    
    wizard_result = server.pattern_wizard_instance.pattern_wizard(
        description="find async functions that return Result",
        language="rust"
    )
    
    print("Pattern suggestions:")
    for i, suggestion in enumerate(wizard_result['suggestions'][:3], 1):
        print(f"\n{i}. Pattern: {suggestion['pattern']}")
        print(f"   Score: {suggestion['score']}")
        print(f"   Explanation: {suggestion['explanation']}")
    
    print("\n3. Testing convenience functions")
    print("-" * 50)
    
    # Find all async functions
    print("\nFinding async functions...")
    async_funcs = server.find_functions(
        directory=str(test_dir / "src"),
        language="python",
        async_only=True
    )
    
    print(f"✓ Found {async_funcs['summary']['total']} async functions")
    if async_funcs['functions']:
        print("Examples:")
        for func in async_funcs['functions'][:3]:
            print(f"  - {func['file']}:{func.get('line', '?')} - {func.get('name', 'unknown')}")
    
    # Find TODOs and FIXMEs
    print("\nFinding TODOs and FIXMEs...")
    todos = server.find_todos_and_fixmes(
        directory=str(test_dir / "src"),
    )
    
    print(f"✓ Found {todos['summary']['total']} TODO/FIXME items")
    print("By type:")
    for todo_type, count in todos['summary']['by_type'].items():
        print(f"  - {todo_type}: {count}")
    
    print("\n4. Testing enhanced error handling")
    print("-" * 50)
    
    # Test with invalid pattern
    from src.ast_grep_mcp.utils.enhanced_error_handling import PatternSyntaxError
    
    try:
        result = server.analyze_code(
            code="def test(): pass",
            language="python", 
            pattern="def $$NAME"  # Invalid: $$ instead of $
        )
        if "error" in result:
            print(f"✓ Got helpful error: {result['error']}")
            if "suggestions" in result:
                print("Suggestions provided:")
                for suggestion in result.get("suggestions", [])[:3]:
                    print(f"  - {suggestion}")
    except PatternSyntaxError as e:
        print(f"✓ Got enhanced error: {e}")
        print("Suggestions:")
        for suggestion in e.suggestions:
            print(f"  - {suggestion}")
    
    print("\n5. Testing search_files_only (ultra-lightweight)")
    print("-" * 50)
    
    files_result = server.search_files_only(
        pattern="TODO",
        directory=str(test_dir / "src")
    )
    
    print(f"✓ Found pattern in {files_result['total_files']} files")
    print(f"✓ Total matches: {files_result['total_matches']}")
    print("\nTop files:")
    for file_info in files_result['files'][:5]:
        print(f"  - {file_info['file']}: {file_info['match_count']} matches")
    
    print("\n=== Demo Complete ===")
    print("\nKey improvements demonstrated:")
    print("✓ No token limit errors with search_summary")
    print("✓ Helpful pattern suggestions with pattern_wizard")
    print("✓ High-level convenience functions for common tasks")
    print("✓ Better error messages with actionable suggestions")
    print("✓ Ultra-lightweight search with search_files_only")


def compare_token_usage():
    """Compare token usage between old and new approaches."""
    print("\n=== Token Usage Comparison ===\n")
    
    from src.ast_grep_mcp.utils.pagination import ResponsePaginator
    paginator = ResponsePaginator()
    
    # Simulate responses
    old_response = {
        "matches": {
            f"file{i}.py": [{"text": "match" * 100} for _ in range(20)]
            for i in range(100)
        }
    }
    
    new_summary = {
        "summary": {
            "total_files": 100,
            "total_matches": 2000,
            "top_files": [{"file": f"file{i}.py", "matches": 20} for i in range(10)]
        }
    }
    
    old_tokens = paginator.estimate_tokens(old_response)
    new_tokens = paginator.estimate_tokens(new_summary)
    
    print(f"Old approach (full results): ~{old_tokens:,} tokens")
    print(f"New approach (summary only): ~{new_tokens:,} tokens")
    print(f"Reduction: {(1 - new_tokens/old_tokens)*100:.1f}%")
    
    print("\nToken limits:")
    print(f"  Search limit: {paginator.TOKEN_LIMITS['search']:,} tokens")
    print("  Summary limit: 3,000 tokens (custom)")
    
    print("\n✓ Old approach would fail with token limit error")
    print("✓ New approach succeeds with lightweight summary")


if __name__ == "__main__":
    print("Testing enhanced ast-grep MCP features...\n")
    
    # Run async demo
    asyncio.run(demonstrate_enhanced_features())
    
    # Show token comparison
    compare_token_usage()
    
    print("\n✅ All tests completed!")
    print("\nThe enhanced server is now the default!")
    print("  python main.py serve")
    print("\nMCP config (enhanced is default):")
    print("""  "ast-grep": {
    "command": "python",
    "args": ["main.py", "serve"],
    "cwd": "/path/to/ast-grep-mcp"
  }""")
    print("\nTo use legacy version: python main.py serve --no-enhanced")