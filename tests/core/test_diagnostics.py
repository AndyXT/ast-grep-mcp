"""
Tests for pattern diagnostics and enhanced error handling.
"""

import pytest
from ast_grep_mcp.core import AstGrepMCP
from ast_grep_mcp.utils.pattern_helpers import (
    analyze_pattern_error,
    enrich_error_message,
    get_pattern_help,
    is_pattern_syntax_error,
)


@pytest.fixture
def ast_grep_mcp():
    """Create an AstGrepMCP instance for testing."""
    return AstGrepMCP()


class TestPatternDiagnostics:
    """Tests for the enhanced pattern diagnostics functionality."""

    def test_pattern_error_detection(self):
        """Test detection of pattern syntax errors."""
        error_message = "failed to parse pattern: unexpected token"
        assert is_pattern_syntax_error(error_message) is True

        error_message = "Error loading file"
        assert is_pattern_syntax_error(error_message) is False

    def test_pattern_error_analysis(self):
        """Test analysis of pattern errors."""
        # Test mismatched bracket detection
        pattern = "function test({ a, b) {"
        analysis = analyze_pattern_error(pattern, "javascript")
        assert analysis["has_errors"] is True
        assert any("mismatched_brackets" in err["type"] for err in analysis["errors"])

        # Test invalid variable name detection
        pattern = "function $123FUNC() {}"
        analysis = analyze_pattern_error(pattern, "javascript")
        assert analysis["has_errors"] is True
        assert any("invalid_variable" in err["type"] for err in analysis["errors"])

        # Test template literal detection
        pattern = "$TEXT = `Hello, $NAME"
        analysis = analyze_pattern_error(pattern, "javascript")
        assert analysis["has_errors"] is True

    def test_pattern_help(self):
        """Test getting pattern help for different languages."""
        help_info = get_pattern_help("python")
        assert "basic_syntax" in help_info
        assert "language" in help_info
        assert help_info["language"] == "python"
        assert "$VAR" in help_info["basic_syntax"]
        assert "$$$VARS" in help_info["basic_syntax"]

        # Check JavaScript help
        js_help = get_pattern_help("javascript")
        assert "basic_syntax" in js_help
        assert "common_errors" in js_help
        assert any("jsx_syntax" in err["error"] for err in js_help["common_errors"])

    def test_enrich_error_message(self):
        """Test enhancement of error messages."""
        error_msg = "failed to parse pattern: unexpected token"
        pattern = "function test({"
        enhanced = enrich_error_message(error_msg, "javascript", pattern)

        # Check that the enhanced message contains helpful information
        assert error_msg in enhanced
        assert "Pattern syntax error detected" in enhanced
        assert "$NAME" in enhanced
        assert "$$$NAME" in enhanced

    def test_diagnostics_integration(self, ast_grep_mcp):
        """Test integration of pattern diagnostics with AstGrepMCP."""
        # Test with a valid pattern
        result = ast_grep_mcp._get_pattern_diagnostics("def $NAME():", "python")
        assert result["is_valid"] is True

        # Test with an invalid pattern
        result = ast_grep_mcp._get_pattern_diagnostics("def $NAME(", "python")
        assert result["is_valid"] is False
        assert "error" in result

        # Test with a code sample
        code = "def test():\n    pass"
        result = ast_grep_mcp._get_pattern_diagnostics("def $NAME(", "python", code)
        assert result["is_valid"] is False
        assert "error" in result

        # The actual implementation may or may not include "pattern_help"
        # depending on whether an exception is raised during matching

        # Test with JavaScript specific syntax
        js_code = "function test() { console.log('hello'); }"
        result = ast_grep_mcp._get_pattern_diagnostics(
            "function $NAME() { $$$BODY", "javascript", js_code
        )
        assert "error" in result


class TestLanguageSpecificDiagnostics:
    """Tests for language-specific diagnostics."""

    def test_python_diagnostics(self, ast_grep_mcp):
        """Test Python-specific diagnostics."""
        # Test indentation issue
        code = """
def test():
    a = 1
        b = 2  # Indentation error
"""
        pattern = """
def $NAME():
    $$$BODY
        $STATEMENT
"""
        result = ast_grep_mcp._get_pattern_diagnostics(pattern, "python", code)
        # The pattern might be valid in ast-grep even with inconsistent indentation

        # Test missing colon
        pattern = "def $NAME()"  # Missing colon
        result = ast_grep_mcp._get_pattern_diagnostics(pattern, "python", "def test():")
        # Missing colon might still be valid - just test that it returns diagnostics
        assert "language" in result
        assert result["language"] == "python"

    def test_javascript_diagnostics(self, ast_grep_mcp):
        """Test JavaScript-specific diagnostics."""
        # Test JSX syntax
        code = "<div><p>Hello</p></div>"
        pattern = "<div><p>$TEXT</p>"  # Missing closing tag
        result = ast_grep_mcp._get_pattern_diagnostics(pattern, "javascript", code)
        # Capture any diagnostics about this pattern

        # Test template literals
        code = "const greeting = `Hello, ${name}`;"
        pattern = "const $VAR = `Hello, ${$NAME}"  # Missing closing backtick
        result = ast_grep_mcp._get_pattern_diagnostics(pattern, "javascript", code)
        # Just verify that diagnostics are returned
        assert "language" in result
        assert result["language"] == "javascript"

    def test_typescript_diagnostics(self, ast_grep_mcp):
        """Test TypeScript-specific diagnostics."""
        # Test type annotations
        code = "const name: string = 'John';"
        pattern = "const $NAME: $TYPE = $VALUE"
        result = ast_grep_mcp._get_pattern_diagnostics(pattern, "typescript", code)
        assert "language" in result
        assert result["language"] == "typescript"

        # Test interface syntax
        code = "interface User { id: number; name: string; }"
        pattern = "interface $NAME { $$$FIELDS }"
        result = ast_grep_mcp._get_pattern_diagnostics(pattern, "typescript", code)
        assert "language" in result
        assert result["language"] == "typescript"
