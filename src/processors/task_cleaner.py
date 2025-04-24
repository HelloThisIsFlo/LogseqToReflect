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
        # Check if the line already starts with a bullet before adding one
        new_content = re.sub(
            r"^(?!-\s+)(#+)\s+TODO\s+(.*)",
            r"- [ ] \1 \2",
            new_content,
            flags=re.MULTILINE,
        )
        new_content = re.sub(
            r"^(?!-\s+)(#+)\s+DONE\s+(.*)",
            r"- [x] \1 \2",
            new_content,
            flags=re.MULTILINE,
        )
        new_content = re.sub(
            r"^(?!-\s+)(#+)\s+DOING\s+(.*)",
            r"- [ ] \1 \2",
            new_content,
            flags=re.MULTILINE,
        )
        new_content = re.sub(
            r"^(?!-\s+)(#+)\s+WAITING\s+(.*)",
            r"- [ ] \1 \2",
            new_content,
            flags=re.MULTILINE,
        )
        new_content = re.sub(
            r"^(?!-\s+)(#+)\s+(?:CANCELLED|CANCELED)\s+(.*)",
            r"- [x] \1 ~~\2~~",
            new_content,
            flags=re.MULTILINE,
        )

        # Handle tasks in headings that already have bullets (e.g., "- ## TODO Task")
        new_content = re.sub(r"-\s+(#+)\s+TODO\s+(.*)", r"- [ ] \1 \2", new_content)
        new_content = re.sub(r"-\s+(#+)\s+DONE\s+(.*)", r"- [x] \1 \2", new_content)
        new_content = re.sub(r"-\s+(#+)\s+DOING\s+(.*)", r"- [ ] \1 \2", new_content)
        new_content = re.sub(r"-\s+(#+)\s+WAITING\s+(.*)", r"- [ ] \1 \2", new_content)
        new_content = re.sub(
            r"-\s+(#+)\s+(?:CANCELLED|CANCELED)\s+(.*)", r"- [x] \1 ~~\2~~", new_content
        )

        return new_content, new_content != content
