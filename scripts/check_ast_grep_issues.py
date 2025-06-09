#!/usr/bin/env python3
"""
Script to analyze AST-Grep results and generate a report.
"""

import json
import sys


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} ast-grep-analysis.json")
        sys.exit(1)

    analysis_file = sys.argv[1]

    try:
        with open(analysis_file, "r") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading analysis file: {e}")
        sys.exit(1)

    # Categorize findings
    categories = {}
    for result in results:
        category = result.get("category", "unknown")
        if category not in categories:
            categories[category] = []
        categories[category].append(result)

    # Print summary
    print("# AST-Grep Analysis Summary\n")
    print(f"Found {len(results)} issues across {len(categories)} categories:\n")

    # Generate a markdown report
    with open("ast-grep-report.md", "w") as report:
        report.write("# AST-Grep Analysis Summary\n\n")
        report.write(
            f"Found {len(results)} issues across {len(categories)} categories:\n\n"
        )

        for category, items in categories.items():
            report.write(f"## {category.title()} Issues ({len(items)})\n\n")

            # Group by pattern name
            patterns = {}
            for item in items:
                pattern_name = item.get("pattern_name", "unknown")
                if pattern_name not in patterns:
                    patterns[pattern_name] = []
                patterns[pattern_name].append(item)

            # Print patterns
            for pattern_name, pattern_items in patterns.items():
                report.write(f"### {pattern_name} ({len(pattern_items)} instances)\n\n")
                for idx, item in enumerate(pattern_items[:5]):  # Limit to 5 examples
                    report.write(
                        f"- `{item['file']}:{item['line']}`: `{item['text']}`\n"
                    )

                if len(pattern_items) > 5:
                    report.write(f"- ... and {len(pattern_items) - 5} more instances\n")

                report.write("\n")

    # Check for critical issues
    critical_categories = ["anti-pattern", "performance"]
    critical_issues = [r for r in results if r.get("category") in critical_categories]

    if critical_issues:
        print(f"Found {len(critical_issues)} critical issues that should be fixed!")
        for issue in critical_issues[:5]:  # Show a few examples
            print(
                f"- {issue['file']}:{issue['line']} - {issue['pattern_name']}: {issue['text']}"
            )
        sys.exit(1)
    else:
        print("No critical issues found. Good job!")


if __name__ == "__main__":
    main()
