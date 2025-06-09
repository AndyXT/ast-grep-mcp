"""
Batch operations for efficient multi-pattern searching.

This module provides functionality to run multiple searches
in parallel for better performance.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
from collections import defaultdict


@dataclass
class BatchSearchRequest:
    """Represents a single search in a batch."""
    pattern: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None


@dataclass 
class BatchSearchResult:
    """Result from a batch search operation."""
    name: str
    pattern: str
    matches: List[Dict[str, Any]]
    count: int
    duration: float
    error: Optional[str] = None
    files_with_matches: int = 0


class BatchSearcher:
    """Handles batch search operations efficiently."""
    
    def __init__(
        self,
        search_func: Callable,
        max_workers: Optional[int] = None
    ):
        """
        Initialize batch searcher.
        
        Args:
            search_func: Function to use for searching
            max_workers: Maximum parallel workers
        """
        self.search_func = search_func
        self.max_workers = max_workers
        self._progress_lock = threading.Lock()
        self._progress = {}
    
    def batch_search(
        self,
        requests: List[Union[BatchSearchRequest, Dict[str, Any]]],
        directory: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        **common_kwargs
    ) -> Dict[str, BatchSearchResult]:
        """
        Execute multiple searches in parallel.
        
        Args:
            requests: List of search requests
            directory: Directory to search in
            progress_callback: Optional progress callback
            **common_kwargs: Common arguments for all searches
            
        Returns:
            Dictionary mapping request names to results
        """
        # Convert dict requests to BatchSearchRequest
        search_requests = []
        for req in requests:
            if isinstance(req, dict):
                search_requests.append(BatchSearchRequest(**req))
            else:
                search_requests.append(req)
        
        results = {}
        total_requests = len(search_requests)
        completed = 0
        
        # Initialize progress
        self._progress = {
            "total": total_requests,
            "completed": 0,
            "in_progress": [],
            "results": {}
        }
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all searches
            future_to_request = {
                executor.submit(
                    self._execute_single_search,
                    req,
                    directory,
                    **common_kwargs
                ): req
                for req in search_requests
            }
            
            # Process results as they complete
            for future in as_completed(future_to_request):
                request = future_to_request[future]
                
                try:
                    result = future.result()
                    results[request.name] = result
                    
                except Exception as e:
                    # Create error result
                    results[request.name] = BatchSearchResult(
                        name=request.name,
                        pattern=request.pattern,
                        matches=[],
                        count=0,
                        duration=0.0,
                        error=str(e)
                    )
                
                # Update progress
                completed += 1
                with self._progress_lock:
                    self._progress["completed"] = completed
                    self._progress["results"][request.name] = results[request.name]
                
                # Call progress callback
                if progress_callback:
                    progress_callback({
                        "completed": completed,
                        "total": total_requests,
                        "current": request.name,
                        "percentage": (completed / total_requests) * 100
                    })
        
        return results
    
    def _execute_single_search(
        self,
        request: BatchSearchRequest,
        directory: str,
        **kwargs
    ) -> BatchSearchResult:
        """Execute a single search request."""
        start_time = time.time()
        
        # Update progress
        with self._progress_lock:
            self._progress["in_progress"].append(request.name)
        
        try:
            # Execute search
            response = self.search_func(
                directory=directory,
                pattern=request.pattern,
                **kwargs
            )
            
            # Extract matches
            matches = []
            files_with_matches = 0
            
            if isinstance(response, dict):
                if "matches" in response:
                    # search_directory format
                    for file_path, file_matches in response.get("matches", {}).items():
                        files_with_matches += 1
                        for match in file_matches:
                            matches.append({
                                "file": file_path,
                                "match": match,
                                "request": request.name
                            })
                
                elif "results" in response:
                    matches = response["results"]
            
            duration = time.time() - start_time
            
            return BatchSearchResult(
                name=request.name,
                pattern=request.pattern,
                matches=matches,
                count=len(matches),
                duration=duration,
                files_with_matches=files_with_matches
            )
            
        finally:
            # Update progress
            with self._progress_lock:
                if request.name in self._progress["in_progress"]:
                    self._progress["in_progress"].remove(request.name)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current batch progress."""
        with self._progress_lock:
            return self._progress.copy()


