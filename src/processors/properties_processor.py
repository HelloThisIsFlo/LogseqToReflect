from .base import ContentProcessor
import re


class PropertiesProcessor(ContentProcessor):
    """Remove unwanted LogSeq property lines like 'filters::' from content, highlight bullets with background-color, and delete extra properties. Also ensure only one blank line in a row."""

    def process(self, content):
        lines = content.split("\n")
        new_lines = []
        i = 0
        changed = False
        while i < len(lines):
            line = lines[i]
            # Check for background-color property
            if re.match(r"^\s*background-color::", line):
                # Find the previous non-property, non-empty line
                j = len(new_lines) - 1
                while j >= 0 and (
                    re.match(r"^\s*([a-zA-Z0-9_-]+)::", new_lines[j])
                    or new_lines[j].strip() == ""
                ):
                    j -= 1
                if j >= 0:
                    # Wrap the previous line's content (after bullet marker) with == ==
                    prev_line = new_lines[j]
                    bullet_match = re.match(r"^(\s*-\s*)(.*)$", prev_line)
                    if bullet_match:
                        prefix, content_part = bullet_match.groups()
                        # Check if content_part starts with heading markers (e.g., '### ')
                        heading_match = re.match(r"(#+\s+)(.*)$", content_part)
                        if heading_match:
                            heading_prefix, heading_text = heading_match.groups()
                            new_lines[j] = f"{prefix}{heading_prefix}=={heading_text}=="
                        else:
                            new_lines[j] = f"{prefix}=={content_part}=="
                        changed = True
                # Skip this property line
                changed = True
                i += 1
                continue
            # Remove filters:: property lines
            if re.match(r"^\s*filters::", line):
                changed = True
                i += 1
                continue
            # Remove any other property lines (e.g. 'priority::', 'id::', etc.)
            if re.match(r"^\s*[a-zA-Z0-9_-]+::", line):
                changed = True
                i += 1
                continue
            new_lines.append(line)
            i += 1
        # Remove multiple blank lines in a row
        cleaned_lines = []
        prev_blank = False
        for l in new_lines:
            if l.strip() == "":
                if not prev_blank:
                    cleaned_lines.append("")
                prev_blank = True
            else:
                cleaned_lines.append(l)
                prev_blank = False
        new_content = "\n".join(cleaned_lines)
        return new_content, changed
