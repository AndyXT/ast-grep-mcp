"""
Tests for the configuration system.
"""

import os
import yaml
import json
import pytest
from ast_grep_mcp.core.config import (
    ServerConfig, PatternConfig, RefactoringConfig, 
    OutputConfig, DiagnosticConfig, LOG_LEVELS
)

class TestServerConfig:
    """Tests for the ServerConfig class."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = ServerConfig()
        
        # Check default values
        assert config.host == "localhost"
        assert config.port == 8080
        assert config.log_level == LOG_LEVELS["info"]
        assert config.log_format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.log_file is None
        assert config.log_to_console is True
        assert config.enable_cache is True
        assert config.cache_size == 100
        assert config.safe_roots == []
        assert config.ignore_file is None
        assert config.use_default_ignores is True
        assert config.ignore_patterns == []
        
        # Check nested configurations
        assert isinstance(config.pattern_config, PatternConfig)
        assert isinstance(config.refactoring_config, RefactoringConfig)
        assert isinstance(config.output_config, OutputConfig)
        assert isinstance(config.diagnostic_config, DiagnosticConfig)
    
    def test_from_dict(self):
        """Test creating a configuration from a dictionary."""
        config_dict = {
            "host": "example.com",
            "port": 9000,
            "log_level": "debug",
            "log_file": "test.log",
            "safe_roots": ["/path1", "/path2"],
            "pattern_config": {
                "validation_strictness": "strict"
            },
            "refactoring_config": {
                "preview_mode": True
            },
            "output_config": {
                "format": "text"
            },
            "diagnostic_config": {
                "verbosity": "detailed"
            }
        }
        
        config = ServerConfig.from_dict(config_dict)
        
        # Check values from dictionary
        assert config.host == "example.com"
        assert config.port == 9000
        assert config.log_level == LOG_LEVELS["debug"]
        assert config.log_file == "test.log"
        assert config.safe_roots == ["/path1", "/path2"]
        
        # Check nested configurations
        assert config.pattern_config.validation_strictness == "strict"
        assert config.refactoring_config.preview_mode is True
        assert config.output_config.format == "text"
        assert config.diagnostic_config.verbosity == "detailed"
    
    def test_validation(self):
        """Test configuration validation."""
        # Invalid port
        with pytest.raises(ValueError) as excinfo:
            ServerConfig(port=70000)
        assert "Invalid port number" in str(excinfo.value)
        
        # Invalid log level
        with pytest.raises(ValueError) as excinfo:
            ServerConfig.from_dict({"log_level": "invalid"})
        assert "Invalid log level" in str(excinfo.value)
        
        # Invalid output format
        with pytest.raises(ValueError) as excinfo:
            ServerConfig(output_config=OutputConfig(format="invalid"))
        assert "Invalid format" in str(excinfo.value)
        
        # Invalid validation strictness
        with pytest.raises(ValueError) as excinfo:
            ServerConfig(pattern_config=PatternConfig(validation_strictness="invalid"))
        assert "Invalid validation strictness" in str(excinfo.value)
        
        # Invalid verbosity
        with pytest.raises(ValueError) as excinfo:
            ServerConfig(diagnostic_config=DiagnosticConfig(verbosity="invalid"))
        assert "Invalid verbosity" in str(excinfo.value)
    
    def test_to_dict(self):
        """Test converting configuration to a dictionary."""
        config = ServerConfig(
            host="test.example.com",
            port=9090,
            log_level=LOG_LEVELS["debug"],
            pattern_config=PatternConfig(validation_strictness="strict"),
            refactoring_config=RefactoringConfig(preview_mode=True)
        )
        
        config_dict = config.to_dict()
        
        # Check values
        assert config_dict["host"] == "test.example.com"
        assert config_dict["port"] == 9090
        assert config_dict["log_level"] == "debug"
        assert config_dict["pattern_config"]["validation_strictness"] == "strict"
        assert config_dict["refactoring_config"]["preview_mode"] is True
    
    def test_to_yaml(self):
        """Test converting configuration to YAML."""
        config = ServerConfig(
            host="yaml.example.com",
            port=9000,
            safe_roots=["/yaml/path1", "/yaml/path2"]
        )
        
        yaml_str = config.to_yaml()
        loaded_config = yaml.safe_load(yaml_str)
        
        # Check values
        assert loaded_config["host"] == "yaml.example.com"
        assert loaded_config["port"] == 9000
        assert loaded_config["safe_roots"] == ["/yaml/path1", "/yaml/path2"]
    
    def test_to_json(self):
        """Test converting configuration to JSON."""
        config = ServerConfig(
            host="json.example.com",
            port=8090,
            safe_roots=["/json/path1", "/json/path2"]
        )
        
        json_str = config.to_json()
        loaded_config = json.loads(json_str)
        
        # Check values
        assert loaded_config["host"] == "json.example.com"
        assert loaded_config["port"] == 8090
        assert loaded_config["safe_roots"] == ["/json/path1", "/json/path2"]


class TestConfigFiles:
    """Tests for loading configuration from files."""
    
    def test_from_yaml_file(self, tmp_path):
        """Test loading configuration from a YAML file."""
        config_data = {
            "host": "yaml-file.example.com",
            "port": 9001,
            "log_level": "warning",
            "safe_roots": ["/yaml-file/path1", "/yaml-file/path2"],
            "pattern_config": {
                "validation_strictness": "relaxed"
            }
        }
        
        # Create a temporary YAML file
        yaml_file = tmp_path / "config.yml"
        with open(yaml_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Load the configuration
        config = ServerConfig.from_file(str(yaml_file))
        
        # Check values
        assert config.host == "yaml-file.example.com"
        assert config.port == 9001
        assert config.log_level == LOG_LEVELS["warning"]
        assert config.safe_roots == ["/yaml-file/path1", "/yaml-file/path2"]
        assert config.pattern_config.validation_strictness == "relaxed"
    
    def test_from_json_file(self, tmp_path):
        """Test loading configuration from a JSON file."""
        config_data = {
            "host": "json-file.example.com",
            "port": 9002,
            "log_level": "error",
            "safe_roots": ["/json-file/path1", "/json-file/path2"],
            "refactoring_config": {
                "preview_mode": True,
                "max_replacements": 50
            }
        }
        
        # Create a temporary JSON file
        json_file = tmp_path / "config.json"
        with open(json_file, "w") as f:
            json.dump(config_data, f)
        
        # Load the configuration
        config = ServerConfig.from_file(str(json_file))
        
        # Check values
        assert config.host == "json-file.example.com"
        assert config.port == 9002
        assert config.log_level == LOG_LEVELS["error"]
        assert config.safe_roots == ["/json-file/path1", "/json-file/path2"]
        assert config.refactoring_config.preview_mode is True
        assert config.refactoring_config.max_replacements == 50
    
    def test_file_not_found(self):
        """Test loading configuration from a non-existent file."""
        with pytest.raises(FileNotFoundError):
            ServerConfig.from_file("non-existent-file.yml")
    
    def test_invalid_file_format(self, tmp_path):
        """Test loading configuration from a file with an invalid format."""
        # Create a temporary file with invalid YAML
        invalid_file = tmp_path / "invalid.yml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content:")
        
        with pytest.raises(ValueError) as excinfo:
            ServerConfig.from_file(str(invalid_file))
        assert "Invalid configuration file format" in str(excinfo.value)
    
    def test_unsupported_file_extension(self, tmp_path):
        """Test loading configuration from a file with an unsupported extension."""
        # Create a temporary file with an unsupported extension
        unsupported_file = tmp_path / "config.txt"
        with open(unsupported_file, "w") as f:
            f.write("host: example.com\nport: 9000\n")
        
        with pytest.raises(ValueError) as excinfo:
            ServerConfig.from_file(str(unsupported_file))
        assert "Unsupported configuration file format" in str(excinfo.value)
    
    def test_find_and_load_config(self, tmp_path):
        """Test finding and loading the nearest configuration file."""
        # Create a directory structure
        project_dir = tmp_path / "project"
        subdir = project_dir / "subdir"
        os.makedirs(subdir)
        
        # Create a configuration file in the project directory
        config_file = project_dir / "ast-grep.yml"
        with open(config_file, "w") as f:
            yaml.dump({"host": "project.example.com", "port": 9003}, f)
        
        # Load the configuration from the subdirectory
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            config = ServerConfig.find_and_load_config()
            
            # Check values
            assert config.host == "project.example.com"
            assert config.port == 9003
            
        finally:
            os.chdir(original_cwd)
    
    def test_save_to_file(self, tmp_path):
        """Test saving configuration to a file."""
        config = ServerConfig(
            host="save.example.com",
            port=9004,
            pattern_config=PatternConfig(validation_strictness="strict"),
            refactoring_config=RefactoringConfig(preview_mode=True)
        )
        
        # Save as YAML
        yaml_file = tmp_path / "save.yml"
        config.save_to_file(str(yaml_file))
        
        # Load and check
        loaded_config = ServerConfig.from_file(str(yaml_file))
        assert loaded_config.host == "save.example.com"
        assert loaded_config.port == 9004
        assert loaded_config.pattern_config.validation_strictness == "strict"
        assert loaded_config.refactoring_config.preview_mode is True
        
        # Save as JSON
        json_file = tmp_path / "save.json"
        config.save_to_file(str(json_file))
        
        # Load and check
        loaded_config = ServerConfig.from_file(str(json_file))
        assert loaded_config.host == "save.example.com"
        assert loaded_config.port == 9004


class TestEnvironmentVariables:
    """Tests for loading configuration from environment variables."""
    
    def test_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("AST_GREP_HOST", "env.example.com")
        monkeypatch.setenv("AST_GREP_PORT", "9005")
        monkeypatch.setenv("AST_GREP_LOG_LEVEL", "debug")
        monkeypatch.setenv("AST_GREP_SAFE_ROOTS", "/env/path1,/env/path2")
        monkeypatch.setenv("AST_GREP_CACHE_SIZE", "200")
        monkeypatch.setenv("AST_GREP_PREVIEW_MODE", "true")
        monkeypatch.setenv("AST_GREP_VALIDATION_STRICTNESS", "strict")
        monkeypatch.setenv("AST_GREP_OUTPUT_FORMAT", "text")
        monkeypatch.setenv("AST_GREP_VERBOSITY", "detailed")
        
        # Load the configuration
        config = ServerConfig.from_env()
        
        # Check values
        assert config.host == "env.example.com"
        assert config.port == 9005
        assert config.log_level == LOG_LEVELS["debug"]
        assert config.safe_roots == ["/env/path1", "/env/path2"]
        assert config.cache_size == 200
        assert config.refactoring_config.preview_mode is True
        assert config.pattern_config.validation_strictness == "strict"
        assert config.output_config.format == "text"
        assert config.diagnostic_config.verbosity == "detailed"
    
    def test_invalid_env_values(self, monkeypatch):
        """Test invalid environment variable values."""
        # Set invalid environment variables
        monkeypatch.setenv("AST_GREP_LOG_LEVEL", "invalid")
        
        # Check validation
        with pytest.raises(ValueError) as excinfo:
            ServerConfig.from_env()
        assert "Invalid log level" in str(excinfo.value)


class TestNestedConfigs:
    """Tests for nested configuration classes."""
    
    def test_pattern_config(self):
        """Test PatternConfig class."""
        # Default configuration
        config = PatternConfig()
        assert config.template_dir is None
        assert config.language_templates == {}
        assert config.validation_strictness == "normal"
        assert config.custom_patterns == {}
        
        # Custom configuration
        config = PatternConfig(
            template_dir="/templates",
            language_templates={"python": "/python-templates"},
            validation_strictness="strict",
            custom_patterns={"python": {"for_loop": "for $VAR in $ITER:"}}
        )
        assert config.template_dir == "/templates"
        assert config.language_templates == {"python": "/python-templates"}
        assert config.validation_strictness == "strict"
        assert config.custom_patterns == {"python": {"for_loop": "for $VAR in $ITER:"}}
    
    def test_refactoring_config(self):
        """Test RefactoringConfig class."""
        # Default configuration
        config = RefactoringConfig()
        assert config.preview_mode is False
        assert config.validate_replacements is True
        assert config.max_replacements is None
        assert config.fix_malformed_output is True
        assert config.enhance_partial_matches is True
        
        # Custom configuration
        config = RefactoringConfig(
            preview_mode=True,
            validate_replacements=False,
            max_replacements=50,
            fix_malformed_output=False,
            enhance_partial_matches=False
        )
        assert config.preview_mode is True
        assert config.validate_replacements is False
        assert config.max_replacements == 50
        assert config.fix_malformed_output is False
        assert config.enhance_partial_matches is False
    
    def test_output_config(self):
        """Test OutputConfig class."""
        # Default configuration
        config = OutputConfig()
        assert config.format == "json"
        assert config.colorize is True
        assert config.show_line_numbers is True
        assert config.show_context is True
        assert config.context_lines == 2
        
        # Custom configuration
        config = OutputConfig(
            format="text",
            colorize=False,
            show_line_numbers=False,
            show_context=False,
            context_lines=5
        )
        assert config.format == "text"
        assert config.colorize is False
        assert config.show_line_numbers is False
        assert config.show_context is False
        assert config.context_lines == 5
    
    def test_diagnostic_config(self):
        """Test DiagnosticConfig class."""
        # Default configuration
        config = DiagnosticConfig()
        assert config.verbosity == "normal"
        assert config.pattern_diagnostics is True
        assert config.show_suggestions is True
        assert config.show_examples is True
        assert config.show_stack_traces is False
        
        # Custom configuration
        config = DiagnosticConfig(
            verbosity="detailed",
            pattern_diagnostics=False,
            show_suggestions=False,
            show_examples=False,
            show_stack_traces=True
        )
        assert config.verbosity == "detailed"
        assert config.pattern_diagnostics is False
        assert config.show_suggestions is False
        assert config.show_examples is False
        assert config.show_stack_traces is True 