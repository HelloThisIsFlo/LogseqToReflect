from .base import ContentProcessor
import re


class PropertiesProcessor(ContentProcessor):
    """Remove unwanted LogSeq property lines like 'filters::' from content."""

    def process(self, content):
        # Remove lines starting with 'filters::' and any resulting blank lines
        new_content = re.sub(r"^\s*filters::.*\n?", "", content, flags=re.MULTILINE)
        return new_content, new_content != content
