from ast_grep_py import SgRoot
from typing import List, Dict, Any, Optional

class AstAnalyzer:
    """AST-based code analyzer using ast-grep"""
    
    def __init__(self):
        self.supported_languages = {
            "python": [".py"],
            "lua": [".lua"],
            "c": [".c", ".h"],
            "rust": [".rs"],
            "go": [".go"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
        }
    
    def parse_code(self, code: str, language: str) -> Optional[SgRoot]:
        """Parse code into an AST representation"""
        if language not in self.supported_languages:
            return None
        
        return SgRoot(code, language)
    
    def find_patterns(self, code: str, language: str, pattern: str) -> List[Dict[str, Any]]:
        """Find all occurrences of a pattern in the code"""
        root = self.parse_code(code, language)
        if not root:
            return []
        
        node = root.root()
        matches = node.find_all(pattern=pattern)
        
        results = []
        for match in matches:
            results.append({
                "text": match.text(),
                "location": {
                    "start": {
                        "line": match.range().start.line,
                        "column": match.range().start.column
                    },
                    "end": {
                        "line": match.range().end.line,
                        "column": match.range().end.column
                    }
                }
            })
        
        return results
    
    def apply_refactoring(self, code: str, language: str, pattern: str, replacement: str) -> str:
        """Apply a pattern-based refactoring to the code"""
        root = self.parse_code(code, language)
        if not root:
            return code
        
        node = root.root()
        matches = node.find_all(pattern=pattern)
        
        edits = []
        for match in matches:
            edit = match.replace(replacement)
            edits.append(edit)
        
        if not edits:
            return code
        
        return node.commit_edits(edits)
    
    def get_supported_languages(self) -> Dict[str, List[str]]:
        """Return a dictionary of supported languages and their file extensions"""
        return self.supported_languages