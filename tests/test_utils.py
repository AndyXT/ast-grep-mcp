"""
Tests for the utils module.
"""
from unittest.mock import patch
from src.ast_grep_mcp.utils import handle_errors


def test_handle_errors_no_error():
    """Test that handle_errors passes through the result when no error occurs."""
    # Define a test function that doesn't raise an exception
    @handle_errors
    def test_func():
        return {"success": True, "value": 42}
    
    # Call the function and check the result
    result = test_func()
    assert result == {"success": True, "value": 42}


def test_handle_errors_with_error():
    """Test that handle_errors handles exceptions properly."""
    # Define a test function that raises an exception
    @handle_errors
    def test_func():
        raise ValueError("Test error")
    
    # Call the function and check that it returns an error dict
    result = test_func()
    assert "error" in result
    assert "ValueError: Test error" in result["error"]
    assert result["success"] is False


def test_handle_errors_analyze_code():
    """Test that handle_errors formats analyze_code errors correctly."""
    # Define a test function that raises an exception but has the analyze_code name
    @handle_errors
    def analyze_code():
        raise ValueError("Test error")
    
    # Call the function and check the format matches analyze_code
    result = analyze_code()
    assert "error" in result
    assert "ValueError: Test error" in result["error"]
    assert "matches" in result
    assert result["matches"] == []
    assert "count" in result
    assert result["count"] == 0


def test_handle_errors_analyze_file():
    """Test that handle_errors formats analyze_file errors correctly."""
    # Define a test function that raises an exception but has the analyze_file name
    @handle_errors
    def analyze_file():
        raise ValueError("Test error")
    
    # Call the function and check the format matches analyze_file
    result = analyze_file()
    assert "error" in result
    assert "ValueError: Test error" in result["error"]
    assert "matches" in result
    assert result["matches"] == []
    assert "count" in result
    assert result["count"] == 0


def test_handle_errors_refactor_code():
    """Test that handle_errors formats refactor_code errors correctly."""
    # Define a test function that raises an exception but has the refactor_code name
    @handle_errors
    def refactor_code(code="original code"):
        raise ValueError("Test error")
    
    # Call the function WITH the code parameter this time
    result = refactor_code(code="original code")
    assert "error" in result
    assert "ValueError: Test error" in result["error"]
    assert "success" in result
    assert result["success"] is False
    assert "original_code" in result
    assert result["original_code"] == "original code"
    assert "refactored_code" in result
    assert result["refactored_code"] == "original code"


def test_handle_errors_get_language_patterns():
    """Test that handle_errors formats get_language_patterns errors correctly."""
    # Define a test function that raises an exception but has the get_language_patterns name
    @handle_errors
    def get_language_patterns():
        raise ValueError("Test error")
    
    # Call the function and check the format matches get_language_patterns
    result = get_language_patterns()
    assert "error" in result
    assert "ValueError: Test error" in result["error"]
    assert "patterns" in result
    assert result["patterns"] == {}


def test_handle_errors_get_supported_languages():
    """Test that handle_errors formats get_supported_languages errors correctly."""
    # Define a test function that raises an exception but has the get_supported_languages name
    @handle_errors
    def get_supported_languages():
        raise ValueError("Test error")
    
    # Call the function and check the format matches get_supported_languages
    result = get_supported_languages()
    assert "error" in result
    assert "ValueError: Test error" in result["error"]
    assert "languages" in result
    assert result["languages"] == {}


def test_handle_errors_logging():
    """Test that handle_errors logs the error properly."""
    # Mock the logger
    with patch("src.ast_grep_mcp.utils.error_handling.logger") as mock_logger:
        # Define a test function that raises an exception
        @handle_errors
        def test_func():
            raise ValueError("Test error")
        
        # Call the function
        test_func()
        
        # Check that the logger was called with the error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "Error in test_func" in call_args
        assert "ValueError: Test error" in call_args 