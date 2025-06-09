"""
Auto-pagination support for large result sets.

This module provides streaming and automatic pagination handling
to simplify working with large result sets.
"""

from typing import Iterator, Dict, Any, Optional, Callable, List
import threading
import queue
import time


class SearchResultStream:
    """Iterator that automatically handles pagination for search results."""
    
    def __init__(
        self,
        search_func: Callable,
        initial_args: Dict[str, Any],
        page_size: int = 100
    ):
        """
        Initialize a search result stream.
        
        Args:
            search_func: The search function to call
            initial_args: Arguments to pass to search function
            page_size: Number of results per page
        """
        self.search_func = search_func
        self.initial_args = initial_args
        self.page_size = page_size
        self.current_page = 1
        self.current_results = []
        self.current_index = 0
        self.total_yielded = 0
        self.has_more = True
        self._exhausted = False
        
        # Progress tracking
        self.total_files = 0
        self.files_processed = 0
        self.start_time = time.time()
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Return the iterator."""
        return self
    
    def __next__(self) -> Dict[str, Any]:
        """Get the next result, fetching new pages as needed."""
        # If we've exhausted current results, fetch next page
        if self.current_index >= len(self.current_results):
            if not self.has_more or self._exhausted:
                raise StopIteration
            
            self._fetch_next_page()
            
            # If no results after fetch, we're done
            if not self.current_results:
                self._exhausted = True
                raise StopIteration
        
        # Return current result and advance
        result = self.current_results[self.current_index]
        self.current_index += 1
        self.total_yielded += 1
        
        # Add progress info to result
        result["_progress"] = {
            "total_yielded": self.total_yielded,
            "current_page": self.current_page,
            "elapsed_seconds": time.time() - self.start_time,
            "files_processed": self.files_processed,
            "total_files": self.total_files
        }
        
        return result
    
    def _fetch_next_page(self):
        """Fetch the next page of results."""
        # Update args with current page
        args = self.initial_args.copy()
        args["page"] = self.current_page
        args["page_size"] = self.page_size
        
        # Call search function
        response = self.search_func(**args)
        
        # Extract results based on response format
        if isinstance(response, dict):
            if "matches" in response:
                # Handle search_directory response format
                self.current_results = []
                for file_path, file_matches in response.get("matches", {}).items():
                    for match in file_matches:
                        self.current_results.append({
                            "file": file_path,
                            "match": match,
                            "type": "search_result"
                        })
                
                # Update progress tracking
                self.files_processed = response.get("files_searched", 0)
                self.total_files = response.get("total_files", 0)
            
            elif "results" in response:
                # Generic results format
                self.current_results = response["results"]
            
            else:
                # Try to extract any list-like data
                for key, value in response.items():
                    if isinstance(value, list):
                        self.current_results = value
                        break
            
            # Check if there are more pages
            self.has_more = response.get("has_more", False)
            if not self.has_more and "page_info" in response:
                page_info = response["page_info"]
                total_pages = page_info.get("total_pages", 1)
                self.has_more = self.current_page < total_pages
        
        else:
            # Unsupported response format
            self.current_results = []
            self.has_more = False
        
        # Reset index and increment page
        self.current_index = 0
        self.current_page += 1


class AsyncSearchStream:
    """Asynchronous search stream with background fetching."""
    
    def __init__(
        self,
        search_func: Callable,
        initial_args: Dict[str, Any],
        page_size: int = 100,
        prefetch_pages: int = 2
    ):
        """
        Initialize async search stream.
        
        Args:
            search_func: The search function to call
            initial_args: Arguments to pass to search function
            page_size: Number of results per page
            prefetch_pages: Number of pages to prefetch
        """
        self.search_func = search_func
        self.initial_args = initial_args
        self.page_size = page_size
        self.prefetch_pages = prefetch_pages
        
        # Result queue and fetching state
        self.result_queue = queue.Queue(maxsize=page_size * prefetch_pages)
        self.fetch_complete = threading.Event()
        self.error = None
        
        # Start background fetching
        self.fetch_thread = threading.Thread(target=self._background_fetch)
        self.fetch_thread.daemon = True
        self.fetch_thread.start()
    
    def __iter__(self):
        """Return iterator."""
        return self
    
    def __next__(self):
        """Get next result from queue."""
        while True:
            try:
                # Try to get result with timeout
                result = self.result_queue.get(timeout=0.1)
                
                # Check for sentinel
                if result is None:
                    if self.error:
                        raise self.error
                    raise StopIteration
                
                return result
                
            except queue.Empty:
                # Check if fetching is complete
                if self.fetch_complete.is_set() and self.result_queue.empty():
                    if self.error:
                        raise self.error
                    raise StopIteration
                # Otherwise continue waiting
    
    def _background_fetch(self):
        """Fetch results in background."""
        try:
            page = 1
            has_more = True
            
            while has_more:
                # Prepare args
                args = self.initial_args.copy()
                args["page"] = page
                args["page_size"] = self.page_size
                
                # Fetch page
                response = self.search_func(**args)
                
                # Process results
                results = self._extract_results(response)
                
                # Put results in queue
                for result in results:
                    self.result_queue.put(result)
                
                # Check if more pages
                has_more = response.get("has_more", False)
                if not has_more and "page_info" in response:
                    page_info = response["page_info"]
                    total_pages = page_info.get("total_pages", 1)
                    has_more = page < total_pages
                
                page += 1
            
        except Exception as e:
            self.error = e
        
        finally:
            # Signal completion
            self.result_queue.put(None)
            self.fetch_complete.set()
    
    def _extract_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract results from response."""
        results = []
        
        if "matches" in response:
            # Handle search_directory format
            for file_path, file_matches in response.get("matches", {}).items():
                for match in file_matches:
                    results.append({
                        "file": file_path,
                        "match": match,
                        "type": "search_result"
                    })
        
        elif "results" in response:
            results = response["results"]
        
        return results


def create_search_stream(
    search_func: Callable,
    pattern: str,
    directory: str,
    **kwargs
) -> SearchResultStream:
    """
    Create a search result stream.
    
    Args:
        search_func: Search function to use
        pattern: Pattern to search for
        directory: Directory to search in
        **kwargs: Additional search arguments
        
    Returns:
        SearchResultStream for iterating results
    """
    initial_args = {
        "pattern": pattern,
        "directory": directory,
        **kwargs
    }
    
    # Remove any existing pagination args
    initial_args.pop("page", None)
    initial_args.pop("page_size", None)
    
    return SearchResultStream(
        search_func=search_func,
        initial_args=initial_args,
        page_size=kwargs.get("stream_page_size", 100)
    )


def search_all_results(
    search_func: Callable,
    pattern: str,
    directory: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Search and collect all results with automatic pagination.
    
    Args:
        search_func: Search function to use
        pattern: Pattern to search for
        directory: Directory to search in
        progress_callback: Optional callback for progress updates
        **kwargs: Additional search arguments
        
    Returns:
        List of all results
    """
    all_results = []
    
    stream = create_search_stream(search_func, pattern, directory, **kwargs)
    
    for result in stream:
        all_results.append(result)
        
        # Call progress callback if provided
        if progress_callback and "_progress" in result:
            progress_callback(result["_progress"])
    
    return all_results