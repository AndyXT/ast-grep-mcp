"""
Tests for the core module.
"""
import pytest
from unittest.mock import patch, MagicMock
import logging
from src.ast_grep_mcp.core import AstGrepMCP, ServerConfig


@pytest.fixture
def ast_grep_mcp():
    """Create an AstGrepMCP instance for testing."""
    with patch("src.ast_grep_mcp.core.ast_grep_mcp.FastMCP") as mock_fastmcp:
        # Set up the mock
        mock_mcp_instance = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_tool_decorator.return_value = lambda x: x  # Identity function to keep the methods
        mock_mcp_instance.tool.return_value = mock_tool_decorator
        mock_fastmcp.return_value = mock_mcp_instance
        
        # Create and return an instance
        instance = AstGrepMCP()
        yield instance


@pytest.fixture
def mock_fastmcp():
    """Create a mock for FastMCP."""
    mock = MagicMock()
    mock_tool_decorator = MagicMock()
    mock_tool_decorator.return_value = lambda x: x  # Identity function
    mock.tool.return_value = mock_tool_decorator
    return mock


def test_init(ast_grep_mcp):
    """Test the initialization of AstGrepMCP."""
    # Test with default config
    assert ast_grep_mcp.config.host == "localhost"
    assert ast_grep_mcp.config.port == 8080
    
    # Test with custom config
    with patch("src.ast_grep_mcp.core.ast_grep_mcp.FastMCP") as mock_fastmcp:
        # Set up the mock
        mock_mcp_instance = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_tool_decorator.return_value = lambda x: x
        mock_mcp_instance.tool.return_value = mock_tool_decorator
        mock_fastmcp.return_value = mock_mcp_instance
        
        config = ServerConfig(host="0.0.0.0", port=9000)
        server = AstGrepMCP(config)
        assert server.config.host == "0.0.0.0"
        assert server.config.port == 9000


def test_init_registers_tools():
    """Test that the AstGrepMCP constructor registers all tools."""
    with patch("src.ast_grep_mcp.core.ast_grep_mcp.FastMCP") as mock_fastmcp:
        # Set up the mock
        mock_mcp_instance = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_tool_decorator.return_value = lambda x: x  # Identity function to keep the methods
        mock_mcp_instance.tool.return_value = mock_tool_decorator
        mock_fastmcp.return_value = mock_mcp_instance
        
        # Initialize AstGrepMCP
        AstGrepMCP()
        
        # Check that tool() was called exactly 6 times
        assert mock_mcp_instance.tool.call_count == 6


def test_config_validation():
    """Test that ServerConfig validates port numbers."""
    # Valid port should work
    config = ServerConfig(port=8080)
    assert config.port == 8080
    
    # Invalid port should raise ValueError
    with pytest.raises(ValueError):
        ServerConfig(port=-1)
    
    with pytest.raises(ValueError):
        ServerConfig(port=70000)


def test_setup_logger():
    """Test that the logger is set up properly."""
    with patch("src.ast_grep_mcp.core.ast_grep_mcp.FastMCP") as mock_fastmcp:
        # Set up the mock
        mock_mcp_instance = MagicMock()
        mock_tool_decorator = MagicMock()
        mock_tool_decorator.return_value = lambda x: x
        mock_mcp_instance.tool.return_value = mock_tool_decorator
        mock_fastmcp.return_value = mock_mcp_instance
        
        # Test with custom log level
        config = ServerConfig(log_level=logging.DEBUG)
        server = AstGrepMCP(config)
        assert server.logger.level == logging.DEBUG


@patch("src.ast_grep_mcp.core.ast_grep_mcp.FastMCP")
def test_start(mock_fastmcp):
    """Test the start method."""
    # Set up the mock
    mock_mcp_instance = MagicMock()
    mock_tool_decorator = MagicMock()
    mock_tool_decorator.return_value = lambda x: x  # Identity function to keep the methods
    mock_mcp_instance.tool.return_value = mock_tool_decorator
    mock_fastmcp.return_value = mock_mcp_instance
    
    # Initialize and start the server
    server = AstGrepMCP()
    server.start()
    
    # Check that run was called once
    mock_mcp_instance.run.assert_called_once()


@patch("src.ast_grep_mcp.core.ast_grep_mcp.FastMCP")
def test_start_with_custom_host_port(mock_fastmcp):
    """Test the start method with custom host and port."""
    # Set up the mock
    mock_mcp_instance = MagicMock()
    mock_tool_decorator = MagicMock()
    mock_tool_decorator.return_value = lambda x: x  # Identity function to keep the methods
    mock_mcp_instance.tool.return_value = mock_tool_decorator
    mock_fastmcp.return_value = mock_mcp_instance
    
    # Initialize and start the server with custom host and port
    config = ServerConfig(host="0.0.0.0", port=9000)
    server = AstGrepMCP(config)
    
    # Capture logs to check for warning
    with patch.object(server.logger, "warning") as mock_warning:
        server.start()
        
        # Should log a warning about FastMCP ignoring host and port
        mock_warning.assert_called_once()
    
    # Check that run was called once
    mock_mcp_instance.run.assert_called_once()


def test_tool_registration(mock_fastmcp):
    """Test that each tool is registered correctly."""
    with patch('src.ast_grep_mcp.core.ast_grep_mcp.FastMCP', return_value=mock_fastmcp):
        # Initialize AstGrepMCP
        AstGrepMCP()
        
        # Check that tool() was called exactly 6 times
        assert mock_fastmcp.tool.call_count == 6 