def create_code_quality_batch(language: str) -> List[BatchSearchRequest]:
    """
    Create a batch of code quality checks for a language.
    
    Args:
        language: Programming language
        
    Returns:
        List of batch search requests
    """
    requests = []
    
    if language == "rust":
        requests.extend([
            BatchSearchRequest(
                pattern="unwrap()",
                name="unwrap_calls",
                category="error_handling",
                description="Direct unwrap() calls",
                severity="warning"
            ),
            BatchSearchRequest(
                pattern="panic!($$$ARGS)",
                name="panic_calls", 
                category="error_handling",
                description="Panic macro calls",
                severity="error"
            ),
            BatchSearchRequest(
                pattern="todo!($$$ARGS)",
                name="todo_macros",
                category="incomplete",
                description="TODO macros",
                severity="info"
            ),
            BatchSearchRequest(
                pattern="unimplemented!($$$ARGS)",
                name="unimplemented_macros",
                category="incomplete", 
                description="Unimplemented macros",
                severity="warning"
            ),
            BatchSearchRequest(
                pattern="unsafe { $$$BODY }",
                name="unsafe_blocks",
                category="security",
                description="Unsafe code blocks",
                severity="warning"
            ),
            BatchSearchRequest(
                pattern="println!($$$ARGS)",
                name="println_calls",
                category="logging",
                description="Direct println! usage",
                severity="info"
            ),
            BatchSearchRequest(
                pattern="clone()",
                name="clone_calls",
                category="performance",
                description="Clone operations",
                severity="info"
            )
        ])
    
    elif language in ["javascript", "typescript"]:
        requests.extend([
            BatchSearchRequest(
                pattern="console.log($$$ARGS)",
                name="console_logs",
                category="logging",
                description="Console.log statements",
                severity="info"
            ),
            BatchSearchRequest(
                pattern="var $NAME",
                name="var_declarations",
                category="modernization",
                description="Var declarations (use const/let)",
                severity="warning"
            ),
            BatchSearchRequest(
                pattern="eval($$$ARGS)",
                name="eval_usage",
                category="security",
                description="Eval function usage",
                severity="error"
            ),
            BatchSearchRequest(
                pattern="debugger",
                name="debugger_statements",
                category="debugging",
                description="Debugger statements",
                severity="warning"
            )
        ])
    
    elif language == "python":
        requests.extend([
            BatchSearchRequest(
                pattern="print($$$ARGS)",
                name="print_statements",
                category="logging",
                description="Print statements",
                severity="info"
            ),
            BatchSearchRequest(
                pattern="except:",
                name="bare_except",
                category="error_handling",
                description="Bare except clauses",
                severity="warning"
            ),
            BatchSearchRequest(
                pattern="eval($$$ARGS)",
                name="eval_usage",
                category="security",
                description="Eval function usage",
                severity="error"
            ),
            BatchSearchRequest(
                pattern="import *",
                name="star_imports",
                category="style",
                description="Star imports",
                severity="warning"
            )
        ])
    
    return requests


def aggregate_batch_results(
    results: Dict[str, BatchSearchResult]
) -> Dict[str, Any]:
    """
    Aggregate batch search results into a summary.
    
    Args:
        results: Batch search results
        
    Returns:
        Aggregated summary
    """
    total_matches = 0
    total_duration = 0.0
    by_category = defaultdict(list)
    by_severity = defaultdict(list)
    errors = []
    
    for name, result in results.items():
        total_matches += result.count
        total_duration += result.duration
        
        if result.error:
            errors.append({
                "name": name,
                "error": result.error
            })
        
        if result.count > 0:
            # Group by category
            category = getattr(result, "category", "uncategorized")
            by_category[category].append({
                "name": name,
                "count": result.count,
                "files": result.files_with_matches
            })
            
            # Group by severity
            severity = getattr(result, "severity", "info")
            by_severity[severity].append({
                "name": name,
                "count": result.count
            })
    
    return {
        "summary": {
            "total_patterns": len(results),
            "total_matches": total_matches,
            "total_duration": total_duration,
            "patterns_with_matches": sum(1 for r in results.values() if r.count > 0),
            "patterns_with_errors": len(errors)
        },
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
        "errors": errors,
        "details": results
    }


def create_security_audit_batch(language: str) -> List[BatchSearchRequest]:
    """Create a batch of security-focused searches."""
    requests = []
    
    if language == "rust":
        requests.extend([
            BatchSearchRequest(
                pattern="unsafe { $$$BODY }",
                name="unsafe_blocks",
                category="memory_safety",
                severity="high"
            ),
            BatchSearchRequest(
                pattern="transmute($$$ARGS)",
                name="transmute_usage",
                category="memory_safety",
                severity="critical"
            ),
            BatchSearchRequest(
                pattern="std::env::var($VAR)",
                name="env_var_access",
                category="configuration",
                severity="medium"
            )
        ])
    
    return requests