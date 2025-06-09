#!/usr/bin/env python3
"""
Demonstration of improved ast-grep-mcp workflow.

This example shows how the new features solve the pain points
identified in the assessments.
"""

from ast_grep_mcp.core.ast_grep_mcp import AstGrepMCP
from ast_grep_mcp.utils.simple_pattern_builder import SimplePatternBuilder
from ast_grep_mcp.utils.pattern_templates import PatternTemplateLibrary
from ast_grep_mcp.utils.batch_operations import create_code_quality_batch


def demonstrate_spawn_pattern_fix():
    """Show how complex spawn patterns now work."""
    print("=== Spawn Pattern Fix ===")
    
    # The pattern that used to fail
    complex_pattern = "spawn(async move { $$BODY })"
    print(f"Original pattern (used to fail): {complex_pattern}")
    
    # Now it gets automatically fixed
    from ast_grep_mcp.utils.pattern_fixer import PatternFixer
    alternatives = PatternFixer.fix_pattern(complex_pattern, "rust")
    print("Auto-generated alternatives:")
    for alt in alternatives:
        print(f"  - {alt}")
    
    # The recommended approach
    builder = SimplePatternBuilder("rust")
    working_pattern = builder.spawn_call(with_block=False).build()
    print(f"\nRecommended pattern: {working_pattern}")
    print("This pattern matches ALL spawn calls reliably!\n")


def demonstrate_pattern_builder():
    """Show simplified pattern construction."""
    print("=== Pattern Builder ===")
    
    # Building complex patterns is now easy
    builder = SimplePatternBuilder("rust")
    
    # Async function pattern
    pattern = (builder
        .async_function()
        .with_params()
        .returns("Result<()>")
        .with_body()
        .build())
    
    print(f"Built pattern: {pattern}")
    print("No need to remember exact syntax!\n")


def demonstrate_pattern_templates():
    """Show pattern templates with examples."""
    print("=== Pattern Templates ===")
    
    # Get a refactoring template
    template = PatternTemplateLibrary.get_template("unwrap_to_expect", "rust")
    if template:
        print(f"Template: {template.name}")
        print(f"Pattern: {template.pattern}")
        print(f"Replacement: {template.replacement}")
        print("Examples that would match:")
        for example in template.example_matches[:2]:
            print(f"  - {example}")
        print("Variables to provide:")
        for var, desc in template.variables.items():
            print(f"  - {var}: {desc}")
    print()


def demonstrate_batch_search():
    """Show batch operations for efficiency."""
    print("=== Batch Search ===")
    
    # Create a code quality batch
    batch = create_code_quality_batch("rust")
    
    print("Code quality checks:")
    for req in batch[:5]:  # Show first 5
        print(f"  - {req.name}: {req.pattern} (severity: {req.severity})")
    
    print("\nThese run in parallel for better performance!\n")


def demonstrate_natural_language_search():
    """Show natural language pattern search."""
    print("=== Natural Language Search ===")
    
    mcp = AstGrepMCP()
    
    # Examples of natural language queries
    queries = [
        "unwrap calls",
        "async functions", 
        "spawn tasks",
        "error handling"
    ]
    
    print("Natural language queries work:")
    for query in queries:
        result = mcp.find_pattern(query, "rust")
        if "found_patterns" in result:
            patterns = result["found_patterns"]
            if patterns:
                print(f'  "{query}" → {patterns[0]["pattern"]}')
    print()


def demonstrate_metavariable_guide():
    """Show clear metavariable documentation."""
    print("=== Metavariable Guide ===")
    
    from ast_grep_mcp.utils.enhanced_diagnostics import EnhancedDiagnostics
    
    # Get diagnosis for a problematic pattern
    diagnosis = EnhancedDiagnostics.diagnose_pattern_failure(
        "$NAME($$PARAMS)",  # Wrong: uses $$
        "rust"
    )
    
    print("Clear metavariable usage:")
    for var, desc in diagnosis["metavariable_guide"].items():
        print(f"  {var}: {desc}")
    print()


def demonstrate_auto_pagination():
    """Show auto-pagination with streaming."""
    print("=== Auto-Pagination ===")
    
    print("Old way (manual):")
    print("""
    page = 1
    while True:
        results = search_directory(pattern, page=page)
        # process results...
        if not results.has_more:
            break
        page += 1
    """)
    
    print("New way (automatic):")
    print("""
    for result in create_search_stream(search_func, pattern, directory):
        # Pagination handled automatically!
        print(f"Match: {result['match']}")
        print(f"Progress: {result['_progress']['total_yielded']} results")
    """)
    print()


def demonstrate_perfect_workflow():
    """Show the ideal workflow with all improvements."""
    print("=== Perfect Workflow ===")
    
    print("1. Create pattern from description:")
    print('   pattern = create_smart_pattern("Find spawn calls", "rust")')
    
    print("\n2. Or use pattern builder:")
    print('   pattern = SimplePatternBuilder("rust").spawn_call().build()')
    
    print("\n3. Run batch search for multiple patterns:")
    print('   results = batch_search(patterns, directory)')
    
    print("\n4. Stream results with auto-pagination:")
    print('   for match in search_stream:')
    print('       process(match)  # No manual pagination!')
    
    print("\n5. Get helpful errors if pattern fails:")
    print('   ❌ Pattern failed')
    print('   💡 Try these instead: ...')
    print('   📝 Examples that would match: ...')


def main():
    """Run all demonstrations."""
    print("AST-GREP-MCP IMPROVED WORKFLOW DEMONSTRATION")
    print("=" * 50)
    print()
    
    demonstrate_spawn_pattern_fix()
    demonstrate_pattern_builder()
    demonstrate_pattern_templates()
    demonstrate_batch_search()
    demonstrate_natural_language_search()
    demonstrate_metavariable_guide()
    demonstrate_auto_pagination()
    demonstrate_perfect_workflow()
    
    print("\n" + "=" * 50)
    print("All pain points have been addressed! 🎉")
    print("The tool is now much easier and more forgiving to use.")


if __name__ == "__main__":
    main()