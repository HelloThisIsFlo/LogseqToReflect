from .base import ContentProcessor
import re


class FirstContentIndentationProcessor(ContentProcessor):
    """
    Handles edge cases where the first line of content is incorrectly indented.
    This typically happens after properties are processed, which can leave the first
    content line with indentation that should be removed.
    """

    def process(self, content):
        lines = content.split("\n")
        new_lines = []
        title_found = False
        first_content_found = False
        changed = False

        for i, line in enumerate(lines):
            # Check if this is a title line
            if re.match(r"^#\s+.+", line.strip()):
                title_found = True
                new_lines.append(line)
                continue

            # Skip empty lines
            if not line.strip():
                new_lines.append(line)
                continue

            # If we already found the title and this is the first non-empty line after it
            # and it's indented, remove the indentation
            if title_found and not first_content_found and line.strip():
                # If line starts with indentation + bullet, remove indentation
                if re.match(r"^\s+-\s+", line):
                    unindented_line = re.sub(r"^\s+(-\s+)", r"\1", line)
                    new_lines.append(unindented_line)
                    first_content_found = True
                    changed = unindented_line != line
                    continue

            # Add all other lines as-is
            new_lines.append(line)
            if line.strip():
                first_content_found = True

        new_content = "\n".join(new_lines)
        return new_content, changed
