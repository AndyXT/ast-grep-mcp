#!/usr/bin/env python3
"""
Demonstration of new AST-Grep MCP features.

This script shows how to use the enhanced pattern validation,
automatic correction suggestions, and streaming capabilities.
"""

import json
import asyncio
from pathlib import Path
import sys

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ast_grep_mcp.core.ast_grep_mcp import AstGrepMCP
from ast_grep_mcp.utils.pattern_diagnostics import PatternAnalyzer
from ast_grep_mcp.utils.pattern_autocorrect import PatternAutoCorrector


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}\n")


def demo_pattern_validation():
    """Demonstrate pattern validation with diagnostics."""
    print_section("Pattern Validation Demo")
    
    analyzer = PatternAnalyzer()
    
    # Test various patterns
    patterns = [
        ("if CONDITION:", "python"),
        ("def NAME(PARAMS):", "python"),
        ("$$PARAMS", "python"),
        ("function $NAME($$ARGS) {", "javascript"),
        ("match $EXPR { $$$ARMS", "rust"),
    ]
    
    for pattern, language in patterns:
        print(f"Pattern: {pattern}")
        print(f"Language: {language}")
        
        result = analyzer.analyze_pattern(pattern, language)
        
        print(f"Valid: {result.is_valid}")
        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error.type}: {error.message} at position {error.position}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")
        
        if result.suggestions:
            print("Suggestions:")
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
        
        if result.corrected_pattern and result.corrected_pattern != pattern:
            print(f"Corrected: {result.corrected_pattern}")
            print(f"Confidence: {result.confidence_score:.2f}")
        
        print()


def demo_pattern_autocorrect():
    """Demonstrate automatic pattern correction."""
    print_section("Pattern Auto-Correction Demo")
    
    corrector = PatternAutoCorrector()
    
    # Test patterns that need correction
    patterns = [
        ("def NAME(PARAMS):", "python"),
        ("$$PARAMS", "python"),
        ("if CONDITION", "python"),
        ("function $NAME($$ARGS)", "javascript"),
        ("$ VAR = $VALUE", "python"),
        ("fucntion $NAME() { }", "javascript"),
    ]
    
    for pattern, language in patterns:
        print(f"Original: {pattern}")
        
        suggestions = corrector.suggest_corrections(pattern, language)
        
        if suggestions:
            print("Suggestions:")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"  {i}. {suggestion.suggested}")
                print(f"     Confidence: {suggestion.confidence:.0%}")
                print(f"     Reason: {suggestion.reason}")
                if suggestion.applied_fixes:
                    print(f"     Fixes: {', '.join(suggestion.applied_fixes)}")
        
        # Try auto-correction
        corrected = corrector.auto_correct_pattern(pattern, language)
        if corrected and corrected != pattern:
            print(f"Auto-corrected: {corrected}")
        
        print()


async def demo_streaming_search():
    """Demonstrate streaming search for large directories."""
    print_section("Streaming Search Demo")
    
    # Initialize MCP server
    mcp = AstGrepMCP()
    
    # Create a sample directory structure for demo
    demo_dir = Path("demo_files")
    demo_dir.mkdir(exist_ok=True)
    
    # Create sample Python files
    for i in range(5):
        file_path = demo_dir / f"module_{i}.py"
        content = f"""
def function_{i}(param1, param2):
    result = param1 + param2
    print(f"Result: {{result}}")
    return result

class TestClass_{i}:
    def __init__(self):
        self.value = {i}
    
    def method(self):
        print(f"Value: {{self.value}}")
"""
        file_path.write_text(content)
    
    print(f"Created demo files in {demo_dir}")
    
    # Stream search for function definitions
    pattern = "def $NAME($$$PARAMS):"
    print(f"\nStreaming search for pattern: {pattern}")
    
    try:
        # Use the streaming search
        result = await mcp.search_directory_stream(
            directory=str(demo_dir),
            pattern=pattern,
            language="python",
            stream_config={
                "batch_size": 2,
                "include_progress": True
            }
        )
        
        # Process streaming results
        if "stream_id" in result:
            print(f"Stream ID: {result['stream_id']}")
            print("Results will be streamed...")
        elif "results" in result:
            print(f"Found {len(result['results'])} matches")
            for file_result in result['results']:
                print(f"\nFile: {file_result['file']}")
                print(f"Matches: {file_result['match_count']}")
                for match in file_result['matches'][:2]:
                    print(f"  - Line {match['line_number']}: {match['matched_text'].strip()}")
    
    except Exception as e:
        print(f"Error during streaming search: {e}")
    
    finally:
        # Clean up demo files
        import shutil
        if demo_dir.exists():
            shutil.rmtree(demo_dir)
            print(f"\nCleaned up {demo_dir}")


def demo_mcp_tools():
    """Demonstrate using the MCP tools directly."""
    print_section("MCP Tools Demo")
    
    mcp = AstGrepMCP()
    
    # 1. Validate Pattern Tool
    print("1. validate_pattern tool:")
    result = mcp.validate_pattern(
        pattern="if CONDITION:",
        language="python",
        code="if x > 0:\n    print(x)"
    )
    print(json.dumps(result, indent=2))
    
    # 2. Suggest Pattern Corrections Tool
    print("\n2. suggest_pattern_corrections tool:")
    result = mcp.suggest_pattern_corrections(
        pattern="def NAME(PARAMS):",
        language="python"
    )
    print(json.dumps(result, indent=2))
    
    # 3. Preview Refactoring Tool
    print("\n3. preview_refactoring tool:")
    code = """
def old_function(x, y):
    return x + y

result = old_function(1, 2)
"""
    result = mcp.preview_refactoring(
        code=code,
        language="python",
        pattern="def old_function($$$PARAMS):\n    return $$$BODY",
        replacement="def new_function($$$PARAMS):\n    return $$$BODY"
    )
    print(json.dumps(result, indent=2))


def main():
    """Run all demos."""
    print("AST-Grep MCP New Features Demo")
    print("=" * 60)
    
    # Run synchronous demos
    demo_pattern_validation()
    demo_pattern_autocorrect()
    demo_mcp_tools()
    
    # Run async demo
    print("\nRunning async streaming demo...")
    asyncio.run(demo_streaming_search())
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()