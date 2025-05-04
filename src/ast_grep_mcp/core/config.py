"""
Configuration for the ast-grep MCP server.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
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

# Output format options
OUTPUT_FORMATS = ["json", "text", "sarif", "html"]

# Diagnostic verbosity levels
VERBOSITY_LEVELS = ["none", "minimal", "normal", "detailed", "diagnostic"]

# Pattern validation strictness settings
VALIDATION_STRICTNESS = ["strict", "normal", "relaxed"]


@dataclass
class PatternConfig:
    """Configuration for pattern matching and templates."""
    
    # Default pattern templates directory or file
    template_dir: Optional[str] = None
    
    # Language-specific pattern template directories
    language_templates: Dict[str, str] = field(default_factory=dict)
    
    # Pattern validation strictness
    validation_strictness: str = "normal"
    
    # Custom patterns included in configuration
    custom_patterns: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_enum_field("validation_strictness", VALIDATION_STRICTNESS)
    
    def _validate_enum_field(self, field_name: str, valid_values: List[str]) -> None:
        """
        Validate that a field has a valid enum value.
        
        Args:
            field_name: Name of the field to validate
            valid_values: List of valid values for the field
        
        Raises:
            ValueError: If the field value is not in valid_values
        """
        field_value = getattr(self, field_name)
        if field_value not in valid_values:
            raise ValueError(
                f"Invalid {field_name.replace('_', ' ')}: {field_value}. "
                f"Valid options are: {', '.join(valid_values)}"
            )


@dataclass
class RefactoringConfig:
    """Configuration for code refactoring."""
    
    # Whether to preview refactorings before applying them
    preview_mode: bool = False
    
    # Whether to validate replacement patterns
    validate_replacements: bool = True
    
    # Maximum number of replacements to perform
    max_replacements: Optional[int] = None
    
    # Whether to attempt fixing malformed outputs
    fix_malformed_output: bool = True
    
    # Whether to enhance partial match handling
    enhance_partial_matches: bool = True


@dataclass
class OutputConfig:
    """Configuration for output formatting."""
    
    # Output format (json, text, sarif, html)
    format: str = "json"
    
    # Whether to colorize output
    colorize: bool = True
    
    # Whether to show line numbers
    show_line_numbers: bool = True
    
    # Whether to show match context
    show_context: bool = True
    
    # Number of context lines to show
    context_lines: int = 2
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_enum_field("format", OUTPUT_FORMATS)
    
    def _validate_enum_field(self, field_name: str, valid_values: List[str]) -> None:
        """
        Validate that a field has a valid enum value.
        
        Args:
            field_name: Name of the field to validate
            valid_values: List of valid values for the field
        
        Raises:
            ValueError: If the field value is not in valid_values
        """
        field_value = getattr(self, field_name)
        if field_value not in valid_values:
            raise ValueError(
                f"Invalid {field_name.replace('_', ' ')}: {field_value}. "
                f"Valid options are: {', '.join(valid_values)}"
            )


@dataclass
class DiagnosticConfig:
    """Configuration for diagnostic output."""
    
    # Verbosity level
    verbosity: str = "normal"
    
    # Whether to show diagnostic information for pattern errors
    pattern_diagnostics: bool = True
    
    # Whether to show suggestions for pattern errors
    show_suggestions: bool = True
    
    # Whether to show example patterns
    show_examples: bool = True
    
    # Whether to show stack traces for errors
    show_stack_traces: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_enum_field("verbosity", VERBOSITY_LEVELS)
    
    def _validate_enum_field(self, field_name: str, valid_values: List[str]) -> None:
        """
        Validate that a field has a valid enum value.
        
        Args:
            field_name: Name of the field to validate
            valid_values: List of valid values for the field
        
        Raises:
            ValueError: If the field value is not in valid_values
        """
        field_value = getattr(self, field_name)
        if field_value not in valid_values:
            raise ValueError(
                f"Invalid {field_name.replace('_', ' ')}: {field_value}. "
                f"Valid options are: {', '.join(valid_values)}"
            )


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
    safe_roots: List[str] = field(default_factory=list)
    
    # Ignore files configuration
    ignore_file: Optional[str] = None
    use_default_ignores: bool = True
    ignore_patterns: List[str] = field(default_factory=list)
    
    # Pattern configuration
    pattern_config: PatternConfig = field(default_factory=PatternConfig)
    
    # Refactoring configuration
    refactoring_config: RefactoringConfig = field(default_factory=RefactoringConfig)
    
    # Output configuration
    output_config: OutputConfig = field(default_factory=OutputConfig)
    
    # Diagnostic configuration
    diagnostic_config: DiagnosticConfig = field(default_factory=DiagnosticConfig)
    
    # Additional custom configuration options
    options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_port_range()
    
    def _validate_port_range(self) -> None:
        """Validate that the port is within the valid range."""
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
        # Make a copy of the dictionary to avoid modifying the original
        config = dict(config_dict)
        
        # Handle log_level if it's a string
        if "log_level" in config and isinstance(config["log_level"], str):
            level_str = config["log_level"].lower()
            if level_str in LOG_LEVELS:
                config["log_level"] = LOG_LEVELS[level_str]
            else:
                raise ValueError(f"Invalid log level: {level_str}. Valid levels are: {', '.join(LOG_LEVELS.keys())}")
        
        # Handle nested configuration objects
        if "pattern_config" in config and isinstance(config["pattern_config"], dict):
            config["pattern_config"] = PatternConfig(**config["pattern_config"])
        
        if "refactoring_config" in config and isinstance(config["refactoring_config"], dict):
            config["refactoring_config"] = RefactoringConfig(**config["refactoring_config"])
        
        if "output_config" in config and isinstance(config["output_config"], dict):
            config["output_config"] = OutputConfig(**config["output_config"])
        
        if "diagnostic_config" in config and isinstance(config["diagnostic_config"], dict):
            config["diagnostic_config"] = DiagnosticConfig(**config["diagnostic_config"])
        
        return cls(**config)
    
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
            AST_GREP_IGNORE_FILE: Path to ignore file
            AST_GREP_USE_DEFAULT_IGNORES: Whether to use default ignores (true, false)
            AST_GREP_PREVIEW_MODE: Whether to preview refactorings (true, false)
            AST_GREP_VALIDATE_REPLACEMENTS: Whether to validate replacements (true, false)
            AST_GREP_OUTPUT_FORMAT: Output format (json, text, sarif, html)
            AST_GREP_VERBOSITY: Diagnostic verbosity level
            AST_GREP_VALIDATION_STRICTNESS: Pattern validation strictness
            
        Returns:
            A ServerConfig instance.
        """
        config_dict = {}
        pattern_config = {}
        refactoring_config = {}
        output_config = {}
        diagnostic_config = {}
        
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
        
        # Ignore files configuration
        if "AST_GREP_IGNORE_FILE" in os.environ:
            config_dict["ignore_file"] = os.environ["AST_GREP_IGNORE_FILE"]
        if "AST_GREP_USE_DEFAULT_IGNORES" in os.environ:
            config_dict["use_default_ignores"] = os.environ["AST_GREP_USE_DEFAULT_IGNORES"].lower() == "true"
        
        # Pattern configuration
        if "AST_GREP_TEMPLATE_DIR" in os.environ:
            pattern_config["template_dir"] = os.environ["AST_GREP_TEMPLATE_DIR"]
        if "AST_GREP_VALIDATION_STRICTNESS" in os.environ:
            pattern_config["validation_strictness"] = os.environ["AST_GREP_VALIDATION_STRICTNESS"]
        
        # Refactoring configuration
        if "AST_GREP_PREVIEW_MODE" in os.environ:
            refactoring_config["preview_mode"] = os.environ["AST_GREP_PREVIEW_MODE"].lower() == "true"
        if "AST_GREP_VALIDATE_REPLACEMENTS" in os.environ:
            refactoring_config["validate_replacements"] = os.environ["AST_GREP_VALIDATE_REPLACEMENTS"].lower() == "true"
        if "AST_GREP_MAX_REPLACEMENTS" in os.environ:
            refactoring_config["max_replacements"] = int(os.environ["AST_GREP_MAX_REPLACEMENTS"])
        if "AST_GREP_FIX_MALFORMED_OUTPUT" in os.environ:
            refactoring_config["fix_malformed_output"] = os.environ["AST_GREP_FIX_MALFORMED_OUTPUT"].lower() == "true"
        
        # Output configuration
        if "AST_GREP_OUTPUT_FORMAT" in os.environ:
            output_config["format"] = os.environ["AST_GREP_OUTPUT_FORMAT"]
        if "AST_GREP_COLORIZE" in os.environ:
            output_config["colorize"] = os.environ["AST_GREP_COLORIZE"].lower() == "true"
        if "AST_GREP_SHOW_LINE_NUMBERS" in os.environ:
            output_config["show_line_numbers"] = os.environ["AST_GREP_SHOW_LINE_NUMBERS"].lower() == "true"
        if "AST_GREP_SHOW_CONTEXT" in os.environ:
            output_config["show_context"] = os.environ["AST_GREP_SHOW_CONTEXT"].lower() == "true"
        if "AST_GREP_CONTEXT_LINES" in os.environ:
            output_config["context_lines"] = int(os.environ["AST_GREP_CONTEXT_LINES"])
        
        # Diagnostic configuration
        if "AST_GREP_VERBOSITY" in os.environ:
            diagnostic_config["verbosity"] = os.environ["AST_GREP_VERBOSITY"]
        if "AST_GREP_PATTERN_DIAGNOSTICS" in os.environ:
            diagnostic_config["pattern_diagnostics"] = os.environ["AST_GREP_PATTERN_DIAGNOSTICS"].lower() == "true"
        if "AST_GREP_SHOW_SUGGESTIONS" in os.environ:
            diagnostic_config["show_suggestions"] = os.environ["AST_GREP_SHOW_SUGGESTIONS"].lower() == "true"
        if "AST_GREP_SHOW_EXAMPLES" in os.environ:
            diagnostic_config["show_examples"] = os.environ["AST_GREP_SHOW_EXAMPLES"].lower() == "true"
        if "AST_GREP_SHOW_STACK_TRACES" in os.environ:
            diagnostic_config["show_stack_traces"] = os.environ["AST_GREP_SHOW_STACK_TRACES"].lower() == "true"
        
        # Add nested configurations if they have any values
        if pattern_config:
            config_dict["pattern_config"] = PatternConfig(**pattern_config)
        if refactoring_config:
            config_dict["refactoring_config"] = RefactoringConfig(**refactoring_config)
        if output_config:
            config_dict["output_config"] = OutputConfig(**output_config)
        if diagnostic_config:
            config_dict["diagnostic_config"] = DiagnosticConfig(**diagnostic_config)
        
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
            
            if not config_dict:
                config_dict = {}
                
            return cls.from_dict(config_dict)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Invalid configuration file format: {str(e)}")
    
    @classmethod
    def find_and_load_config(cls, start_dir: Optional[str] = None) -> "ServerConfig":
        """
        Find and load the nearest ast-grep.yml configuration file.
        
        This method looks for ast-grep.yml or ast-grep.yaml in the current
        directory and parent directories.
        
        Args:
            start_dir: Directory to start the search from
            
        Returns:
            A ServerConfig instance
        """
        current_dir = Path(start_dir or os.getcwd())
        
        # Look for config file in current and parent directories
        while current_dir != current_dir.parent:
            for name in ["ast-grep.yml", "ast-grep.yaml", "ast-grep.json"]:
                config_file = current_dir / name
                if config_file.exists() and config_file.is_file():
                    try:
                        return cls.from_file(str(config_file))
                    except Exception:
                        # Continue to the next file if loading fails
                        pass
            
            current_dir = current_dir.parent
        
        # Return default config if no config file is found
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            A dictionary representation of the configuration
        """
        # Convert log level back to string
        config_dict = {}
        
        # Server configuration
        config_dict["host"] = self.host
        config_dict["port"] = self.port
        
        # Logging configuration
        for level_name, level_value in LOG_LEVELS.items():
            if level_value == self.log_level:
                config_dict["log_level"] = level_name
                break
        else:
            config_dict["log_level"] = str(self.log_level)
        
        config_dict["log_format"] = self.log_format
        config_dict["log_file"] = self.log_file
        config_dict["log_to_console"] = self.log_to_console
        
        # Cache configuration
        config_dict["enable_cache"] = self.enable_cache
        config_dict["cache_size"] = self.cache_size
        
        # Security configuration
        config_dict["safe_roots"] = self.safe_roots
        
        # Ignore files configuration
        config_dict["ignore_file"] = self.ignore_file
        config_dict["use_default_ignores"] = self.use_default_ignores
        config_dict["ignore_patterns"] = self.ignore_patterns
        
        # Pattern configuration
        config_dict["pattern_config"] = {
            "template_dir": self.pattern_config.template_dir,
            "language_templates": self.pattern_config.language_templates,
            "validation_strictness": self.pattern_config.validation_strictness,
            "custom_patterns": self.pattern_config.custom_patterns
        }
        
        # Refactoring configuration
        config_dict["refactoring_config"] = {
            "preview_mode": self.refactoring_config.preview_mode,
            "validate_replacements": self.refactoring_config.validate_replacements,
            "max_replacements": self.refactoring_config.max_replacements,
            "fix_malformed_output": self.refactoring_config.fix_malformed_output,
            "enhance_partial_matches": self.refactoring_config.enhance_partial_matches
        }
        
        # Output configuration
        config_dict["output_config"] = {
            "format": self.output_config.format,
            "colorize": self.output_config.colorize,
            "show_line_numbers": self.output_config.show_line_numbers,
            "show_context": self.output_config.show_context,
            "context_lines": self.output_config.context_lines
        }
        
        # Diagnostic configuration
        config_dict["diagnostic_config"] = {
            "verbosity": self.diagnostic_config.verbosity,
            "pattern_diagnostics": self.diagnostic_config.pattern_diagnostics,
            "show_suggestions": self.diagnostic_config.show_suggestions,
            "show_examples": self.diagnostic_config.show_examples,
            "show_stack_traces": self.diagnostic_config.show_stack_traces
        }
        
        # Additional custom configuration options
        config_dict["options"] = self.options
        
        return config_dict
    
    def to_yaml(self) -> str:
        """
        Convert the configuration to YAML.
        
        Returns:
            A YAML representation of the configuration
        """
        return yaml.dump(self.to_dict(), sort_keys=False)
    
    def to_json(self) -> str:
        """
        Convert the configuration to JSON.
        
        Returns:
            A JSON representation of the configuration
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save the configuration to a file.
        
        Args:
            file_path: Path to save the configuration to
        """
        path = Path(file_path)
        
        if path.suffix.lower() in ('.yml', '.yaml'):
            with open(path, 'w') as f:
                f.write(self.to_yaml())
        elif path.suffix.lower() == '.json':
            with open(path, 'w') as f:
                f.write(self.to_json())
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
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