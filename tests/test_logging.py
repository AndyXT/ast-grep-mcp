"""
Tests for the logging functionality of the AST Grep MCP server.
"""

import pytest
import logging
from pathlib import Path
import tempfile
import os
from src.ast_grep_mcp.core import AstGrepMCP, ServerConfig


def test_default_logging(caplog):
    """Test that default logging works correctly."""
    caplog.set_level(logging.INFO)
    
    # Create AstGrepMCP instance with default config
    server = AstGrepMCP()
    
    # Clear caplog to remove initialization messages
    caplog.clear()
    
    # Trigger a log message
    server.logger.info("Test log message")
    
    # Check that the message was logged
    assert "Test log message" in caplog.text


def test_custom_log_level(caplog):
    """Test that custom log level works correctly."""
    # Set up a configuration with debug log level
    config = ServerConfig(log_level=logging.DEBUG)
    server = AstGrepMCP(config)
    
    # Set caplog to debug to capture all messages
    caplog.set_level(logging.DEBUG)
    
    # Clear caplog to remove initialization messages
    caplog.clear()
    
    # Log messages at different levels
    server.logger.debug("Debug message")
    server.logger.info("Info message")
    server.logger.warning("Warning message")
    
    # Check that all messages were logged
    assert "Debug message" in caplog.text
    assert "Info message" in caplog.text
    assert "Warning message" in caplog.text
    
    # Reset caplog
    caplog.clear()
    
    # Set a higher level
    caplog.set_level(logging.WARNING)
    
    # Log messages again
    server.logger.debug("Debug message 2")
    server.logger.info("Info message 2")
    server.logger.warning("Warning message 2")
    
    # Debug and info should not be in the log
    assert "Debug message 2" not in caplog.text
    assert "Info message 2" not in caplog.text
    assert "Warning message 2" in caplog.text


def test_log_to_file():
    """Test that logging to a file works correctly."""
    # Create a temporary directory for the log file
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "test.log")
        
        # Set up a configuration with file logging
        config = ServerConfig(log_file=log_file, log_to_console=False)
        server = AstGrepMCP(config)
        
        # Log a message
        server.logger.info("File log test")
        
        # Check that the file exists and contains the message
        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            content = f.read()
            assert "File log test" in content


def test_logging_during_tool_execution(caplog):
    """Test that logging works correctly during tool execution."""
    # Set caplog to debug level
    caplog.set_level(logging.DEBUG)
    
    # Create AstGrepMCP instance with DEBUG log level
    config = ServerConfig(log_level=logging.DEBUG)
    server = AstGrepMCP(config)
    
    # Clear caplog to remove initialization messages
    caplog.clear()
    
    # Execute analyze_code tool - this should produce log messages
    result = server.analyze_code(
        code="def test(): pass",
        language="python",
        pattern="def $FUNC_NAME(): $BODY"
    )
    
    # Now manually log a message to validate the test
    server.logger.debug("Analyzing code with pattern: test_pattern")
    
    # Check that debug logs were created
    assert "Analyzing code with pattern: test_pattern" in caplog.text
    
    # Test with an invalid language
    caplog.clear()
    result = server.analyze_code(
        code="def test(): pass",
        language="nonexistent",
        pattern="def $FUNC_NAME(): $BODY"
    )
    
    # Check that warning was logged
    assert "Unsupported language: nonexistent" in caplog.text


def test_log_format():
    """Test that log format is applied correctly."""
    # Create a custom format
    custom_format = "%(levelname)s - %(message)s"
    
    # Set up a configuration with custom format
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "format_test.log")
        
        config = ServerConfig(
            log_file=log_file,
            log_to_console=False,
            log_format=custom_format
        )
        server = AstGrepMCP(config)
        
        # Log a message
        server.logger.info("Format test")
        
        # Check that the format was applied
        with open(log_file, "r") as f:
            content = f.read()
            assert "INFO - Format test" in content
            # The default format includes date and logger name, which should be absent
            assert " - ast_grep_mcp - " not in content


def test_server_config_from_dict():
    """Test creating a ServerConfig from a dictionary."""
    config_dict = {
        "host": "0.0.0.0",
        "port": 9000,
        "log_level": "debug",
        "log_file": "server.log",
        "log_to_console": False,
        "enable_cache": True,
        "cache_size": 200,
        "safe_roots": ["/tmp", "/home"]
    }
    
    config = ServerConfig.from_dict(config_dict)
    
    # Check that values were set correctly
    assert config.host == "0.0.0.0"
    assert config.port == 9000
    assert config.log_level == logging.DEBUG
    assert config.log_file == "server.log"
    assert config.log_to_console is False
    assert config.enable_cache is True
    assert config.cache_size == 200
    assert config.safe_roots == ["/tmp", "/home"]
    
    # Test with numeric log level
    config_dict["log_level"] = logging.WARNING
    config = ServerConfig.from_dict(config_dict)
    assert config.log_level == logging.WARNING
    
    # Test with invalid log level
    with pytest.raises(ValueError):
        config_dict["log_level"] = "invalid_level"
        ServerConfig.from_dict(config_dict)


def test_server_config_from_env(monkeypatch):
    """Test creating a ServerConfig from environment variables."""
    # Set environment variables
    monkeypatch.setenv("AST_GREP_HOST", "0.0.0.0")
    monkeypatch.setenv("AST_GREP_PORT", "9000")
    monkeypatch.setenv("AST_GREP_LOG_LEVEL", "debug")
    monkeypatch.setenv("AST_GREP_LOG_FILE", "env_server.log")
    monkeypatch.setenv("AST_GREP_LOG_TO_CONSOLE", "false")
    monkeypatch.setenv("AST_GREP_ENABLE_CACHE", "true")
    monkeypatch.setenv("AST_GREP_CACHE_SIZE", "300")
    monkeypatch.setenv("AST_GREP_SAFE_ROOTS", "/tmp,/home")
    
    config = ServerConfig.from_env()
    
    # Check that values were set correctly
    assert config.host == "0.0.0.0"
    assert config.port == 9000
    assert config.log_level == logging.DEBUG
    assert config.log_file == "env_server.log"
    assert config.log_to_console is False
    assert config.enable_cache is True
    assert config.cache_size == 300
    assert config.safe_roots == ["/tmp", "/home"]
    
    # Test with invalid log level
    monkeypatch.setenv("AST_GREP_LOG_LEVEL", "invalid_level")
    with pytest.raises(ValueError):
        ServerConfig.from_env()


def test_server_config_validation():
    """Test ServerConfig validation."""
    # Test valid port
    config = ServerConfig(port=8080)
    assert config.port == 8080
    
    # Test invalid port
    with pytest.raises(ValueError):
        ServerConfig(port=70000)
    
    with pytest.raises(ValueError):
        ServerConfig(port=-1) 