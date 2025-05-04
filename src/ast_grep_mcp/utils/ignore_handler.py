"""
Ignore file handler for AST Grep MCP.

This module provides functionality to parse and apply .ast-grepignore files,
which follow a similar format to .gitignore files.
"""

import os
import re
from pathlib import Path
from typing import List, Set, Optional


class IgnorePattern:
    """
    A compiled ignore pattern with matching functionality.
    """
    def __init__(self, pattern: str, base_dir: Optional[Path] = None):
        """
        Initialize an ignore pattern.
        
        Args:
            pattern: The ignore pattern string
            base_dir: The base directory for relative patterns
        """
        self.original_pattern = pattern.strip()
        self.negate = pattern.startswith('!')
        self.pattern = pattern[1:].strip() if self.negate else pattern.strip()
        self.base_dir = base_dir
        
        # Skip empty patterns and comments
        if not self.pattern or self.pattern.startswith('#'):
            self._is_valid = False
            return
        
        self._is_valid = True
        self._compile_pattern()
    
    def _compile_pattern(self):
        """
        Compile the ignore pattern into a regex pattern.
        """
        if not self._is_valid:
            return
        
        pattern = self.pattern
        
        # Handle directory-specific pattern
        self.dir_only = pattern.endswith('/')
        if self.dir_only:
            pattern = pattern[:-1]
        
        # Escape special regex characters, but not * or ?
        pattern = re.escape(pattern).replace('\\*', '*').replace('\\?', '?')
        
        # Convert glob patterns to regex patterns
        pattern = pattern.replace('*', '.*')
        pattern = pattern.replace('?', '.')
        
        # Anchor the pattern based on whether it starts with /
        if pattern.startswith('/'):
            pattern = f"^{pattern[1:]}"
        else:
            pattern = f"(^|/){pattern}"
        
        # For directory patterns, we need to match all files/dirs inside too
        if self.dir_only:
            pattern = f"{pattern}(/.*)?"
        
        # Compile the regex
        self._regex = re.compile(pattern)
    
    def matches(self, path: str) -> bool:
        """
        Check if the pattern matches the given path.
        
        Args:
            path: The path to check
            
        Returns:
            True if the pattern matches the path, False otherwise
        """
        if not self._is_valid:
            return False
        
        # Normalize the path
        norm_path = os.path.normpath(path).replace('\\', '/')
        
        # Convert absolute path to relative path if base_dir is set
        if self.base_dir and Path(path).is_absolute():
            try:
                rel_path = Path(path).relative_to(self.base_dir)
                norm_path = str(rel_path).replace('\\', '/')
            except ValueError:
                # Path is not relative to base_dir
                return False
        
        # Special case for directory patterns - direct child match
        if self.dir_only and '/' in norm_path:
            dir_part = norm_path.split('/')[0] + '/'
            if dir_part == self.pattern + '/':
                return True
        
        # For directory-only patterns, we need to ensure we're matching a directory
        # Only if the path actually exists (to avoid issues in tests)
        if self.dir_only and os.path.exists(path) and not os.path.isdir(path):
            # Check if it's a file inside a matched directory
            parent_dir = os.path.dirname(path)
            if parent_dir and self.matches(parent_dir):
                return True
            return False
        
        return bool(self._regex.search(norm_path))
    
    @property
    def is_valid(self) -> bool:
        """Check if the pattern is valid."""
        return self._is_valid


class IgnoreHandler:
    """
    Handler for .ast-grepignore files.
    
    This class parses ignore files and checks if paths should be ignored.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the ignore handler.
        
        Args:
            base_dir: The base directory for relative patterns
        """
        self.base_dir = Path(base_dir) if base_dir else None
        self.patterns: List[IgnorePattern] = []
        self.loaded_files: Set[str] = set()
    
    def add_pattern(self, pattern: str) -> None:
        """
        Add an ignore pattern.
        
        Args:
            pattern: The pattern to add
        """
        ignore_pattern = IgnorePattern(pattern, self.base_dir)
        if ignore_pattern.is_valid:
            self.patterns.append(ignore_pattern)
    
    def load_file(self, file_path: str) -> bool:
        """
        Load patterns from an ignore file.
        
        Args:
            file_path: Path to the ignore file
            
        Returns:
            True if the file was loaded successfully, False otherwise
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return False
        
        # Avoid loading the same file multiple times
        abs_path = str(path.absolute())
        if abs_path in self.loaded_files:
            return True
        
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.add_pattern(line)
            
            self.loaded_files.add(abs_path)
            return True
            
        except Exception:
            return False
    
    def load_default_ignores(self) -> None:
        """
        Load default ignore patterns.
        """
        default_patterns = [
            # Common version control directories
            '.git/',
            '.svn/',
            '.hg/',
            
            # Common build directories
            'build/',
            'dist/',
            'target/',
            
            # Common virtual environment directories
            'venv/',
            '.venv/',
            'env/',
            '.env/',
            
            # Python cache files
            '__pycache__/',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.pytest_cache/',
            '.ruff_cache/',
            
            # JavaScript/Node.js
            'node_modules/',
            '.npm/',
            
            # IDE files
            '.idea/',
            '.vscode/',
            '*.swp',
            '*.swo',
            
            # Other common files to ignore
            '.DS_Store',
            'Thumbs.db'
        ]
        
        for pattern in default_patterns:
            self.add_pattern(pattern)
    
    def should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored.
        
        This method applies all loaded patterns to determine if a path
        should be ignored.
        
        Args:
            path: The path to check
            
        Returns:
            True if the path should be ignored, False otherwise
        """
        # Normalize the path
        norm_path = os.path.normpath(path)
        
        # Apply patterns in order, with later patterns overriding earlier ones
        ignored = False
        for pattern in self.patterns:
            if pattern.matches(norm_path):
                ignored = not pattern.negate
        
        return ignored
    
    def find_nearest_ignore_file(self, start_dir: Optional[str] = None) -> Optional[str]:
        """
        Find the nearest .ast-grepignore file in the current or parent directories.
        
        Args:
            start_dir: Directory to start the search from
            
        Returns:
            Path to the ignore file if found, None otherwise
        """
        current_dir = Path(start_dir or os.getcwd())
        
        # Look for .ast-grepignore file in current and parent directories
        while current_dir != current_dir.parent:
            ignore_file = current_dir / '.ast-grepignore'
            if ignore_file.exists() and ignore_file.is_file():
                return str(ignore_file)
            current_dir = current_dir.parent
        
        return None
    
    def load_nearest_ignore_file(self, start_dir: Optional[str] = None) -> bool:
        """
        Load the nearest .ast-grepignore file.
        
        Args:
            start_dir: Directory to start the search from
            
        Returns:
            True if an ignore file was found and loaded, False otherwise
        """
        ignore_file = self.find_nearest_ignore_file(start_dir)
        if ignore_file:
            return self.load_file(ignore_file)
        return False 