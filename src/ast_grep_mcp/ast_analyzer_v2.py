"""
Enhanced AST analyzer using native metavariable extraction.

This is an improved version of ast_analyzer.py that uses ast-grep's native
metavariable capture API instead of complex regex patterns.
"""

import logging
import re
import os
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

from ast_grep_py import SgRoot

from .utils.error_handling import PatternValidationError
from .utils.result_cache import ResultCache
from .utils.pattern_suggestions import suggest_patterns, build_suggestion_message
from .utils.native_metavars import NativeMetavarExtractor


class AstAnalyzerV2:
    """Enhanced AST analyzer with native metavariable support."""
    
    def __init__(self, cache_size: int = 128, performance_config=None):
        """Initialize the analyzer with cache."""
        self.logger = logging.getLogger("ast_grep_mcp.ast_analyzer_v2")
        self.cache = ResultCache(maxsize=cache_size)
        self.metavar_extractor = NativeMetavarExtractor()
        self.performance_config = performance_config
        
        # Language mappings
        self.supported_languages = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts"],
            "tsx": [".tsx"],
            "go": [".go"],
            "rust": [".rs"],
            "c": [".c", ".h"],
            "lua": [".lua"]
        }
        
        self.language_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript", 
            ".tsx": "tsx",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".h": "c",
            ".lua": "lua"
        }
    
    def parse_code(self, code: str, language: str) -> Optional[SgRoot]:
        """Parse code into an AST root."""
        try:
            root = SgRoot(code, language)
            return root
        except Exception as e:
            self.logger.error(f"Failed to parse code: {e}")
            return None
    
    def find_patterns(
        self, 
        code: str, 
        language: str, 
        pattern: str
    ) -> List[Dict[str, Any]]:
        """
        Find all occurrences of a pattern in code using native metavariables.
        
        Args:
            code: Source code to search
            language: Programming language
            pattern: AST pattern to search for
            
        Returns:
            List of match dictionaries with metavariable captures
        """
        # Clean up pattern - remove any double $$ and replace with single $
        original_pattern = pattern
        pattern = self._normalize_pattern(pattern)
        
        root = self.parse_code(code, language)
        if not root:
            self.logger.warning(f"Failed to parse code for language: {language}")
            return []
        
        node = root.root()
        matches = []
        
        try:
            # Log pattern being used for debugging
            self.logger.debug(f"Language: {language}, Pattern: '{pattern}'")
            
            # Find all pattern matches
            found_matches = node.find_all(pattern=pattern)
            
            # Log number of matches found
            self.logger.debug(f"Found {len(found_matches)} matches for pattern '{pattern}'")
            
            for match in found_matches:
                # Get match range
                match_range = match.range()
                start_line = match_range.start.line + 1  # Convert to 1-based
                end_line = match_range.end.line + 1
                
                # Extract metavariables using native API
                metavariables = self.metavar_extractor.extract_metavariables(
                    match, pattern
                )
                
                match_info = {
                    "match": match.text(),
                    "location": {
                        "start": {
                            "line": start_line,
                            "column": match_range.start.column
                        },
                        "end": {
                            "line": end_line,
                            "column": match_range.end.column
                        }
                    },
                    "metavariables": metavariables
                }
                
                matches.append(match_info)
                
                # Check performance limits
                if self.performance_config and self.performance_config.max_results_per_file:
                    if len(matches) >= self.performance_config.max_results_per_file:
                        self.logger.warning(
                            f"Reached max results per file limit ({self.performance_config.max_results_per_file})"
                        )
                        break
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error finding patterns: {error_msg}")
            self.logger.error(f"Pattern: {pattern}")
            self.logger.error(f"Language: {language}")
            
            # Enhance error message with helpful context
            enhanced_error = self._enhance_error_message(error_msg, pattern, language, original_pattern)
            raise PatternValidationError(enhanced_error, pattern=pattern, language=language)
        
        return matches
    
    def _normalize_pattern(self, pattern: str) -> str:
        """Normalize pattern by fixing common issues."""
        original = pattern
        
        # Replace $$ with $ (common mistake)
        pattern = re.sub(r'\$\$(?!\$)', '$', pattern)
        
        # Note: Complex patterns like $NAME($$$PARAMS) often don't work well
        # with ast-grep. Simpler patterns like "async fn $NAME" are recommended.
        
        # Log if pattern was modified
        if original != pattern:
            self.logger.info(f"Pattern normalized from '{original}' to '{pattern}'")
        
        return pattern
    
    def _enhance_error_message(self, error_msg: str, pattern: str, language: str, original_pattern: str) -> str:
        """Enhance error message with helpful context and examples."""
        enhanced_msg = f"Pattern matching failed for {language}\n" + "=" * 50 + "\n\n"
        
        # Show the original and normalized patterns
        enhanced_msg += f"📥 Original Pattern: {original_pattern}\n"
        if pattern != original_pattern:
            enhanced_msg += f"🔄 Normalized Pattern: {pattern}\n"
        
        enhanced_msg += f"\n❌ Error: {error_msg}\n"
        
        # Analyze the pattern for common issues
        issues = []
        
        # Check for complex parameter patterns
        if "$$$PARAMS" in pattern and language in ["rust", "go"]:
            issues.append("• Complex parameter patterns like fn $NAME($$$PARAMS) often don't work well")
            issues.append("  Try simpler patterns: 'fn $NAME' or 'async fn $NAME'")
        
        # Check for missing syntax elements
        if language == "python" and any(kw in pattern for kw in ["def", "class", "if", "for"]) and ":" not in pattern:
            issues.append("• Python statements require colons (:)")
            issues.append("  Example: 'def $NAME($$$PARAMS):' not 'def $NAME($$$PARAMS)'")
        
        # Check for incorrect metavariable syntax
        if "$$" in original_pattern and "$$$" not in original_pattern:
            issues.append("• Found $$ - use $$$ for capturing multiple elements")
        
        # Language-specific advice
        if language == "rust":
            enhanced_msg += "\n💡 Rust Pattern Tips:\n"
            enhanced_msg += "  • Use 'fn $NAME' to match any function\n"
            enhanced_msg += "  • Use 'async fn $NAME' for async functions\n"
            enhanced_msg += "  • Use 'impl $TYPE' for impl blocks\n"
            enhanced_msg += "  • Avoid complex patterns with parameters\n"
        elif language == "javascript" or language == "typescript":
            enhanced_msg += "\n💡 JavaScript/TypeScript Pattern Tips:\n"
            enhanced_msg += "  • Use 'function $NAME($$$PARAMS) { $$$BODY }' for functions\n"
            enhanced_msg += "  • Use '($$$PARAMS) => $EXPR' for arrow functions\n"
            enhanced_msg += "  • Use 'class $NAME { $$$BODY }' for classes\n"
        elif language == "python":
            enhanced_msg += "\n💡 Python Pattern Tips:\n"
            enhanced_msg += "  • Use 'def $NAME($$$PARAMS):' for functions\n"
            enhanced_msg += "  • Use 'class $NAME:' for classes\n"
            enhanced_msg += "  • Remember colons after statements\n"
        
        if issues:
            enhanced_msg += "\n⚠️  Potential Issues:\n" + "\n".join(issues) + "\n"
        
        # Add a simple working example
        enhanced_msg += "\n✅ Try a simpler pattern first:\n"
        simple_patterns = {
            "rust": "fn $NAME",
            "python": "def $NAME",
            "javascript": "function $NAME",
            "typescript": "function $NAME",
            "go": "func $NAME",
            "c": "$TYPE $NAME",
            "lua": "function $NAME"
        }
        enhanced_msg += f"  {simple_patterns.get(language, '$NAME')}\n"
        
        return enhanced_msg
    
    def analyze_code(
        self, 
        code: str, 
        language: str, 
        pattern: str
    ) -> Dict[str, Any]:
        """
        Analyze code with a pattern and return matches or suggestions.
        
        Args:
            code: Source code to analyze
            language: Programming language
            pattern: Pattern to search for
            
        Returns:
            Analysis results with matches and suggestions
        """
        if language not in self.supported_languages:
            return {"error": f"Unsupported language: {language}"}
        
        try:
            matches = self.find_patterns(code, language, pattern)
            result = {
                "matches": matches,
                "count": len(matches),
                "pattern": pattern,
                "language": language,
            }
            
            # Add suggestions if no matches
            if not matches:
                suggestions = suggest_patterns(pattern, code, language)
                result["suggestions"] = suggestions
                result["suggestion_message"] = build_suggestion_message(
                    pattern, language, suggestions
                )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error analyzing code: {error_msg}")
            
            # Try to provide suggestions even on error
            try:
                suggestions = suggest_patterns(pattern, code, language)
                return {
                    "error": error_msg,
                    "suggestions": suggestions,
                    "suggestion_message": build_suggestion_message(
                        pattern, language, suggestions
                    )
                }
            except Exception:
                return {"error": error_msg}
    
    def apply_refactoring(
        self,
        code: str,
        language: str,
        pattern: str,
        replacement: str
    ) -> str:
        """
        Apply pattern-based refactoring using native metavariables.
        
        Args:
            code: Source code to refactor
            language: Programming language
            pattern: Pattern to search for
            replacement: Replacement pattern
            
        Returns:
            Refactored code
        """
        root = self.parse_code(code, language)
        if not root:
            return code
        
        node = root.root()
        
        try:
            # Find all matches
            matches = node.find_all(pattern=pattern)
            
            if not matches:
                self.logger.info("No matches found for refactoring")
                return code
            
            # Create edit operations
            edits = []
            for match in matches:
                # Extract metavariables
                metavars = self.metavar_extractor.extract_metavariables(
                    match, pattern
                )
                
                # Substitute into replacement
                new_text = self.metavar_extractor.substitute_metavariables(
                    replacement, metavars
                )
                
                # Create edit operation
                edit = match.replace(new_text)
                edits.append(edit)
            
            # Apply all edits
            if edits:
                result = node.commit_edits(edits)
                return result
            
        except Exception as e:
            self.logger.error(f"Error applying refactoring: {e}")
        
        return code
    
    def analyze_file(
        self, 
        file_path: Union[str, Path], 
        pattern: str
    ) -> Dict[str, Any]:
        """
        Analyze a file with a pattern.
        
        Args:
            file_path: Path to the file
            pattern: Pattern to search for
            
        Returns:
            Analysis results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        # Determine language from extension
        ext = file_path.suffix.lower()
        language = self.language_extensions.get(ext)
        
        if not language:
            return {"error": f"Unsupported file extension: {ext}"}
        
        try:
            code = file_path.read_text(encoding="utf-8")
            result = self.analyze_code(code, language, pattern)
            result["file"] = str(file_path)
            return result
        except Exception as e:
            return {"error": f"Error reading file: {e}"}
    
    def search_directory(
        self,
        directory: str,
        pattern: str,
        parallel: bool = True,
        max_workers: Optional[int] = None,
        file_filter: Optional[Callable[[Path], bool]] = None,
        batch_size: Optional[int] = None,
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
                "matches": {},
            }

        # Get all files in the directory
        files = self._collect_supported_files(directory, file_filter)

        num_files = len(files)
        self.logger.info(f"Found {num_files} files to search in {directory}")

        # For small number of files, sequential processing is faster
        if not parallel or num_files <= 50:
            self.logger.info(
                "Using sequential processing (less than 50 files or parallel disabled)"
            )
            all_results = {}
            total_matches = 0
            for file in files:
                file_path, matches, language = self._process_file(file, pattern)
                if matches:
                    # Check total results limit
                    if self.performance_config and self.performance_config.max_total_results:
                        if total_matches + len(matches) > self.performance_config.max_total_results:
                            # Truncate matches to stay under limit
                            remaining = self.performance_config.max_total_results - total_matches
                            if remaining > 0:
                                matches = matches[:remaining]
                                all_results[file_path] = {
                                    "matches": matches,
                                    "count": len(matches),
                                    "language": language,
                                    "truncated": True
                                }
                                total_matches += len(matches)
                            self.logger.warning(
                                f"Reached total results limit ({self.performance_config.max_total_results})"
                            )
                            break
                    
                    all_results[file_path] = {
                        "matches": matches,
                        "count": len(matches),
                        "language": language,
                    }
                    total_matches += len(matches)

            return {
                "directory": directory,
                "files_searched": num_files,
                "files_with_matches": len(all_results),
                "matches": all_results,
            }

        # Calculate optimal settings for parallel processing
        cpu_count = os.cpu_count() or 4

        # Limit max workers based on the number of files and CPUs
        if max_workers is None:
            if num_files < 100:
                max_workers = min(2, cpu_count)
            elif num_files < 500:
                max_workers = min(cpu_count - 1, 4)
            else:
                max_workers = min(cpu_count, 8)

        # Calculate batch size based on number of files and workers
        if batch_size is None:
            if num_files < 100:
                batch_size = max(5, math.ceil(num_files / max_workers))
            else:
                batch_size = max(10, math.ceil(num_files / (max_workers * 2)))

        # Create batches of files
        batches = [files[i : i + batch_size] for i in range(0, len(files), batch_size)]

        self.logger.info(
            f"Using parallel processing with {max_workers} workers, "
            f"{len(batches)} batches, {batch_size} files per batch"
        )

        # Process batches in parallel
        all_results = {}

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit batch jobs instead of individual files
            futures = [
                executor.submit(self._process_file_batch, batch, pattern)
                for batch in batches
            ]

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
            "matches": all_results,
        }

    def _collect_supported_files(
        self, directory: str, file_filter: Optional[Callable[[Path], bool]] = None
    ) -> List[str]:
        """
        Collect all supported files in a directory.

        Args:
            directory: Directory to search
            file_filter: Optional function to filter files (returns True to include)

        Returns:
            List of file paths
        """
        files = []

        # Walk the directory tree and collect files
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = Path(os.path.join(root, filename))
                
                # Check if extension is supported
                ext = file_path.suffix.lower()
                if ext in self.language_extensions:
                    # Apply optional filter
                    if file_filter is None or file_filter(file_path):
                        files.append(str(file_path))

        return files

    def _process_file(
        self, file_path: str, pattern: str
    ) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        Process a single file for pattern matching.

        Args:
            file_path: Path to the file to analyze
            pattern: Pattern to search for

        Returns:
            Tuple of (file_path, matches, language)
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        language = self.language_extensions.get(extension, "")

        if not language:
            return file_path, [], ""

        try:
            # Check file size if performance config is set
            if self.performance_config and self.performance_config.max_file_size:
                file_size = path.stat().st_size
                if file_size > self.performance_config.max_file_size:
                    self.logger.warning(
                        f"Skipping {file_path}: file size ({file_size} bytes) exceeds limit "
                        f"({self.performance_config.max_file_size} bytes)"
                    )
                    return file_path, [], language
            
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()

            matches = self.find_patterns(code, language, pattern)
            return file_path, matches, language
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return file_path, [], language

    def _process_file_batch(
        self, files: List[str], pattern: str
    ) -> Dict[str, Dict[str, Any]]:
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
                    "language": language,
                }

        return batch_results


# For backward compatibility
def create_analyzer(cache_size: int = 128) -> AstAnalyzerV2:
    """Create an enhanced analyzer instance."""
    return AstAnalyzerV2(cache_size)


if __name__ == "__main__":
    # Test the enhanced analyzer
    analyzer = create_analyzer()
    
    test_code = """
    def calculate_sum(a, b):
        result = a + b
        return result
    """
    
    # Test pattern matching
    pattern = "def $NAME($$$PARAMS):\n    $$$BODY"
    results = analyzer.analyze_code(test_code, "python", pattern)
    print("Analysis results:")
    print(results)
    
    # Test refactoring
    replacement = "def $NAME($$$PARAMS) -> int:\n    $$$BODY"
    refactored = analyzer.apply_refactoring(
        test_code, "python", pattern, replacement
    )
    print("\nRefactored code:")
    print(refactored)