import os
import tempfile

from src.ast_grep_mcp.utils.security import (
    sanitize_pattern,
    is_safe_path,
    validate_file_access,
)


class TestPatternSanitization:
    """Tests for the pattern sanitization functionality."""

    def test_sanitize_pattern_with_safe_patterns(self):
        """Test that safe patterns are not modified."""
        safe_patterns = [
            "def $FUNC_NAME():",
            "class $CLASS_NAME:",
            "if $CONDITION:",
            "function $NAME($$$PARAMS) { $$$BODY }",
            "import $MODULE from '$PATH'",
            "$CONDITION ? $TRUE_EXPR : $FALSE_EXPR",
            "try { $$$BODY } catch($ERROR) { $$$HANDLER }",
            "if (x > 0 && y < 10) { $$$BODY }",
            "if (x >= 0 || y <= 10) { $$$BODY }",
            "x | y | z",  # Bitwise OR is safe and should be preserved
        ]

        for pattern in safe_patterns:
            sanitized = sanitize_pattern(pattern)
            assert (
                sanitized == pattern
            ), f"Safe pattern was modified: {pattern} -> {sanitized}"

    def test_sanitize_pattern_removes_dangerous_constructs(self):
        """Test that dangerous constructs are removed from patterns."""
        patterns_with_dangerous_constructs = [
            ("`ls -la`", ""),  # Backticks should be removed
            (
                "function() { $(rm -rf /); }",
                "function() {  }",
            ),  # Command substitution should be removed
            (
                "code with `nested backticks` in it",
                "code with  in it",
            ),  # Nested backticks
            (
                "multiple $(cmd1) $(cmd2) substitutions",
                "multiple   substitutions",
            ),  # Multiple substitutions
        ]

        for original, expected in patterns_with_dangerous_constructs:
            sanitized = sanitize_pattern(original)
            assert sanitized.replace(" ", "") == expected.replace(
                " ", ""
            ), f"Pattern not sanitized correctly: {original} -> {sanitized}, expected {expected}"

    def test_sanitize_pattern_with_empty_input(self):
        """Test sanitization with empty or None input."""
        assert sanitize_pattern("") == ""
        assert sanitize_pattern(None) == ""


class TestPathValidation:
    """Tests for path validation functionality."""

    def test_is_safe_path_with_no_safe_roots(self):
        """Test that any path is considered safe when no safe_roots are specified."""
        assert is_safe_path("/etc/passwd") is True
        assert is_safe_path("/home/user/code.py") is True
        assert is_safe_path("relative/path.txt") is True

    def test_is_safe_path_with_safe_roots(self):
        """Test path validation with specified safe roots."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some example directories and files
            safe_dir = os.path.join(temp_dir, "safe_dir")
            unsafe_dir = os.path.join(temp_dir, "unsafe_dir")
            os.makedirs(safe_dir)
            os.makedirs(unsafe_dir)

            # Create test files
            safe_file = os.path.join(safe_dir, "safe_file.txt")
            unsafe_file = os.path.join(unsafe_dir, "unsafe_file.txt")
            with open(safe_file, "w") as f:
                f.write("safe content")
            with open(unsafe_file, "w") as f:
                f.write("unsafe content")

            # Set up safe roots
            safe_roots = [safe_dir]

            # Test validation
            assert is_safe_path(safe_file, safe_roots) is True
            assert is_safe_path(safe_dir, safe_roots) is True
            assert is_safe_path(unsafe_file, safe_roots) is False
            assert is_safe_path(unsafe_dir, safe_roots) is False

    def test_validate_file_access(self):
        """Test validate_file_access function."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file
            test_file = os.path.join(temp_dir, "test_file.txt")
            with open(test_file, "w") as f:
                f.write("test content")

            # Test with no safe roots
            assert validate_file_access(test_file) is None

            # Test with matching safe root
            assert validate_file_access(test_file, [temp_dir]) is None

            # Test with non-matching safe root
            other_dir = os.path.join(temp_dir, "other")
            os.makedirs(other_dir)
            error = validate_file_access(test_file, [other_dir])
            assert error is not None
            assert "restricted" in error

    def test_path_traversal_attack(self):
        """Test that path traversal attacks are prevented."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file in a subdirectory
            safe_dir = os.path.join(temp_dir, "safe_dir")
            os.makedirs(safe_dir)

            # Create sensitive file outside safe directory
            sensitive_file = os.path.join(temp_dir, "sensitive.txt")
            with open(sensitive_file, "w") as f:
                f.write("sensitive data")

            # Test path traversal attempt
            traversal_path = os.path.join(safe_dir, "../sensitive.txt")
            assert is_safe_path(traversal_path, [safe_dir]) is False

            traversal_path2 = os.path.join(safe_dir, "../../etc/passwd")
            assert is_safe_path(traversal_path2, [safe_dir]) is False
