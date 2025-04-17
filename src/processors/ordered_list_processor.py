from .base import ContentProcessor
import re


class OrderedListProcessor(ContentProcessor):
    """Convert LogSeq ordered-list property into Markdown numbered list items."""

    def process(self, content):
        # Find bullets followed by logseq.order-list-type:: number property and convert them
        pattern = re.compile(
            r"(?m)^(?P<indent>\s*)-\s+(?P<item>.+?)\r?\n\s*logseq\.order-list-type::\s*number\r?\n?"
        )

        def repl(m):
            indent = m.group("indent") or ""
            item = m.group("item")
            return f"{indent}1. {item}\n"

        new_content = pattern.sub(repl, content)
        return new_content, new_content != content
