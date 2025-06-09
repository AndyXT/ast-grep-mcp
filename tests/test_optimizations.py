"""
Tests for the performance optimizations in ast-grep-mcp.
"""

import pytest
import tempfile
import os
import shutil
from src.ast_grep_mcp.ast_analyzer import AstAnalyzer
from src.ast_grep_mcp.utils.benchmarks import create_synthetic_files


@pytest.mark.parametrize("batch_size", [None, 5, 10])
def test_batch_processing(batch_size):
    """Test that batch processing works with different batch sizes."""
    analyzer = AstAnalyzer()
    temp_dir = tempfile.mkdtemp(prefix="ast_grep_test_opt_")

    try:
        # Create a small set of test files
        dir_path, num_files = create_synthetic_files(
            temp_dir, num_files=20, language="python", complexity="simple"
        )

        # Test parallel processing with the given batch size
        result = analyzer.search_directory(
            dir_path,
            pattern="def $NAME($$$PARAMS)",
            parallel=True,
            batch_size=batch_size,
        )

        # Verify basic structure of the result
        assert "directory" in result
        assert "files_searched" in result
        assert "files_with_matches" in result
        assert "matches" in result

        # Should find at least some matches
        assert result["files_with_matches"] > 0

    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_parallel_vs_sequential():
    """
    Test that parallel processing finds the same matches as sequential.

    This ensures correctness of the parallel implementation.
    """
    analyzer = AstAnalyzer()
    temp_dir = tempfile.mkdtemp(prefix="ast_grep_test_opt_")

    try:
        # Create a small set of test files
        dir_path, num_files = create_synthetic_files(
            temp_dir, num_files=15, language="python", complexity="medium"
        )

        pattern = "class $NAME"

        # Search with sequential processing
        sequential_result = analyzer.search_directory(
            dir_path, pattern=pattern, parallel=False
        )

        # Search with parallel processing
        parallel_result = analyzer.search_directory(
            dir_path,
            pattern=pattern,
            parallel=True,
            batch_size=5,  # Small batch size for testing
        )

        # Both should find the same number of files with matches
        assert (
            sequential_result["files_with_matches"]
            == parallel_result["files_with_matches"]
        )

        # Both should find matches in the same files
        sequential_files = set(sequential_result["matches"].keys())
        parallel_files = set(parallel_result["matches"].keys())
        assert sequential_files == parallel_files

        # Check that each file has the same number of matches
        for file_path in sequential_files:
            assert (
                sequential_result["matches"][file_path]["count"]
                == parallel_result["matches"][file_path]["count"]
            )

    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@pytest.mark.parametrize(
    "num_files,expected_parallel",
    [
        (5, False),  # Small number of files -> sequential
        (60, True),  # Larger number -> parallel
    ],
)
def test_auto_parallel_decision(num_files, expected_parallel):
    """Test that the analyzer makes the right decision about parallel processing."""
    analyzer = AstAnalyzer()

    # Mock the logger to track decisions
    class LoggerMock:
        def __init__(self):
            self.messages = []

        def info(self, msg):
            self.messages.append(msg)

        def warning(self, msg):
            pass

        def error(self, msg):
            pass

        def debug(self, msg):
            pass

    # Save original logger and replace with mock
    original_logger = analyzer.logger
    mock_logger = LoggerMock()
    analyzer.logger = mock_logger

    try:
        # Create a temporary directory structure
        temp_dir = tempfile.mkdtemp(prefix="ast_grep_test_")

        # Create mock file list
        files = [f"file_{i}.py" for i in range(num_files)]

        # Mock the os.walk to return our files
        original_walk = os.walk

        def mock_walk(directory, *args, **kwargs):
            yield directory, [], files

        # Mock the _process_file method to avoid actual file processing
        original_process_file = analyzer._process_file
        analyzer._process_file = lambda file_path, pattern: (file_path, [], "python")

        # Replace os.walk with our mock
        os.walk = mock_walk

        try:
            # Call search_directory
            analyzer.search_directory(temp_dir, "test_pattern")

            # Check if it used the expected processing mode
            used_parallel = any(
                "parallel processing" in msg for msg in mock_logger.messages
            )
            used_sequential = any(
                "sequential processing" in msg for msg in mock_logger.messages
            )

            if expected_parallel:
                assert used_parallel, "Should have used parallel processing"
            else:
                assert used_sequential, "Should have used sequential processing"

        finally:
            # Restore original methods
            os.walk = original_walk
            analyzer._process_file = original_process_file

            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    finally:
        # Restore original logger
        analyzer.logger = original_logger
