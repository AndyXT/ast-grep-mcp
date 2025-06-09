"""
Pagination utilities for handling large result sets.
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass
import json
import logging

T = TypeVar('T')

@dataclass
class PaginatedResponse(Generic[T]):
    """Container for paginated responses."""
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": self.items,
            "pagination": {
                "total_count": self.total_count,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_previous": self.has_previous,
                "next_page": self.next_page,
                "previous_page": self.previous_page,
            },
            "summary": self.summary,
        }


class ResponsePaginator:
    """Handles pagination of large responses."""
    
    # Token limits for different response types (reduced to prevent MCP errors)
    TOKEN_LIMITS = {
        "default": 20000,  # ~20k tokens (safe limit)
        "search": 15000,   # ~15k tokens for search results
        "analysis": 18000, # ~18k tokens for analysis
        "minimal": 8000,   # ~8k tokens for minimal responses
    }
    
    # Approximate characters per token
    CHARS_PER_TOKEN = 4
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def estimate_size(self, data: Any) -> int:
        """Estimate the size of data in characters."""
        try:
            # Convert to JSON to get accurate size
            json_str = json.dumps(data, default=str)
            return len(json_str)
        except:
            # Fallback to string representation
            return len(str(data))
    
    def estimate_tokens(self, data: Any) -> int:
        """Estimate token count for data."""
        size = self.estimate_size(data)
        return size // self.CHARS_PER_TOKEN
    
    def should_paginate(self, data: Any, response_type: str = "default") -> bool:
        """Check if data should be paginated."""
        limit = self.TOKEN_LIMITS.get(response_type, self.TOKEN_LIMITS["default"])
        estimated_tokens = self.estimate_tokens(data)
        
        if estimated_tokens > limit:
            self.logger.info(
                f"Response size ({estimated_tokens} tokens) exceeds {response_type} limit ({limit} tokens). "
                f"Pagination will be applied. Use page_size and page parameters to control results."
            )
        
        return estimated_tokens > limit
    
    def paginate_list(
        self, 
        items: List[T], 
        page: int = 1, 
        page_size: Optional[int] = None,
        response_type: str = "default",
        summary_fn: Optional[callable] = None
    ) -> PaginatedResponse[T]:
        """
        Paginate a list of items.
        
        Args:
            items: List of items to paginate
            page: Current page number (1-based)
            page_size: Items per page (auto-calculated if None)
            response_type: Type of response for token limits
            summary_fn: Optional function to generate summary
            
        Returns:
            PaginatedResponse object
        """
        total_count = len(items)
        
        # Auto-calculate page size if not provided
        if page_size is None:
            # Estimate size of single item
            if items:
                item_tokens = self.estimate_tokens(items[0])
                limit = self.TOKEN_LIMITS.get(response_type, self.TOKEN_LIMITS["default"])
                # Aim for pages that are 60% of limit to leave room for metadata and safety margin
                target_tokens = int(limit * 0.6)
                page_size = max(1, target_tokens // max(1, item_tokens))
                # Cap page size to prevent overly large responses
                page_size = min(page_size, 50)  # Maximum 50 items per page
            else:
                page_size = 20  # Default to smaller page size
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        page = max(1, min(page, total_pages))  # Clamp to valid range
        
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        
        page_items = items[start_idx:end_idx]
        
        # Generate summary if function provided
        summary = None
        if summary_fn:
            try:
                summary = summary_fn(items)
            except Exception as e:
                self.logger.warning(f"Failed to generate summary: {e}")
        
        return PaginatedResponse(
            items=page_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
            next_page=page + 1 if page < total_pages else None,
            previous_page=page - 1 if page > 1 else None,
            summary=summary
        )
    
    def paginate_dict(
        self,
        data: Dict[str, List[Any]],
        page: int = 1,
        items_per_key: Optional[int] = None,
        response_type: str = "default"
    ) -> Dict[str, Any]:
        """
        Paginate a dictionary with list values.
        
        Args:
            data: Dictionary with list values
            page: Current page number
            items_per_key: Items per key per page
            response_type: Type of response for token limits
            
        Returns:
            Paginated dictionary
        """
        result = {
            "data": {},
            "pagination": {
                "page": page,
                "total_items": 0,
                "items_shown": 0,
            }
        }
        
        # Calculate items per key if not provided
        if items_per_key is None:
            total_keys = len(data)
            if total_keys > 0:
                limit = self.TOKEN_LIMITS.get(response_type, self.TOKEN_LIMITS["default"])
                # Rough estimate: divide limit by number of keys
                items_per_key = max(1, (limit // self.CHARS_PER_TOKEN) // (total_keys * 100))
            else:
                items_per_key = 10
        
        total_items = 0
        items_shown = 0
        
        for key, items in data.items():
            if isinstance(items, list):
                total_items += len(items)
                start_idx = (page - 1) * items_per_key
                end_idx = min(start_idx + items_per_key, len(items))
                
                if start_idx < len(items):
                    result["data"][key] = items[start_idx:end_idx]
                    items_shown += len(result["data"][key])
                else:
                    result["data"][key] = []
            else:
                result["data"][key] = items
        
        result["pagination"]["total_items"] = total_items
        result["pagination"]["items_shown"] = items_shown
        result["pagination"]["items_per_key"] = items_per_key
        
        # Calculate if there are more pages
        max_items_in_any_key = max(
            (len(v) if isinstance(v, list) else 0 for v in data.values()),
            default=0
        )
        total_pages = (max_items_in_any_key + items_per_key - 1) // items_per_key
        result["pagination"]["total_pages"] = total_pages
        result["pagination"]["has_next"] = page < total_pages
        result["pagination"]["has_previous"] = page > 1
        
        return result
    
    def create_summary(self, data: Dict[str, Any], max_items: int = 5) -> Dict[str, Any]:
        """
        Create a summary of large data.
        
        Args:
            data: Data to summarize
            max_items: Maximum items to show per category
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_files": 0,
            "total_matches": 0,
            "files_with_matches": 0,
            "top_files": [],
            "language_breakdown": {},
            "truncated": False
        }
        
        if "matches" in data and isinstance(data["matches"], dict):
            summary["total_files"] = len(data["matches"])
            
            # Count matches and get top files
            file_match_counts = []
            for file_path, matches in data["matches"].items():
                match_count = len(matches) if isinstance(matches, list) else 0
                if match_count > 0:
                    summary["files_with_matches"] += 1
                    summary["total_matches"] += match_count
                    file_match_counts.append((file_path, match_count))
            
            # Sort by match count and get top files
            file_match_counts.sort(key=lambda x: x[1], reverse=True)
            summary["top_files"] = [
                {"file": f, "matches": c} 
                for f, c in file_match_counts[:max_items]
            ]
            
            if len(file_match_counts) > max_items:
                summary["truncated"] = True
        
        return summary