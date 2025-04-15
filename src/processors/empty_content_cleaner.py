from .base import ContentProcessor
import re

class EmptyContentCleaner(ContentProcessor):
    """Clean up empty lines and empty bullet points left after content removal"""
    def process(self, content):
        lines = content.split("\n")
        new_lines = []

        for i, line in enumerate(lines):
            # Skip empty bullet points (just "- " with possible whitespace)
            if re.match(r"^\s*-\s*$", line):
                continue

            # Add non-empty lines or lines that aren't just whitespace after a task
            # BUT preserve empty lines between sections (before headings)
            if (
                i > 0
                and not line.strip()
                and re.match(r"^\s*-\s*\[[ x]\]", lines[i - 1])
            ):
                # Check if this empty line is followed by a heading
                if i < len(lines) - 1 and lines[i + 1].strip().startswith("#"):
                    new_lines.append(line)
                continue

            new_lines.append(line)

        new_content = "\n".join(new_lines)
        return new_content, new_content != content
