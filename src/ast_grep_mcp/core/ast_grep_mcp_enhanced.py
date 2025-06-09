"""
Enhanced AstGrepMCP class with improved token management and convenience functions.
"""

from typing import Dict, Any, Optional, List

from .ast_grep_mcp import AstGrepMCP
from ..utils.search_enhancements import EnhancedSearchMixin
from ..utils.pattern_wizard import PatternWizard
from ..utils.convenience_functions import ConvenienceFunctionsMixin
from ..utils.enhanced_error_handling import (
    enhanced_error_handler,
    TokenLimitError,
    PatternSyntaxError,
)
from ..utils.enhanced_project_analysis import EnhancedProjectAnalyzer
from ..utils.real_streaming import StreamingSearchEngine, StreamingSecurityAuditor
from ..utils.pattern_debugging import PatternDebugger
from ..utils.unified_search import UnifiedSearchMixin
from ..utils.project_diagnostic import ProjectDiagnostic


class AstGrepMCPEnhanced(AstGrepMCP, EnhancedSearchMixin, ConvenienceFunctionsMixin, UnifiedSearchMixin):
    """Enhanced AST Grep MCP with better token management and usability."""
    
    def __init__(self, config=None):
        super().__init__(config)
        
        # Initialize enhanced components
        EnhancedSearchMixin.__init__(self)
        self.pattern_wizard_instance = PatternWizard(self.logger)
        self.project_analyzer = EnhancedProjectAnalyzer(self.logger)
        self.streaming_engine = StreamingSearchEngine(self.analyzer, self.logger)
        self.security_auditor = StreamingSecurityAuditor(self.streaming_engine)
        self.pattern_debugger = PatternDebugger(self.analyzer, self.logger)
        self.project_diagnostic = ProjectDiagnostic(self.logger)
        
        # Override token limits for better performance and reliability
        self.paginator.TOKEN_LIMITS = {
            "default": 8000,   # Much more conservative
            "search": 5000,    # Very conservative for searches
            "analysis": 6000,  # Conservative for analysis  
            "minimal": 2000,   # Very small for basic operations
            "summary": 1500,   # Extra small for summaries
        }
        
        # Register enhanced tools
        self._register_enhanced_tools()
    
    def _register_enhanced_tools(self):
        """Register enhanced tools with better error handling."""
        
        # Enhanced search functions
        @self.mcp.tool(
            name="search_summary",
            description="Get a lightweight summary of search results without full match details"
        )
        @enhanced_error_handler("summary")
        def search_summary_tool(
            pattern: str,
            directory: str = ".",
            file_extensions: Optional[List[str]] = None,
            language: Optional[str] = None,
        ) -> Dict[str, Any]:
            return self.search_summary(pattern, directory, file_extensions, language)
        
        @self.mcp.tool(
            name="search_stream",
            description="Create a streaming search for progressive result loading"
        )
        @enhanced_error_handler("minimal")
        def search_stream_tool(
            pattern: str,
            directory: str,
            file_extensions: Optional[List[str]] = None,
            language: Optional[str] = None,
            page_size: int = 10,
        ) -> Dict[str, Any]:
            return self.search_stream(pattern, directory, file_extensions, language, page_size)
        
        @self.mcp.tool(
            name="get_stream_results",
            description="Get next batch of results from a search stream"
        )
        @enhanced_error_handler("minimal")
        def get_stream_results_tool(
            search_id: str,
            batch_size: int = 10
        ) -> Dict[str, Any]:
            return self.get_stream_results(search_id, batch_size)
        
        @self.mcp.tool(
            name="search_files_only",
            description="Search and return only file paths with match counts (lightweight)"
        )
        @enhanced_error_handler("minimal")
        def search_files_only_tool(
            pattern: str,
            directory: str = ".",
            file_extensions: Optional[List[str]] = None,
            language: Optional[str] = None,
        ) -> Dict[str, Any]:
            return self.search_files_only(pattern, directory, file_extensions, language)
        
        # Pattern wizard
        @self.mcp.tool(
            name="pattern_wizard",
            description="Generate pattern suggestions from natural language description"
        )
        @enhanced_error_handler("default")
        def pattern_wizard_tool(
            description: str,
            language: str,
            examples: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            return self.pattern_wizard_instance.pattern_wizard(description, language, examples)
        
        @self.mcp.tool(
            name="explain_pattern", 
            description="Get detailed explanation of what a pattern does"
        )
        @enhanced_error_handler("default")
        def explain_pattern_tool(
            pattern: str,
            language: str
        ) -> Dict[str, Any]:
            return self.pattern_wizard_instance.explain_pattern(pattern, language)
        
        # Convenience functions
        @self.mcp.tool(
            name="find_functions",
            description="Find function definitions with various filters"
        )
        @enhanced_error_handler("search")
        def find_functions_tool(
            directory: str = ".",
            language: Optional[str] = None,
            async_only: bool = False,
            public_only: bool = False,
            name_pattern: Optional[str] = None,
            return_type: Optional[str] = None,
        ) -> Dict[str, Any]:
            return self.find_functions(
                directory, language, async_only, public_only, name_pattern, return_type
            )
        
        @self.mcp.tool(
            name="find_classes",
            description="Find class/struct definitions"
        )
        @enhanced_error_handler("search")
        def find_classes_tool(
            directory: str = ".",
            language: Optional[str] = None,
            with_inheritance: bool = False,
            name_pattern: Optional[str] = None,
        ) -> Dict[str, Any]:
            return self.find_classes(directory, language, with_inheritance, name_pattern)
        
        @self.mcp.tool(
            name="find_todos_and_fixmes",
            description="Find TODO, FIXME, and other code comments"
        )
        @enhanced_error_handler("search")
        def find_todos_tool(
            directory: str = ".",
            include_patterns: Optional[List[str]] = None,
            case_sensitive: bool = False,
        ) -> Dict[str, Any]:
            return self.find_todos_and_fixmes(directory, include_patterns, case_sensitive)
        
        @self.mcp.tool(
            name="find_potential_bugs",
            description="Find potential bugs and code smells"
        )
        @enhanced_error_handler("search")
        def find_bugs_tool(
            directory: str = ".",
            language: Optional[str] = None,
            bug_patterns: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            return self.find_potential_bugs(directory, language, bug_patterns)
        
        @self.mcp.tool(
            name="find_imports",
            description="Find import statements"
        )
        @enhanced_error_handler("search")
        def find_imports_tool(
            directory: str = ".",
            language: Optional[str] = None,
            module_name: Optional[str] = None,
            unused: bool = False,
        ) -> Dict[str, Any]:
            return self.find_imports(directory, language, module_name, unused)
        
        # Enhanced project analysis
        @self.mcp.tool(
            name="analyze_project_structure_enhanced",
            description="Enhanced project structure analysis with better language detection"
        )
        @enhanced_error_handler("analysis")
        def analyze_project_enhanced_tool(
            directory: str
        ) -> Dict[str, Any]:
            return self.project_analyzer.analyze_project_structure_enhanced(directory)
        
        # Real streaming search
        @self.mcp.tool(
            name="create_real_search_stream",
            description="Create real streaming search for large codebases"
        )
        @enhanced_error_handler("minimal")
        def create_real_stream_tool(
            pattern: str,
            directory: str,
            language: Optional[str] = None,
            file_extensions: Optional[List[str]] = None,
            chunk_size: int = 10
        ) -> Dict[str, Any]:
            return self.streaming_engine.create_search_stream(
                pattern, directory, language, file_extensions, chunk_size
            )
        
        @self.mcp.tool(
            name="get_search_stream_chunk",
            description="Get next chunk from real search stream"
        )
        @enhanced_error_handler("minimal")
        def get_stream_chunk_tool(
            stream_id: str,
            timeout: float = 30.0
        ) -> Dict[str, Any]:
            return self.streaming_engine.get_stream_chunk(stream_id, timeout)
        
        @self.mcp.tool(
            name="get_search_stream_progress",
            description="Get progress of real search stream"
        )
        @enhanced_error_handler("minimal")
        def get_stream_progress_tool(
            stream_id: str
        ) -> Dict[str, Any]:
            return self.streaming_engine.get_stream_progress(stream_id)
        
        # Streaming security audit
        @self.mcp.tool(
            name="run_security_audit_streaming",
            description="Run security audit with streaming results for large codebases"
        )
        @enhanced_error_handler("minimal")
        def security_audit_streaming_tool(
            directory: str,
            language: str,
            chunk_size: int = 5,
            severity_filter: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            return self.security_auditor.run_security_audit_streaming(
                directory, language, chunk_size, severity_filter
            )
        
        # Pattern debugging
        @self.mcp.tool(
            name="debug_pattern_matching",
            description="Debug why a pattern doesn't match and get suggestions"
        )
        @enhanced_error_handler("default")
        def debug_pattern_tool(
            code: str,
            pattern: str,
            language: str,
            max_partial_matches: int = 5
        ) -> Dict[str, Any]:
            return self.pattern_debugger.debug_pattern_matching(
                code, pattern, language, max_partial_matches
            )
        
        # Unified search tools (addressing user feedback about too many overlapping tools)
        @self.mcp.tool(
            name="search",
            description="Unified search with smart defaults - replaces confusing array of search_* functions"
        )
        @enhanced_error_handler("search")
        def unified_search_tool(
            pattern: str,
            directory: str = ".",
            language: Optional[str] = None,
            mode: str = "auto",
            max_results: int = 100,
            include_context: bool = False,
            file_extensions: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            return self.search(
                pattern, directory, language, mode, max_results, include_context, file_extensions
            )
        
        @self.mcp.tool(
            name="analyze_project",
            description="High-level project analysis with guided next steps - start here for new codebases"
        )
        @enhanced_error_handler("analysis")
        def analyze_project_tool(
            directory: str = "."
        ) -> Dict[str, Any]:
            return self.analyze_project(directory)
        
        @self.mcp.tool(
            name="search_functions",
            description="Improved function search with automatic fallbacks - replaces broken find_functions"
        )
        @enhanced_error_handler("search")
        def search_functions_tool(
            directory: str = ".",
            language: Optional[str] = None,
            async_only: bool = False,
            public_only: bool = False,
            pattern: Optional[str] = None
        ) -> Dict[str, Any]:
            return self.search_functions(directory, language, async_only, public_only, pattern)
        
        @self.mcp.tool(
            name="search_direct",
            description="Direct search that always returns results immediately (never streaming) - use for simple searches"
        )
        @enhanced_error_handler("search")
        def search_direct_tool(
            pattern: str,
            directory: str = ".",
            language: Optional[str] = None,
            max_results: int = 50
        ) -> Dict[str, Any]:
            return self.search_direct(pattern, directory, language, max_results)
        
        # Project diagnostic tools
        @self.mcp.tool(
            name="diagnose_directory",
            description="Diagnose directory and language detection issues - use when tool analyzes wrong directory"
        )
        @enhanced_error_handler("default")
        def diagnose_directory_tool(
            directory: str,
            expected_language: Optional[str] = None,
            expected_project_type: Optional[str] = None
        ) -> Dict[str, Any]:
            return self.project_diagnostic.diagnose_directory_detection(
                directory, expected_language, expected_project_type
            )
        
        @self.mcp.tool(
            name="validate_search_setup",
            description="Validate search directory and parameters before running search"
        )
        @enhanced_error_handler("default")
        def validate_search_tool(
            directory: str,
            pattern: str,
            language: Optional[str] = None
        ) -> Dict[str, Any]:
            return self.project_diagnostic.validate_search_directory(directory, pattern, language)
    
    # Override the main search_directory to add better error handling and auto-pagination
    @enhanced_error_handler("search")
    def search_directory(self, *args, **kwargs):
        """Enhanced search_directory with better error handling and auto-pagination."""
        # Force smaller page sizes to prevent token issues
        if 'page_size' not in kwargs:
            kwargs['page_size'] = 3  # Very small default
        elif kwargs.get('page_size', 10) > 5:
            kwargs['page_size'] = 5  # Cap at 5
        
        # Force max_results limit if not specified
        if 'max_results' not in kwargs:
            kwargs['max_results'] = 10  # Hard limit on results
        
        try:
            # First try with the original method
            result = super().search_directory(*args, **kwargs)
            return result
        except Exception as e:
            # If it's already an enhanced error, re-raise
            if isinstance(e, (TokenLimitError, PatternSyntaxError)):
                raise
            
            # Check if it's a token limit error from MCP
            error_str = str(e).lower()
            if "token" in error_str and "limit" in error_str:
                # Extract token counts if possible
                import re
                match = re.search(r'(\d+)\s*tokens.*exceeds.*(\d+)', str(e))
                if match:
                    actual = int(match.group(1))
                    limit = int(match.group(2))
                    raise TokenLimitError(actual, limit, "search")
                else:
                    raise TokenLimitError(30000, 25000, "search")  # Defaults
            
            # For any other error, suggest using search_summary instead
            from ..utils.enhanced_error_handling import EnhancedError
            suggestions = [
                "Try search_summary() for a lightweight overview",
                "Use search_files_only() to identify files first", 
                "Search a smaller directory or specific files",
                "Add file_extensions filter to narrow results"
            ]
            raise EnhancedError(f"Search failed: {str(e)}", suggestions)


def create_enhanced_server(config=None):
    """Create an enhanced AST Grep MCP server instance."""
    return AstGrepMCPEnhanced(config)