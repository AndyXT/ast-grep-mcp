"""
Tests for the server module.
"""
from unittest.mock import patch, MagicMock
import tempfile
from src.ast_grep_mcp.server import (
    analyze_code,
    refactor_code,
    analyze_file,
    get_language_patterns,
    get_supported_languages,
    run_server
)


def test_analyze_code_supported_language():
    """Test analyze_code with a supported language."""
    code = "def hello(): pass"
    pattern = "def $FUNC_NAME(): pass"
    result = analyze_code(code, "python", pattern)
    assert "matches" in result
    assert "count" in result
    assert "language" in result
    assert result["language"] == "python"
    assert result["count"] == 1


def test_analyze_code_unsupported_language():
    """Test analyze_code with an unsupported language."""
    code = "def hello(): pass"
    pattern = "def $FUNC_NAME(): pass"
    result = analyze_code(code, "invalid_language", pattern)
    assert "error" in result
    assert "matches" in result
    assert "Language 'invalid_language' is not supported" in result["error"]
    assert len(result["matches"]) == 0


def test_refactor_code_supported_language():
    """Test refactor_code with a supported language."""
    code = "def hello(): pass"
    pattern = "def $FUNC_NAME(): pass"
    replacement = "def $FUNC_NAME():\n    print('Hello')"
    result = refactor_code(code, "python", pattern, replacement)
    assert "original_code" in result
    assert "refactored_code" in result
    assert "success" in result
    assert "language" in result
    assert result["language"] == "python"
    assert result["success"] is True
    assert result["refactored_code"] != result["original_code"]


def test_refactor_code_unsupported_language():
    """Test refactor_code with an unsupported language."""
    code = "def hello(): pass"
    pattern = "def $FUNC_NAME(): pass"
    replacement = "def $FUNC_NAME():\n    print('Hello')"
    result = refactor_code(code, "invalid_language", pattern, replacement)
    assert "error" in result
    assert "success" in result
    assert "Language 'invalid_language' is not supported" in result["error"]
    assert result["success"] is False


def test_refactor_code_no_matches():
    """Test refactor_code with no pattern matches."""
    code = "x = 1"
    pattern = "def $FUNC_NAME(): pass"
    replacement = "def $FUNC_NAME():\n    print('Hello')"
    result = refactor_code(code, "python", pattern, replacement)
    assert "original_code" in result
    assert "refactored_code" in result
    assert "success" in result
    assert result["success"] is False
    assert result["refactored_code"] == result["original_code"]


def test_analyze_file_nonexistent():
    """Test analyze_file with a nonexistent file."""
    result = analyze_file("/nonexistent/file.py", "def $FUNC_NAME(): pass")
    assert "error" in result
    assert "matches" in result
    assert "does not exist" in result["error"]
    assert len(result["matches"]) == 0


def test_analyze_file_unsupported_extension():
    """Test analyze_file with an unsupported file extension."""
    with tempfile.NamedTemporaryFile(suffix=".unknown") as tmp:
        result = analyze_file(tmp.name, "def $FUNC_NAME(): pass")
        assert "error" in result
        assert "matches" in result
        assert "Unsupported file type" in result["error"]
        assert len(result["matches"]) == 0


def test_analyze_file_valid():
    """Test analyze_file with a valid file."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+") as tmp:
        tmp.write("def hello(): pass")
        tmp.flush()
        result = analyze_file(tmp.name, "def $FUNC_NAME(): pass")
        assert "file" in result
        assert "language" in result
        assert "matches" in result
        assert "count" in result
        assert result["language"] == "python"
        assert result["count"] == 1
        assert len(result["matches"]) == 1


@patch('src.ast_grep_mcp.server._get_ast_grep_mcp')
def test_get_language_patterns_supported(mock_get_ast_grep_mcp):
    """Test get_language_patterns with a supported language."""
    # Mock the AstGrepMCP instance
    mock_instance = MagicMock()
    mock_instance.get_language_patterns.return_value = {
        "language": "python",
        "patterns": {"function": "def $NAME()"}
    }
    mock_get_ast_grep_mcp.return_value = mock_instance
    
    # Call the function to test
    result = get_language_patterns("python")
    
    # Verify the result
    assert "language" in result
    assert "patterns" in result
    assert result["language"] == "python"
    assert isinstance(result["patterns"], dict)
    assert "function" in result["patterns"]
    
    # Verify the mock was called correctly
    mock_get_ast_grep_mcp.assert_called_once()
    mock_instance.get_language_patterns.assert_called_once_with("python")


def test_get_language_patterns_unsupported():
    """Test get_language_patterns with an unsupported language."""
    result = get_language_patterns("invalid_language")
    assert "error" in result
    assert "patterns" in result
    assert "not supported" in result["error"]
    assert isinstance(result["patterns"], dict)
    assert len(result["patterns"]) == 0


def test_get_supported_languages():
    """Test get_supported_languages."""
    result = get_supported_languages()
    assert "languages" in result
    assert isinstance(result["languages"], dict)
    assert "python" in result["languages"]
    assert "javascript" in result["languages"]


@patch('src.ast_grep_mcp.core.ast_grep_mcp.FastMCP')
@patch('src.ast_grep_mcp.server.ServerConfig')
@patch('src.ast_grep_mcp.server.AstGrepMCP')
def test_run_server(mock_ast_grep_mcp_class, mock_server_config, mock_fastmcp):
    """Test run_server function."""
    # Set up mocks
    mock_instance = MagicMock()
    mock_ast_grep_mcp_class.return_value = mock_instance
    mock_config = MagicMock()
    mock_server_config.return_value = mock_config
    
    # Run the function
    run_server(host="0.0.0.0", port=9000)
    
    # Check that the mocks were called correctly
    mock_server_config.assert_called_once_with(host="0.0.0.0", port=9000)
    mock_ast_grep_mcp_class.assert_called_once_with(mock_config)
    mock_instance.start.assert_called_once() 