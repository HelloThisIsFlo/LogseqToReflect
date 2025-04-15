from .base import ContentProcessor
import re

class LinkProcessor(ContentProcessor):
    """Process LogSeq links for Reflect compatibility"""

    def process(self, content):
        # Remove LogSeq block IDs
        new_content = re.sub(
            r"id:: [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
            "",
            content,
        )

        # Remove LogSeq properties like collapsed:: true
        new_content = re.sub(r"\s+[a-z]+:: (?:true|false)", "", new_content)

        return new_content, new_content != content
