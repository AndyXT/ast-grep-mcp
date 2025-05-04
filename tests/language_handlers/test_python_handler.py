from src.ast_grep_mcp.language_handlers.python_handler import PythonHandler

class TestPythonHandler:
    def test_language_name(self):
        """Test that the language name is correct."""
        handler = PythonHandler()
        assert handler.language_name == "python"
    
    def test_file_extensions(self):
        """Test that the file extensions are correct."""
        handler = PythonHandler()
        assert handler.file_extensions == [".py"]
    
    def test_get_default_patterns(self):
        """Test that the default patterns include all categories."""
        handler = PythonHandler()
        patterns = handler.get_default_patterns()
        
        # Verify we have at least 25 patterns
        assert len(patterns) >= 25, f"Expected at least 25 patterns, got {len(patterns)}"
        
        # Verify key patterns are present
        basic_constructs = [
            "function_definition", "class_definition", "method_definition",
            "if_statement", "for_loop", "while_loop", "try_except", "with_statement"
        ]
        for pattern in basic_constructs:
            assert pattern in patterns, f"Missing basic construct pattern: {pattern}"
        
        # Verify anti-patterns are present
        anti_patterns = [
            "bare_except", "except_pass", "mutable_default_arg",
            "global_statement", "nested_function", "nested_loops"
        ]
        for pattern in anti_patterns:
            assert pattern in patterns, f"Missing anti-pattern: {pattern}"
        
        # Verify performance optimizations are present
        performance_patterns = [
            "list_in_loop", "string_concat_in_loop", "inefficient_dict_lookup",
            "repeated_calculation", "inefficient_list_creation"
        ]
        for pattern in performance_patterns:
            assert pattern in patterns, f"Missing performance pattern: {pattern}"
        
        # Verify security vulnerabilities are present
        security_patterns = [
            "eval_call", "exec_call", "shell_true", "pickle_load",
            "yaml_load", "sql_format"
        ]
        for pattern in security_patterns:
            assert pattern in patterns, f"Missing security pattern: {pattern}"
        
        # Verify refactoring patterns are present
        refactoring_patterns = [
            "if_return_early", "multiple_if_returns", "dict_get_with_default",
            "try_except_else", "repeated_condition", "explicit_none_compare"
        ]
        for pattern in refactoring_patterns:
            assert pattern in patterns, f"Missing refactoring pattern: {pattern}" 