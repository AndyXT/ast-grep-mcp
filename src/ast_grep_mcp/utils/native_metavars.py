"""
Native metavariable extraction using ast-grep-py's built-in capabilities.

This module provides a cleaner, more reliable way to extract metavariables
from ast-grep matches, replacing the complex regex-based approach.
"""

import re
import logging
from typing import Dict, List, Set, Tuple
from ast_grep_py import SgNode

logger = logging.getLogger("ast_grep_mcp.native_metavars")


class NativeMetavarExtractor:
    """Extract metavariables using ast-grep's native API."""
    
    def __init__(self):
        self.logger = logger
    
    def extract_metavar_names(self, pattern: str) -> Tuple[Set[str], Set[str]]:
        """
        Extract metavariable names from a pattern.
        
        Args:
            pattern: The ast-grep pattern
            
        Returns:
            Tuple of (single_vars, multi_vars) where:
            - single_vars: Set of single metavariable names (e.g., NAME from $NAME)
            - multi_vars: Set of multi metavariable names (e.g., PARAMS from $$$PARAMS)
        """
        # Extract single metavariables ($NAME)
        # Must not be preceded or followed by $
        single_vars = set(re.findall(r'(?<!\$)\$([A-Z][A-Z0-9_]*)(?!\$)', pattern))
        
        # Extract multi metavariables ($$$NAME)
        multi_vars = set(re.findall(r'\$\$\$([A-Z][A-Z0-9_]*)', pattern))
        
        # Handle special cases like $$NAME (should be $$$NAME)
        double_vars = set(re.findall(r'(?<!\$)\$\$([A-Z][A-Z0-9_]*)(?!\$)', pattern))
        if double_vars:
            self.logger.warning(
                f"Found double-dollar variables {double_vars}, treating as multi-vars"
            )
            multi_vars.update(double_vars)
        
        return single_vars, multi_vars
    
    def extract_metavariables(self, match: SgNode, pattern: str) -> Dict[str, str]:
        """
        Extract metavariable values from a match using native ast-grep API.
        
        Args:
            match: The matched SgNode
            pattern: The pattern used for matching
            
        Returns:
            Dictionary mapping metavariable names to their captured values
        """
        captures = {}
        
        # Extract metavariable names from pattern
        single_vars, multi_vars = self.extract_metavar_names(pattern)
        
        self.logger.debug(f"Pattern: {pattern}")
        self.logger.debug(f"Single metavars: {single_vars}")
        self.logger.debug(f"Multi metavars: {multi_vars}")
        
        # Extract single metavariables
        for var_name in single_vars:
            try:
                var_match = match.get_match(var_name)
                if var_match:
                    captures[f"${var_name}"] = var_match.text()
                    self.logger.debug(f"Captured ${var_name}: {var_match.text()}")
                else:
                    # No match means empty
                    captures[f"${var_name}"] = ""
                    self.logger.debug(f"${var_name} is empty")
            except Exception as e:
                self.logger.debug(f"Could not capture ${var_name}: {e}")
                captures[f"${var_name}"] = ""
        
        # Extract multi metavariables
        for var_name in multi_vars:
            try:
                multi_matches = match.get_multiple_matches(var_name)
                if multi_matches:
                    # Join the text of all matches
                    # Filter out punctuation nodes if needed
                    texts = []
                    for m in multi_matches:
                        text = m.text()
                        # Include all text, including punctuation
                        texts.append(text)
                    
                    # Join with appropriate spacing
                    joined_text = self._smart_join(texts, var_name)
                    captures[f"$$${var_name}"] = joined_text
                    self.logger.debug(f"Captured $$${var_name}: {joined_text}")
                else:
                    # No matches means empty
                    captures[f"$$${var_name}"] = ""
                    self.logger.debug(f"$$${var_name} is empty")
            except Exception as e:
                self.logger.debug(f"Could not capture $$${var_name}: {e}")
                captures[f"$$${var_name}"] = ""
        
        return captures
    
    def _smart_join(self, texts: List[str], var_name: str) -> str:
        """
        Intelligently join text fragments based on context.
        
        Args:
            texts: List of text fragments
            var_name: The variable name for context
            
        Returns:
            Joined text with appropriate spacing
        """
        if not texts:
            return ""
        
        # For parameters, join without extra spaces around commas
        if var_name in ["PARAMS", "ARGS", "VALUES"]:
            # Join all parts, ensuring space after comma
            result = ""
            for i, text in enumerate(texts):
                if text == ",":
                    result += ", "
                else:
                    if i > 0 and texts[i-1] != ",":
                        result += " "
                    result += text
            return result.strip()
        
        # For body/statements, join with newlines
        if var_name in ["BODY", "STATEMENTS", "CONTENT"]:
            # Join with newline and proper indentation
            result = []
            for text in texts:
                # Skip empty texts
                if text.strip():
                    result.append(text)
            return "\n    ".join(result) if result else ""
        
        # Default: join with spaces
        return " ".join(texts)
    
    def substitute_metavariables(
        self, 
        replacement: str, 
        captures: Dict[str, str]
    ) -> str:
        """
        Substitute captured metavariables into a replacement pattern.
        
        Args:
            replacement: The replacement pattern
            captures: Dictionary of captured metavariables
            
        Returns:
            The replacement with metavariables substituted
        """
        result = replacement
        
        # Sort by length descending to avoid partial replacements
        # e.g., replace $$$PARAMS before $PARAMS
        sorted_captures = sorted(
            captures.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        )
        
        for var_name, value in sorted_captures:
            if var_name in result:
                result = result.replace(var_name, value)
                self.logger.debug(f"Substituted {var_name} with {value}")
        
        return result


def create_native_extractor() -> NativeMetavarExtractor:
    """Create a native metavariable extractor instance."""
    return NativeMetavarExtractor()


# Example usage
if __name__ == "__main__":
    from ast_grep_py import SgRoot
    
    # Example code
    code = """
    function greet(name, age) {
        console.log("Hello " + name);
        console.log("Age: " + age);
    }
    """
    
    # Parse and find pattern
    root = SgRoot(code, "javascript")
    pattern = "function $NAME($$$PARAMS) { $$$BODY }"
    matches = root.root().find_all(pattern=pattern)
    
    if matches:
        extractor = create_native_extractor()
        for match in matches:
            print(f"Match: {match.text()}")
            captures = extractor.extract_metavariables(match, pattern)
            print(f"Captures: {captures}")
            
            # Test substitution
            replacement = "const $NAME = ($$$PARAMS) => { $$$BODY }"
            result = extractor.substitute_metavariables(replacement, captures)
            print(f"Transformed: {result}")