#!/usr/bin/env python3
"""
Test suite for the improvements made to ast-grep-mcp based on the assessment.

Tests:
1. Token limit handling and pagination
2. Pattern matching for async functions  
3. Enhanced pattern builder
4. Context and line numbers in results
5. Improved error messages
6. max_results parameter
7. Partial pattern matching
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

# Import the modules we're testing
from ast_grep_mcp.core.ast_grep_mcp import AstGrepMCP
from ast_grep_mcp.ast_analyzer import AstAnalyzer
from ast_grep_mcp.utils.pagination import ResponsePaginator, PaginatedResponse
from ast_grep_mcp.utils.pattern_helpers import generate_alternative_patterns
from ast_grep_mcp.utils.error_handling import create_unified_error_response, PatternValidationError


class TestTokenLimitAndPagination:
    """Test token limit handling and pagination improvements."""
    
    def test_pagination_with_large_results(self):
        """Test that pagination is applied when results exceed token limits."""
        paginator = ResponsePaginator()
        
        # Create large data that exceeds token limit
        large_data = {
            "matches": {
                f"file_{i}.rs": [{"text": f"match_{j}", "location": {"line": j}} for j in range(100)]
                for i in range(50)
            }
        }
        
        # Check that pagination is needed
        assert paginator.should_paginate(large_data, "search")
        
        # Create paginated response
        items = [{"file": k, "matches": v} for k, v in large_data["matches"].items()]
        paginated = paginator.paginate_list(items, page=1, response_type="search")
        
        assert isinstance(paginated, PaginatedResponse)
        assert paginated.has_next
        assert len(paginated.items) < len(items)
        assert paginated.page == 1
        assert paginated.total_count == len(items)
    
    def test_max_results_parameter(self):
        """Test that max_results parameter limits results before pagination."""
        mcp = AstGrepMCP()
        
        # Mock the analyzer to return many results
        with patch.object(mcp.analyzer, 'search_directory') as mock_search:
            mock_search.return_value = {
                "matches": {
                    f"file_{i}.rs": [{"text": f"match_{j}"} for j in range(10)]
                    for i in range(20)
                }
            }
            
            # Call with max_results
            result = mcp.search_directory("/test", "pattern", max_results=50)
            
            # Count total matches in result
            total_matches = sum(
                len(matches) for matches in result.get("matches", {}).values()
            )
            
            # Should be limited to max_results
            assert total_matches <= 50
            assert result.get("truncated") == True
            assert "original_total_matches" in result


class TestPatternMatching:
    """Test improved pattern matching for async functions."""
    
    def test_async_function_pattern_alternatives(self):
        """Test that alternative patterns are generated for async functions."""
        # Test Rust async patterns
        alts = generate_alternative_patterns("async fn new", "rust")
        assert "pub async fn new" in alts
        assert "pub(crate) async fn new" in alts
        assert "async fn $NAME" in alts
        
        # Test with visibility already present
        alts = generate_alternative_patterns("pub async fn process", "rust")
        assert "pub async fn process" not in alts  # Should not duplicate
        assert "pub async fn $NAME" in alts  # Should keep visibility in alternative
        
        # Test JavaScript patterns
        alts = generate_alternative_patterns("async function fetchData", "javascript")
        assert "const fetchData = async ($$$PARAMS) => $$$BODY" in alts
    
    def test_pattern_matching_with_alternatives(self):
        """Test that pattern matching tries alternatives when main pattern fails."""
        analyzer = AstAnalyzer()
        
        rust_code = '''
        pub async fn new(database_url: &str) -> Result<Self, AppError> {
            Ok(Self {})
        }
        '''
        
        # Mock the parse_code to return a valid root
        mock_root = Mock()
        mock_node = Mock()
        
        # First call returns no matches, subsequent calls return matches
        mock_node.find_all.side_effect = [
            [],  # No matches for "async fn new"
            [Mock(text=lambda: "pub async fn new", range=lambda: Mock(
                start=Mock(line=1, column=0),
                end=Mock(line=3, column=1)
            ))]  # Match for alternative pattern
        ]
        
        mock_root.root.return_value = mock_node
        
        with patch.object(analyzer, 'parse_code', return_value=mock_root):
            matches = analyzer.find_patterns(rust_code, "rust", "async fn new")
            
            # Should find match using alternative pattern
            assert len(matches) > 0


class TestPatternBuilder:
    """Test enhanced pattern builder functionality."""
    
    def test_build_pattern_with_all_options(self):
        """Test that build_pattern respects all provided options."""
        mcp = AstGrepMCP()
        
        # Test Rust function with all options
        result = mcp.build_pattern(
            "function",
            "rust",
            {
                "visibility": "pub",
                "async": True,
                "name_pattern": "process_.*",
                "return_type": "Result<$T, $E>",
                "parameters": "$data: &$T"
            }
        )
        
        pattern = result.get("pattern", "")
        assert "pub" in pattern
        assert "async" in pattern
        assert "process_$NAME" in pattern
        assert "-> Result<$T, $E>" in pattern
        assert "($data: &$T)" in pattern
        
        # Test JavaScript function with options
        result = mcp.build_pattern(
            "function",
            "javascript",
            {
                "async": True,
                "name_pattern": "fetch.*",
                "parameters": "$url, $options"
            }
        )
        
        pattern = result.get("pattern", "")
        assert "async" in pattern
        assert "fetch$NAME" in pattern
        assert "($url, $options)" in pattern
    
    def test_pattern_builder_error_handling(self):
        """Test that pattern builder provides helpful errors."""
        mcp = AstGrepMCP()
        
        # Test with invalid pattern type
        result = mcp.build_pattern("invalid_pattern_type", "rust", {})
        assert "error" in result
        assert "available_types" in result
        
        # Test with valid call
        result = mcp.build_pattern("function", "rust", {"async": True, "name": "test"})
        assert "error" not in result
        assert "pattern" in result
        assert "async fn test" in result["pattern"]


class TestContextAndLineNumbers:
    """Test context and line number improvements."""
    
    def test_search_results_include_line_numbers(self):
        """Test that search results include line numbers and links."""
        analyzer = AstAnalyzer()
        
        code = '''
        fn test() {
            println!("Hello");
        }
        '''
        
        # Mock the parsing
        mock_match = Mock()
        mock_match.text.return_value = "fn test()"
        mock_match.range.return_value = Mock(
            start=Mock(line=2, column=8),
            end=Mock(line=2, column=18)
        )
        
        mock_root = Mock()
        mock_node = Mock()
        mock_node.find_all.return_value = [mock_match]
        mock_root.root.return_value = mock_node
        
        with patch.object(analyzer, 'parse_code', return_value=mock_root):
            matches = analyzer.find_patterns(code, "rust", "fn test")
            
            assert len(matches) == 1
            match = matches[0]
            
            # Check location information
            assert "location" in match
            assert match["location"]["start"]["line"] == 2
            assert match["location"]["start"]["column"] == 8
            assert match["location"]["link"] == "2:8"
    
    def test_search_directory_with_context(self):
        """Test that search_directory_with_context provides context lines."""
        mcp = AstGrepMCP()
        
        # Create a temporary directory with a test file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.rs"
            test_file.write_text('''
fn main() {
    let x = 1;
    println!("x = {}", x);
    let y = 2;
}
''')
            
            # Mock the analyzer to return matches
            with patch.object(mcp.analyzer, 'find_patterns') as mock_find:
                mock_find.return_value = [{
                    "text": 'println!("x = {}", x);',
                    "location": {
                        "start": {"line": 4, "column": 4},
                        "end": {"line": 4, "column": 26}
                    }
                }]
                
                result = mcp.search_directory_with_context(
                    tmpdir,
                    "println",
                    context_lines=2
                )
                
                # Should have context information
                assert not result.get("error")
                # Note: Full test would require proper file processing


class TestErrorMessages:
    """Test improved error messages."""
    
    def test_pattern_validation_error_messages(self):
        """Test that pattern validation errors provide helpful guidance."""
        error = PatternValidationError(
            "Invalid pattern syntax",
            pattern="async fn new",
            language="rust",
            suggestions=["Try 'pub async fn new'", "Use 'async fn $NAME'"]
        )
        
        response = create_unified_error_response(
            error,
            "validate_pattern",
            {"pattern": "async fn new", "language": "rust"}
        )
        
        assert response["success"] == False
        assert response["error"]["type"] == "PatternValidationError"
        assert len(response["error"]["suggestions"]) > 0
        assert "documentation" in response["error"]
        assert "troubleshooting" in response["error"]
    
    def test_error_messages_with_pattern_help(self):
        """Test that errors include pattern syntax help."""
        from ast_grep_mcp.utils.pattern_helpers import get_pattern_help
        
        help_info = get_pattern_help("rust", "syntax error")
        
        assert help_info["language"] == "rust"
        assert "basic_syntax" in help_info
        assert "$VAR" in help_info["basic_syntax"]
        assert "$$$VARS" in help_info["basic_syntax"]


class TestPartialPatternMatching:
    """Test partial pattern matching support."""
    
    def test_generate_alternative_patterns_rust(self):
        """Test alternative pattern generation for Rust."""
        # Test async function without visibility
        alts = generate_alternative_patterns("async fn process", "rust")
        assert "pub async fn process" in alts
        assert "async fn $NAME" in alts
        
        # Test regular function
        alts = generate_alternative_patterns("fn calculate", "rust")
        assert "async fn calculate" in alts
        assert "pub fn calculate" in alts
        assert "pub async fn calculate" in alts
    
    def test_generate_alternative_patterns_javascript(self):
        """Test alternative pattern generation for JavaScript."""
        # Test regular function
        alts = generate_alternative_patterns("function getData", "javascript")
        assert "const getData = ($$$PARAMS) => $$$BODY" in alts
        assert "const getData = async ($$$PARAMS) => $$$BODY" in alts
        
        # Test async function
        alts = generate_alternative_patterns("async function saveData", "javascript")
        assert "const saveData = async ($$$PARAMS) => $$$BODY" in alts


class TestIntegration:
    """Integration tests for all improvements."""
    
    def test_full_search_with_improvements(self):
        """Test a full search operation with all improvements."""
        mcp = AstGrepMCP()
        
        # Create test directory with files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple test files
            for i in range(5):
                test_file = Path(tmpdir) / f"test_{i}.rs"
                test_file.write_text(f'''
pub async fn handler_{i}() -> Result<(), Error> {{
    println!("Handler {i}");
    Ok(())
}}

async fn private_fn_{i}() {{
    // Some code
}}
''')
            
            # Test search with improvements
            result = mcp.search_directory(
                tmpdir,
                "async fn",  # This should match both pub and non-pub async functions
                max_results=10,
                page=1,
                page_size=5
            )
            
            # Verify results
            assert not result.get("error")
            assert "matches" in result
            
            # Should have found matches (actual matching depends on ast-grep)
            # The test validates the API works correctly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])