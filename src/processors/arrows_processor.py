from .base import ContentProcessor
import re


class ArrowsProcessor(ContentProcessor):
    """Replace all '->' and '=>' in the text with '→', and all '<-' and '<=' with '←'."""

    def process(self, content):
        # Replace right arrows
        new_content = re.sub(r"(->|=>)", "→", content)
        # Replace left arrows
        new_content = re.sub(r"(<-|<=)", "←", new_content)
        return new_content, new_content != content
