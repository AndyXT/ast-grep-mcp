#!/usr/bin/env python3
"""Test different Rust function pattern syntaxes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ast_grep_mcp.ast_analyzer_v2 import AstAnalyzerV2
import logging

logging.basicConfig(level=logging.WARNING)

def test_patterns():
    analyzer = AstAnalyzerV2()
    
    # Test different function styles
    test_cases = [
        # (code, description)
        ("fn simple() {}", "no params, no return"),
        ("fn with_params(x: i32) {}", "one param"),
        ("fn multi_params(x: i32, y: String) {}", "multiple params"),
        ("fn with_return() -> i32 { 42 }", "with return type"),
        ("async fn async_simple() {}", "async no params"),
        ("async fn async_params(x: String) {}", "async with param"),
        ("pub async fn pub_async(port: String) -> Result<(), Error> {}", "full async function"),
    ]
    
    # Patterns to test
    patterns = [
        # Try different syntaxes
        "fn $NAME() { $$$BODY }",
        "fn $NAME($$$PARAMS) { $$$BODY }",
        "fn $NAME($$$) { $$$BODY }",
        "fn $NAME($$$) { $$$}",
        "async fn $NAME() { $$$BODY }",
        "async fn $NAME($$$PARAMS) { $$$BODY }",
        "async fn $NAME($$$) { $$$}",
        "pub async fn $NAME($$$) -> $$$RET { $$$}",
    ]
    
    print("Testing Rust Function Pattern Syntaxes")
    print("=" * 70)
    
    for code, desc in test_cases:
        print(f"\nCode: {code}")
        print(f"Description: {desc}")
        print("-" * 50)
        
        for pattern in patterns:
            try:
                matches = analyzer.find_patterns(code, "rust", pattern)
                if matches:
                    print(f"✓ Pattern '{pattern}' - MATCHED")
            except Exception:
                pass
    
    # Now test what ast-grep expects
    print("\n\nTesting exact match patterns:")
    print("=" * 70)
    
    code = "pub async fn connect(port: String) -> Result<(), Error> { Ok(()) }"
    exact_patterns = [
        # Try to find the exact syntax
        "pub async fn connect(port: String) -> Result<(), Error> { Ok(()) }",
        "pub async fn $NAME(port: String) -> Result<(), Error> { Ok(()) }",
        "pub async fn $NAME($PARAM: String) -> Result<(), Error> { Ok(()) }",
        "pub async fn $NAME($PARAM: $TYPE) -> Result<(), Error> { $EXPR }",
        "pub async fn $NAME($$$) -> $TYPE { $$$}",
        "pub async fn $NAME",  # Just the signature
    ]
    
    for pattern in exact_patterns:
        try:
            matches = analyzer.find_patterns(code, "rust", pattern)
            if matches:
                print(f"✓ Pattern worked: {pattern}")
                print(f"  Matched: {matches[0]['match'][:60]}...")
        except Exception:
            pass


if __name__ == "__main__":
    test_patterns()