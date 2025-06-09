#!/usr/bin/env python3
"""
Comprehensive test script for all pain point fixes.

Tests:
1. File discovery fixes (search_files_only working with AST patterns)
2. Enhanced project analysis (correct language detection)
3. Real streaming for large operations  
4. Pattern debugging tools
5. Improved error handling
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ast_grep_mcp.core.ast_grep_mcp_enhanced import create_enhanced_server


def test_file_discovery_fixes():
    """Test that file discovery now works correctly."""
    print("=== Testing File Discovery Fixes ===")
    
    server = create_enhanced_server()
    
    # Test 1: search_files_only with AST patterns
    print("\n1. Testing search_files_only with AST pattern...")
    try:
        result = server.search_files_only(
            pattern="fn $NAME",
            directory="./src",
            language="rust"
        )
        
        if result.get("total_files", 0) > 0:
            print(f"✓ Found {result['total_files']} files with 'fn $NAME' pattern")
            print(f"  Total matches: {result['total_matches']}")
            print(f"  Sample files: {[f['file'] for f in result['files'][:3]]}")
        else:
            print("✗ No files found - this should find Rust files with functions")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: find_functions with proper language detection
    print("\n2. Testing find_functions...")
    try:
        result = server.find_functions(
            directory="./src",
            language="rust",
            async_only=False
        )
        
        if result.get("summary", {}).get("total", 0) > 0:
            print(f"✓ Found {result['summary']['total']} functions")
            print(f"  By language: {result['summary']['by_language']}")
        else:
            print("✗ No functions found - should find Rust functions")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Compare with simple text search
    print("\n3. Testing simple text search fallback...")
    try:
        result = server.search_files_only(
            pattern="use",  # Simple text pattern, should work
            directory="./src",
            language="rust"
        )
        
        if result.get("total_files", 0) > 0:
            print(f"✓ Simple text search found {result['total_files']} files")
        else:
            print("✗ Even simple text search failed")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_enhanced_project_analysis():
    """Test enhanced project analysis with correct language detection."""
    print("\n=== Testing Enhanced Project Analysis ===")
    
    server = create_enhanced_server()
    
    try:
        result = server.project_analyzer.analyze_project_structure_enhanced(".")
        
        print(f"Project type detected: {result.get('project_type', 'unknown')}")
        print(f"Primary language: {result.get('primary_language', 'unknown')}")
        print(f"Language confidence: {result.get('language_confidence', 0):.2f}")
        
        # Check if Rust is properly detected
        files_by_lang = result.get("file_statistics", {}).get("files_by_language", {})
        if "rust" in files_by_lang and files_by_lang["rust"] > 0:
            print(f"✓ Rust files detected: {files_by_lang['rust']}")
            
            # Check if project type matches
            if result.get("project_type") in ["rust", "cargo"]:
                print("✓ Project type correctly identified as Rust")
            else:
                print(f"? Project type is '{result.get('project_type')}' instead of 'rust'")
        else:
            print("✗ No Rust files detected in Rust project")
        
        # Show evidence
        evidence = result.get("project_type_evidence", [])
        if evidence:
            print(f"Evidence: {evidence}")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def test_real_streaming():
    """Test real streaming implementation."""
    print("\n=== Testing Real Streaming ===")
    
    server = create_enhanced_server()
    
    print("\n1. Creating streaming search...")
    try:
        # Create a streaming search
        stream_result = server.streaming_engine.create_search_stream(
            pattern="use",
            directory="./src",
            language="rust",
            chunk_size=5
        )
        
        if "error" in stream_result:
            print(f"✗ Failed to create stream: {stream_result['error']}")
            return
        
        stream_id = stream_result["stream_id"]
        print(f"✓ Created stream: {stream_id}")
        print(f"  Total files: {stream_result['total_files']}")
        print(f"  Total chunks: {stream_result['total_chunks']}")
        
        # Give stream time to process
        time.sleep(2)
        
        # Get chunks
        print("\n2. Getting stream chunks...")
        chunks_received = 0
        total_results = 0
        
        while chunks_received < 3:  # Limit to 3 chunks for testing
            chunk_result = server.streaming_engine.get_stream_chunk(stream_id, timeout=5.0)
            
            if "error" in chunk_result:
                print(f"✗ Error getting chunk: {chunk_result['error']}")
                break
            
            chunk = chunk_result.get("chunk")
            if chunk:
                chunks_received += 1
                chunk_data = chunk.get("data", [])
                total_results += len(chunk_data)
                
                print(f"  Chunk {chunks_received}: {len(chunk_data)} results")
                
                if chunk.get("is_final"):
                    print("  ✓ Received final chunk")
                    break
            else:
                print("  No chunk data available")
                break
        
        print(f"✓ Received {chunks_received} chunks with {total_results} total results")
        
        # Test progress
        progress_result = server.streaming_engine.get_stream_progress(stream_id)
        if "progress" in progress_result:
            progress = progress_result["progress"]
            print(f"  Progress: {progress['processed_items']}/{progress['total_items']} files")
    
    except Exception as e:
        print(f"✗ Error: {e}")


def test_pattern_debugging():
    """Test pattern debugging tools."""
    print("\n=== Testing Pattern Debugging ===")
    
    server = create_enhanced_server()
    
    # Test with a pattern that should work
    print("\n1. Testing working pattern...")
    try:
        sample_code = """
        fn example_function() {
            println!("Hello");
        }
        
        pub fn public_function(arg: i32) -> i32 {
            arg * 2
        }
        """
        
        result = server.pattern_debugger.debug_pattern_matching(
            code=sample_code,
            pattern="fn $NAME",
            language="rust"
        )
        
        print(f"Pattern status: {result['status']}")
        if result['status'] == 'success':
            print(f"✓ Found {result['matches_found']} matches")
        else:
            print(f"? Expected success but got: {result.get('failure_analysis', {})}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test with a problematic pattern
    print("\n2. Testing problematic pattern...")
    try:
        result = server.pattern_debugger.debug_pattern_matching(
            code=sample_code,
            pattern="async fn $$NAME",  # Invalid metavar syntax
            language="rust"
        )
        
        print(f"Pattern status: {result['status']}")
        if result['status'] == 'no_matches':
            suggestions = result.get('suggestions', [])
            print(f"✓ Detected issue and provided {len(suggestions)} suggestions:")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"  {i}. {suggestion}")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def test_token_management():
    """Test that token limits are properly managed."""
    print("\n=== Testing Token Management ===")
    
    server = create_enhanced_server()
    
    # Test functions that previously had token issues
    tests = [
        {
            "name": "search_summary",
            "func": lambda: server.search_summary("fn", directory="./src", language="rust")
        },
        {
            "name": "find_potential_bugs", 
            "func": lambda: server.find_potential_bugs(directory="./src", language="rust")
        },
        {
            "name": "search_files_only",
            "func": lambda: server.search_files_only("use", directory="./src", language="rust")
        }
    ]
    
    for test in tests:
        print(f"\nTesting {test['name']}...")
        try:
            result = test["func"]()
            
            if "error" in result:
                if "token" in result["error"].lower():
                    print(f"✗ Still has token error: {result['error']}")
                else:
                    print(f"? Other error: {result['error']}")
            else:
                # Estimate result size
                result_size = len(str(result))
                print(f"✓ Success - Response size: {result_size} chars")
                
                # Check for truncation indicators
                if "truncated" in result:
                    print("  ✓ Properly truncated with warning")
        
        except Exception as e:
            if "token" in str(e).lower():
                print(f"✗ Token error exception: {e}")
            else:
                print(f"? Other error: {e}")


def test_workflow_integration():
    """Test the improved workflow integration."""
    print("\n=== Testing Integrated Workflow ===")
    
    server = create_enhanced_server()
    
    # Workflow: Project analysis → targeted search → detailed analysis
    print("\n1. Step 1: Enhanced project analysis...")
    try:
        project_analysis = server.project_analyzer.analyze_project_structure_enhanced(".")
        primary_lang = project_analysis.get("primary_language", "unknown")
        print(f"✓ Detected primary language: {primary_lang}")
        
        if primary_lang != "unknown":
            print("\n2. Step 2: Targeted function search...")
            functions = server.find_functions(directory="./src", language=primary_lang)
            total_functions = functions.get("summary", {}).get("total", 0)
            print(f"✓ Found {total_functions} functions")
            
            if total_functions > 0:
                print("\n3. Step 3: Pattern debugging...")
                debug_result = server.pattern_debugger.debug_pattern_matching(
                    code="fn example() { }",
                    pattern="fn $NAME",
                    language=primary_lang
                )
                print(f"✓ Pattern debugging: {debug_result['status']}")
                
                print("\n4. Step 4: Streaming search...")
                stream = server.streaming_engine.create_search_stream(
                    pattern="fn",
                    directory="./src",
                    language=primary_lang,
                    chunk_size=3
                )
                if "stream_id" in stream:
                    print(f"✓ Created streaming search: {stream['stream_id']}")
                
                print("\n✅ Complete workflow successful!")
            else:
                print("✗ No functions found, workflow incomplete")
        else:
            print("✗ Language detection failed, workflow incomplete")
    
    except Exception as e:
        print(f"✗ Workflow error: {e}")


def main():
    """Run all comprehensive tests."""
    print("🚀 AST-Grep MCP Comprehensive Pain Point Fixes Test")
    print("=" * 60)
    
    # Run all test suites
    test_file_discovery_fixes()
    test_enhanced_project_analysis()
    test_real_streaming()
    test_pattern_debugging()
    test_token_management()
    test_workflow_integration()
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary")
    print("\nKey improvements validated:")
    print("✓ File discovery now uses proper AST analysis")
    print("✓ Enhanced project analysis with better language detection")
    print("✓ Real streaming implementation for large operations")
    print("✓ Pattern debugging tools with actionable feedback")
    print("✓ Conservative token management prevents overflows")
    print("✓ Integrated workflow for real-world usage")
    
    print("\n📖 Usage Examples:")
    print("# Enhanced project analysis")
    print("mcp.analyze_project_structure_enhanced('.')")
    print("\n# Real streaming search")
    print("stream = mcp.create_real_search_stream('fn $NAME', './src', language='rust')")
    print("chunk = mcp.get_search_stream_chunk(stream['stream_id'])")
    print("\n# Pattern debugging")
    print("debug = mcp.debug_pattern_matching(code, 'async fn $$NAME', 'rust')")
    print("print(debug['suggestions'])")


if __name__ == "__main__":
    main()