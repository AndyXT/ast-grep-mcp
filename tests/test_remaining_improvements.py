#!/usr/bin/env python3
"""
Test suite for the remaining improvements.

Tests address:
1. Complex pattern syntax fixes (spawn patterns)
2. Pattern builder
3. Pattern templates
4. Batch search
5. Streaming support
"""

import pytest
from unittest.mock import patch
import tempfile

from ast_grep_mcp.core.ast_grep_mcp import AstGrepMCP
from ast_grep_mcp.utils.simple_pattern_builder import SimplePatternBuilder, create_pattern_for_concept
from ast_grep_mcp.utils.pattern_templates import PatternTemplateLibrary
from ast_grep_mcp.utils.batch_operations import BatchSearcher, BatchSearchRequest, create_code_quality_batch
from ast_grep_mcp.utils.auto_paginate import SearchResultStream, create_search_stream


class TestPatternBuilder:
    """Test the simplified pattern builder."""
    
    def test_rust_function_pattern(self):
        """Test building Rust function patterns."""
        builder = SimplePatternBuilder("rust")
        
        # Simple function
        pattern = builder.function().build()
        assert pattern == "fn $NAME"
        
        # Function with params and body
        pattern = builder.function().with_params().with_body().build()
        assert pattern == "fn $NAME($$$PARAMS) { $$$BODY }"
        
        # Async function with return type
        pattern = builder.async_function().with_params().returns("Result<()>").with_body().build()
        assert pattern == "async fn $NAME($$$PARAMS) -> Result<()> { $$$BODY }"
    
    def test_python_patterns(self):
        """Test building Python patterns."""
        builder = SimplePatternBuilder("python")
        
        # Function pattern
        pattern = builder.function().with_params().with_body().build()
        assert pattern == "def $NAME($$$PARAMS):\n    $$$BODY"
        
        # Async function
        pattern = builder.async_function().with_params().with_body().build()
        assert pattern == "async def $NAME($$$PARAMS):\n    $$$BODY"
    
    def test_javascript_patterns(self):
        """Test building JavaScript patterns."""
        builder = SimplePatternBuilder("javascript")
        
        # Regular function
        pattern = builder.function().with_params().with_body().build()
        assert pattern == "function $NAME($$$PARAMS) { $$$BODY }"
        
        # Method call
        pattern = builder.method_call().build()
        assert pattern == "$OBJ.$METHOD($$$ARGS)"
    
    def test_spawn_patterns(self):
        """Test spawn pattern building."""
        builder = SimplePatternBuilder("rust")
        
        # General spawn (should work)
        pattern = builder.spawn_call(with_block=False).build()
        assert pattern == "spawn($$$ARGS)"
        
        # Spawn with block (might not match)
        pattern = builder.spawn_call(with_block=True).build()
        assert pattern == "spawn(async move { $$$BODY })"
    
    def test_pattern_from_example(self):
        """Test creating pattern from example."""
        example = 'fn process_data(input: &str) -> Result<()> { Ok(()) }'
        pattern = SimplePatternBuilder.from_example(example, "rust")
        
        assert "fn $NAME" in pattern
        # Note: &str is not a string literal, so won't be replaced
        # String literals would be in quotes like "hello"
    
    def test_pattern_for_concept(self):
        """Test creating patterns for concepts."""
        # Rust spawn concept
        result = create_pattern_for_concept("spawn tasks", "rust")
        assert len(result["patterns"]) > 0
        assert "spawn($$$ARGS)" in result["patterns"]
        
        # Rust error handling
        result = create_pattern_for_concept("error handling", "rust")
        assert len(result["patterns"]) > 0
        assert "unwrap()" in result["patterns"]


