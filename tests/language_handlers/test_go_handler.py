from src.ast_grep_mcp.language_handlers.go_handler import GoHandler


class TestGoHandler:
    def test_language_name(self):
        """Test that the language name is correct."""
        handler = GoHandler()
        assert handler.language_name == "go"

    def test_file_extensions(self):
        """Test that the file extensions are correct."""
        handler = GoHandler()
        assert handler.file_extensions == [".go"]

    def test_get_default_patterns(self):
        """Test that the default patterns include all categories."""
        handler = GoHandler()
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
            "interface",
            "method",
            "import",
            "for_loop",
            "range_loop",
            "switch",
        ]
        for pattern in basic_constructs:
            assert pattern in patterns, f"Missing basic construct pattern: {pattern}"

        # Verify anti-patterns are present
        anti_patterns = [
            "naked_return",
            "empty_interface_param",
            "panic_call",
            "goroutine_without_sync",
            "bool_param_leading",
            "large_struct",
        ]
        for pattern in anti_patterns:
            assert pattern in patterns, f"Missing anti-pattern: {pattern}"

        # Verify performance optimizations are present
        performance_patterns = [
            "string_concat_plus",
            "inefficient_slice_append",
            "unnecessary_allocation",
            "map_without_capacity",
            "mutex_copy",
        ]
        for pattern in performance_patterns:
            assert pattern in patterns, f"Missing performance pattern: {pattern}"

        # Verify security vulnerabilities are present
        security_patterns = [
            "sql_injection",
            "command_injection",
            "weak_rand",
            "insecure_temp_file",
            "http_redirect_open",
        ]
        for pattern in security_patterns:
            assert pattern in patterns, f"Missing security pattern: {pattern}"

        # Verify refactoring patterns are present
        refactoring_patterns = [
            "nil_check",
            "error_check",
            "nested_if",
            "explicit_type_conversion",
            "repeated_condition",
            "switch_two_cases",
            "map_value_check",
        ]
        for pattern in refactoring_patterns:
            assert pattern in patterns, f"Missing refactoring pattern: {pattern}"
