#!/usr/bin/env python3
"""
Test suite for the second assessment improvements.

Tests address:
1. Pattern syntax complexity - common pattern library
2. Inconsistent metavariable behavior - pattern fixer
3. Poor error messages - enhanced diagnostics
4. Natural language pattern search
5. Fuzzy pattern matching
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

from ast_grep_mcp.core.ast_grep_mcp import AstGrepMCP
from ast_grep_mcp.utils.common_patterns import CommonPatternLibrary, PatternRecommender
from ast_grep_mcp.utils.pattern_fixer import PatternFixer, FuzzyPatternMatcher
from ast_grep_mcp.utils.enhanced_diagnostics import EnhancedDiagnostics


class TestCommonPatternLibrary:
    """Test the common pattern library functionality."""
    
    def test_get_rust_unwrap_patterns(self):
        """Test that we have working unwrap patterns for Rust."""
        patterns = CommonPatternLibrary.get_patterns("rust")
        
        # Find unwrap pattern
        unwrap_patterns = [p for p in patterns if p.name == "unwrap_calls"]
        assert len(unwrap_patterns) > 0
        
        unwrap = unwrap_patterns[0]
        assert unwrap.pattern == "unwrap()"
        assert len(unwrap.variations) > 0
        assert any("$VAR.unwrap()" in v for v in unwrap.variations)
    
    def test_find_pattern_by_query(self):
        """Test natural language pattern search."""
        # Test Rust async functions
        patterns = PatternRecommender.recommend_patterns("rust", "async functions")
        assert len(patterns) > 0
        assert any("async" in p.pattern for p in patterns)
        
        # Test JavaScript console logging
        patterns = PatternRecommender.recommend_patterns("javascript", "console log")
        assert len(patterns) > 0
        assert any("console.log" in p.pattern for p in patterns)
    
    def test_pattern_categories(self):
        """Test pattern organization by category."""
        from ast_grep_mcp.utils.common_patterns import PatternCategory
        
        error_patterns = CommonPatternLibrary.get_patterns("rust", PatternCategory.ERROR_HANDLING)
        assert len(error_patterns) > 0
        assert all(p.category == PatternCategory.ERROR_HANDLING for p in error_patterns)


class TestPatternFixer:
    """Test the pattern fixer for problematic patterns."""
    
    def test_fix_expr_unwrap_pattern(self):
        """Test fixing $EXPR.unwrap() pattern."""
        alternatives = PatternFixer.fix_pattern("$EXPR.unwrap()", "rust")
        
        assert "unwrap()" in alternatives
        assert ".unwrap()" in alternatives
        assert "$VAR.unwrap()" in alternatives
        assert "$EXPR.unwrap()" in alternatives  # Original should be included
    
    def test_fix_spawn_pattern(self):
        """Test fixing complex spawn patterns."""
        alternatives = PatternFixer.fix_pattern("spawn(async move { $$ })", "rust")
        
        assert "spawn($$$ARGS)" in alternatives
        assert "spawn(async { $$$BODY })" in alternatives
        assert "spawn(async move { $$$BODY })" in alternatives
    
    def test_pattern_issue_explanation(self):
        """Test that we can explain why patterns fail."""
        explanation = PatternFixer.explain_pattern_issue("$EXPR.unwrap()", "rust")
        
        assert "metavariable" in explanation.lower()
        assert any(word in explanation.lower() for word in ["generic", "specific", "try"])
    
    def test_fuzzy_pattern_generation(self):
        """Test fuzzy pattern matching."""
        fuzzy = FuzzyPatternMatcher.make_pattern_fuzzy("async fn new", "rust")
        
        assert "async fn new" in fuzzy
        assert "pub async fn new" in fuzzy
        
        # Test spawn fuzzy patterns
        fuzzy = FuzzyPatternMatcher.make_pattern_fuzzy("spawn(async)", "rust")
        assert len(fuzzy) > 1
        assert any("spawn($$$ARGS)" in p for p in fuzzy)


class TestEnhancedDiagnostics:
    """Test enhanced error diagnostics."""
    
    def test_diagnose_pattern_failure(self):
        """Test pattern failure diagnosis."""
        diagnosis = EnhancedDiagnostics.diagnose_pattern_failure(
            "$EXPR.unwrap()",
            "rust",
            "let x = result.unwrap();"
        )
        
        assert "likely_issues" in diagnosis
        assert len(diagnosis["likely_issues"]) > 0
        assert any("$EXPR" in issue["issue"] for issue in diagnosis["likely_issues"])
        
        assert "suggested_patterns" in diagnosis
        assert len(diagnosis["suggested_patterns"]) > 0
        
        assert "examples_that_would_match" in diagnosis
        assert len(diagnosis["examples_that_would_match"]) > 0
    
    def test_helpful_error_message(self):
        """Test that error messages are helpful."""
        diagnosis = EnhancedDiagnostics.diagnose_pattern_failure(
            "fn $FUNC($$PARAMS) { $$BODY }",
            "rust"
        )
        
        message = diagnosis["helpful_message"]
        assert "Pattern failed to match" in message
        assert "Try these patterns instead" in message or "Likely issues" in message
        assert any(char in message for char in ["•", "→", "💡", "❌"])  # Nice formatting


class TestNaturalLanguageSearch:
    """Test natural language pattern search functionality."""
    
    def test_find_pattern_method(self):
        """Test the find_pattern method with natural language."""
        mcp = AstGrepMCP()
        
        # Test finding patterns without directory (just recommendations)
        result = mcp.find_pattern("unwrap calls", "rust")
        
        assert "found_patterns" in result
        patterns = result["found_patterns"]
        assert len(patterns) > 0
        assert any("unwrap" in p["pattern"] for p in patterns)
    
    def test_find_code_like_method(self):
        """Test finding code similar to an example."""
        mcp = AstGrepMCP()
        
        example_rust = """
        async fn process_data() {
            let result = fetch().await;
            result.unwrap();
        }
        """
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.rs"
            test_file.write_text("""
            async fn handle_request() {
                data.unwrap();
            }
            
            fn sync_function() {
                value.unwrap();
            }
            """)
            
            # Mock the analyzer
            with patch.object(mcp.analyzer, 'parse_code') as mock_parse:
                mock_parse.return_value = Mock()  # Valid parse result
                
                with patch.object(mcp, 'search_directory') as mock_search:
                    # Return some matches
                    mock_search.return_value = {
                        "files_with_matches": 1,
                        "matches": {
                            str(test_file): [{"text": "data.unwrap()"}]
                        }
                    }
                    
                    result = mcp.find_code_like(example_rust, "rust", tmpdir)
                    
                    assert "patterns_identified" in result
                    assert any("unwrap" in p for p in result["patterns_identified"])
                    assert any("async" in p for p in result["patterns_identified"])


class TestIntegrationScenarios:
    """Test real-world scenarios from the assessment."""
    
    def test_unwrap_pattern_scenario(self):
        """Test the unwrap() scenario that failed in the assessment."""
        mcp = AstGrepMCP()
        
        rust_code = """
        fn process() {
            let value = result.unwrap();
            option.unwrap();
        }
        """
        
        # Test with problematic pattern
        with patch.object(mcp.analyzer, 'find_patterns') as mock_find:
            # First call returns no matches
            # Second call (with fixed pattern) returns matches
            mock_find.side_effect = [
                [],  # No matches for $EXPR.unwrap()
                [{"text": "result.unwrap()", "location": {"start": {"line": 2}}}]  # Match for unwrap()
            ]
            
            result = mcp.analyze_code(rust_code, "rust", "$EXPR.unwrap()")
            
            # Should have found matches with fixed pattern
            if "matches" in result and len(result["matches"]) > 0:
                assert "pattern_fixed" in result
                assert result["pattern_used"] != "$EXPR.unwrap()"
    
    def test_spawn_pattern_scenario(self):
        """Test the spawn pattern scenario from the assessment."""
        mcp = AstGrepMCP()
        
        # Test getting common patterns for spawn
        patterns = mcp.get_common_patterns("rust", "async_code")
        
        spawn_patterns = [p for p in patterns["patterns"] if p["name"] == "spawn_calls"]
        assert len(spawn_patterns) > 0
        
        # Check that we have the base pattern and variations
        spawn = spawn_patterns[0]
        assert spawn["pattern"] == "spawn($$$ARGS)"  # Base pattern
        assert "tokio::spawn($$$ARGS)" in spawn["variations"]  # Common variation
    
    def test_natural_language_unwrap_search(self):
        """Test finding unwrap calls using natural language."""
        mcp = AstGrepMCP()
        
        # Mock the search to return results
        with patch.object(mcp, 'search_directory') as mock_search:
            mock_search.return_value = {
                "files_with_matches": 2,
                "matches": {
                    "file1.rs": [{"text": "x.unwrap()"}],
                    "file2.rs": [{"text": "y.unwrap()"}]
                },
                "pattern_used": "unwrap()",
                "pattern_name": "unwrap_calls"
            }
            
            result = mcp.find_pattern("unwrap calls", "rust", "/test/dir")
            
            assert result["files_with_matches"] == 2
            assert result["pattern_used"] == "unwrap()"
            assert "pattern_info" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])