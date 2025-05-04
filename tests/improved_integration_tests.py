"""
Improved integration tests with reduced mocking to catch real-world issues.

These tests focus on testing the complete system rather than mocking components,
which allows us to catch integration issues between components.
"""

import os
import tempfile

from src.ast_grep_mcp.core import AstGrepMCP, ServerConfig
from src.ast_grep_mcp.ast_analyzer import AstAnalyzer
from src.ast_grep_mcp.utils.security import sanitize_pattern


class TestJavaScriptPatternMatching:
    """Test JavaScript pattern matching without mocking the pattern engine."""

    def test_javascript_template_literals_matching(self):
        """Test matching JavaScript template literals without mocks."""
        analyzer = AstAnalyzer()
        
        # Template literal code
        code = "const message = `Hello, ${name}! You have ${count} messages.`;"
        pattern = "const $VAR = `$$$TEMPLATE`;"
        
        # Test actual pattern matching
        matches = analyzer.find_patterns(code, "javascript", pattern)
        
        # Verify that we get the expected match
        assert len(matches) == 1
        assert "Hello, ${name}! You have ${count} messages." in matches[0]["text"]
    
    def test_javascript_arrow_function_matching(self):
        """Test matching JavaScript arrow functions without mocks."""
        analyzer = AstAnalyzer()
        
        # Arrow function code
        code = "const greet = (name) => { return `Hello, ${name}`; };"
        pattern = "($PARAM) => { return $$$EXPR; }"
        
        # Test actual pattern matching
        matches = analyzer.find_patterns(code, "javascript", pattern)
        
        # Verify that we get the expected match
        assert len(matches) == 1
        assert "(name) => { return `Hello, ${name}`; }" in matches[0]["text"]


class TestJavaScriptRefactoring:
    """Test JavaScript refactoring without mocking the refactoring engine."""

    def test_template_literal_refactoring(self):
        """Test converting string concatenation to template literals without mocks."""
        analyzer = AstAnalyzer()
        
        # String concatenation code
        code = "const greeting = 'Hello, ' + name + '!';"
        pattern = "'$STR1' + $VAR + '$STR2'"
        replacement = "`$STR1${$VAR}$STR2`"
        
        # Perform the actual refactoring
        refactored = analyzer.apply_refactoring(code, "javascript", pattern, replacement)
        
        # Verify the refactored code has proper template literals
        assert "`Hello, ${name}!`" in refactored
    
    def test_arrow_function_refactoring(self):
        """Test refactoring regular functions to arrow functions without mocks."""
        analyzer = AstAnalyzer()
        
        # Regular function code
        code = "function add(a, b) { return a + b; }"
        pattern = "function $NAME($PARAMS) { return $EXPR; }"
        replacement = "const $NAME = ($PARAMS) => $EXPR;"
        
        # Perform the actual refactoring
        refactored = analyzer.apply_refactoring(code, "javascript", pattern, replacement)
        
        # Verify the refactored code uses arrow function syntax
        assert "const add = (a, b) => a + b;" in refactored


class TestIntegratedSecurityFeatures:
    """Test security features without mocking."""

    def test_pattern_sanitization_with_js_operators(self):
        """Test that JS logical operators are correctly preserved during sanitization."""
        # Pattern with logical operators
        pattern = "if (x > 0 && y < 10 || z === 0) { $$$BODY }"
        
        # Sanitize the pattern
        sanitized = sanitize_pattern(pattern)
        
        # Operators should be preserved
        assert "&&" in sanitized
        assert "||" in sanitized
        assert pattern == sanitized
    
    def test_actual_command_injection_sanitization(self):
        """Test that command injection attempts are actually sanitized."""
        # Pattern with command injection attempt
        dangerous_pattern = "function hello() { `rm -rf /`; $$$BODY }"
        
        # Sanitize the pattern
        sanitized = sanitize_pattern(dangerous_pattern)
        
        # Command should be removed but function structure preserved
        assert "`rm -rf /`" not in sanitized
        assert "function hello() {" in sanitized
        assert "$$$BODY" in sanitized
    
    def test_nested_templates_sanitization(self):
        """Test sanitization of nested template literals."""
        # Pattern with nested template literals
        pattern = "const x = `outer ${`inner ${value}`}`;"
        
        # Sanitize the pattern
        sanitized = sanitize_pattern(pattern)
        
        # The nested structure should be preserved
        assert "outer ${`inner ${value}`}" in sanitized


