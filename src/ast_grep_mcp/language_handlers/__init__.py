from .base import LanguageHandler
from .python_handler import PythonHandler
from .javascript_handler import JavaScriptHandler, TypeScriptHandler
from .rust_handler import RustHandler
from .c_handler import CHandler
from .go_handler import GoHandler

# Register all language handlers
handlers = {
    handler.language_name: handler()
    for handler in [
        PythonHandler, JavaScriptHandler, TypeScriptHandler,
        RustHandler,
        CHandler,
        GoHandler
    ]
}

def get_handler(language: str) -> LanguageHandler:
    """Get a handler for the specified language"""
    return handlers.get(language)

def get_all_handlers() -> dict:
    """Get a dictionary of all registered handlers"""
    return handlers