class TestPatternTemplates:
    """Test pattern template library."""
    
    def test_get_rust_templates(self):
        """Test Rust pattern templates."""
        templates = PatternTemplateLibrary.rust_templates()
        
        # Check unwrap_to_expect template
        assert "unwrap_to_expect" in templates
        template = templates["unwrap_to_expect"]
        assert template.pattern == "$EXPR.unwrap()"
        assert template.replacement == '$EXPR.expect("$MESSAGE")'
        assert len(template.example_matches) > 0
    
    def test_get_template_by_name(self):
        """Test getting specific template."""
        template = PatternTemplateLibrary.get_template("unwrap_to_expect", "rust")
        assert template is not None
        assert template.name == "unwrap_to_expect"
        
        # Non-existent template
        template = PatternTemplateLibrary.get_template("nonexistent", "rust")
        assert template is None
    
    def test_spawn_template(self):
        """Test spawn pattern template."""
        templates = PatternTemplateLibrary.rust_templates()
        spawn_template = templates["async_block_spawn"]
        
        assert spawn_template.pattern == "spawn($$$ARGS)"
        assert spawn_template.category == "async"
        assert len(spawn_template.example_matches) > 0
    
    def test_javascript_templates(self):
        """Test JavaScript templates."""
        templates = PatternTemplateLibrary.javascript_templates()
        
        assert "console_to_logger" in templates
        template = templates["console_to_logger"]
        assert template.pattern == "console.log($$$ARGS)"
        assert template.replacement == "logger.info($$$ARGS)"


class TestBatchOperations:
    """Test batch search operations."""
    
    def test_batch_search_request(self):
        """Test batch search request creation."""
        request = BatchSearchRequest(
            pattern="unwrap()",
            name="unwrap_calls",
            category="error_handling",
            severity="warning"
        )
        
        assert request.pattern == "unwrap()"
        assert request.name == "unwrap_calls"
        assert request.severity == "warning"
    
    def test_code_quality_batch(self):
        """Test creating code quality batch."""
        batch = create_code_quality_batch("rust")
        
        assert len(batch) > 0
        
        # Check for key patterns
        pattern_names = [req.name for req in batch]
        assert "unwrap_calls" in pattern_names
        assert "panic_calls" in pattern_names
        assert "unsafe_blocks" in pattern_names
    
    def test_batch_searcher(self):
        """Test batch searcher with mocked search."""
        # Mock search function
        def mock_search(directory, pattern, **kwargs):
            if "unwrap" in pattern:
                return {
                    "matches": {
                        "file1.rs": [{"text": "x.unwrap()"}],
                        "file2.rs": [{"text": "y.unwrap()"}]
                    },
                    "files_with_matches": 2
                }
            return {"matches": {}, "files_with_matches": 0}
        
        searcher = BatchSearcher(search_func=mock_search, max_workers=2)
        
        requests = [
            BatchSearchRequest(pattern="unwrap()", name="unwraps"),
            BatchSearchRequest(pattern="panic!($$$ARGS)", name="panics")
        ]
        
        results = searcher.batch_search(requests, "/test/dir")
        
        assert "unwraps" in results
        assert results["unwraps"].count == 2
        assert results["unwraps"].files_with_matches == 2
        
        assert "panics" in results
        assert results["panics"].count == 0


class TestAutoPagination:
    """Test auto-pagination functionality."""
    
    def test_search_result_stream(self):
        """Test search result streaming."""
        # Mock search function with pagination
        def mock_search(**kwargs):
            page = kwargs.get("page", 1)
            if page == 1:
                return {
                    "matches": {
                        "file1.rs": [{"text": "match1"}],
                        "file2.rs": [{"text": "match2"}]
                    },
                    "has_more": True,
                    "page_info": {"total_pages": 2}
                }
            elif page == 2:
                return {
                    "matches": {
                        "file3.rs": [{"text": "match3"}]
                    },
                    "has_more": False
                }
            return {"matches": {}, "has_more": False}
        
        stream = SearchResultStream(
            search_func=mock_search,
            initial_args={"pattern": "test", "directory": "/test"},
            page_size=2
        )
        
        results = list(stream)
        assert len(results) == 3
        assert results[0]["match"]["text"] == "match1"
        assert results[2]["match"]["text"] == "match3"
    
    def test_create_search_stream(self):
        """Test creating search stream helper."""
        def mock_search(**kwargs):
            return {"matches": {}, "has_more": False}
        
        stream = create_search_stream(
            search_func=mock_search,
            pattern="test",
            directory="/test"
        )
        
        assert isinstance(stream, SearchResultStream)
        assert stream.page_size == 100  # Default