class TestCompleteCodeAnalysisWorkflow:
    """Test the complete workflow from user input to output."""

    def setup_method(self):
        """Set up test environment with real code files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
        
        # Create test JavaScript file
        self.js_file = os.path.join(self.test_dir, "test.js")
        with open(self.js_file, "w") as f:
            f.write("""
            // Test JavaScript file
            function fetchData(callback) {
                fetch('/api/data')
                    .then(response => response.json())
                    .then(data => callback(null, data))
                    .catch(error => callback(error));
            }
            
            const greeting = 'Hello, ' + name + '!';
            
            const checkCondition = (x, y) => {
                if (x > 0 && y < 10) {
                    return true;
                }
                return false;
            };
            """)
        
        # Create test Python file
        self.py_file = os.path.join(self.test_dir, "test.py")
        with open(self.py_file, "w") as f:
            f.write("""
            # Test Python file
            def process_data(data):
                result = []
                for item in data:
                    if item and item.get('value') > 0:
                        result.append(item['value'])
                return result
                
            def unsafe_exec(code):
                return eval(code)  # Security risk
            """)
        
        # Initialize with the test directory as a safe root
        self.config = ServerConfig(
            log_to_console=False,
            safe_roots=[self.test_dir]
        )
        self.ast_grep_mcp = AstGrepMCP(self.config)
    
    def teardown_method(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
    
    def test_analyze_file_end_to_end(self):
        """Test analyzing a file with a pattern, end-to-end."""
        # JavaScript callback pattern
        result = self.ast_grep_mcp.analyze_file(self.js_file, "function $NAME($CALLBACK)")
        
        # Should find the fetchData function
        assert "error" not in result
        assert result["count"] == 1
        assert "fetchData" in result["matches"][0]["text"]
    
    def test_security_vulnerability_detection(self):
        """Test detecting security vulnerabilities in Python code."""
        # Test for eval usage (security risk)
        result = self.ast_grep_mcp.analyze_file(self.py_file, "eval($EXPR)")
        
        # Should find the eval call
        assert "error" not in result
        assert result["count"] == 1
        assert "eval(code)" in result["matches"][0]["text"]
    
    def test_directory_search_end_to_end(self):
        """Test searching a directory with a pattern, end-to-end."""
        # Search for if statements
        result = self.ast_grep_mcp.search_directory(self.test_dir, "if ($CONDITION)")
        
        # Should find at least 2 if statements (one in JS, one in Python)
        assert "error" not in result
        assert result["files_with_matches"] >= 2
        
        # Verify results
        js_matches = [match for file, data in result["matches"].items() 
                     if file.endswith(".js") for match in data["matches"]]
        py_matches = [match for file, data in result["matches"].items() 
                     if file.endswith(".py") for match in data["matches"]]
        
        assert len(js_matches) >= 1
        assert len(py_matches) >= 1
    
    def test_refactoring_end_to_end(self):
        """Test refactoring code with a pattern, end-to-end."""
        # Get the content of the JavaScript file
        with open(self.js_file, "r") as f:
            code = f.read()
        
        # Refactor string concatenation to template literals
        result = self.ast_grep_mcp.refactor_code(
            code,
            "javascript",
            "'$STR1' + $VAR + '$STR2'",
            "`$STR1${$VAR}$STR2`"
        )
        
        # Verify the refactoring was successful
        assert "error" not in result
        assert "refactored_code" in result
        assert "`Hello, ${name}!`" in result["refactored_code"]
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attacks are prevented."""
        # Try to access a file outside the safe root using path traversal
        parent_dir = os.path.dirname(self.test_dir)
        traversal_path = os.path.join(self.test_dir, "../outside.txt")
        
        # Create a file outside the safe root
        outside_file = os.path.join(parent_dir, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("sensitive data")
        
        # Try to analyze the file
        result = self.ast_grep_mcp.analyze_file(traversal_path, "sensitive")
        
        # Should be blocked by security checks
        assert "error" in result
        assert "restricted" in result["error"]


class TestLanguageHandlerIntegration:
    """Test language handlers integration without mocking."""
    
    def test_get_language_patterns_without_mocks(self):
        """Test getting language patterns without mocking the handlers."""
        ast_grep_mcp = AstGrepMCP()
        
        # Get JavaScript patterns
        js_result = ast_grep_mcp.get_language_patterns("javascript")
        
        # Verify we get actual patterns
        assert "error" not in js_result
        assert "patterns" in js_result
        assert len(js_result["patterns"]) > 10
        
        # Verify common patterns are present
        assert "function_declaration" in js_result["patterns"]
        assert "arrow_function" in js_result["patterns"]
        
        # Get Python patterns
        py_result = ast_grep_mcp.get_language_patterns("python")
        
        # Verify we get actual patterns
        assert "error" not in py_result
        assert "patterns" in py_result
        assert len(py_result["patterns"]) > 10
        
        # Verify common patterns are present
        assert "function_definition" in py_result["patterns"]
        assert "class_definition" in py_result["patterns"]
    
    def test_get_supported_languages_without_mocks(self):
        """Test getting supported languages without mocking."""
        ast_grep_mcp = AstGrepMCP()
        
        # Get supported languages
        result = ast_grep_mcp.get_supported_languages()
        
        # Verify we get the expected languages
        assert "error" not in result
        assert "languages" in result
        assert "javascript" in result["languages"]
        assert "python" in result["languages"]
        assert "typescript" in result["languages"]
        
        # Verify file extensions match
        assert ".js" in result["languages"]["javascript"]
        assert ".py" in result["languages"]["python"]
        assert ".ts" in result["languages"]["typescript"] 