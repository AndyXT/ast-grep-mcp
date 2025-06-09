import pytest
from typer.testing import CliRunner
import json
import tempfile
from pathlib import Path
import sys
import re

# Add the root directory to sys.path to allow importing main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from src.ast_grep_mcp.core import ServerConfig

# Create a CLI runner with colors disabled
runner = CliRunner()


# Helper function to strip ANSI escape sequences from strings
def strip_ansi(text):
    """Strip ANSI escape sequences from text"""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def test_version_command():
    """Test the version command."""
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "AST Grep MCP Server v" in result.stdout
    assert "Configuration" in result.stdout
    assert "Default host: localhost" in result.stdout
    assert "Default port: 8080" in result.stdout
    assert "Default cache size: 128" in result.stdout
    assert "Default log level: INFO" in result.stdout


def test_help_command():
    """Test the main help command."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "AST Grep MCP server CLI" in result.stdout
    assert "start" in result.stdout
    assert "serve" in result.stdout
    assert "version" in result.stdout
    assert "interactive" in result.stdout
    assert "benchmark" in result.stdout


def test_start_help_command():
    """Test the help output for the start command."""
    result = runner.invoke(app, ["start", "--help"])
    clean_output = strip_ansi(result.stdout)

    assert result.exit_code == 0
    assert "Start the AST Grep MCP server" in clean_output
    assert "--host" in clean_output
    assert "--port" in clean_output
    assert "--log-level" in clean_output
    assert "--log-file" in clean_output
    assert "--log-to-console" in clean_output
    assert "--cache-size" in clean_output
    assert "--config" in clean_output


def test_configuration_file_json():
    """Test loading configuration from a JSON file."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a JSON configuration file
        config_file = Path(temp_dir) / "config.json"
        config_data = {
            "host": "127.0.0.1",
            "port": 9000,
            "log_level": "debug",
            "cache_size": 256,
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Test the config file loading
        config = ServerConfig.from_file(str(config_file))

        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.log_level == 10  # DEBUG = 10
        assert config.cache_size == 256


def test_configuration_file_yaml():
    """Test loading configuration from a YAML file."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a YAML configuration file
        config_file = Path(temp_dir) / "config.yaml"
        config_data = """
        host: 127.0.0.1
        port: 9000
        log_level: debug
        cache_size: 256
        """

        with open(config_file, "w") as f:
            f.write(config_data)

        # Test the config file loading
        config = ServerConfig.from_file(str(config_file))

        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.log_level == 10  # DEBUG = 10
        assert config.cache_size == 256


def test_invalid_configuration_file():
    """Test loading an invalid configuration file."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create an invalid JSON configuration file
        config_file = Path(temp_dir) / "invalid_config.json"

        with open(config_file, "w") as f:
            f.write("{invalid json")

        # Test that loading the invalid file raises an error
        with pytest.raises(ValueError):
            ServerConfig.from_file(str(config_file))


def test_nonexistent_configuration_file():
    """Test loading a nonexistent configuration file."""
    with pytest.raises(FileNotFoundError):
        ServerConfig.from_file("/nonexistent/config.json")


def test_unsupported_configuration_file_format():
    """Test loading a configuration file with an unsupported format."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file with unsupported extension
        config_file = Path(temp_dir) / "config.txt"

        with open(config_file, "w") as f:
            f.write("Some configuration")

        # Test that loading the unsupported format raises an error
        with pytest.raises(ValueError):
            ServerConfig.from_file(str(config_file))


def test_interactive_command_help():
    """Test that the interactive command help shows the right information."""
    result = runner.invoke(app, ["interactive", "--help"])

    assert result.exit_code == 0
    assert "Start an interactive AST Grep session" in result.stdout
    assert "This mode allows you to test patterns" in result.stdout
