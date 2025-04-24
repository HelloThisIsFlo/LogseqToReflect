from .base import ContentProcessor
import re


class CodeBlockProcessor(ContentProcessor):
    """
    Ensures that code blocks are always in their own bullet points.
    If a code block is not in a separate bullet, it will be moved to a new bullet
    at the same indentation level as its parent.
    """

    def process(self, content):
        if not content:
            return content, False

        lines = content.split("\n")
        result = []
        changes_made = False
        i = 0

        # Process line by line
        while i < len(lines):
            line = lines[i]

            # Check if this is a code block start marker
            if line.strip().startswith("```"):
                # Get indentation of the current line
                indentation = re.match(r"^(\s*)", line).group(1)

                # Check if this line is a bullet point
                is_bullet = bool(re.match(r"^\s*- ", line))

                # If not a bullet point, we need to add it
                if not is_bullet and i > 0:
                    prev_line = lines[i - 1]

                    # Get previous line's indentation
                    prev_indent_match = re.match(r"^(\s*)", prev_line)
                    if prev_indent_match:
                        prev_indentation = prev_indent_match.group(1)

                        # Check if previous line is a bullet
                        prev_is_bullet = bool(re.match(r"^\s*- ", prev_line))

                        if prev_is_bullet:
                            # Increase indentation by 2 spaces from the previous bullet
                            indentation = prev_indentation + "  "
                            code_block_indent = indentation + "  "

                            # Create a new bullet for the code block
                            result.append(f"{indentation}- {line.strip()}")
                            changes_made = True

                            # Process the code block content with proper indentation
                            i += 1
                            while i < len(lines) and not lines[i].strip() == "```":
                                result.append(f"{code_block_indent}{lines[i].strip()}")
                                i += 1

                            # Add the closing backticks with proper indentation
                            if i < len(lines):
                                result.append(f"{code_block_indent}```")
                                i += 1

                            continue

            # Add line as is if no changes needed
            result.append(line)
            i += 1

        new_content = "\n".join(result)
        return new_content, changes_made
