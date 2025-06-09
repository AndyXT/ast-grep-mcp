#!/usr/bin/env python3
"""
Demo script showcasing the enhanced features of ast-grep MCP.

This script demonstrates all the improvements suggested in the feedback.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demo_enhanced_features():
    """Demonstrate all the new enhanced features."""
    
    # Connect to the ast-grep MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ast_grep_mcp"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("=== AST-GREP MCP Enhanced Features Demo ===\n")
            
            # 1. Better Error Messages
            print("1. Better Error Messages")
            print("-" * 50)
            try:
                # This will trigger the enhanced error handling
                result = await session.call_tool(
                    "search_directory_invalid",  # Invalid method name
                    arguments={"directory": "/path", "pattern": "test"}
                )
            except Exception as e:
                print(f"Enhanced error message:\n{e}\n")
            
            # 2. Enhanced Search with Context
            print("2. Enhanced Search with Context and Metrics")
            print("-" * 50)
            result = await session.call_tool(
                "search_directory_with_context",
                arguments={
                    "directory": ".",
                    "pattern": "def $FUNC($$$PARAMS)",
                    "context_lines": 3,
                    "include_metrics": True
                }
            )
            print(f"Found {result.get('total_matches', 0)} matches with context")
            if result.get('metrics'):
                print(f"Metrics: {result['metrics']}")
            print()
            
            # 3. Pre-built Security Rules
            print("3. Security Audit with Pre-built Rules")
            print("-" * 50)
            result = await session.call_tool(
                "run_security_audit",
                arguments={
                    "language": "python",
                    "directory": "."
                }
            )
            print(f"Risk Level: {result.get('risk_level', 'Unknown')}")
            print(f"Total Findings: {result.get('total_findings', 0)}")
            if result.get('recommendations'):
                print("Recommendations:")
                for rec in result['recommendations']:
                    print(f"  - {rec}")
            print()
            
            # 4. Pattern Builder
            print("4. Pattern Builder for Complex Patterns")
            print("-" * 50)
            result = await session.call_tool(
                "build_pattern",
                arguments={
                    "pattern_type": "function",
                    "language": "python",
                    "options": {
                        "name": "test_*",
                        "decorator": "pytest.mark.parametrize"
                    }
                }
            )
            print(f"Built pattern: {result.get('pattern')}")
            print(f"Description: {result.get('description')}")
            print()
            
            # 5. Streaming Results (Already implemented)
            print("5. Streaming Results for Large Codebases")
            print("-" * 50)
            result = await session.call_tool(
                "search_directory_stream",
                arguments={
                    "directory": ".",
                    "pattern": "import $MODULE",
                    "language": "python",
                    "stream_config": {
                        "batch_size": 50,
                        "enable_progress": True
                    }
                }
            )
            print(f"Streaming session created: {result.get('session_id')}")
            print(f"Estimated files: {result.get('search_info', {}).get('estimated_files', 0)}")
            print()
            
            # 6. Cross-file Analysis
            print("6. Cross-file Analysis")
            print("-" * 50)
            
            # Find trait implementations (Rust example)
            if False:  # Skip if not a Rust project
                result = await session.call_tool(
                    "find_trait_implementations",
                    arguments={
                        "trait_name": "Display",
                        "directory": "."
                    }
                )
                print(f"Found {result.get('total_implementations', 0)} implementations")
            
            # Find function calls
            result = await session.call_tool(
                "find_function_calls",
                arguments={
                    "function_name": "print",
                    "directory": ".",
                    "language": "python"
                }
            )
            print(f"Found {result.get('total_calls', 0)} calls to 'print'")
            
            # Analyze dependencies
            result = await session.call_tool(
                "analyze_dependencies",
                arguments={
                    "directory": ".",
                    "language": "python"
                }
            )
            print(f"External dependencies: {len(result.get('external_dependencies', []))}")
            print(f"Internal dependencies: {len(result.get('internal_dependencies', []))}")
            print()
            
            # 7. Project Overview
            print("7. Project Structure Analysis")
            print("-" * 50)
            result = await session.call_tool(
                "analyze_project_structure",
                arguments={"directory": "."}
            )
            print(f"Project Type: {result.get('project_type')}")
            print(f"Primary Language: {result.get('primary_language')}")
            print(f"Total Files: {result.get('file_statistics', {}).get('total_files', 0)}")
            print(f"Total Lines: {result.get('code_statistics', {}).get('total_lines', 0)}")
            print(f"Has Tests: {result.get('has_tests', False)}")
            print()
            
            # 8. Code Quality Analysis
            print("8. Code Quality Analysis")
            print("-" * 50)
            result = await session.call_tool(
                "analyze_code_quality",
                arguments={
                    "directory": ".",
                    "include_metrics": True
                }
            )
            print(f"Quality Grade: {result.get('quality_grade')}")
            print(f"Quality Score: {result.get('quality_score')}/100")
            if result.get('metrics'):
                print(f"Total Issues: {result['metrics'].get('total_issues', 0)}")
            print()
            
            # 9. Generate Comprehensive Report
            print("9. Comprehensive Review Report")
            print("-" * 50)
            result = await session.call_tool(
                "generate_review_report",
                arguments={
                    "directory": ".",
                    "output_format": "markdown",
                    "include_security": True,
                    "include_quality": True,
                    "include_metrics": True
                }
            )
            print(f"Executive Summary: {result.get('executive_summary')}")
            print(f"Overall Score: {result.get('overall_score', {}).get('grade', 'N/A')}")
            
            # Save the report
            with open("review_report.md", "w") as f:
                f.write(result.get('formatted_report', ''))
            print("Full report saved to: review_report.md")


async def demo_ideal_workflow():
    """Demonstrate the ideal workflow mentioned in the feedback."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "ast_grep_mcp"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n\n=== Ideal Workflow Demo ===\n")
            
            project_dir = "."
            
            # 1. Start with overview
            print("1. Project Overview")
            overview = await session.call_tool(
                "analyze_project_structure",
                arguments={"directory": project_dir}
            )
            print(f"Project Type: {overview.get('project_type')}")
            print(f"Primary Language: {overview.get('primary_language')}")
            print(f"Total Files: {overview.get('file_statistics', {}).get('total_files', 0)}")
            
            # 2. Run security audit
            print("\n2. Security Audit")
            language = overview.get('primary_language', 'python')
            if language != 'unknown':
                security = await session.call_tool(
                    "run_security_audit",
                    arguments={
                        "language": language,
                        "directory": project_dir
                    }
                )
                print(f"Risk Level: {security.get('risk_level')}")
                for severity, count in security.get('findings_by_severity', {}).items():
                    if count > 0:
                        print(f"  {severity}: {count} issues")
            
            # 3. Check code quality
            print("\n3. Code Quality")
            quality = await session.call_tool(
                "analyze_code_quality",
                arguments={
                    "directory": project_dir,
                    "include_metrics": True
                }
            )
            print(f"Quality Grade: {quality.get('quality_grade')}")
            for smell_type, issues in quality.get('issues', {}).items():
                if issues:
                    print(f"  {smell_type}: {len(issues)} issues")
            
            # 4. Generate report
            print("\n4. Generating Comprehensive Report")
            report = await session.call_tool(
                "generate_review_report",
                arguments={
                    "directory": project_dir,
                    "output_format": "markdown",
                    "include_security": True,
                    "include_quality": True,
                    "include_metrics": True
                }
            )
            
            print(f"\nExecutive Summary: {report.get('executive_summary')}")
            print("\nReport saved to: review_report.md")


if __name__ == "__main__":
    print("Starting AST-GREP MCP Enhanced Features Demo\n")
    
    # Run the enhanced features demo
    asyncio.run(demo_enhanced_features())
    
    # Run the ideal workflow demo
    asyncio.run(demo_ideal_workflow())
    
    print("\nDemo completed!")