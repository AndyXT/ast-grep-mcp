from .base import LanguageHandler
from .python_handler import PythonHandler
from .javascript_handler import JavaScriptHandler

# Register all language handlers
handlers = {
    handler.language_name: handler()
    for handler in [PythonHandler, JavaScriptHandler]
}

def get_handler(language: str) -> LanguageHandler:
    """Get a handler for the specified language"""
    return handlers.get(language)

def get_all_handlers() -> dict:
    """Get a dictionary of all registered handlers"""
    return handlers