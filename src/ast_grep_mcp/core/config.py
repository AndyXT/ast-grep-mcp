"""
Configuration for the ast-grep MCP server.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging


@dataclass
class ServerConfig:
    """Configuration class for the AST Grep MCP server."""
    
    # Server configuration
    host: str = "localhost"
    port: int = 8080
    
    # Logging configuration
    log_level: int = logging.INFO
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
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