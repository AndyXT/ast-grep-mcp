"""
Tests for pattern autocorrection functionality.
"""

from ast_grep_mcp.utils.pattern_autocorrect import (
    PatternAutoCorrector,
    PatternSuggestion,
    create_pattern_suggestion_message,
)


class TestPatternAutoCorrector:
    """Test the PatternAutoCorrector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.corrector = PatternAutoCorrector()

    def test_basic_corrections(self):
        """Test basic pattern corrections."""
        # Double dollar to triple dollar
        suggestions = self.corrector.suggest_corrections("$$PARAMS", "python")
        assert len(suggestions) > 0
        assert "$$$PARAMS" in [s.suggested for s in suggestions]

        # Space after dollar
        suggestions = self.corrector.suggest_corrections("$ VAR = $VALUE", "python")
        assert len(suggestions) > 0
        assert "$VAR = $VALUE" in [s.suggested for s in suggestions]

        # Missing dollar sign
        suggestions = self.corrector.suggest_corrections("if CONDITION:", "python")
        assert len(suggestions) > 0
        assert "if $CONDITION:" in [s.suggested for s in suggestions]

    def test_language_specific_corrections(self):
        """Test language-specific corrections."""
        # Python missing colon
        suggestions = self.corrector.suggest_corrections(
            "def $NAME($$$PARAMS)", "python"
        )
        assert len(suggestions) > 0
        assert "def $NAME($$$PARAMS):" in [s.suggested for s in suggestions]

        # JavaScript arrow function
        suggestions = self.corrector.suggest_corrections("=> $EXPR", "javascript")
        assert len(suggestions) > 0
        assert "() => $EXPR" in [s.suggested for s in suggestions]

        # Template literal fix
        suggestions = self.corrector.suggest_corrections(
            "'hello ${$NAME}'", "javascript"
        )
        assert len(suggestions) > 0
        assert "`hello ${$NAME}`" in [s.suggested for s in suggestions]

    def test_typo_corrections(self):
        """Test typo corrections."""
        # Function typo
        suggestions = self.corrector.suggest_corrections(
            "fucntion $NAME() {}", "javascript"
        )
        assert len(suggestions) > 0
        assert "function $NAME() {}" in [s.suggested for s in suggestions]

        # Class typo
        suggestions = self.corrector.suggest_corrections("clss $NAME:", "python")
        assert len(suggestions) > 0
        assert "class $NAME:" in [s.suggested for s in suggestions]

    def test_template_matching(self):
        """Test pattern template matching."""
        # Close to function pattern
        suggestions = self.corrector.suggest_corrections("def NAME(PARAMS):", "python")
        assert len(suggestions) > 0
        # Should suggest adding dollar signs
        assert any("def $NAME($$$PARAMS):" in s.suggested for s in suggestions)

        # Close to for loop
        suggestions = self.corrector.suggest_corrections("for VAR in ITER:", "python")
        assert len(suggestions) > 0
        assert any("for $VAR in $ITER:" in s.suggested for s in suggestions)

    def test_auto_correct_pattern(self):
        """Test automatic pattern correction."""
        # High confidence correction
        corrected = self.corrector.auto_correct_pattern("$$PARAMS", "python")
        assert corrected == "$$$PARAMS"

        # Low confidence - should return None
        corrected = self.corrector.auto_correct_pattern("some random text", "python")
        assert corrected is None

    def test_quick_fixes(self):
        """Test quick fixes for specific error types."""
        # Unclosed bracket
        fixes = self.corrector.get_quick_fixes(
            "if ($COND", "javascript", "unclosed_bracket"
        )
        assert "if ($COND)" in fixes

        # Missing dollar
        fixes = self.corrector.get_quick_fixes(
            "if CONDITION:", "python", "missing_dollar"
        )
        assert "if $CONDITION:" in fixes

        # Invalid variadic
        fixes = self.corrector.get_quick_fixes(
            "function $NAME($$PARAMS)", "javascript", "invalid_variadic"
        )
        assert "function $NAME($$$PARAMS)" in fixes

    def test_multiple_corrections(self):
        """Test patterns needing multiple corrections."""
        # Multiple issues
        suggestions = self.corrector.suggest_corrections(
            "fucntion NAME($$PARAMS) {", "javascript"
        )
        assert len(suggestions) > 0
        # Should fix typo, add dollar, and fix variadic
        top_suggestion = suggestions[0].suggested
        assert "function" in top_suggestion
        assert "$NAME" in top_suggestion
        assert "$$$PARAMS" in top_suggestion

    def test_suggestion_confidence(self):
        """Test suggestion confidence scores."""
        suggestions = self.corrector.suggest_corrections("$$PARAMS", "python")
        assert len(suggestions) > 0
        # Direct rule-based correction should have high confidence
        assert suggestions[0].confidence > 0.8

        suggestions = self.corrector.suggest_corrections("some pattern", "python")
        if suggestions:
            # Template matches should have lower confidence
            assert all(s.confidence <= 0.9 for s in suggestions)

    def test_rust_patterns(self):
        """Test Rust-specific patterns."""
        # Missing semicolon
        suggestions = self.corrector.suggest_corrections("let $VAR = $VALUE", "rust")
        assert len(suggestions) > 0
        assert "let $VAR = $VALUE;" in [s.suggested for s in suggestions]

        # Struct pattern
        suggestions = self.corrector.suggest_corrections(
            "struct NAME { FIELDS }", "rust"
        )
        assert len(suggestions) > 0
        assert any("struct $NAME { $$$FIELDS }" in s.suggested for s in suggestions)

    def test_go_patterns(self):
        """Test Go-specific patterns."""
        # Function pattern
        suggestions = self.corrector.suggest_corrections("func NAME() {}", "go")
        assert len(suggestions) > 0
        assert any("func $NAME() {}" in s.suggested for s in suggestions)

    def test_c_patterns(self):
        """Test C-specific patterns."""
        # Struct pattern
        suggestions = self.corrector.suggest_corrections("struct NAME { FIELDS };", "c")
        assert len(suggestions) > 0
        assert any("struct $NAME { $$$FIELDS };" in s.suggested for s in suggestions)


class TestSuggestionMessage:
    """Test suggestion message formatting."""

    def test_create_message(self):
        """Test creating a suggestion message."""
        suggestions = [
            PatternSuggestion(
                original="$$PARAMS",
                suggested="$$$PARAMS",
                confidence=0.9,
                reason="Applied automatic fixes",
                applied_fixes=["Convert $$ to $$$ for variadic capture"],
            ),
            PatternSuggestion(
                original="$$PARAMS",
                suggested="$PARAMS",
                confidence=0.6,
                reason="Alternative fix",
                applied_fixes=["Convert to single capture"],
            ),
        ]

        message = create_pattern_suggestion_message(suggestions)
        assert "Pattern correction suggestions:" in message
        assert "$$$PARAMS" in message
        assert "90%" in message
        assert "Convert $$ to $$$ for variadic capture" in message

    def test_empty_suggestions(self):
        """Test message for empty suggestions."""
        message = create_pattern_suggestion_message([])
        assert message == "No suggestions available."
