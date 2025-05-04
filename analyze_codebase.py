"""
AST Grep Analyzer for Python codebase.
This script uses ast-grep to analyze the codebase for anti-patterns, code smells,
security vulnerabilities, and performance issues.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any

# Import directly from the local ast-grep-mcp package
sys.path.append(os.path.abspath("."))
from src.ast_grep_mcp.ast_analyzer import AstAnalyzer
from src.ast_grep_mcp.language_handlers.python_handler import PythonHandler

def find_python_files(directory: str) -> List[str]:
    """Find all Python files in the given directory."""
    # Use a list comprehension to avoid nested loops
    return [
        os.path.join(root, file)
        for root, _, files in os.walk(directory)
        for file in files
        if file.endswith(".py")
    ]

def analyze_file(file_path: str, analyzer: AstAnalyzer, patterns: Dict[str, str], category: str) -> List[Dict[str, Any]]:
    """Analyze a file using the given patterns."""
    results = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            
        for pattern_name, pattern in patterns.items():
            matches = analyzer.find_patterns(code, "python", pattern)
            if matches:
                for match in matches:
                    results.append({
                        "file": file_path,
                        "pattern_name": pattern_name,
                        "pattern": pattern,
                        "category": category,
                        "line": match["location"]["start"]["line"] + 1,  # 1-based line numbers
                        "column": match["location"]["start"]["column"] + 1,  # 1-based column numbers
                        "text": match["text"]
                    })
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="AST Grep Analyzer for Python codebase")
    parser.add_argument("--directory", default="src", help="Directory to analyze")
    parser.add_argument("--output", default="ast-grep-analysis.json", help="Output file path")
    args = parser.parse_args()
    
    analyzer = AstAnalyzer()
    handler = PythonHandler()
    python_files = find_python_files(args.directory)
    
    # Get all pattern categories
    all_patterns = handler.get_default_patterns()
    
    # Anti-patterns and code smells
    anti_patterns = {
        "bare_except": all_patterns["bare_except"],
        "except_pass": all_patterns["except_pass"],
        "mutable_default_arg": all_patterns["mutable_default_arg"],
        "global_statement": all_patterns["global_statement"],
        "nested_function": all_patterns["nested_function"],
        "nested_loops": all_patterns["nested_loops"],
        "long_function": all_patterns["long_function"],
    }
    
    # Security vulnerabilities
    security_patterns = {
        "eval_call": all_patterns["eval_call"],
        "exec_call": all_patterns["exec_call"],
        "shell_true": all_patterns["shell_true"],
        "pickle_load": all_patterns["pickle_load"],
        "yaml_load": all_patterns["yaml_load"],
        "sql_format": all_patterns["sql_format"],
        "open_file_without_close": all_patterns["open_file_without_close"],
        "tempfile_insecure": all_patterns["tempfile_insecure"],
    }
    
    # Performance optimizations
    performance_patterns = {
        "list_in_loop": all_patterns["list_in_loop"],
        "string_concat_in_loop": all_patterns["string_concat_in_loop"],
        "inefficient_dict_lookup": all_patterns["inefficient_dict_lookup"],
        "repeated_calculation": all_patterns["repeated_calculation"],
        "inefficient_list_creation": all_patterns["inefficient_list_creation"],
        "unnecessary_list": all_patterns["unnecessary_list"],
    }
    
    # Refactoring opportunities - removed problematic patterns
    refactoring_patterns = {
        # Removed problematic patterns that cause AST node detection errors
        # "if_return_early": all_patterns["if_return_early"],
        # "multiple_if_returns": all_patterns["multiple_if_returns"],
        "dict_get_with_default": all_patterns["dict_get_with_default"],
        "try_except_else": all_patterns["try_except_else"],
        "explicit_none_compare": all_patterns["explicit_none_compare"],
        "redundant_with_open": all_patterns["redundant_with_open"],
    }
    
    # Analyze files
    all_results = []
    
    for category, patterns in [
        ("anti-pattern", anti_patterns),
        ("security", security_patterns),
        ("performance", performance_patterns),
        ("refactoring", refactoring_patterns)
    ]:
        print(f"Analyzing for {category} issues...")
        for file_path in python_files:
            results = analyze_file(file_path, analyzer, patterns, category)
            all_results.extend(results)
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    if all_results:
        print(f"\nFound {len(all_results)} issues:")
        categories = {}
        for result in all_results:
            cat = result["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in categories.items():
            print(f" - {cat}: {count} issues")
        
        print(f"\nFull results saved to {args.output}")
    else:
        print("No issues found!")

if __name__ == "__main__":
    main()