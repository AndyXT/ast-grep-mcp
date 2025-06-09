"""
Enhanced search functionality with better token management and streaming support.
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
from dataclasses import dataclass
from collections import defaultdict
import time

from ..utils.error_handling import handle_errors


@dataclass
class SearchSummary:
    """Lightweight summary of search results."""
    total_files: int
    files_with_matches: int
    total_matches: int
    language_breakdown: Dict[str, int]
    top_files: List[Dict[str, Any]]
    search_time: float
    pattern: str
    directory: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "summary": {
                "total_files": self.total_files,
                "files_with_matches": self.files_with_matches,
                "total_matches": self.total_matches,
                "language_breakdown": self.language_breakdown,
                "top_files": self.top_files[:10],  # Limit to top 10
                "search_time": round(self.search_time, 2),
            },
            "search_info": {
                "pattern": self.pattern,
                "directory": self.directory,
            },
            "hints": {
                "next_steps": [
                    "Use search_directory() with specific file paths for details",
                    "Use search_stream() for progressive result loading",
                    "Add file_extensions filter to narrow results",
                ],
                "example": f"search_directory(directory='{self.top_files[0]['file']}', pattern='{self.pattern}')"
                if self.top_files else None
            }
        }


class SearchStream:
    """Streaming search results handler."""
    
    def __init__(self, search_id: str, pattern: str, directory: str):
        self.search_id = search_id
        self.pattern = pattern
        self.directory = directory
        self.results_queue = []
        self.is_complete = False
        self.total_processed = 0
        self.logger = logging.getLogger(__name__)
    
    def add_result(self, file_path: str, matches: List[Dict[str, Any]]):
        """Add a result to the stream."""
        self.results_queue.append({
            "file": file_path,
            "matches": matches,
            "match_count": len(matches)
        })
        self.total_processed += 1
    
    def get_next_batch(self, batch_size: int = 10) -> Dict[str, Any]:
        """Get next batch of results."""
        batch = self.results_queue[:batch_size]
        self.results_queue = self.results_queue[batch_size:]
        
        return {
            "search_id": self.search_id,
            "batch": batch,
            "has_more": len(self.results_queue) > 0 or not self.is_complete,
            "total_processed": self.total_processed,
            "is_complete": self.is_complete and len(self.results_queue) == 0
        }
    
    def complete(self):
        """Mark stream as complete."""
        self.is_complete = True


class EnhancedSearchMixin:
    """Mixin to add enhanced search capabilities to AstGrepTool."""
    
    def __init__(self):
        self._search_streams = {}
        self._search_cache = {}
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        from pathlib import Path
        
        file_ext = Path(file_path).suffix.lower()
        
        # Language mappings based on file extensions
        extension_map = {
            ".py": "python",
            ".js": "javascript", 
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript", 
            ".rs": "rust",
            ".go": "go",
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".cc": "cpp",
            ".hpp": "cpp",
            ".java": "java",
            ".kt": "kotlin",
            ".lua": "lua",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".scala": "scala",
            ".clj": "clojure",
            ".hs": "haskell"
        }
        
        return extension_map.get(file_ext)
    
    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for a language."""
        extension_map = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "rust": [".rs"],
            "go": [".go"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cxx", ".cc", ".hpp"],
            "java": [".java"],
            "kotlin": [".kt"],
            "lua": [".lua"],
            "ruby": [".rb"],
            "php": [".php"],
            "swift": [".swift"],
            "scala": [".scala"],
            "clojure": [".clj"],
            "haskell": [".hs"]
        }
        return extension_map.get(language, [])
    
    @handle_errors
    def search_summary(
        self,
        pattern: str,
        directory: str = ".",
        file_extensions: Optional[List[str]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a quick summary of search results without full match details.
        
        This is optimized for low token usage and provides an overview
        that helps decide where to search in detail.
        """
        start_time = time.time()
        
        # Validate inputs
        if not pattern:
            return {"error": "Pattern cannot be empty"}
        
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            if not dir_path.is_dir():
                return {"error": f"Path is not a directory: {directory}"}
        except Exception as e:
            return {"error": f"Invalid directory path: {directory} - {str(e)}"}
        
        # Determine file extensions
        if file_extensions is None and language:
            file_extensions = self._get_extensions_for_language(language)
        
        # Create file filter
        def file_filter(path: Path) -> bool:
            if self.ignore_handler.should_ignore(str(path)):
                return False
            
            if file_extensions:
                return path.suffix.lower() in file_extensions
            
            # If no extensions specified, check all supported files
            ext = path.suffix.lower()
            for exts in self.analyzer.supported_languages.values():
                if ext in exts:
                    return True
            return False
        
        # Collect summary data
        total_files = 0
        files_with_matches = 0
        total_matches = 0
        language_breakdown = defaultdict(int)
        file_match_data = []
        
        # Process files to gather summary
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file() or not file_filter(file_path):
                continue
            
            total_files += 1
            
            # Detect language
            ext = file_path.suffix.lower()
            file_language = None
            for lang, exts in self.analyzer.supported_languages.items():
                if ext in exts:
                    file_language = lang
                    language_breakdown[lang] += 1
                    break
            
            if not file_language:
                continue
            
            # Quick match count (without full details)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Use analyzer for quick match count
                matches = self.analyzer.analyze_code(
                    content, file_language, pattern
                )
                
                if matches and matches.get("matches"):
                    match_count = len(matches["matches"])
                    if match_count > 0:
                        files_with_matches += 1
                        total_matches += match_count
                        file_match_data.append({
                            "file": str(file_path.relative_to(dir_path)),
                            "matches": match_count,
                            "language": file_language
                        })
            except Exception as e:
                self.logger.debug(f"Error processing {file_path}: {e}")
                continue
        
        # Sort files by match count
        file_match_data.sort(key=lambda x: x["matches"], reverse=True)
        
        search_time = time.time() - start_time
        
        # Create summary with aggressive truncation to prevent token limits
        summary = SearchSummary(
            total_files=total_files,
            files_with_matches=files_with_matches,
            total_matches=total_matches,
            language_breakdown=dict(language_breakdown),
            top_files=file_match_data[:10],  # Reduced to top 10 files
            search_time=search_time,
            pattern=pattern,
            directory=str(dir_path)
        )
        
        result = summary.to_dict()
        
        # Add truncation info if we have many results
        if len(file_match_data) > 10:
            result["truncated"] = {
                "total_files_with_matches": len(file_match_data),
                "shown": 10,
                "suggestion": "Use search_stream() or search_directory() with specific directories for more results"
            }
        
        return result
    
    @handle_errors
    def search_stream(
        self,
        pattern: str,
        directory: str,
        file_extensions: Optional[List[str]] = None,
        language: Optional[str] = None,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Create a streaming search that returns results progressively.
        
        Returns a search_id that can be used to retrieve results in batches.
        """
        import uuid
        
        search_id = str(uuid.uuid4())
        
        # Create search stream
        stream = SearchStream(search_id, pattern, directory)
        self._search_streams[search_id] = stream
        
        # Start search in background (in real implementation, this would be async)
        # For now, we'll return the stream configuration
        return {
            "search_id": search_id,
            "status": "created",
            "config": {
                "pattern": pattern,
                "directory": directory,
                "file_extensions": file_extensions,
                "language": language,
                "page_size": page_size,
            },
            "usage": {
                "get_results": f"Use get_stream_results('{search_id}') to retrieve results",
                "example": f"results = get_stream_results('{search_id}', batch_size={page_size})"
            }
        }
    
    @handle_errors
    def get_stream_results(
        self,
        search_id: str,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Retrieve next batch of results from a search stream."""
        if search_id not in self._search_streams:
            return {"error": f"Search stream not found: {search_id}"}
        
        stream = self._search_streams[search_id]
        return stream.get_next_batch(batch_size)
    
    @handle_errors
    def search_files_only(
        self,
        pattern: str,
        directory: str = ".",
        file_extensions: Optional[List[str]] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for pattern and return only file paths with match counts.
        
        This is extremely lightweight and suitable for large codebases.
        """
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                return {"error": f"Directory not found: {directory}"}
            if not dir_path.is_dir():
                return {"error": f"Path is not a directory: {directory}"}
        except Exception as e:
            return {"error": f"Invalid directory path: {directory} - {str(e)}"}
        
        # Determine file extensions
        if file_extensions is None and language:
            file_extensions = self._get_extensions_for_language(language)
        
        results = []
        total_matches = 0
        
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Check extensions
            if file_extensions and file_path.suffix.lower() not in file_extensions:
                continue
            
            # Detect language if needed
            if language:
                file_lang = self._detect_language(str(file_path))
                if file_lang != language:
                    continue
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Detect language for this file
                file_lang = self._detect_language(str(file_path))
                if not file_lang:
                    continue
                
                # Use AST analyzer for proper pattern matching
                if hasattr(self, 'analyzer'):
                    try:
                        analysis_result = self.analyzer.analyze_code(content, file_lang, pattern)
                        if analysis_result and analysis_result.get("matches"):
                            match_count = len(analysis_result["matches"])
                            if match_count > 0:
                                total_matches += match_count
                                results.append({
                                    "file": str(file_path.relative_to(dir_path)),
                                    "match_count": match_count,
                                    "size": len(content),
                                    "lines": content.count('\n') + 1,
                                    "language": file_lang
                                })
                    except Exception:
                        # Fallback to simple regex for basic patterns
                        if any(char in pattern for char in ['$', '{', '}', '(', ')']):
                            # Skip AST patterns that can't be regex-matched
                            continue
                        else:
                            # Simple text search for literal patterns
                            import re
                            matches = list(re.finditer(re.escape(pattern), content, re.IGNORECASE))
                            if matches:
                                match_count = len(matches)
                                total_matches += match_count
                                results.append({
                                    "file": str(file_path.relative_to(dir_path)),
                                    "match_count": match_count,
                                    "size": len(content),
                                    "lines": content.count('\n') + 1,
                                    "language": file_lang
                                })
                else:
                    # Fallback: simple text search if no analyzer
                    if not any(char in pattern for char in ['$', '{', '}', '$$']):
                        import re
                        matches = list(re.finditer(re.escape(pattern), content, re.IGNORECASE))
                        if matches:
                            match_count = len(matches)
                            total_matches += match_count
                            results.append({
                                "file": str(file_path.relative_to(dir_path)),
                                "match_count": match_count,
                                "size": len(content),
                                "lines": content.count('\n') + 1,
                                "language": file_lang
                            })
            except Exception as e:
                # Log the error but continue processing other files
                if hasattr(self, 'logger'):
                    self.logger.debug(f"Error processing {file_path}: {e}")
                continue
        
        # Sort by match count and limit results to prevent token issues
        results.sort(key=lambda x: x["match_count"], reverse=True)
        
        # Limit to 50 files max to prevent token overflow
        limited_results = results[:50]
        
        response = {
            "pattern": pattern,
            "directory": str(dir_path),
            "total_files": len(limited_results),
            "total_matches": total_matches,
            "files": limited_results,
            "hint": "Use search_directory() with specific file paths for detailed matches"
        }
        
        # Add truncation info if needed
        if len(results) > 50:
            response["truncated"] = {
                "total_files_found": len(results),
                "shown": 50,
                "suggestion": "Use more specific directory or file_extensions filter"
            }
        
        return response