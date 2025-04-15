from abc import ABC, abstractmethod


class ContentProcessor(ABC):
    """Base class for content processors"""

    @abstractmethod
    def process(self, content):
        """
        Process the content and return a tuple of (new_content, changed).
        """
        pass
