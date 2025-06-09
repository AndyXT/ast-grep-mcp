"""
Unified search interface with smart defaults and progressive disclosure.

This addresses the user feedback about having too many overlapping search tools.
Instead of 8+ different search methods, this provides a clear, unified interface.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from ..utils.error_handling import handle_errors
from .improved_validation import validate_pattern_with_suggestions


class UnifiedSearchMixin:
    """Mixin providing a unified search interface with smart defaults."""
    
    @handle_errors
    def search(
        self,
        pattern: str,
        directory: str = ".",
        language: Optional[str] = None,
        mode: str = "auto",
        max_results: int = 100,
        include_context: bool = False,
        file_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Unified search with smart defaults and automatic mode selection.
        
        This replaces the confusing array of search_* functions with one clear interface.
        
        Args:
            pattern: Pattern to search for (AST pattern or text)
            directory: Directory to search in
            language: Programming language (auto-detected if None)
            mode: Search mode - "auto", "summary", "detailed", "streaming"
            max_results: Maximum number of results to return
            include_context: Whether to include context lines around matches
            file_extensions: Specific file extensions to search
            
        Returns:
            Unified search results with suggestions for next steps
        """
        # Validate pattern and provide suggestions if there are issues
        validation = validate_pattern_with_suggestions(
            pattern, language, directory, getattr(self, 'logger', None)
        )
        
        # If pattern has critical errors, return validation results
        if not validation["valid"]:
            return {
                "error": "Pattern validation failed",
                "validation": validation,
                "pattern": pattern,
                "suggestions": validation.get("suggestions", []),
                "help": validation.get("help", "")
            }
        
        # Auto-detect language if not specified
        if not language:
            language = self._auto_detect_language(directory, file_extensions)
        
        # Choose search mode automatically if "auto"
        if mode == "auto":
            mode = self._choose_optimal_mode(directory, pattern, max_results)
        
        search_params = {
            "pattern": pattern,
            "directory": directory,
            "language": language,
            "file_extensions": file_extensions or self._get_extensions_for_language(language) if language else None
        }
        
        # Execute search based on mode
        if mode == "summary":
            result = self._execute_summary_search(**search_params)
        elif mode == "detailed":
            result = self._execute_detailed_search(include_context=include_context, **search_params)
        elif mode == "streaming":
            result = self._execute_streaming_search(max_results=max_results, **search_params)
        else:
            # Default to summary for unknown modes
            result = self._execute_summary_search(**search_params)
        
        # Enhance result with metadata and suggestions
        result = self._enhance_search_result(result, pattern, directory, language, mode)
        
        # Add pattern validation warnings if any
        if validation.get("warnings") or validation.get("suggestions"):
            result["pattern_validation"] = {
                "warnings": validation.get("warnings", []),
                "suggestions": validation.get("suggestions", []),
                "examples": validation.get("examples", [])
            }
        
        return result
    
    @handle_errors
    def search_direct(
        self,
        pattern: str,
        directory: str = ".",
        language: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Direct search that always returns results immediately (never streaming).
        
        Use this when you want guaranteed direct results without streaming complexity.
        """
        # Force summary mode for direct results
        return self.search(
            pattern=pattern,
            directory=directory,
            language=language,
            mode="summary",  # Always direct results
            max_results=max_results
        )
    
    @handle_errors
    def analyze_project(self, directory: str = ".") -> Dict[str, Any]:
        """
        High-level project analysis with guided next steps.
        
        This is the entry point for users who want to understand a codebase.
        """
        # Enhanced project analysis
        if hasattr(self, 'project_analyzer'):
            project_info = self.project_analyzer.analyze_project_structure_enhanced(directory)
        else:
            # Fallback to basic analysis
            project_info = self._basic_project_analysis(directory)
        
        # Generate smart recommendations
        recommendations = self._generate_analysis_recommendations(project_info)
        
        return {
            "project_overview": project_info,
            "recommended_searches": recommendations,
            "quick_start_guide": self._get_quick_start_guide(project_info),
            "usage_examples": self._get_usage_examples(project_info)
        }
    
    @handle_errors
    def search_functions(
        self,
        directory: str = ".",
        language: Optional[str] = None,
        async_only: bool = False,
        public_only: bool = False,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simplified function search with automatic fallbacks.
        
        This replaces the broken find_functions() with a more reliable implementation.
        """
        # Use custom pattern if provided, otherwise build smart pattern
        if pattern:
            search_pattern = pattern
        else:
            search_pattern = self._build_smart_function_pattern(language, async_only, public_only)
        
        # CRITICAL FIX: Force direct results for function search
        # Users expect actual function data, not streaming metadata
        result = self.search(
            pattern=search_pattern,
            directory=directory,
            language=language,
            mode="summary",  # Force direct results
            max_results=50
        )
        
        # Transform to function-specific format
        return self._transform_to_function_result(result, async_only, public_only)
    
    def _auto_detect_language(self, directory: str, file_extensions: Optional[List[str]]) -> Optional[str]:
        """Auto-detect the primary language in a directory."""
        try:
            # CRITICAL FIX: Properly resolve relative paths from current working directory
            if directory == "." or directory == "./":
                dir_path = Path.cwd()
            elif directory.startswith("./"):
                dir_path = Path.cwd() / directory[2:]
            elif not Path(directory).is_absolute():
                dir_path = Path.cwd() / directory
            else:
                dir_path = Path(directory)
            
            dir_path = dir_path.resolve()
            
            if not dir_path.exists():
                if hasattr(self, 'logger') and self.logger:
                    self.logger.warning(f"Directory does not exist for language detection: {directory} -> {dir_path}")
                    self.logger.warning(f"Current working directory: {Path.cwd()}")
                return None
            
            # Log directory being analyzed for debugging
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"Auto-detecting language in: {dir_path}")
            
            # Use enhanced project analyzer if available for better detection
            if hasattr(self, 'project_analyzer'):
                analysis = self.project_analyzer.analyze_project_structure_enhanced(str(dir_path))
                if "error" in analysis:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.warning(f"Project analysis failed: {analysis['error']}")
                elif "primary_language" in analysis and analysis["primary_language"]:
                    detected_lang = analysis["primary_language"]
                    if hasattr(self, 'logger') and self.logger:
                        confidence = analysis.get("language_confidence", 0)
                        self.logger.info(f"Enhanced analyzer detected {detected_lang} with {confidence:.1%} confidence")
                    return detected_lang
            
            # Fallback to simple extension counting
            if hasattr(self, 'logger') and self.logger:
                self.logger.info("Using fallback extension-based language detection")
                
            extension_counts = {}
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
            
            # Map extensions to languages
            ext_to_lang = {
                ".py": "python",
                ".rs": "rust", 
                ".js": "javascript",
                ".jsx": "javascript",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".go": "go",
                ".c": "c",
                ".h": "c",
                ".cpp": "cpp",
                ".java": "java"
            }
            
            # Find most common language
            lang_counts = {}
            for ext, count in extension_counts.items():
                if ext in ext_to_lang:
                    lang = ext_to_lang[ext]
                    lang_counts[lang] = lang_counts.get(lang, 0) + count
            
            if lang_counts:
                detected_lang = max(lang_counts, key=lang_counts.get)
                if hasattr(self, 'logger') and self.logger:
                    self.logger.info(f"Fallback detection found {detected_lang} ({lang_counts[detected_lang]} files)")
                return detected_lang
            
            if hasattr(self, 'logger') and self.logger:
                self.logger.warning(f"No recognizable code files found in {dir_path}")
            return None
            
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Language detection failed for {directory}: {e}")
            return None
    
    def _choose_optimal_mode(self, directory: str, pattern: str, max_results: int) -> str:
        """Choose the optimal search mode based on context."""
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                return "summary"
            
            # Count total files (with limit to prevent hanging)
            file_count = 0
            try:
                for f in dir_path.rglob("*"):
                    if f.is_file():
                        file_count += 1
                        # Stop counting at 15000 to prevent delays
                        if file_count > 15000:
                            break
            except Exception:
                file_count = 0
            
            # CRITICAL FIX: Always default to direct results unless clearly needed
            # Only use streaming for genuinely large codebases or user explicitly requests it
            if file_count > 15000 and max_results > 1000:
                return "streaming"
            else:
                return "summary"  # Always prefer direct results
                
        except Exception:
            return "summary"  # Direct results as safe default
    
    def _execute_summary_search(self, **params) -> Dict[str, Any]:
        """Execute a summary search."""
        if hasattr(self, 'search_summary'):
            return self.search_summary(**params)
        else:
            return {"error": "Summary search not available"}
    
    def _execute_detailed_search(self, include_context: bool = False, **params) -> Dict[str, Any]:
        """Execute a detailed search."""
        if include_context and hasattr(self, 'search_directory_with_context'):
            return self.search_directory_with_context(**params)
        elif hasattr(self, 'search_directory'):
            return self.search_directory(**params)
        else:
            return {"error": "Detailed search not available"}
    
    def _execute_streaming_search(self, max_results: int, **params) -> Dict[str, Any]:
        """Execute a streaming search."""
        if hasattr(self, 'streaming_engine'):
            stream_result = self.streaming_engine.create_search_stream(**params)
            # Add clear warning and instructions
            if "stream_id" in stream_result:
                stream_result["warning"] = "This search uses streaming. Use get_search_stream_chunk() to retrieve results."
                stream_result["usage"] = f"get_search_stream_chunk('{stream_result['stream_id']}')"
                stream_result["alternative"] = "For direct results, use mode='summary' or mode='detailed'"
            return stream_result
        elif hasattr(self, 'search_stream'):
            stream_result = self.search_stream(**params)
            if "search_id" in stream_result:
                stream_result["warning"] = "This search uses streaming. Use get_stream_results() to retrieve results."
                stream_result["usage"] = f"get_stream_results('{stream_result['search_id']}')"
                stream_result["alternative"] = "For direct results, use mode='summary' or mode='detailed'"
            return stream_result
        else:
            # Fallback to summary for direct results
            return self._execute_summary_search(**params)
    
    def _enhance_search_result(
        self,
        result: Dict[str, Any],
        pattern: str,
        directory: str,
        language: Optional[str],
        mode: str
    ) -> Dict[str, Any]:
        """Enhance search results with metadata and suggestions."""
        if "error" in result:
            return result
        
        # Add search metadata
        result["search_metadata"] = {
            "pattern": pattern,
            "directory": directory,
            "language": language,
            "mode": mode
        }
        
        # Add suggestions for next steps
        suggestions = []
        
        total_matches = result.get("summary", {}).get("total_matches", 0) or result.get("total_matches", 0)
        
        if total_matches == 0:
            suggestions.extend([
                "Try a simpler pattern (e.g., 'fn $NAME' instead of complex patterns)",
                "Verify the directory contains files in the expected language",
                "Use analyze_project() to understand the codebase structure first"
            ])
        elif total_matches > 100 and mode != "streaming":
            suggestions.extend([
                "Consider using streaming mode for large result sets",
                "Narrow your search with more specific patterns",
                "Add file_extensions filter to limit scope"
            ])
        elif mode == "summary" and total_matches > 0:
            suggestions.extend([
                "Use mode='detailed' to see full match details",
                "Try search_functions() for structured function analysis",
                "Use include_context=True to see surrounding code"
            ])
        
        if suggestions:
            result["next_steps"] = suggestions
        
        return result
    
    def _build_smart_function_pattern(
        self,
        language: Optional[str],
        async_only: bool,
        public_only: bool
    ) -> str:
        """Build a smart function pattern that's likely to work."""
        if language == "rust":
            if async_only:
                return "pub async fn $NAME" if public_only else "async fn $NAME"
            else:
                return "pub fn $NAME" if public_only else "fn $NAME"
        elif language == "python":
            return "async def $NAME" if async_only else "def $NAME"
        elif language in ["javascript", "typescript"]:
            return "async function $NAME" if async_only else "function $NAME"
        else:
            # Generic fallback
            return "function $NAME" if not async_only else "async function $NAME"
    
    def _transform_to_function_result(
        self,
        search_result: Dict[str, Any],
        async_only: bool,
        public_only: bool
    ) -> Dict[str, Any]:
        """Transform unified search result to function-specific format."""
        if "error" in search_result:
            return search_result
        
        # Extract function count from search results
        summary = search_result.get("summary", {})
        total_functions = summary.get("total_matches", 0)
        
        return {
            "functions_found": total_functions,
            "search_mode": search_result.get("search_metadata", {}).get("mode", "unknown"),
            "pattern_used": search_result.get("search_metadata", {}).get("pattern", "unknown"),
            "files_searched": summary.get("total_files", 0),
            "files_with_functions": summary.get("files_with_matches", 0),
            "top_files": summary.get("top_files", [])[:10],
            "filters_applied": {
                "async_only": async_only,
                "public_only": public_only
            },
            "suggestions": search_result.get("next_steps", []),
            "raw_search_result": search_result  # Include full result for debugging
        }
    
    def _generate_analysis_recommendations(self, project_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate smart recommendations based on project analysis."""
        recommendations = []
        
        primary_language = project_info.get("primary_language")
        if primary_language:
            recommendations.append({
                "action": f"search_functions(language='{primary_language}')",
                "description": f"Find all {primary_language} functions in the project",
                "why": "Get an overview of the codebase structure"
            })
            
            if primary_language == "rust":
                recommendations.append({
                    "action": "search('unsafe { $$$CODE }', language='rust')",
                    "description": "Find unsafe code blocks",
                    "why": "Identify potentially risky code sections"
                })
            elif primary_language == "python":
                recommendations.append({
                    "action": "search('def $NAME($$$ARGS) -> $RET', language='python')",
                    "description": "Find functions with type annotations",
                    "why": "Assess code quality and documentation"
                })
        
        # Add general recommendations
        recommendations.append({
            "action": "search('TODO', mode='summary')",
            "description": "Find all TODO comments",
            "why": "Identify pending work and technical debt"
        })
        
        return recommendations
    
    def _get_quick_start_guide(self, project_info: Dict[str, Any]) -> List[str]:
        """Get a quick start guide based on project type."""
        primary_language = project_info.get("primary_language", "unknown")
        
        guide = [
            "1. Start with: analyze_project() to understand the codebase",
            f"2. Find functions: search_functions(language='{primary_language}')",
            "3. Search for patterns: search('your_pattern_here')", 
            "4. For large results: search(mode='streaming')",
            "5. Get help: Each result includes 'next_steps' suggestions"
        ]
        
        return guide
    
    def _get_usage_examples(self, project_info: Dict[str, Any]) -> Dict[str, str]:
        """Get usage examples tailored to the project."""
        primary_language = project_info.get("primary_language", "unknown")
        
        examples = {
            "Basic search": f"search('fn $NAME', language='{primary_language}')",
            "Function analysis": f"search_functions(language='{primary_language}')",
            "TODO hunting": "search('TODO', mode='summary')",
            "Project overview": "analyze_project()"
        }
        
        if primary_language == "rust":
            examples.update({
                "Find async functions": "search_functions(async_only=True)",
                "Security scan": "search('unwrap()', mode='summary')"
            })
        elif primary_language == "python":
            examples.update({
                "Find classes": "search('class $NAME', mode='detailed')",
                "Error handling": "search('except $EXCEPTION:', mode='summary')"
            })
        
        return examples
    
    def _basic_project_analysis(self, directory: str) -> Dict[str, Any]:
        """Basic project analysis fallback."""
        try:
            # CRITICAL FIX: Use same directory resolution as _auto_detect_language
            if directory == "." or directory == "./":
                dir_path = Path.cwd()
            elif directory.startswith("./"):
                dir_path = Path.cwd() / directory[2:]
            elif not Path(directory).is_absolute():
                dir_path = Path.cwd() / directory
            else:
                dir_path = Path(directory)
            
            dir_path = dir_path.resolve()
            
            # Add validation and logging
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"Running basic project analysis on: {dir_path}")
                self.logger.info(f"Current working directory: {Path.cwd()}")
            
            if not dir_path.exists():
                return {
                    "error": f"Directory does not exist: {directory} -> {dir_path}",
                    "requested_directory": directory,
                    "resolved_directory": str(dir_path),
                    "current_working_directory": str(Path.cwd())
                }
            
            if not dir_path.is_dir():
                return {
                    "error": f"Path exists but is not a directory: {directory} -> {dir_path}",
                    "requested_directory": directory,
                    "resolved_directory": str(dir_path)
                }
            
            file_count = sum(1 for f in dir_path.rglob("*") if f.is_file())
            detected_language = self._auto_detect_language(directory, None)
            
            result = {
                "directory": str(dir_path),
                "requested_directory": directory,
                "total_files": file_count,
                "primary_language": detected_language,
                "analysis_type": "basic",
                "diagnostic_info": {
                    "working_directory": str(Path.cwd()),
                    "directory_validation": "passed",
                    "language_detection_method": "fallback_extension_counting"
                }
            }
            
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"Basic analysis complete: {file_count} files, detected {detected_language}")
            
            return result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "requested_directory": directory,
                "analysis_type": "basic",
                "diagnostic_info": {
                    "working_directory": str(Path.cwd()),
                    "error_type": type(e).__name__
                }
            }
            
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Basic project analysis failed for {directory}: {e}")
            
            return error_result