from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LanguageHandler(ABC):
    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name"""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """Return file extensions associated with this language"""
        pass
    
    @abstractmethod
    def get_default_patterns(self) -> Dict[str, str]:
        """Return dictionary of common patterns for this language"""
        pass