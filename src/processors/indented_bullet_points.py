from .base import ContentProcessor
import re


class IndentedBulletPointsProcessor(ContentProcessor):
    """
    Process indented bullet points with tabs and convert them to a format compatible with Reflect.

    1. Removes one level of tab indentation from bullet points directly under headings
    2. Preserves the hierarchical structure of nested bullet points
    3. Ensures proper indentation levels are maintained throughout bullet hierarchies
    4. Preserves indentation for list items that contain headings with tasks
    """

    def process(self, content):
        lines = content.split("\n")
        new_lines = []
        current_section = None

        for i, line in enumerate(lines):
            # Check if line is a heading (starts with #)
            if line.strip().startswith("#"):
                current_section = line
                new_lines.append(line)
                continue

            # Count leading tabs to determine indentation level
            leading_tabs = 0
            for char in line:
                if char == "\t":
                    leading_tabs += 1
                else:
                    break

            # Check if this is a bullet point (after tabs there's "- ")
            trimmed_line = line.lstrip("\t")
            is_bullet = trimmed_line.startswith("- ")

            # Check if this is a bullet with a heading that might include a task
            # Match any heading level (1-6 #) followed by a task marker
            contains_heading_with_task = (
                is_bullet
                and re.search(r"#{1,6}\s+\[([ x])\]", trimmed_line) is not None
            )

            if is_bullet:
                # Special case for bullets containing heading tasks - preserve original indentation
                if contains_heading_with_task:
                    new_lines.append(line)
                # Handle indentation levels based on bullet hierarchy
                elif current_section is not None and leading_tabs == 1:
                    # Top level bullet under a section heading - remove the leading tab
                    new_lines.append(trimmed_line)
                elif leading_tabs > 0:
                    # Keep proper indentation for nested bullets, preserving hierarchy
                    # but reduce level by 1 for top-level bullets
                    indentation = "\t" * (leading_tabs - 1)
                    new_lines.append(f"{indentation}{trimmed_line}")
                else:
                    # Already a top-level bullet without indentation
                    new_lines.append(line)
            else:
                # Not a bullet point, keep as is
                new_lines.append(line)

                # If we have a non-empty, non-heading, non-bullet line,
                # reset the current section (we're no longer directly under a heading)
                if line.strip() and not line.strip().startswith("#"):
                    current_section = None

        new_content = "\n".join(new_lines)
        return new_content, new_content != content
