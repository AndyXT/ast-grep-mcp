#!/usr/bin/env python3
"""
Test script to validate the critical fixes for ast-grep MCP.

This script tests the specific issues identified:
1. _detect_language AttributeError
2. Token limit management  
3. Search returning 0 results
4. Language detection accuracy
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ast_grep_mcp.core.ast_grep_mcp_enhanced import create_enhanced_server


def test_detect_language_fix():
    """Test that _detect_language AttributeError is fixed."""
    print("Testing _detect_language fix...")
    
    server = create_enhanced_server()
    
    # These were failing with AttributeError before
    test_cases = [
        {
            "name": "search_files_only with language",
            "func": lambda: server.search_files_only(
                pattern="fn",
                directory="./src",
                language="rust"
            )
        },
        {
            "name": "find_functions with language", 
            "func": lambda: server.find_functions(
                directory="./src",
                language="rust"
            )
        },
        {
            "name": "find_imports with language",
            "func": lambda: server.find_imports(
                directory="./src", 
                language="rust"
            )
        }
    ]
    
    results = {}
    for test in test_cases:
        try:
            result = test["func"]()
            results[test["name"]] = {
                "status": "SUCCESS",
                "error": None,
                "has_results": bool(result and result.get("total_files", 0) > 0)
            }
            print(f"✓ {test['name']}: SUCCESS")
        except AttributeError as e:
            if "_detect_language" in str(e):
                results[test["name"]] = {
                    "status": "FAILED - AttributeError still present",
                    "error": str(e),
                    "has_results": False
                }
                print(f"✗ {test['name']}: FAILED - {str(e)}")
            else:
                results[test["name"]] = {
                    "status": "FAILED - Other AttributeError", 
                    "error": str(e),
                    "has_results": False
                }
                print(f"? {test['name']}: OTHER ERROR - {str(e)}")
        except Exception as e:
            results[test["name"]] = {
                "status": "FAILED - Other error",
                "error": str(e),
                "has_results": False
            }
            print(f"? {test['name']}: OTHER ERROR - {str(e)}")
    
    return results


def test_token_management():
    """Test that token limits are properly managed."""
    print("\nTesting token limit management...")
    
    server = create_enhanced_server()
    
    # Test functions that previously exceeded token limits
    test_cases = [
        {
            "name": "search_summary large directory",
            "func": lambda: server.search_summary(
                pattern="fn",
                directory="./src"
            )
        },
        {
            "name": "search_files_only large pattern",
            "func": lambda: server.search_files_only(
                pattern="use",
                directory="./src"  
            )
        },
        {
            "name": "find_potential_bugs",
            "func": lambda: server.find_potential_bugs(
                directory="./src",
                language="rust"
            )
        }
    ]
    
    results = {}
    for test in test_cases:
        try:
            result = test["func"]()
            # Check if results are truncated appropriately
            is_truncated = "truncated" in result or result.get("total_files", 0) <= 50
            results[test["name"]] = {
                "status": "SUCCESS",
                "error": None,
                "is_truncated": is_truncated,
                "result_size": len(str(result))
            }
            print(f"✓ {test['name']}: SUCCESS (size: {len(str(result))} chars)")
        except Exception as e:
            if "token" in str(e).lower() and "limit" in str(e).lower():
                results[test["name"]] = {
                    "status": "FAILED - Token limit still exceeded",
                    "error": str(e),
                    "is_truncated": False,
                    "result_size": 0
                }
                print(f"✗ {test['name']}: TOKEN LIMIT ERROR - {str(e)}")
            else:
                results[test["name"]] = {
                    "status": "FAILED - Other error",
                    "error": str(e),
                    "is_truncated": False,
                    "result_size": 0
                }
                print(f"? {test['name']}: OTHER ERROR - {str(e)}")
    
    return results


def test_search_accuracy():
    """Test that searches actually find results."""
    print("\nTesting search result accuracy...")
    
    server = create_enhanced_server()
    
    # Test with patterns that should definitely find results in this Rust project
    test_cases = [
        {
            "name": "search for 'use' statements",
            "pattern": "use",
            "should_find": True
        },
        {
            "name": "search for 'fn' functions", 
            "pattern": "fn",
            "should_find": True
        },
        {
            "name": "search for 'struct' definitions",
            "pattern": "struct", 
            "should_find": True
        },
        {
            "name": "search for non-existent pattern",
            "pattern": "XYZABC123_DEFINITELY_NOT_FOUND",
            "should_find": False
        }
    ]
    
    results = {}
    for test in test_cases:
        try:
            # Try multiple search methods
            summary = server.search_summary(
                pattern=test["pattern"],
                directory="./src",
                language="rust"
            )
            
            files_result = server.search_files_only(
                pattern=test["pattern"],
                directory="./src",
                language="rust"
            )
            
            summary_matches = summary.get("summary", {}).get("total_matches", 0)
            files_matches = files_result.get("total_matches", 0)
            
            found_results = summary_matches > 0 or files_matches > 0
            
            results[test["name"]] = {
                "status": "SUCCESS" if found_results == test["should_find"] else "FAILED",
                "expected": test["should_find"],
                "found": found_results,
                "summary_matches": summary_matches,
                "files_matches": files_matches
            }
            
            if found_results == test["should_find"]:
                print(f"✓ {test['name']}: SUCCESS (found: {found_results})")
            else:
                print(f"✗ {test['name']}: FAILED (expected: {test['should_find']}, found: {found_results})")
                
        except Exception as e:
            results[test["name"]] = {
                "status": "ERROR",
                "expected": test["should_find"],
                "found": False,
                "error": str(e),
                "summary_matches": 0,
                "files_matches": 0
            }
            print(f"? {test['name']}: ERROR - {str(e)}")
    
    return results


def test_language_detection():
    """Test language detection accuracy."""
    print("\nTesting language detection...")
    
    server = create_enhanced_server()
    
    # Test language detection methods
    test_files = [
        {"file": "src/main.rs", "expected": "rust"},
        {"file": "main.py", "expected": "python"},
        {"file": "example.js", "expected": "javascript"},
        {"file": "test.go", "expected": "go"}
    ]
    
    results = {}
    for test in test_files:
        try:
            detected = server._detect_language(test["file"])
            results[test["file"]] = {
                "status": "SUCCESS" if detected == test["expected"] else "FAILED",
                "expected": test["expected"],
                "detected": detected
            }
            
            if detected == test["expected"]:
                print(f"✓ {test['file']}: {detected}")
            else:
                print(f"✗ {test['file']}: expected {test['expected']}, got {detected}")
                
        except Exception as e:
            results[test["file"]] = {
                "status": "ERROR",
                "expected": test["expected"],
                "detected": None,
                "error": str(e)
            }
            print(f"? {test['file']}: ERROR - {str(e)}")
    
    return results


def main():
    """Run all tests and provide summary."""
    print("=== AST-Grep MCP Critical Fixes Validation ===\n")
    
    test_results = {}
    
    # Run all test suites
    test_results["detect_language"] = test_detect_language_fix()
    test_results["token_management"] = test_token_management()
    test_results["search_accuracy"] = test_search_accuracy()
    test_results["language_detection"] = test_language_detection()
    
    # Summarize results
    print("\n=== SUMMARY ===")
    
    total_tests = 0
    passed_tests = 0
    
    for suite_name, suite_results in test_results.items():
        suite_passed = sum(1 for r in suite_results.values() if r.get("status") == "SUCCESS")
        suite_total = len(suite_results)
        total_tests += suite_total
        passed_tests += suite_passed
        
        print(f"{suite_name}: {suite_passed}/{suite_total} tests passed")
        
        # Show failures
        failures = [name for name, result in suite_results.items() if result.get("status") != "SUCCESS"]
        if failures:
            print(f"  Failures: {', '.join(failures)}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All critical fixes validated successfully!")
        return True
    else:
        print("⚠️  Some issues remain - see failures above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)