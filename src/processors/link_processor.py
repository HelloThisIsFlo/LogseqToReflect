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
        changed = new_content != content

        # Process the content line by line for more precise handling
        lines = new_content.split("\n")
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            i += 1

            # Case 1: Line only contains a property (no bullet point)
            if re.match(r"^\s*[a-z]+::\s+(?:true|false)\s*$", line):
                changed = True
                continue

            # Case 2: Line starts with a bullet and only contains a property followed by indented content on next line
            # Example: "- collapsed:: true\n  content..."
            if (
                re.match(r"^\s*-\s+[a-z]+::\s+(?:true|false)\s*$", line)
                and i < len(lines)
                and lines[i].strip()
            ):
                indent_match = re.match(
                    r"^(\s*)-\s+[a-z]+::\s+(?:true|false)\s*$", line
                )
                if indent_match:
                    indentation = indent_match.group(1)
                    # We found a property line with content on next line
                    bullet_line = f"{indentation}- "

                    # If next line is indented content that belongs to this bullet
                    if (
                        i < len(lines)
                        and re.match(r"^\s+", lines[i])
                        and not lines[i].lstrip().startswith("-")
                    ):
                        # Add the bullet followed directly by the content (without a newline between)
                        next_line = lines[i]
                        # Make sure we maintain the proper indentation for the content
                        if next_line.strip():
                            next_line_content = next_line.lstrip()
                            bullet_line += next_line_content
                            new_lines.append(bullet_line)
                            i += 1

                            # Handle additional lines of content for this bullet
                            while (
                                i < len(lines)
                                and lines[i].strip()
                                and not lines[i].lstrip().startswith("-")
                            ):
                                new_lines.append(lines[i])
                                i += 1

                        else:
                            # Empty line case
                            new_lines.append(bullet_line)
                    else:
                        # No content case
                        new_lines.append(bullet_line)

                    changed = True
                    continue

            # Case 3: Line contains a bullet with a property followed by content on same line
            # Example: "- collapsed:: true Some content"
            if re.match(r"^\s*-\s+[a-z]+::\s+(?:true|false)\s+.+", line):
                # Keep the bullet and the content, removing just the property
                new_line = re.sub(
                    r"^(\s*-\s+)[a-z]+::\s+(?:true|false)\s+(.+)$", r"\1\2", line
                )
                new_lines.append(new_line)
                changed = True
                continue

            # Case 4: Line contains an inline property within it
            if re.search(r"\s+[a-z]+::\s+(?:true|false)", line):
                # Remove just the property part
                new_line = re.sub(r"\s+[a-z]+::\s+(?:true|false)", "", line)
                new_lines.append(new_line)
                changed = True
                continue

            # Default: Keep the line as is
            new_lines.append(line)

        new_content = "\n".join(new_lines)

        # Clean up any extra whitespace while preserving indentation
        new_content = re.sub(
            r"[ \t]+$", "", new_content, flags=re.MULTILINE
        )  # Remove trailing spaces
        new_content = re.sub(
            r"^[ \t]+$", "", new_content, flags=re.MULTILINE
        )  # Remove lines with only spaces
        new_content = re.sub(
            r"\n{3,}", "\n\n", new_content
        )  # Collapse multiple newlines

        # Fix empty bullet points
        new_content = re.sub(r"^(\s*)-\s*$", r"\1- ", new_content, flags=re.MULTILINE)

        return new_content, changed
