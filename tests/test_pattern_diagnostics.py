"""
Tests for enhanced pattern diagnostics and error recovery.
"""

from ast_grep_mcp.utils.pattern_diagnostics import (
    PatternAnalyzer,
    create_enhanced_diagnostic,
)


class TestPatternAnalyzer:
    """Test the PatternAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PatternAnalyzer()

    def test_empty_pattern(self):
        """Test empty pattern detection."""
        result = self.analyzer.analyze_pattern("", "python")
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].type == "empty_pattern"

    def test_bracket_balance(self):
        """Test bracket balance checking."""
        # Unclosed bracket
        result = self.analyzer.analyze_pattern("if ($COND {", "javascript")
        assert not result.is_valid
        errors = [e for e in result.errors if e.type == "unclosed_bracket"]
        assert len(errors) == 1

        # Extra closing bracket
        result = self.analyzer.analyze_pattern("if $COND)", "python")
        assert not result.is_valid
        errors = [e for e in result.errors if e.type == "extra_closing_bracket"]
        assert len(errors) == 1

        # Mismatched brackets
        result = self.analyzer.analyze_pattern("[$ITEM}", "python")
        assert not result.is_valid
        errors = [e for e in result.errors if e.type == "mismatched_bracket"]
        assert len(errors) == 1

    def test_metavariable_validation(self):
        """Test metavariable syntax validation."""
        # Invalid double dollar
        result = self.analyzer.analyze_pattern("$$PARAMS", "python")
        assert not result.is_valid
        errors = [e for e in result.errors if e.type == "invalid_variadic"]
        assert len(errors) == 1
        assert errors[0].auto_fixable

        # Invalid name starting with number
        result = self.analyzer.analyze_pattern("$123VAR", "python")
        assert not result.is_valid
        errors = [e for e in result.errors if e.type == "invalid_metavar_name"]
        assert len(errors) == 1

        # Valid metavariables
        result = self.analyzer.analyze_pattern("$VAR = $$$VALUES", "python")
        assert result.is_valid

    def test_language_specific_validation(self):
        """Test language-specific pattern validation."""
        # Python missing colon
        result = self.analyzer.analyze_pattern("if $COND", "python")
        errors = [e for e in result.errors if e.type == "missing_colon"]
        assert len(errors) == 1

        # JavaScript invalid arrow function
        result = self.analyzer.analyze_pattern("=> $EXPR", "javascript")
        errors = [e for e in result.errors if e.type == "invalid_arrow_function"]
        assert len(errors) == 1

    def test_auto_correction(self):
        """Test automatic pattern correction."""
        # Double dollar to triple dollar
        result = self.analyzer.analyze_pattern("function $NAME($$PARAMS)", "javascript")
        assert result.corrected_pattern == "function $NAME($$$PARAMS)"
        assert result.confidence_score > 0.8

        # Space after dollar
        result = self.analyzer.analyze_pattern("$ VAR = $VALUE", "python")
        assert result.corrected_pattern == "$VAR = $VALUE"

        # Missing closing bracket
        result = self.analyzer.analyze_pattern("if ($COND", "javascript")
        assert result.corrected_pattern == "if ($COND)"

        # Python missing colon
        result = self.analyzer.analyze_pattern("def $NAME($$$PARAMS)", "python")
        assert result.corrected_pattern == "def $NAME($$$PARAMS):"

    def test_pattern_suggestions(self):
        """Test pattern suggestions."""
        # Similar to function definition
        result = self.analyzer.analyze_pattern("func $NAME($$$PARAMS)", "python")
        assert len(result.suggestions) > 0
        assert any("Did you mean" in s for s in result.suggestions)


class TestEnhancedDiagnostic:
    """Test the create_enhanced_diagnostic function."""

    def test_basic_diagnostic(self):
        """Test basic diagnostic creation."""
        result = create_enhanced_diagnostic("$VAR = $VALUE", "python")
        assert result["is_valid"]
        assert result["pattern"] == "$VAR = $VALUE"
        assert result["language"] == "python"

    def test_error_diagnostic(self):
        """Test diagnostic with errors."""
        result = create_enhanced_diagnostic("$$ARGS", "python")
        assert not result["is_valid"]
        assert len(result["errors"]) > 0
        assert "help_message" in result

    def test_diagnostic_with_correction(self):
        """Test diagnostic with auto-correction."""
        result = create_enhanced_diagnostic("function $NAME($$PARAMS) {", "javascript")
        assert not result["is_valid"]  # Unclosed brace
        assert "corrected_pattern" in result
        assert result["corrected_pattern"] == "function $NAME($$$PARAMS) {}"
        assert result["correction_confidence"] > 0.7

    def test_diagnostic_with_error_message(self):
        """Test diagnostic with external error message."""
        result = create_enhanced_diagnostic(
            "invalid pattern", "python", "Syntax error: unexpected token"
        )
        assert not result["is_valid"]
        assert result["original_error"] == "Syntax error: unexpected token"
        assert "help_message" in result

    def test_complex_pattern_diagnostic(self):
        """Test diagnostic for complex patterns."""
        pattern = """
        class $NAME:
            def __init__(self, $$PARAMS):
                $$$BODY
        """
        result = create_enhanced_diagnostic(pattern, "python")
        # Should detect double dollar issue
        assert not result["is_valid"]
        errors = result["errors"]
        variadic_errors = [e for e in errors if e["type"] == "invalid_variadic"]
        assert len(variadic_errors) > 0

        # Should have correction
        assert "corrected_pattern" in result
        assert "$$$PARAMS" in result["corrected_pattern"]


class TestRealWorldPatterns:
    """Test with real-world pattern examples."""

    def test_common_mistakes(self):
        """Test common pattern mistakes."""
        test_cases = [
            # Missing dollar sign
            ("if CONDITION:", "python", False),
            # Space after dollar
            ("$ NAME = $VALUE", "python", False),
            # Wrong variadic syntax
            ("console.log($$ARGS)", "javascript", False),
            # Unclosed brackets
            ("match $EXPR { $$$ARMS", "rust", False),
            # Valid patterns
            ("$VAR = $VALUE", "python", True),
            ("function $NAME($$$PARAMS) { $$$BODY }", "javascript", True),
            ("fn $NAME($$$PARAMS) -> $RET { $$$BODY }", "rust", True),
        ]

        for pattern, language, should_be_valid in test_cases:
            result = create_enhanced_diagnostic(pattern, language)
            assert result["is_valid"] == should_be_valid, f"Pattern: {pattern}"

            # Invalid patterns should have corrections or suggestions
            if not should_be_valid:
                assert (
                    "corrected_pattern" in result
                    or "suggestions" in result
                    or "errors" in result
                )

    def test_language_specific_patterns(self):
        """Test language-specific pattern validation."""
        # Python patterns
        python_patterns = [
            ("def $NAME($$$PARAMS):", True),
            ("class $NAME($BASE):", True),
            ("if $COND", False),  # Missing colon
            ("for $VAR in $ITER", False),  # Missing colon
        ]

        for pattern, should_be_valid in python_patterns:
            result = create_enhanced_diagnostic(pattern, "python")
            assert result["is_valid"] == should_be_valid

        # JavaScript patterns
        js_patterns = [
            ("($$$PARAMS) => $EXPR", True),
            ("const $NAME = ($$$PARAMS) => { $$$BODY }", True),
            ("<$COMPONENT $$$PROPS />", True),  # JSX
            ("=> $EXPR", False),  # Invalid arrow function
        ]

        for pattern, should_be_valid in js_patterns:
            result = create_enhanced_diagnostic(pattern, "javascript")
            assert result["is_valid"] == should_be_valid
