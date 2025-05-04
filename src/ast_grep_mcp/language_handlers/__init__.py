from .base import LanguageHandler
from .python_handler import PythonHandler
from .javascript_handler import JavaScriptHandler, TypeScriptHandler
from .rust_handler import RustHandler
from .c_handler import CHandler
from .go_handler import GoHandler

# Create handler classes
handler_classes = [
    PythonHandler,
    JavaScriptHandler,
    TypeScriptHandler,
    RustHandler,
    CHandler,
    GoHandler
]

# Register all language handlers
# Fixed: Get the actual language_name string value instead of using the property object as a key
handlers = {}
for handler_class in handler_classes:
    # Instantiate the handler class
    handler_instance = handler_class()
    # Get the language name string
    language_name = handler_instance.language_name
    # Add to handlers dictionary with the string as key
    handlers[language_name] = handler_instance

def get_handler(language: str) -> LanguageHandler:
    """Get a handler for the specified language"""
    return handlers.get(language)

def get_all_handlers() -> dict:
    """Get a dictionary of all registered handlers"""
    return handlers