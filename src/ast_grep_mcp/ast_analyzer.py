from ast_grep_py import SgRoot
from typing import List, Dict, Any, Optional, Tuple, Callable, Iterable
from pathlib import Path
import multiprocessing
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
import math

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
        self.logger = logging.getLogger("ast_grep_mcp.analyzer")
    
    def parse_code(self, code: str, language: str) -> Optional[SgRoot]:
        """Parse code into an AST representation"""
        if language not in self.supported_languages:
            return None
        
        return SgRoot(code, language)
    
    def find_patterns(self, code: str, language: str, pattern: str) -> List[Dict[str, Any]]:
        """Find all occurrences of a pattern in the code"""
        root = self.parse_code(code, language)
        if not root:
            self.logger.error(f"Failed to parse code for language: {language}")
            return []
        
        node = root.root()
        try:
            matches = node.find_all(pattern=pattern)
            match_count = len(matches)
            
            # Log the pattern and match count for debugging
            self.logger.debug(f"Pattern '{pattern}' found {match_count} matches in {language} code")
            
            results = []
            for match in matches:
                match_text = match.text()
                match_range = match.range()
                
                # Create a result object with detailed information
                result = {
                    "text": match_text,
                    "location": {
                        "start": {
                            "line": match_range.start.line,
                            "column": match_range.start.column
                        },
                        "end": {
                            "line": match_range.end.line,
                            "column": match_range.end.column
                        }
                    }
                }
                
                results.append(result)
                
                # Log the first few matches for debugging
                if len(results) <= 3:
                    self.logger.debug(f"Match {len(results)}: {match_text[:50]}" + ("..." if len(match_text) > 50 else ""))
            
            return results
        except Exception as e:
            self.logger.error(f"Error in pattern matching: {str(e)}")
            self.logger.error(f"Pattern: '{pattern}'")
            self.logger.error(f"Language: {language}")
            # Return empty list on error
            return []
    
    def apply_refactoring(self, code: str, language: str, pattern: str, replacement: str) -> str:
        """Apply a pattern-based refactoring to the code"""
        root = self.parse_code(code, language)
        if not root:
            self.logger.error(f"Failed to parse code for language: {language}")
            return code
        
        node = root.root()
        
        try:
            # Find all matches
            matches = node.find_all(pattern=pattern)
            match_count = len(matches)
            
            self.logger.debug(f"Pattern '{pattern}' found {match_count} matches for refactoring")
            
            # Create edits for each match
            edits = []
            for match in matches:
                try:
                    edit = match.replace(replacement)
                    edits.append(edit)
                    
                    # Log the replacement for the first few matches
                    if len(edits) <= 3:
                        self.logger.debug(f"Replacement {len(edits)}: '{match.text()[:40]}...' -> '{replacement[:40]}...'")
                except Exception as e:
                    self.logger.error(f"Error creating replacement: {str(e)}")
            
            if not edits:
                self.logger.debug("No matches found or no valid edits created")
                return code
            
            # Apply all edits
            try:
                refactored_code = node.commit_edits(edits)
                self.logger.debug(f"Applied {len(edits)} edits to the code")
                return refactored_code
            except Exception as e:
                self.logger.error(f"Error applying edits: {str(e)}")
                return code
            
        except Exception as e:
            self.logger.error(f"Error in pattern matching for refactoring: {str(e)}")
            self.logger.error(f"Pattern: '{pattern}'")
            self.logger.error(f"Replacement: '{replacement}'")
            self.logger.error(f"Language: {language}")
            # Return original code on error
            return code
    
    def get_supported_languages(self) -> Dict[str, List[str]]:
        """Return a dictionary of supported languages and their file extensions"""
        return self.supported_languages
    
    def _process_file(self, file_path: str, pattern: str) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        Process a single file for pattern matching.
        
        This is a helper function for parallel processing.
        
        Args:
            file_path: Path to the file to analyze
            pattern: Pattern to search for
            
        Returns:
            Tuple of (file_path, matches, language)
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        language = None
        
        # Determine language from file extension
        for lang, exts in self.supported_languages.items():
            if extension in exts:
                language = lang
                break
        
        if not language:
            return file_path, [], ""
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            matches = self.find_patterns(code, language, pattern)
            return file_path, matches, language
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return file_path, [], language
    
    def _process_file_batch(self, files: List[str], pattern: str) -> Dict[str, Dict[str, Any]]:
        """
        Process a batch of files in a single process.
        
        Args:
            files: List of file paths to process
            pattern: Pattern to search for
            
        Returns:
            Dictionary of results with file paths as keys
        """
        batch_results = {}
        
        for file_path in files:
            file_path, matches, language = self._process_file(file_path, pattern)
            if matches:
                batch_results[file_path] = {
                    "matches": matches,
                    "count": len(matches),
                    "language": language
                }
        
        return batch_results
    
    def search_directory(
        self, 
        directory: str, 
        pattern: str, 
        parallel: bool = True,
        max_workers: Optional[int] = None,
        file_filter: Optional[Callable[[Path], bool]] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for pattern matches in all files in a directory.
        
        Args:
            directory: Directory to search
            pattern: Pattern to search for
            parallel: Whether to use parallel processing
            max_workers: Maximum number of worker processes (default: CPU count)
            file_filter: Optional function to filter files (returns True to include)
            batch_size: Number of files to process in each batch (None = auto-calculate)
            
        Returns:
            Dictionary with matches grouped by file
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return {
                "error": f"Directory '{directory}' does not exist or is not a directory",
                "matches": {}
            }
        
        # Get all files in the directory
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = Path(os.path.join(root, filename))
                extension = file_path.suffix.lower()
                
                # Check if file has a supported extension
                is_supported = any(
                    extension in exts for exts in self.supported_languages.values()
                )
                
                # Apply custom filter if provided
                if is_supported and (file_filter is None or file_filter(file_path)):
                    files.append(str(file_path))
        
        num_files = len(files)
        self.logger.info(f"Found {num_files} files to search in {directory}")
        
        # For small number of files, sequential processing is faster
        # Only use parallel for larger file sets
        if not parallel or num_files <= 50:
            self.logger.info("Using sequential processing (less than 50 files or parallel disabled)")
            all_results = {}
            for file in files:
                file_path, matches, language = self._process_file(file, pattern)
                if matches:
                    all_results[file_path] = {
                        "matches": matches,
                        "count": len(matches),
                        "language": language
                    }
            
            return {
                "directory": directory,
                "files_searched": num_files,
                "files_with_matches": len(all_results),
                "matches": all_results
            }
        
        # Calculate optimal settings for parallel processing
        cpu_count = os.cpu_count() or 4
        
        # Limit max workers based on the number of files and CPUs
        if max_workers is None:
            # Use fewer workers for smaller file sets
            if num_files < 100:
                max_workers = min(2, cpu_count)
            elif num_files < 500:
                max_workers = min(cpu_count - 1, 4)
            else:
                max_workers = min(cpu_count, 8)
        
        # Calculate batch size based on number of files and workers
        if batch_size is None:
            # Process multiple files per worker to reduce overhead
            if num_files < 100:
                batch_size = max(5, math.ceil(num_files / max_workers))
            else:
                batch_size = max(10, math.ceil(num_files / (max_workers * 2)))
        
        # Create batches of files
        batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
        
        self.logger.info(
            f"Using parallel processing with {max_workers} workers, "
            f"{len(batches)} batches, {batch_size} files per batch"
        )
        
        # Process batches in parallel
        all_results = {}
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit batch jobs instead of individual files
            futures = [executor.submit(self._process_file_batch, batch, pattern) for batch in batches]
            
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    all_results.update(batch_results)
                except Exception as e:
                    self.logger.error(f"Error processing batch: {str(e)}")
        
        return {
            "directory": directory,
            "files_searched": num_files,
            "files_with_matches": len(all_results),
            "matches": all_results
        }