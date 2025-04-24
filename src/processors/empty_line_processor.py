from .base import ContentProcessor
import re


class EmptyLineBetweenBulletsProcessor(ContentProcessor):
    """
    Removes empty lines between bullet points while preserving:
    1. Empty lines within a bullet's content
    2. Empty lines within code blocks
    3. Empty lines after title and tags
    """

    def process(self, content):
        if not content:
            return content, False

        lines = content.split("\n")
        result = []
        changes_made = False
        in_code_block = False
        i = 0

        # Title and tag handling (first 2-4 lines)
        if len(lines) > 0:
            result.append(lines[0])
            i += 1
        if len(lines) > 1 and lines[1].strip() == "":
            result.append(lines[1])
            i += 1
        if len(lines) > 2 and re.match(r"^#\w+", lines[2].strip()):
            result.append(lines[2])
            i += 1
            if len(lines) > 3 and lines[3].strip() == "":
                result.append(lines[3])
                i += 1

        # Main processing
        while i < len(lines):
            line = lines[i]
            current_line = line.strip()

            # Track code blocks
            if current_line.startswith("```"):
                in_code_block = not in_code_block
                result.append(line)
                i += 1
                continue

            # Handle empty lines
            if current_line == "":
                if in_code_block:
                    result.append(line)
                    i += 1
                    continue

                # Find next non-empty line
                next_idx = i + 1
                while next_idx < len(lines) and lines[next_idx].strip() == "":
                    next_idx += 1
                next_line = lines[next_idx] if next_idx < len(lines) else ""
                next_is_bullet = next_line.lstrip().startswith("-")

                # Remove the empty line if the next non-empty line is a bullet
                if next_is_bullet:
                    changes_made = True
                    i += 1
                    continue

                # Otherwise, keep the empty line
                result.append(line)
            else:
                result.append(line)
            i += 1

        new_content = "\n".join(result)
        return new_content, changes_made
