#!/usr/bin/env python
"""
Pattern Examples for ast-grep-mcp

This script demonstrates how to use ast-grep patterns with the ast-grep-mcp server.
Run it to see how patterns match against sample code.
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the path to import ast_grep_mcp
sys.path.append(str(Path(__file__).parent.parent))

from src.ast_grep_mcp.ast_analyzer import AstAnalyzer
from src.ast_grep_mcp.language_handlers import get_handler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('pattern_examples')

# Sample Python code
PYTHON_CODE = """
def simple_function(a, b, c):
    return a + b + c

class MyClass:
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value
        
    @property
    def doubled_value(self):
        return self.value * 2

for i in range(10):
    print(f"Value: {i}")

if x > 5:
    print("x is greater than 5")
else:
    print("x is not greater than 5")

try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")
"""

# Sample JavaScript code
JAVASCRIPT_CODE = """
function calculateSum(a, b, c) {
    return a + b + c;
}

class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    
    greet() {
        return `Hello, my name is ${this.name}`;
    }
}

const items = [1, 2, 3, 4, 5];
for (const item of items) {
    console.log(`Item: ${item}`);
}

if (x > 5) {
    console.log("x is greater than 5");
} else {
    console.log("x is not greater than 5");
}

try {
    const result = 10 / 0;
} catch (error) {
    console.error(`Error: ${error.message}`);
}

// React component example
const MyComponent = ({ name }) => {
    return <div className="container">Hello {name}</div>;
};
"""

def test_pattern(code, language, pattern):
    """Test a pattern against code and print the results."""
    analyzer = AstAnalyzer()
    matches = analyzer.find_patterns(code, language, pattern)
    
    if matches:
        logger.info(f"Pattern: '{pattern}' found {len(matches)} matches:")
        for i, match in enumerate(matches, 1):
            text = match["text"].replace("\n", "\\n")
            if len(text) > 60:
                text = text[:57] + "..."
            logger.info(f"  Match {i}: {text}")
    else:
        logger.warning(f"Pattern: '{pattern}' found NO matches.")

def main():
    """Run pattern examples."""
    logger.info("AST-GREP-MCP PATTERN EXAMPLES")
    logger.info("============================")
    
    # Get all language handlers to demonstrate patterns
    analyzer = AstAnalyzer()
    
    # Show Python examples
    logger.info("\nPYTHON PATTERN EXAMPLES:")
    logger.info("------------------------")
    
    python_patterns = [
        "def $NAME($$$PARAMS)",  # Function definition
        "def $NAME($$$PARAMS):\n    $$$BODY",  # Function with body
        "class $NAME",  # Class definition
        "class $NAME:\n    $$$BODY",  # Class with body
        "@$DECORATOR\ndef $NAME($$$PARAMS)",  # Decorated function
        "for $VAR in $ITER",  # For loop
        "if $CONDITION:\n    $$$BODY",  # If statement
        "print($$$ARGS)",  # Print statement
        "try:\n    $$$BODY\nexcept $EXCEPTION:\n    $$$HANDLER",  # Try-except
    ]
    
    for pattern in python_patterns:
        test_pattern(PYTHON_CODE, "python", pattern)
    
    # Show JavaScript examples
    logger.info("\nJAVASCRIPT PATTERN EXAMPLES:")
    logger.info("--------------------------")
    
    js_patterns = [
        "function $NAME($$$PARAMS) { $$$BODY }",  # Function definition
        "class $NAME { $$$BODY }",  # Class definition
        "($$$PARAMS) => $$$BODY",  # Arrow function
        "for (const $VAR of $ITERABLE) { $$$BODY }",  # For-of loop
        "if ($CONDITION) { $$$BODY }",  # If statement
        "console.log($$$ARGS)",  # Console.log
        "try { $$$BODY } catch ($ERR) { $$$HANDLER }",  # Try-catch
        "<$TAG $$$PROPS>$$$CHILDREN</$TAG>",  # JSX element
    ]
    
    for pattern in js_patterns:
        test_pattern(JAVASCRIPT_CODE, "javascript", pattern)
    
    # Show how to get language-specific patterns
    logger.info("\nAVAILABLE PATTERNS FROM LANGUAGE HANDLERS:")
    logger.info("-----------------------------------------")
    
    python_handler = get_handler("python")
    js_handler = get_handler("javascript")
    ts_handler = get_handler("typescript")
    
    if python_handler:
        patterns = python_handler.get_default_patterns()
        logger.info(f"Python patterns available: {len(patterns)}")
        for name, pattern in list(patterns.items())[:5]:
            logger.info(f"  {name}: {pattern}")
        if len(patterns) > 5:
            logger.info(f"  ... and {len(patterns) - 5} more patterns")
    
    if js_handler:
        patterns = js_handler.get_default_patterns()
        logger.info(f"JavaScript patterns available: {len(patterns)}")
        for name, pattern in list(patterns.items())[:5]:
            logger.info(f"  {name}: {pattern}")
        if len(patterns) > 5:
            logger.info(f"  ... and {len(patterns) - 5} more patterns")
    
    if ts_handler:
        patterns = ts_handler.get_default_patterns()
        ts_only = {k: v for k, v in patterns.items() if k not in js_handler.get_default_patterns()}
        logger.info(f"TypeScript-specific patterns available: {len(ts_only)}")
        for name, pattern in list(ts_only.items())[:5]:
            logger.info(f"  {name}: {pattern}")
        if len(ts_only) > 5:
            logger.info(f"  ... and {len(ts_only) - 5} more patterns")

if __name__ == "__main__":
    main() 