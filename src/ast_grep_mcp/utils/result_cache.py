"""
Result caching for ast-grep-mcp.

This module provides LRU caching for code analysis and refactoring results.
"""

import functools
import logging
from typing import Dict, Any, Callable, TypeVar, cast
import time

# Type variable for decorated functions
T = TypeVar('T')

class ResultCache:
    """
    LRU Cache for ast-grep analysis results.
    
    This class provides a cache for ast-grep analysis results to avoid
    repeated expensive operations on the same code and patterns.
    """
    
    def __init__(self, maxsize: int = 128):
        """
        Initialize the cache.
        
        Args:
            maxsize: Maximum number of items to store in the cache (default: 128)
        """
        self.maxsize = maxsize
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_size = 0
        self.logger = logging.getLogger("ast_grep_mcp.cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache usage.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_ratio = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "size": self._cache_size,
            "hit_ratio": hit_ratio,
            "maxsize": self.maxsize
        }
    
    def log_stats(self) -> None:
        """Log cache statistics."""
        stats = self.get_stats()
        self.logger.info(
            f"Cache stats: {stats['hits']} hits, {stats['misses']} misses, "
            f"{stats['hit_ratio']:.2%} hit ratio, {stats['size']}/{stats['maxsize']} items"
        )
    
    def lru_cache(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to cache function results using LRU caching.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function with caching
        """
        # Create the LRU cache using functools
        cached_func = functools.lru_cache(maxsize=self.maxsize)(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Get cache info before call
            info_before = cached_func.cache_info()
            
            # Call the cached function
            result = cached_func(*args, **kwargs)
            
            # Get cache info after call
            info_after = cached_func.cache_info()
            
            # Update stats
            if info_after.hits > info_before.hits:
                self._cache_hits += 1
                self.logger.debug(f"Cache hit for {func.__name__}")
            else:
                self._cache_misses += 1
                self.logger.debug(f"Cache miss for {func.__name__}")
            
            self._cache_size = info_after.currsize
            
            # Log performance improvement if cache hit
            if info_after.hits > info_before.hits:
                self.logger.debug(f"Cache hit saved {time.time() - start_time:.4f}s")
            
            return result
        
        # Add cache_info accessor to the wrapper
        wrapper.cache_info = cached_func.cache_info  # type: ignore
        wrapper.cache_clear = cached_func.cache_clear  # type: ignore
        
        return cast(Callable[..., T], wrapper)

# Global cache instance for use throughout the application
result_cache = ResultCache()

# Convenience decorator for use in other modules
def cached(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for caching function results.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with caching
    """
    return result_cache.lru_cache(func) 