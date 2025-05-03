import tempfile
import os

from src.ast_grep_mcp.core import AstGrepMCP, ServerConfig

class TestSecurityIntegration:
    """Integration tests for security features in AstGrepMCP."""
    
    def test_pattern_sanitization_in_analyze_code(self):
        """Test that patterns are sanitized in analyze_code."""
        # Create an instance with logging disabled
        config = ServerConfig(log_to_console=False)
        instance = AstGrepMCP(config)
        
        # Test with a malicious pattern that still works when sanitized
        # (backticks are removed, but the pattern is still valid)
        dangerous_pattern = "def hello`evil command`()"
        code = "def hello():\n    print('world')"
        
        # The pattern should be sanitized and still work as expected
        result = instance.analyze_code(code, "python", dangerous_pattern)
        
        # Verify that the pattern was sanitized but still matched
        assert "error" not in result
        assert result["count"] == 1
        assert len(result["matches"]) == 1
    
    def test_pattern_sanitization_in_refactor_code(self):
        """Test that patterns are sanitized in refactor_code."""
        # Create an instance with logging disabled
        config = ServerConfig(log_to_console=False)
        instance = AstGrepMCP(config)
        
        # Test with malicious pattern and replacement
        dangerous_pattern = "print`rm -rf /`($MSG)"
        dangerous_replacement = "console.log$(rm -rf /)($MSG)"
        code = "print('hello world')"
        
        # The pattern and replacement should be sanitized
        result = instance.refactor_code(code, "python", dangerous_pattern, dangerous_replacement)
        
        # Pattern should still work after sanitization
        assert "error" not in result
        assert result["success"] is True
        assert "console.log" in result["refactored_code"]
    
    def test_file_access_restrictions(self):
        """Test that file access is restricted to safe roots."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create safe and unsafe directories
            safe_dir = os.path.join(temp_dir, "safe")
            unsafe_dir = os.path.join(temp_dir, "unsafe")
            os.makedirs(safe_dir)
            os.makedirs(unsafe_dir)
            
            # Create test files
            safe_file = os.path.join(safe_dir, "safe.py")
            unsafe_file = os.path.join(unsafe_dir, "unsafe.py")
            
            with open(safe_file, "w") as f:
                f.write("def safe_function():\n    print('safe')")
            
            with open(unsafe_file, "w") as f:
                f.write("def unsafe_function():\n    print('unsafe')")
            
            # Configure instance with safe roots
            config = ServerConfig(
                log_to_console=False,
                safe_roots=[safe_dir]
            )
            instance = AstGrepMCP(config)
            
            # Test access to safe file
            safe_result = instance.analyze_file(safe_file, "def $NAME")
            assert "error" not in safe_result
            assert safe_result["count"] == 1
            
            # Test access to unsafe file
            unsafe_result = instance.analyze_file(unsafe_file, "def $NAME")
            assert "error" in unsafe_result
            assert "Access denied" in unsafe_result["error"]
            assert unsafe_result["matches"] == []
    
    def test_directory_traversal_prevention(self):
        """Test that directory traversal attacks are prevented."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a safe directory
            safe_dir = os.path.join(temp_dir, "safe")
            os.makedirs(safe_dir)
            
            # Create a sensitive file outside safe directory
            sensitive_file = os.path.join(temp_dir, "sensitive.py")
            with open(sensitive_file, "w") as f:
                f.write("def sensitive_function():\n    print('sensitive')")
            
            # Configure instance with safe roots
            config = ServerConfig(
                log_to_console=False,
                safe_roots=[safe_dir]
            )
            instance = AstGrepMCP(config)
            
            # Attempt directory traversal
            traversal_path = os.path.join(safe_dir, "../sensitive.py")
            result = instance.analyze_file(traversal_path, "def $NAME")
            
            # Should be blocked
            assert "error" in result
            assert "Access denied" in result["error"]
            assert result["matches"] == []
    
    def test_directory_search_security(self):
        """Test that directory search respects safe roots."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create safe and unsafe directories
            safe_dir = os.path.join(temp_dir, "safe")
            unsafe_dir = os.path.join(temp_dir, "unsafe")
            os.makedirs(safe_dir)
            os.makedirs(unsafe_dir)
            
            # Create test files
            safe_file = os.path.join(safe_dir, "safe.py")
            unsafe_file = os.path.join(unsafe_dir, "unsafe.py")
            
            with open(safe_file, "w") as f:
                f.write("def safe_function():\n    print('safe')")
            
            with open(unsafe_file, "w") as f:
                f.write("def unsafe_function():\n    print('unsafe')")
            
            # Configure instance with safe roots
            config = ServerConfig(
                log_to_console=False,
                safe_roots=[safe_dir]
            )
            instance = AstGrepMCP(config)
            
            # Test search in safe directory
            safe_result = instance.search_directory(safe_dir, "def $NAME")
            assert "error" not in safe_result
            
            # Test search in unsafe directory
            unsafe_result = instance.search_directory(unsafe_dir, "def $NAME")
            assert "error" in unsafe_result
            assert "Access denied" in unsafe_result["error"] 