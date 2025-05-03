"""
Tests for the server module.
"""
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path
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


@patch('src.ast_grep_mcp.server.get_handler')
def test_get_language_patterns_supported(mock_get_handler):
    """Test get_language_patterns with a supported language."""
    # Mock the handler to return some patterns
    mock_handler = MagicMock()
    mock_handler.get_default_patterns.return_value = {"function": "def $NAME()"}
    mock_get_handler.return_value = mock_handler
    
    result = get_language_patterns("python")
    assert "language" in result
    assert "patterns" in result
    assert result["language"] == "python"
    assert isinstance(result["patterns"], dict)
    assert "function" in result["patterns"]


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


def test_run_server():
    """Test run_server function."""
    with patch("src.ast_grep_mcp.server.mcp.run") as mock_run:
        # Default parameters
        run_server()
        mock_run.assert_called_once()

        # Reset mock
        mock_run.reset_mock()

        # Custom parameters - should still print a note and call run
        with patch("builtins.print") as mock_print:
            run_server(host="0.0.0.0", port=9000)
            mock_print.assert_called_once()
            mock_run.assert_called_once() 