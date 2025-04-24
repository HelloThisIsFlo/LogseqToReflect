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

        # Keep track of the first two lines (title and possibly a tag)
        # First line is always the title
        if len(lines) > 0:
            result.append(lines[0])
            i += 1

        # Second line should be empty
        if len(lines) > 1 and lines[1].strip() == "":
            result.append(lines[1])
            i += 1

        # Third line might be a tag line
        if len(lines) > 2 and re.match(r"^#\w+", lines[2].strip()):
            result.append(lines[2])
            i += 1
            # If there's a tag, the fourth line should be empty
            if len(lines) > 3 and lines[3].strip() == "":
                result.append(lines[3])
                i += 1

        # Process the rest of the file
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
                # Always keep empty lines in code blocks
                if in_code_block:
                    result.append(line)
                    i += 1
                    continue

                # Check if this is an empty line between bullets
                if (
                    i + 1 < len(lines)
                    and lines[i + 1].strip().startswith("-")
                    and result
                    and result[-1].strip().startswith("-")
                ):
                    # Remove the empty line between bullets
                    changes_made = True
                    i += 1
                    continue

                # Check if this is an empty line that's part of a bullet content
                # Look at the previous and next line
                prev_indentation = 0
                next_indentation = 0

                if result:
                    prev_line = result[-1]
                    prev_indentation = len(prev_line) - len(prev_line.lstrip())

                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_indentation = len(next_line) - len(next_line.lstrip())
                    next_is_bullet = next_line.strip().startswith("-")

                    # If the next line is a bullet point with the same indentation as the previous line,
                    # and the previous line is not a bullet point, this is likely an empty line between bullets
                    if (
                        next_is_bullet
                        and result
                        and not prev_line.strip().startswith("-")
                        and next_indentation <= prev_indentation
                    ):
                        changes_made = True
                        i += 1
                        continue

                # Keep other empty lines (they're likely part of bullet content or structure)
                result.append(line)
            else:
                # Non-empty line
                result.append(line)

            i += 1

        new_content = "\n".join(result)
        return new_content, changes_made
