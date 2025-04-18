from .base import ContentProcessor
import re


class TaskCleaner(ContentProcessor):
    """Clean up tasks in LogSeq format for Reflect"""

    def process(self, content):
        # Remove LOGBOOK sections
        new_content = re.sub(r"\s+:LOGBOOK:.*?:END:", "", content, flags=re.DOTALL)

        # Convert cancelled tasks to completed strikethrough
        new_content = re.sub(
            r"-\s+(?:CANCELLED|CANCELED)\s+(.*)", r"- [x] ~~\1~~", new_content
        )

        # Convert waiting tasks to normal todos
        new_content = re.sub(r"-\s+WAITING\s+(.*)", r"- [ ] \1", new_content)

        # Replace task markers in bullet lists
        new_content = re.sub(r"- TODO ", "- [ ] ", new_content)
        new_content = re.sub(r"- DONE ", "- [x] ", new_content)
        new_content = re.sub(r"- DOING ", "- [ ] ", new_content)

        # Handle tasks in headings (e.g., "## TODO Task")
        new_content = re.sub(r"(#+)\s+TODO\s+(.*)", r"\1 [ ] \2", new_content)
        new_content = re.sub(r"(#+)\s+DONE\s+(.*)", r"\1 [x] \2", new_content)
        new_content = re.sub(r"(#+)\s+DOING\s+(.*)", r"\1 [ ] \2", new_content)
        new_content = re.sub(r"(#+)\s+WAITING\s+(.*)", r"\1 [ ] \2", new_content)
        new_content = re.sub(
            r"(#+)\s+(?:CANCELLED|CANCELED)\s+(.*)", r"\1 [x] ~~\2~~", new_content
        )

        return new_content, new_content != content
