from .base import ContentProcessor
import re


class LinkProcessor(ContentProcessor):
    """Process LogSeq links for Reflect compatibility"""

    def process(self, content):
        # Remove LogSeq block IDs (entire line, any indentation, 7 or 8 char UUID)
        new_content = re.sub(
            r"^\s*id:: [a-f0-9]{7,8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\s*$",
            "",
            content,
            flags=re.MULTILINE,
        )

        # Remove LogSeq properties like collapsed:: true
        new_content = re.sub(r"\s+[a-z]+:: (?:true|false)", "", new_content)

        return new_content, new_content != content
