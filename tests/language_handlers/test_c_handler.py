from src.ast_grep_mcp.language_handlers.c_handler import CHandler


class TestCHandler:
    def test_language_name(self):
        """Test that the language name is correct."""
        handler = CHandler()
        assert handler.language_name == "c"

    def test_file_extensions(self):
        """Test that the file extensions are correct."""
        handler = CHandler()
        assert handler.file_extensions == [".c", ".h"]

    def test_get_default_patterns(self):
        """Test that the default patterns include all categories."""
        handler = CHandler()
        patterns = handler.get_default_patterns()

        # Verify we have at least 25 patterns
        assert (
            len(patterns) >= 25
        ), f"Expected at least 25 patterns, got {len(patterns)}"

        # Verify key patterns are present
        basic_constructs = [
            "function",
            "struct",
            "variable",
            "comment",
            "enum",
            "typedef",
            "function_pointer",
            "macro",
            "include",
            "switch",
        ]
        for pattern in basic_constructs:
            assert pattern in patterns, f"Missing basic construct pattern: {pattern}"

        # Verify anti-patterns are present
        anti_patterns = [
            "goto",
            "magic_number",
            "nested_conditional",
            "large_function",
            "global_var",
            "deeply_nested_loop",
        ]
        for pattern in anti_patterns:
            assert pattern in patterns, f"Missing anti-pattern: {pattern}"

        # Verify performance optimizations are present
        performance_patterns = [
            "unnecessary_copy",
            "inefficient_string_concat",
            "malloc_without_check",
            "repeated_array_element_access",
            "redundant_condition",
        ]
        for pattern in performance_patterns:
            assert pattern in patterns, f"Missing performance pattern: {pattern}"

        # Verify security vulnerabilities are present
        security_patterns = [
            "buffer_overflow",
            "format_string_vulnerability",
            "gets_call",
            "integer_overflow",
            "null_pointer_deref",
            "use_after_free",
        ]
        for pattern in security_patterns:
            assert pattern in patterns, f"Missing security pattern: {pattern}"

        # Verify refactoring patterns are present
        refactoring_patterns = [
            "if_return_pattern",
            "void_parameter",
            "switch_without_default",
            "multiple_return_paths",
            "malloc_sizeof_type",
            "redundant_null_check",
        ]
        for pattern in refactoring_patterns:
            assert pattern in patterns, f"Missing refactoring pattern: {pattern}"
