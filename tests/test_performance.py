"""
Tests for the performance optimizations in ast-grep-mcp.
"""

import pytest
import tempfile
import os
import shutil
from src.ast_grep_mcp.utils.result_cache import ResultCache, cached
from src.ast_grep_mcp.utils.benchmarks import (
    create_synthetic_files,
    Benchmark,
    run_benchmarks,
)
from src.ast_grep_mcp.ast_analyzer import AstAnalyzer


class TestResultCache:
    """Tests for the ResultCache class."""

    def test_cache_initialization(self):
        """Test that cache initializes correctly."""
        cache = ResultCache(maxsize=100)
        assert cache.maxsize == 100
        assert cache._cache_hits == 0
        assert cache._cache_misses == 0

    def test_cache_decorator(self):
        """Test that cache decorator works."""
        cache = ResultCache(maxsize=10)

        # Define a test function with the cache decorator
        @cache.lru_cache
        def add(a, b):
            return a + b

        # Call the function twice with the same arguments
        result1 = add(1, 2)
        result2 = add(1, 2)

        # Results should be equal and the second call should be a cache hit
        assert result1 == result2
        assert cache._cache_hits == 1
        assert cache._cache_misses == 1

    def test_cache_stats(self):
        """Test that cache stats are calculated correctly."""
        cache = ResultCache(maxsize=10)

        # Add some cache hits and misses
        cache._cache_hits = 5
        cache._cache_misses = 10
        cache._cache_size = 3

        # Get stats
        stats = cache.get_stats()

        # Check stats
        assert stats["hits"] == 5
        assert stats["misses"] == 10
        assert stats["size"] == 3
        assert stats["hit_ratio"] == 5 / 15
        assert stats["maxsize"] == 10


class TestCachedFunctions:
    """Tests for functions with caching."""

    def test_cached_function(self):
        """Test that a cached function returns the same result for the same inputs."""

        @cached
        def example_func(a, b, c):
            return a + b + c

        # Call the function twice with the same arguments
        result1 = example_func(1, 2, 3)
        result2 = example_func(1, 2, 3)

        # Results should be equal and from cache
        assert result1 == result2

        # Different arguments should give different results
        # Note: Need to use different values that don't add up to the same sum
        result3 = example_func(10, 20, 30)
        assert result1 != result3


@pytest.mark.slow
class TestParallelization:
    """Tests for the parallel directory search feature."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="ast_grep_test_")
        self.analyzer = AstAnalyzer()

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_directory_search_parallel(self):
        """Test that parallel directory search works."""
        # Create test files
        dir_path, num_files = create_synthetic_files(
            self.temp_dir,
            num_files=20,  # Small number for quick test
            language="python",
        )

        # Search with pattern (non-parallel)
        sequential_result = self.analyzer.search_directory(
            dir_path, pattern="def $NAME($$$PARAMS)", parallel=False
        )

        # Search with pattern (parallel)
        parallel_result = self.analyzer.search_directory(
            dir_path, pattern="def $NAME($$$PARAMS)", parallel=True
        )

        # Both should find the same number of matches
        assert parallel_result["files_searched"] == sequential_result["files_searched"]
        assert (
            parallel_result["files_with_matches"]
            == sequential_result["files_with_matches"]
        )


@pytest.mark.benchmark
@pytest.mark.slow
class TestBenchmarks:
    """Benchmarking tests for performance improvements."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="ast_grep_benchmark_")

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_benchmark_creation(self):
        """Test that benchmarks can be created."""
        benchmark = Benchmark("Test Benchmark", iterations=2)
        assert benchmark.name == "Test Benchmark"
        assert benchmark.iterations == 2

    def test_file_creation(self):
        """Test synthetic file creation."""
        directory, num_files = create_synthetic_files(
            self.temp_dir, num_files=5, language="python"
        )

        assert os.path.exists(directory)
        assert num_files == 5

        # Count files in directory
        file_count = len([f for f in os.listdir(directory) if f.endswith(".py")])
        assert file_count == 5

    @pytest.mark.skip(reason="Full benchmark test takes too long for regular test runs")
    def test_full_benchmark(self):
        """Run a full benchmark (skip by default as it takes too long)."""
        # Run benchmarks with a small number of files for faster test
        result = run_benchmarks(output_dir=self.temp_dir, num_files=50)

        # Check if we got results
        assert "avg_speedup" in result
        assert "success" in result

        # Even with small file count, we should see some speedup
        assert result["avg_speedup"] > 1.0
