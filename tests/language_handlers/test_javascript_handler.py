from src.ast_grep_mcp.language_handlers.javascript_handler import JavaScriptHandler, TypeScriptHandler

class TestJavaScriptHandler:
    def test_language_name(self):
        """Test that the language name is correct."""
        handler = JavaScriptHandler()
        assert handler.language_name == "javascript"
    
    def test_file_extensions(self):
        """Test that the file extensions are correct."""
        handler = JavaScriptHandler()
        assert handler.file_extensions == [".js", ".jsx"]
    
    def test_get_default_patterns(self):
        """Test that the default patterns include all categories."""
        handler = JavaScriptHandler()
        patterns = handler.get_default_patterns()
        
        # Verify we have at least 25 patterns
        assert len(patterns) >= 25, f"Expected at least 25 patterns, got {len(patterns)}"
        
        # Verify key patterns are present
        basic_constructs = [
            "function_declaration", "arrow_function", "class_declaration",
            "method_definition", "object_literal", "array_literal", "import_statement"
        ]
        for pattern in basic_constructs:
            assert pattern in patterns, f"Missing basic construct pattern: {pattern}"
        
        # Verify anti-patterns are present
        anti_patterns = [
            "var_declaration", "setTimeout_zero", "with_statement",
            "alert", "document_write", "nested_callbacks"
        ]
        for pattern in anti_patterns:
            assert pattern in patterns, f"Missing anti-pattern: {pattern}"
        
        # Verify performance optimizations are present
        performance_patterns = [
            "array_push_in_loop", "inefficient_dom_query", "redundant_jquery_selector",
            "innerHTML_in_loop", "blocking_event_handler"
        ]
        for pattern in performance_patterns:
            assert pattern in patterns, f"Missing performance pattern: {pattern}"
        
        # Verify security vulnerabilities are present
        security_patterns = [
            "eval_call", "innerHTML_user_input", "document_location_href",
            "insecure_cookie", "dangerouslySetInnerHTML"
        ]
        for pattern in security_patterns:
            assert pattern in patterns, f"Missing security pattern: {pattern}"
        
        # Verify refactoring patterns are present
        refactoring_patterns = [
            "nested_if", "callback_to_promise", "repeated_condition",
            "boolean_literal_compare", "unnecessary_return", "promise_then_catch"
        ]
        for pattern in refactoring_patterns:
            assert pattern in patterns, f"Missing refactoring pattern: {pattern}"


class TestTypeScriptHandler:
    def test_language_name(self):
        """Test that the language name is correct."""
        handler = TypeScriptHandler()
        assert handler.language_name == "typescript"
    
    def test_file_extensions(self):
        """Test that the file extensions are correct."""
        handler = TypeScriptHandler()
        assert handler.file_extensions == [".ts", ".tsx"]
    
    def test_get_default_patterns(self):
        """Test that the handler includes both JavaScript and TypeScript patterns."""
        handler = TypeScriptHandler()
        patterns = handler.get_default_patterns()
        
        # Verify we have at least 40 patterns (JS + TS specific)
        assert len(patterns) >= 40, f"Expected at least 40 patterns, got {len(patterns)}"
        
        # Verify TypeScript specific patterns are present
        ts_specific = [
            "interface_declaration", "type_declaration", "enum_declaration", 
            "typed_function", "typed_arrow_function", "typed_method",
            "type_annotation", "type_assertion", "generic_type"
        ]
        for pattern in ts_specific:
            assert pattern in patterns, f"Missing TypeScript pattern: {pattern}"
        
        # Verify TypeScript anti-patterns are present
        ts_anti_patterns = [
            "any_type", "non_null_assertion", "type_assertion_any",
            "nested_type_assertion", "complex_intersection", "complex_union"
        ]
        for pattern in ts_anti_patterns:
            assert pattern in patterns, f"Missing TypeScript anti-pattern: {pattern}"
        
        # Verify TypeScript refactoring patterns are present
        ts_refactoring = [
            "optional_chain", "nullish_coalescing", "type_guard",
            "type_predicate", "keyof_operator", "mapped_type"
        ]
        for pattern in ts_refactoring:
            assert pattern in patterns, f"Missing TypeScript refactoring pattern: {pattern}"
        
        # Verify JavaScript patterns are also included
        js_patterns = ["function_declaration", "arrow_function", "class_declaration"]
        for pattern in js_patterns:
            assert pattern in patterns, f"Missing JavaScript pattern in TypeScript handler: {pattern}" 