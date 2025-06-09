#!/usr/bin/env python3
"""
Demo: How to correctly search for async functions in Rust using ast-grep MCP.

This demonstrates the RIGHT way to use patterns for Rust code.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demo_rust_async_search():
    """Show the correct way to search for async functions in Rust."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ast_grep_mcp"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("=== Searching for Async Functions in Rust ===\n")
            
            # The CORRECT patterns for Rust
            correct_patterns = [
                ("async fn $NAME", "Find all async functions"),
                ("pub async fn $NAME", "Find public async functions"),
                ("async fn connect", "Find specific async function"),
                ("$EXPR.await", "Find await expressions"),
                ("tokio::spawn", "Find tokio spawn calls"),
            ]
            
            project_dir = "."  # Your Rust project directory
            
            for pattern, description in correct_patterns:
                print(f"\n{description}")
                print(f"Pattern: {pattern}")
                print("-" * 50)
                
                result = await session.call_tool(
                    "search_directory",
                    arguments={
                        "directory": project_dir,
                        "pattern": pattern,
                        "file_extensions": [".rs"]
                    }
                )
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                elif result.get("matches"):
                    count = sum(len(matches) for matches in result["matches"].values())
                    print(f"Found {count} matches in {len(result['matches'])} files")
                    
                    # Show first few matches
                    shown = 0
                    for file, matches in result["matches"].items():
                        for match in matches[:2]:  # Show max 2 per file
                            print(f"\n  File: {file}")
                            print(f"  Line {match['location']['start']['line']}: {match['match'][:60]}...")
                            shown += 1
                            if shown >= 5:
                                break
                        if shown >= 5:
                            break
                else:
                    print("No matches found")
                    if "debug_info" in result:
                        print(f"Debug: {result['debug_info']}")
            
            # Show what DOESN'T work
            print("\n\n=== Common Mistakes (These Won't Work) ===\n")
            
            wrong_patterns = [
                "async fn $NAME($$$PARAMS) { $$$BODY }",  # $$$ doesn't work for params
                "pub async fn $NAME($$PARAMS)",           # $$ is invalid
                "async fn $NAME<$T>($PARAM: $T)",         # Too complex
            ]
            
            for pattern in wrong_patterns:
                print(f"\n❌ WRONG: {pattern}")
                result = await session.call_tool(
                    "analyze_code",
                    arguments={
                        "code": "pub async fn test(x: String) {}",
                        "language": "rust",
                        "pattern": pattern
                    }
                )
                print(f"   Result: {result.get('count', 0)} matches")
                if result.get("debug_info"):
                    print(f"   Suggestion: {result['debug_info'].get('suggestion', 'N/A')}")


async def demo_rust_security_audit():
    """Show how to run a security audit on Rust code."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ast_grep_mcp"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n\n=== Rust Security Audit ===\n")
            
            # Run security audit
            result = await session.call_tool(
                "run_security_audit",
                arguments={
                    "language": "rust",
                    "directory": "."
                }
            )
            
            if "error" not in result:
                print(f"Risk Level: {result.get('risk_level', 'Unknown')}")
                print(f"Total Findings: {result.get('total_findings', 0)}")
                
                if result.get("findings_by_severity"):
                    print("\nFindings by Severity:")
                    for sev, count in result["findings_by_severity"].items():
                        if count > 0:
                            print(f"  {sev}: {count}")
                
                if result.get("recommendations"):
                    print("\nRecommendations:")
                    for rec in result["recommendations"]:
                        print(f"  - {rec}")
            else:
                print(f"Error: {result['error']}")


async def demo_pattern_builder():
    """Show how to use the pattern builder for Rust."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ast_grep_mcp"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n\n=== Pattern Builder for Rust ===\n")
            
            # Build patterns
            pattern_types = [
                ("async_function", {"name": None}),
                ("unsafe_block", {}),
                ("impl_block", {"type": "MyStruct"}),
            ]
            
            for ptype, options in pattern_types:
                result = await session.call_tool(
                    "build_pattern",
                    arguments={
                        "pattern_type": ptype,
                        "language": "rust",
                        "options": options
                    }
                )
                
                if "pattern" in result:
                    print(f"\n{ptype}:")
                    print(f"  Pattern: {result['pattern']}")
                    print(f"  Description: {result.get('description', 'N/A')}")


if __name__ == "__main__":
    print("AST-GREP MCP - Rust Async Functions Demo")
    print("=" * 50)
    
    # Run demos
    asyncio.run(demo_rust_async_search())
    asyncio.run(demo_rust_security_audit())
    asyncio.run(demo_pattern_builder())
    
    print("\n\nKey Takeaways:")
    print("1. Use simple patterns like 'async fn $NAME' for Rust")
    print("2. Don't use $$$ for function parameters")
    print("3. Start with exact matches, then add metavariables")
    print("4. Check debug_info when no matches are found")
    print("5. Use the pattern cookbook for reference")