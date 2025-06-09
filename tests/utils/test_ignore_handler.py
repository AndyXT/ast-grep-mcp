"""
Tests for the ignore file handler.
"""

import os
import tempfile
import shutil
from pathlib import Path
from ast_grep_mcp.utils.ignore_handler import IgnoreHandler, IgnorePattern


class TestIgnorePattern:
    """Tests for the IgnorePattern class."""

    def test_basic_pattern(self):
        """Test basic pattern matching."""
        pattern = IgnorePattern("*.txt")

        # Check pattern matching
        assert pattern.matches("file.txt") is True
        assert pattern.matches("path/to/file.txt") is True
        assert pattern.matches("file.py") is False
        assert pattern.matches("path/to/file.py") is False

    def test_directory_pattern(self):
        """Test directory pattern matching."""
        pattern = IgnorePattern("node_modules/")

        # Create a temporary directory structure using tempfile
        test_dir = tempfile.mkdtemp()
        try:
            node_modules_dir = os.path.join(test_dir, "node_modules")
            src_dir = os.path.join(test_dir, "src")
            src_node_modules_dir = os.path.join(src_dir, "node_modules")

            os.makedirs(node_modules_dir, exist_ok=True)
            os.makedirs(src_node_modules_dir, exist_ok=True)

            # Check pattern matching
            assert pattern.matches(node_modules_dir) is True
            assert pattern.matches(os.path.join(node_modules_dir, "file.txt")) is True
            assert pattern.matches(src_node_modules_dir) is True
            assert (
                pattern.matches(os.path.join(src_node_modules_dir, "file.txt")) is True
            )
            assert pattern.matches("nodemodules") is False
        finally:
            # Clean up entire test directory
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_negated_pattern(self):
        """Test negated pattern matching."""
        pattern = IgnorePattern("!important.txt")

        # Check pattern matching
        assert pattern.matches("important.txt") is True
        assert pattern.matches("path/to/important.txt") is True
        assert pattern.negate is True

    def test_anchored_pattern(self):
        """Test anchored pattern matching."""
        pattern = IgnorePattern("/root-only.txt")

        # Check pattern matching
        assert pattern.matches("root-only.txt") is True
        assert pattern.matches("path/to/root-only.txt") is False

    def test_invalid_pattern(self):
        """Test invalid pattern handling."""
        pattern = IgnorePattern("")
        assert pattern.is_valid is False

        pattern = IgnorePattern("# This is a comment")
        assert pattern.is_valid is False

        pattern = IgnorePattern("   ")
        assert pattern.is_valid is False

    def test_relative_to_base_dir(self):
        """Test pattern matching relative to a base directory."""
        base_dir = Path("/base/dir")
        pattern = IgnorePattern("*.txt", base_dir)

        # Check pattern matching
        assert pattern.matches("/base/dir/file.txt") is True
        assert pattern.matches("/base/dir/path/to/file.txt") is True
        assert pattern.matches("/other/dir/file.txt") is False


