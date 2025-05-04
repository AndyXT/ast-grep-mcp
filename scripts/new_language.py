#!/usr/bin/env python3
"""
Template handler generator script for ast-grep-mcp.

Usage:
    python scripts/new_language.py <language_name>
    
Example:
    python scripts/new_language.py rust
"""

import sys
import re
from pathlib import Path

# Template for a new language handler
HANDLER_TEMPLATE = '''"""
{language_title} language handler for ast-grep.
"""

from typing import Dict, List
from .base import LanguageHandler

class {class_name}Handler(LanguageHandler):
    @property
    def language_name(self) -> str:
        return "{language_name}"
        
    @property
    def file_extensions(self) -> List[str]:
        return [{file_extensions}]
        
    def get_default_patterns(self) -> Dict[str, str]:
        """
        Return default AST patterns for {language_title}.
        
        Includes patterns for:
        - Common code constructs
        - Anti-patterns and code smells
        - Performance optimizations
        - Security vulnerabilities
        - Refactoring opportunities
        """
        return {{
            # Basic code constructs
            "function": "{function_pattern}",
            "struct": "{struct_pattern}",
            "variable": "{variable_pattern}",
            "comment": "{comment_pattern}",
            
            # TODO: Add more patterns (at least 25 total)
            # Anti-patterns
            
            # Performance optimizations
            
            # Security vulnerabilities
            
            # Refactoring patterns
        }}
'''

# Template for updating the __init__.py file
INIT_UPDATE_TEMPLATE = '''from .{language_name}_handler import {class_name}Handler

# Register all language handlers
handlers = {{
    handler.language_name: handler()
    for handler in [
        PythonHandler,
        JavaScriptHandler,
        {new_handlers}
    ]
}}
'''

# Language specific configurations
LANGUAGE_CONFIG = {
    "c": {
        "file_extensions": '".c", ".h"',
        "function_pattern": "\\$RET_TYPE \\$NAME(\\$\\$\\$PARAMS)",
        "struct_pattern": "struct \\$NAME { \\$\\$\\$FIELDS }",
        "variable_pattern": "\\$TYPE \\$NAME = \\$VALUE;",
        "comment_pattern": "/* \\$\\$\\$COMMENT */"
    },
    "go": {
        "file_extensions": '".go"',
        "function_pattern": "func \\$NAME(\\$\\$\\$PARAMS) \\$\\$\\$RETURN_TYPE",
        "struct_pattern": "type \\$NAME struct { \\$\\$\\$FIELDS }",
        "variable_pattern": "\\$NAME := \\$VALUE",
        "comment_pattern": "// \\$\\$\\$COMMENT"
    },
    "rust": {
        "file_extensions": '".rs"',
        "function_pattern": "fn \\$NAME(\\$\\$\\$PARAMS) -> \\$RET_TYPE",
        "struct_pattern": "struct \\$NAME { \\$\\$\\$FIELDS }",
        "variable_pattern": "let \\$NAME = \\$VALUE;",
        "comment_pattern": "// \\$\\$\\$COMMENT"
    }
}

def generate_handler(language_name: str) -> None:
    """Generate a new language handler file."""
    language_name = language_name.lower()
    
    # Check if language is supported
    if language_name not in LANGUAGE_CONFIG:
        print(f"Error: Language '{language_name}' is not currently supported by this script.")
        print(f"Supported languages: {', '.join(LANGUAGE_CONFIG.keys())}")
        print("You can still create a handler manually by adding the necessary configuration.")
        sys.exit(1)
    
    # Create class name (capitalize first letter)
    class_name = language_name.capitalize()
    
    # Set paths
    handlers_dir = Path("src/ast_grep_mcp/language_handlers")
    handler_file = handlers_dir / f"{language_name}_handler.py"
    init_file = handlers_dir / "__init__.py"
    
    # Check if handler already exists
    if handler_file.exists():
        print(f"Error: Handler file for {language_name} already exists at {handler_file}")
        sys.exit(1)
    
    # Make sure the handlers directory exists
    if not handlers_dir.exists():
        print(f"Error: Handlers directory does not exist at {handlers_dir}")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Get language configuration
    lang_config = LANGUAGE_CONFIG[language_name]
    
    # Generate handler content
    handler_content = HANDLER_TEMPLATE.format(
        language_name=language_name,
        language_title=language_name.title(),
        class_name=class_name,
        file_extensions=lang_config["file_extensions"],
        function_pattern=lang_config["function_pattern"],
        struct_pattern=lang_config["struct_pattern"],
        variable_pattern=lang_config["variable_pattern"],
        comment_pattern=lang_config["comment_pattern"]
    )
    
    # Write handler file
    with open(handler_file, "w") as f:
        f.write(handler_content)
    
    print(f"✅ Created language handler: {handler_file}")
    
    # Update __init__.py to register the new handler
    if init_file.exists():
        with open(init_file, "r") as f:
            init_content = f.read()
        
        # Check if handler is already registered
        if f"{class_name}Handler" in init_content:
            print(f"⚠️ Handler {class_name}Handler already registered in {init_file}")
        else:
            # Extract existing handlers
            handlers_pattern = r"for handler in \[([\s\S]*?)\]"
            match = re.search(handlers_pattern, init_content)
            
            if match:
                existing_handlers = match.group(1).strip()
                # Add new handler to the list
                new_handlers = existing_handlers
                if f"{class_name}Handler" not in new_handlers:
                    if new_handlers.endswith(","):
                        new_handlers += f"\n        {class_name}Handler"
                    else:
                        new_handlers += f",\n        {class_name}Handler"
                
                # Update the init file
                updated_init = re.sub(
                    handlers_pattern, 
                    f"for handler in [\n        {new_handlers}\n    ]", 
                    init_content
                )
                
                # Make sure import is added
                import_line = f"from .{language_name}_handler import {class_name}Handler"
                if import_line not in updated_init:
                    # Find the last import line
                    import_match = re.search(r"(from .*?\n)(?!from)", updated_init)
                    if import_match:
                        # Insert after the last import
                        updated_init = updated_init.replace(
                            import_match.group(1),
                            f"{import_match.group(1)}{import_line}\n"
                        )
                    else:
                        # Add at the beginning
                        updated_init = f"{import_line}\n{updated_init}"
                
                with open(init_file, "w") as f:
                    f.write(updated_init)
                
                print(f"✅ Updated {init_file} to register the new handler")
            else:
                print(f"⚠️ Could not update {init_file}. Manual registration required.")
    else:
        print(f"⚠️ {init_file} does not exist. Manual registration required.")
    
    print(f"\n🎉 Successfully generated handler for {language_name}!")
    print("Next steps:")
    print(f"1. Complete the pattern library in {handler_file}")
    print("2. Add unit tests for the new handler")
    print("3. Add documentation with examples for each pattern")

def main():
    """Main entry point for the template generator script."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <language_name>")
        print(f"Example: python {sys.argv[0]} rust")
        sys.exit(1)
    
    language_name = sys.argv[1].lower()
    generate_handler(language_name)

if __name__ == "__main__":
    main() 