class TestMCPIntegration:
    """Test integration of new features with MCP."""
    
    def test_pattern_builder_tool(self):
        """Test pattern builder tool method."""
        mcp = AstGrepMCP()
        
        result = mcp.pattern_builder("rust")
        
        assert "builder_methods" in result
        assert len(result["builder_methods"]) > 0
        assert "example" in result
    
    def test_get_pattern_template_tool(self):
        """Test get pattern template tool."""
        mcp = AstGrepMCP()
        
        # Valid template
        result = mcp.get_pattern_template("unwrap_to_expect", "rust")
        assert "pattern" in result
        assert result["pattern"] == "$EXPR.unwrap()"
        
        # Invalid template
        result = mcp.get_pattern_template("nonexistent", "rust")
        assert "error" in result
        assert "available_templates" in result
    
    def test_batch_search_tool(self):
        """Test batch search tool."""
        mcp = AstGrepMCP()
        
        with patch.object(mcp, 'search_directory') as mock_search:
            mock_search.return_value = {
                "matches": {"file.rs": [{"text": "unwrap()"}]},
                "files_with_matches": 1
            }
            
            patterns = [
                {"pattern": "unwrap()", "name": "unwraps"},
                {"pattern": "panic!($$$ARGS)", "name": "panics"}
            ]
            
            with tempfile.TemporaryDirectory() as tmpdir:
                result = mcp.batch_search(patterns, tmpdir)
                
                assert "summary" in result
                assert result["summary"]["total_patterns"] == 2
    
    def test_create_smart_pattern_tool(self):
        """Test smart pattern creation."""
        mcp = AstGrepMCP()
        
        result = mcp.create_smart_pattern(
            "find spawn calls",
            "rust",
            ["spawn(async { work() })", "tokio::spawn(async move { })"]
        )
        
        assert "patterns" in result
        assert len(result["patterns"]) > 0
        
        # Check that spawn pattern is included
        patterns = [p["pattern"] if isinstance(p, dict) else p for p in result["patterns"]]
        assert any("spawn" in p for p in patterns)


class TestComplexPatternFixes:
    """Test fixes for complex pattern syntax issues."""
    
    def test_spawn_pattern_alternatives(self):
        """Test that spawn patterns generate working alternatives."""
        from ast_grep_mcp.utils.pattern_fixer import PatternFixer
        
        # User tries complex pattern
        pattern = "spawn(async move { $$BODY })"
        alternatives = PatternFixer.fix_pattern(pattern, "rust")
        
        # Should include simpler working pattern
        assert "spawn($$$ARGS)" in alternatives
        # Should fix $$ to $$$
        assert "spawn(async move { $$$BODY })" in alternatives
    
    def test_metavariable_explanation(self):
        """Test metavariable usage is explained."""
        from ast_grep_mcp.utils.enhanced_diagnostics import EnhancedDiagnostics
        
        diagnosis = EnhancedDiagnostics.diagnose_pattern_failure(
            "$NAME($$PARAMS)",
            "rust"
        )
        
        assert "metavariable_guide" in diagnosis
        guide = diagnosis["metavariable_guide"]
        assert "$$VAR" in guide
        assert "INCORRECT" in guide["$$VAR"]
        assert "$$$VAR" in guide


if __name__ == "__main__":
    pytest.main([__file__, "-v"])