class TestIgnoreHandler:
    """Tests for the IgnoreHandler class."""

    def test_add_pattern(self):
        """Test adding patterns to the handler."""
        handler = IgnoreHandler()

        # Add patterns
        handler.add_pattern("*.txt")
        handler.add_pattern("node_modules/")
        handler.add_pattern("!important.txt")

        # Check pattern count
        assert len(handler.patterns) == 3

    def test_should_ignore(self):
        """Test checking if a path should be ignored."""
        handler = IgnoreHandler()

        # Add patterns
        handler.add_pattern("*.txt")
        handler.add_pattern("node_modules/")
        handler.add_pattern("!important.txt")

        # Check should_ignore
        assert handler.should_ignore("file.txt") is True
        assert handler.should_ignore("path/to/file.txt") is True
        assert handler.should_ignore("file.py") is False
        assert handler.should_ignore("important.txt") is False
        assert handler.should_ignore("path/to/important.txt") is False

        # Create a temporary directory for node_modules test
        os.makedirs("node_modules", exist_ok=True)
        try:
            assert handler.should_ignore("node_modules") is True
            assert handler.should_ignore("node_modules/file.js") is True
        finally:
            os.rmdir("node_modules")

    def test_load_file(self, tmp_path):
        """Test loading patterns from a file."""
        # Create a temporary ignore file
        ignore_file = tmp_path / ".ast-grepignore"
        with open(ignore_file, "w") as f:
            f.write("# Comment line\n")
            f.write("*.txt\n")
            f.write("node_modules/\n")
            f.write("\n")  # Empty line
            f.write("!important.txt\n")

        # Load the file
        handler = IgnoreHandler()
        result = handler.load_file(str(ignore_file))

        # Check loading result
        assert result is True
        assert len(handler.patterns) == 3  # Comment and empty line should be skipped

        # Check should_ignore
        assert handler.should_ignore("file.txt") is True
        assert handler.should_ignore("important.txt") is False

    def test_load_nonexistent_file(self):
        """Test loading patterns from a non-existent file."""
        handler = IgnoreHandler()
        result = handler.load_file("nonexistent-file")

        # Check loading result
        assert result is False
        assert len(handler.patterns) == 0

    def test_load_default_ignores(self):
        """Test loading default ignore patterns."""
        handler = IgnoreHandler()
        handler.load_default_ignores()

        # Check that default patterns were loaded
        assert len(handler.patterns) > 0

        # Check some common default ignores
        assert handler.should_ignore(".git/config") is True
        assert handler.should_ignore("__pycache__/module.pyc") is True
        assert handler.should_ignore("node_modules/package.json") is True
        assert handler.should_ignore(".vscode/settings.json") is True

    def test_find_nearest_ignore_file(self, tmp_path):
        """Test finding the nearest ignore file."""
        # Create a directory structure
        project_dir = tmp_path / "project"
        subdir = project_dir / "subdir"
        os.makedirs(subdir)

        # Create an ignore file in the project directory
        ignore_file = project_dir / ".ast-grepignore"
        with open(ignore_file, "w") as f:
            f.write("*.txt\n")

        # Find the ignore file from the subdirectory
        handler = IgnoreHandler()
        found_file = handler.find_nearest_ignore_file(str(subdir))

        # Check the found file
        assert found_file is not None
        assert os.path.normpath(found_file) == os.path.normpath(str(ignore_file))

    def test_load_nearest_ignore_file(self, tmp_path):
        """Test loading the nearest ignore file."""
        # Create a directory structure
        project_dir = tmp_path / "project"
        subdir = project_dir / "subdir"
        os.makedirs(subdir)

        # Create an ignore file in the project directory
        ignore_file = project_dir / ".ast-grepignore"
        with open(ignore_file, "w") as f:
            f.write("*.txt\n")

        # Load the nearest ignore file from the subdirectory
        handler = IgnoreHandler()
        result = handler.load_nearest_ignore_file(str(subdir))

        # Check loading result
        assert result is True
        assert len(handler.patterns) == 1
        assert handler.should_ignore("file.txt") is True

    def test_base_dir(self):
        """Test using a base directory with the handler."""
        base_dir = "/base/dir"
        handler = IgnoreHandler(base_dir)

        # Add patterns
        handler.add_pattern("*.txt")

        # Check should_ignore with absolute paths
        assert handler.should_ignore("/base/dir/file.txt") is True
        assert handler.should_ignore("/other/dir/file.txt") is False

    def test_multiple_patterns(self):
        """Test applying multiple patterns in order."""
        handler = IgnoreHandler()

        # Add patterns in a specific order
        handler.add_pattern("*.log")
        handler.add_pattern("!important.log")
        handler.add_pattern("logs/*.log")
        handler.add_pattern("!logs/debug.log")

        # Check should_ignore
        assert handler.should_ignore("file.log") is True
        assert handler.should_ignore("important.log") is False
        assert handler.should_ignore("logs/file.log") is True
        assert handler.should_ignore("logs/debug.log") is False

    def test_load_same_file_twice(self, tmp_path):
        """Test loading the same file twice doesn't duplicate patterns."""
        # Create a temporary ignore file
        ignore_file = tmp_path / ".ast-grepignore"
        with open(ignore_file, "w") as f:
            f.write("*.txt\n")

        # Load the file twice
        handler = IgnoreHandler()
        handler.load_file(str(ignore_file))
        handler.load_file(str(ignore_file))

        # Check loading result
        assert len(handler.patterns) == 1  # Patterns should not be duplicated
