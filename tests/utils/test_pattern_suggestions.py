from unittest.mock import patch, MagicMock
from ast_grep_mcp.utils.pattern_suggestions import (
    get_pattern_variants,
    get_similar_patterns,
    suggest_patterns,
    build_suggestion_message,
)


class TestPatternSuggestions:
    """Tests for the pattern suggestion system"""

    def test_get_pattern_variants(self):
        """Test generation of pattern variants"""
        # Test with function definition pattern
        pattern = "def $FUNCTION_NAME($$$PARAMS):"
        variants = get_pattern_variants(pattern)

        # Should have multiple variants
        assert len(variants) > 0

        # Should include a variant with wildcard for function name
        assert any("def $_($$$" in v for v in variants)

        # Should include a variant with wildcard for params
        assert "def $FUNCTION_NAME($$$_):" in variants

    def test_get_pattern_variants_multiline(self):
        """Test variant generation for multiline patterns"""
        pattern = "def $NAME($$$PARAMS):\n    $$$BODY"
        variants = get_pattern_variants(pattern)

        # Should have multiple variants
        assert len(variants) > 0

        # Should include a variant with just the first line
        assert "def $NAME($$$PARAMS):" in variants

    @patch("ast_grep_mcp.utils.pattern_suggestions.get_handler")
    def test_get_similar_patterns(self, mock_get_handler):
        """Test finding similar patterns from the library"""
        # Create mock handler with patterns
        mock_handler = MagicMock()
        mock_handler.get_default_patterns.return_value = {
            "function_definition": "def $NAME($$$PARAMS):",
            "function_call": "$NAME($$$ARGS)",
            "if_statement": "if $CONDITION:",
        }
        mock_get_handler.return_value = mock_handler

        # Python function pattern
        pattern = "def my_function(arg1, arg2):"
        similar = get_similar_patterns(pattern, "python")

        # Should find similar patterns for function definitions
        assert len(similar) > 0

        # First result should be a function definition pattern
        assert "function_definition" in similar[0][0]

    @patch("ast_grep_mcp.utils.pattern_suggestions.get_handler")
    def test_get_similar_patterns_non_existent_language(self, mock_get_handler):
        """Test with a language that doesn't exist"""
        mock_get_handler.return_value = None
        similar = get_similar_patterns("pattern", "non_existent_language")
        assert similar == []

    @patch("ast_grep_mcp.utils.pattern_suggestions.get_handler")
    def test_suggest_patterns(self, mock_get_handler):
        """Test the complete pattern suggestion system"""
        # Create mock handler with patterns
        mock_handler = MagicMock()
        mock_handler.get_default_patterns.return_value = {
            "function_definition": "def $NAME($$$PARAMS):",
            "function_call": "$NAME($$$ARGS)",
            "if_statement": "if $CONDITION:",
        }
        mock_get_handler.return_value = mock_handler

        python_code = """
def example_function(a, b):
    result = a + b
    return result

class MyClass:
    def __init__(self, value):
        self.value = value
        """

        # Test with a pattern that won't match
        pattern = "def my_function($$$):"
        suggestions = suggest_patterns(pattern, python_code, "python")

        # Should have suggestions in all categories
        assert "variants" in suggestions
        assert "similar_patterns" in suggestions
        assert "examples" in suggestions

        # Should have at least one variant
        assert len(suggestions["variants"]) > 0

        # Should have at least one similar pattern
        assert len(suggestions["similar_patterns"]) > 0

        # Should have at least one example
        assert len(suggestions["examples"]) > 0

    def test_build_suggestion_message(self):
        """Test building a user-friendly message with suggestions"""
        suggestions = {
            "variants": ["def $_($$$):", "def $NAME($$$_):"],
            "similar_patterns": ["function_definition: def $NAME($$$PARAMS):"],
            "examples": ["def $NAME($$$PARAMS):", "class $NAME:"],
        }

        message = build_suggestion_message(
            "def my_function($$$):", "python", suggestions
        )

        # Message should include the pattern
        assert "def my_function($$$):" in message

        # Message should mention the language
        assert "python" in message

        # Should include "Did you mean"
        assert "Did you mean" in message

        # Should include variants
        assert "def $_($$$):" in message

        # Should include similar patterns
        assert "function_definition" in message

        # Should include examples
        assert "Example patterns" in message

        # Should include tips
        assert "Pattern writing tips" in message

    @patch("ast_grep_mcp.utils.pattern_suggestions.get_handler")
    def test_suggestions_have_actionable_content(self, mock_get_handler):
        """Test that suggestions are actionable and helpful"""
        # Create mock handler with patterns
        mock_handler = MagicMock()
        mock_handler.get_default_patterns.return_value = {
            "function_definition": "def $NAME($$$PARAMS):",
            "function_with_body": "def $NAME($$$PARAMS):\n    $$$BODY",
        }
        mock_get_handler.return_value = mock_handler

        python_code = """
def example_function(a, b):
    return a + b
        """

        # Test with a slightly incorrect pattern
        pattern = "def example_function(a, b) {"
        suggestions = suggest_patterns(pattern, python_code, "python")

        # Should have variants that are closer to Python syntax
        assert any(":" in v for v in suggestions["variants"])

        # The message should be helpful
        message = build_suggestion_message(pattern, "python", suggestions)

        # Check that the message is helpful
        assert ":" in message  # Python uses : not { for blocks

        # Check the pattern variants are useful
        variants = suggestions["variants"]
        assert any(
            ("example_function" in v and ":" in v) for v in variants
        ), f"No useful variants among: {variants}"

        # Check for at least some examples
        assert len(suggestions["examples"]) > 0
