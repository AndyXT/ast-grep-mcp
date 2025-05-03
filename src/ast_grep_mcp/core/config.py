"""
Configuration for the ast-grep MCP server.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging
import os
import sys
import json
import yaml
from pathlib import Path


# Logging level mapping from string to int
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


@dataclass
class ServerConfig:
    """Configuration class for the AST Grep MCP server."""
    
    # Server configuration
    host: str = "localhost"
    port: int = 8080
    
    # Logging configuration
    log_level: int = logging.INFO
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    log_to_console: bool = True
    
    # Cache configuration
    enable_cache: bool = True
    cache_size: int = 100
    
    # Security configuration
    safe_roots: list[str] = field(default_factory=list)
    
    # Additional custom configuration options
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.port < 0 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ServerConfig":
        """
        Create a ServerConfig from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration values.
            
        Returns:
            A ServerConfig instance.
        """
        # Handle log_level if it's a string
        if "log_level" in config_dict and isinstance(config_dict["log_level"], str):
            level_str = config_dict["log_level"].lower()
            if level_str in LOG_LEVELS:
                config_dict["log_level"] = LOG_LEVELS[level_str]
            else:
                raise ValueError(f"Invalid log level: {level_str}. Valid levels are: {', '.join(LOG_LEVELS.keys())}")
        
        return cls(**config_dict)
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """
        Create a ServerConfig from environment variables.
        
        Environment variables:
            AST_GREP_HOST: Server host
            AST_GREP_PORT: Server port
            AST_GREP_LOG_LEVEL: Logging level (debug, info, warning, error, critical)
            AST_GREP_LOG_FILE: Log file path
            AST_GREP_LOG_TO_CONSOLE: Whether to log to console (true, false)
            AST_GREP_ENABLE_CACHE: Whether to enable caching (true, false)
            AST_GREP_CACHE_SIZE: Cache size
            AST_GREP_SAFE_ROOTS: Comma-separated list of safe roots
            
        Returns:
            A ServerConfig instance.
        """
        config_dict = {}
        
        # Server configuration
        if "AST_GREP_HOST" in os.environ:
            config_dict["host"] = os.environ["AST_GREP_HOST"]
        if "AST_GREP_PORT" in os.environ:
            config_dict["port"] = int(os.environ["AST_GREP_PORT"])
        
        # Logging configuration
        if "AST_GREP_LOG_LEVEL" in os.environ:
            level_str = os.environ["AST_GREP_LOG_LEVEL"].lower()
            if level_str in LOG_LEVELS:
                config_dict["log_level"] = LOG_LEVELS[level_str]
            else:
                raise ValueError(f"Invalid log level: {level_str}. Valid levels are: {', '.join(LOG_LEVELS.keys())}")
        if "AST_GREP_LOG_FILE" in os.environ:
            config_dict["log_file"] = os.environ["AST_GREP_LOG_FILE"]
        if "AST_GREP_LOG_TO_CONSOLE" in os.environ:
            config_dict["log_to_console"] = os.environ["AST_GREP_LOG_TO_CONSOLE"].lower() == "true"
        
        # Cache configuration
        if "AST_GREP_ENABLE_CACHE" in os.environ:
            config_dict["enable_cache"] = os.environ["AST_GREP_ENABLE_CACHE"].lower() == "true"
        if "AST_GREP_CACHE_SIZE" in os.environ:
            config_dict["cache_size"] = int(os.environ["AST_GREP_CACHE_SIZE"])
        
        # Security configuration
        if "AST_GREP_SAFE_ROOTS" in os.environ:
            config_dict["safe_roots"] = os.environ["AST_GREP_SAFE_ROOTS"].split(",")
        
        return cls(**config_dict)
    
    @classmethod
    def from_file(cls, config_file: str) -> "ServerConfig":
        """
        Create a ServerConfig from a configuration file.
        
        Args:
            config_file: Path to the configuration file (JSON or YAML)
            
        Returns:
            A ServerConfig instance.
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the configuration file format is not supported or invalid.
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            if config_path.suffix.lower() in ('.yml', '.yaml'):
                with open(config_path, 'r') as f:
                    config_dict = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
            
            return cls.from_dict(config_dict)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Invalid configuration file format: {str(e)}")
    
    def setup_logging(self, name: str = "ast_grep_mcp") -> logging.Logger:
        """
        Set up logging with the configured settings.
        
        Args:
            name: The logger name.
            
        Returns:
            A configured logger.
        """
        # Get or create the logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatters
        formatter = logging.Formatter(self.log_format)
        
        # Add console handler if enabled
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Add file handler if log_file is specified
        if self.log_file:
            # Create the directory if it doesn't exist
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger 