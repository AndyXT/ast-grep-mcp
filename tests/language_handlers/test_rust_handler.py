import pytest
from src.ast_grep_mcp.language_handlers.rust_handler import RustHandler

class TestRustHandler:
    def test_language_name(self):
        """Test that the language name is correct."""
        handler = RustHandler()
        assert handler.language_name == "rust"
    
    def test_file_extensions(self):
        """Test that the file extensions are correct."""
        handler = RustHandler()
        assert handler.file_extensions == [".rs"]
    
    def test_get_default_patterns(self):
        """Test that the default patterns include all categories."""
        handler = RustHandler()
        patterns = handler.get_default_patterns()
        
        # Verify we have at least 25 patterns
        assert len(patterns) >= 25, f"Expected at least 25 patterns, got {len(patterns)}"
        
        # Verify key patterns are present
        basic_constructs = [
            "function", "struct", "variable", "comment", "enum", "impl", 
            "trait", "impl_trait", "match", "macro_invocation"
        ]
        for pattern in basic_constructs:
            assert pattern in patterns, f"Missing basic construct pattern: {pattern}"
        
        # Verify anti-patterns are present
        anti_patterns = [
            "unwrap", "expect", "clone_in_loop", "nested_match", 
            "needless_return", "large_enum_variant"
        ]
        for pattern in anti_patterns:
            assert pattern in patterns, f"Missing anti-pattern: {pattern}"
        
        # Verify performance optimizations are present
        performance_patterns = [
            "box_vec_new", "string_add_push_str", "redundant_clone",
            "unnecessary_sort_by", "inefficient_iterator_chain"
        ]
        for pattern in performance_patterns:
            assert pattern in patterns, f"Missing performance pattern: {pattern}"
        
        # Verify security vulnerabilities are present
        security_patterns = [
            "dangerous_transmute", "unsafe_code_block", "raw_pointer_deref",
            "format_string_injection", "regex_dos"
        ]
        for pattern in security_patterns:
            assert pattern in patterns, f"Missing security pattern: {pattern}"
        
        # Verify refactoring patterns are present
        refactoring_patterns = [
            "if_let_chain", "match_to_if_let", "explicit_deref",
            "manual_filter_map", "mutex_guard", "redundant_closure"
        ]
        for pattern in refactoring_patterns:
            assert pattern in patterns, f"Missing refactoring pattern: {pattern}" 