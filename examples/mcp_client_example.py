#!/usr/bin/env python3
"""
Example MCP client demonstrating how to use the new AST-Grep MCP features.

This shows how a client would interact with the MCP server to:
1. Validate patterns with detailed diagnostics
2. Get automatic pattern correction suggestions
3. Stream search results for large directories
"""

import json
import time
from typing import Dict, Any


def send_mcp_request(tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a request to the MCP server.
    
    In a real implementation, this would use the MCP protocol.
    For demo purposes, we'll simulate the response.
    """
    print(f"\n[Client] Calling tool: {tool}")
    print(f"[Client] Arguments: {json.dumps(arguments, indent=2)}")
    
    # Simulate MCP response based on tool
    if tool == "validate_pattern":
        return {
            "is_valid": False,
            "errors": [
                {
                    "type": "missing_dollar",
                    "message": "Metavariable 'CONDITION' should be prefixed with $",
                    "position": 3,
                    "severity": "error",
                    "suggestion": "Change 'CONDITION' to '$CONDITION'"
                }
            ],
            "suggestions": [
                "if $CONDITION:",
                "if $COND:"
            ],
            "corrected_pattern": "if $CONDITION:",
            "confidence_score": 0.95,
            "language_examples": [
                "if x > 0:",
                "if condition:",
                "if True:"
            ]
        }
    
    elif tool == "suggest_pattern_corrections":
        return {
            "suggestions": [
                {
                    "original": arguments["pattern"],
                    "suggested": "def $NAME($$$PARAMS):",
                    "confidence": 0.9,
                    "reason": "Function parameters should use $$$ for variadic capture",
                    "applied_fixes": [
                        "Add $ to metavariable",
                        "Convert $$ to $$$ for variadic capture"
                    ]
                },
                {
                    "original": arguments["pattern"],
                    "suggested": "def $NAME($PARAM1, $PARAM2):",
                    "confidence": 0.7,
                    "reason": "Alternative with explicit parameters",
                    "applied_fixes": ["Add $ to metavariables"]
                }
            ],
            "pattern_type": "function_definition",
            "language": arguments["language"]
        }
    
    elif tool == "search_directory_stream":
        return {
            "stream_id": "search_12345",
            "estimated_files": 150,
            "batch_size": arguments.get("stream_config", {}).get("batch_size", 50),
            "message": "Search initiated. Results will be streamed.",
            "initial_results": [
                {
                    "file": "/project/src/utils.py",
                    "matches": [
                        {
                            "line_number": 10,
                            "matched_text": "def process_data(items):",
                            "metavariables": {
                                "$NAME": "process_data",
                                "$$$PARAMS": "items"
                            }
                        }
                    ],
                    "match_count": 1
                }
            ]
        }
    
    return {"error": "Unknown tool"}


def demo_pattern_validation():
    """Demonstrate pattern validation workflow."""
    print("\n" + "=" * 60)
    print("DEMO: Pattern Validation Workflow")
    print("=" * 60)
    
    # User tries to write a pattern
    pattern = "if CONDITION:"
    language = "python"
    
    print("\n[User] I want to match if statements in Python")
    print(f"[User] My pattern: {pattern}")
    
    # Client validates the pattern
    response = send_mcp_request("validate_pattern", {
        "pattern": pattern,
        "language": language,
        "code": "if x > 0:\n    print(x)"
    })
    
    print("\n[Server Response]")
    if not response["is_valid"]:
        print("❌ Pattern is invalid!")
        for error in response["errors"]:
            print(f"   - {error['type']}: {error['message']}")
            if error.get("suggestion"):
                print(f"     💡 {error['suggestion']}")
        
        if response.get("corrected_pattern"):
            print(f"\n✅ Suggested correction: {response['corrected_pattern']}")
            print(f"   Confidence: {response['confidence_score']:.0%}")
    
    # Show language examples
    if response.get("language_examples"):
        print(f"\n📚 Example matches in {language}:")
        for example in response["language_examples"]:
            print(f"   - {example}")


def demo_pattern_correction():
    """Demonstrate automatic pattern correction."""
    print("\n" + "=" * 60)
    print("DEMO: Automatic Pattern Correction")
    print("=" * 60)
    
    # User writes an incorrect pattern
    pattern = "def NAME(PARAMS):"
    language = "python"
    
    print("\n[User] I want to match Python function definitions")
    print(f"[User] My pattern: {pattern}")
    
    # Get correction suggestions
    response = send_mcp_request("suggest_pattern_corrections", {
        "pattern": pattern,
        "language": language
    })
    
    print("\n[Server Response]")
    print(f"Pattern type detected: {response.get('pattern_type', 'unknown')}")
    print("\n📝 Correction suggestions:")
    
    for i, suggestion in enumerate(response["suggestions"], 1):
        print(f"\n{i}. {suggestion['suggested']}")
        print(f"   Confidence: {suggestion['confidence']:.0%}")
        print(f"   Reason: {suggestion['reason']}")
        if suggestion["applied_fixes"]:
            print("   Fixes applied:")
            for fix in suggestion["applied_fixes"]:
                print(f"     - {fix}")


def demo_streaming_search():
    """Demonstrate streaming search for large codebases."""
    print("\n" + "=" * 60)
    print("DEMO: Streaming Search for Large Codebases")
    print("=" * 60)
    
    print("\n[User] Search for all error handling patterns in my large project")
    
    # Initiate streaming search
    response = send_mcp_request("search_directory_stream", {
        "directory": "/large/project",
        "pattern": "try:\n    $$$TRY_BODY\nexcept $EXCEPTION:\n    $$$EXCEPT_BODY",
        "language": "python",
        "stream_config": {
            "batch_size": 50,
            "include_progress": True
        }
    })
    
    print("\n[Server Response]")
    print(f"🔍 Stream ID: {response['stream_id']}")
    print(f"📊 Estimated files: {response['estimated_files']}")
    print(f"📦 Batch size: {response['batch_size']}")
    print(f"\n{response['message']}")
    
    # Show initial results
    if response.get("initial_results"):
        print("\n📄 Initial results:")
        for file_result in response["initial_results"]:
            print(f"\nFile: {file_result['file']}")
            print(f"Matches: {file_result['match_count']}")
            for match in file_result["matches"]:
                print(f"  Line {match['line_number']}: {match['matched_text']}")
                if match.get("metavariables"):
                    print(f"  Variables: {match['metavariables']}")
    
    # Simulate streaming updates
    print("\n[Streaming updates would appear here...]")
    for i in range(3):
        time.sleep(0.5)
        print(f"  📦 Batch {i+1}: Processed 50 files, found 12 matches")


def demo_advanced_workflow():
    """Demonstrate a complete workflow using multiple tools."""
    print("\n" + "=" * 60)
    print("DEMO: Advanced Workflow - Refactoring Deprecated API Usage")
    print("=" * 60)
    
    print("\n[Scenario] Developer wants to find and update deprecated API calls")
    
    # Step 1: User writes initial pattern
    print("\n1️⃣ Writing pattern for deprecated API...")
    pattern = "requests.get(URL)"  # Missing $ for metavariable
    
    # Step 2: Validate and correct pattern
    print(f"\n[User] Pattern: {pattern}")
    print("[Client] Validating pattern...")
    
    # Get correction
    corrected = "requests.get($URL)"
    print(f"[Server] Corrected pattern: {corrected}")
    
    # Step 3: Search for matches
    print("\n2️⃣ Searching codebase...")
    print(f"[Client] Using pattern: {corrected}")
    print("[Server] Found 47 matches across 23 files")
    
    # Step 4: Preview refactoring
    print("\n3️⃣ Preview refactoring...")
    print("[User] Replace with: httpx.get($URL)")
    print("\n[Server] Refactoring preview:")
    print("  - requests.get('https://api.example.com/data')")
    print("  + httpx.get('https://api.example.com/data')")
    print("\n  23 files would be modified")
    print("  47 replacements would be made")
    
    # Step 5: Apply refactoring
    print("\n4️⃣ Apply refactoring?")
    print("[User] Yes, apply changes")
    print("[Server] ✅ Successfully refactored 47 instances in 23 files")


def main():
    """Run all demos."""
    print("\nAST-Grep MCP Client Examples")
    print("Demonstrating new MCP features")
    
    # Run demos
    demo_pattern_validation()
    demo_pattern_correction()
    demo_streaming_search()
    demo_advanced_workflow()
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("\nThese examples show how clients can leverage the new MCP features:")
    print("- Pattern validation with helpful error messages")
    print("- Automatic pattern correction suggestions")
    print("- Streaming search for large codebases")
    print("- Complete refactoring workflows with preview")
    print("=" * 60)


if __name__ == "__main__":
    main()