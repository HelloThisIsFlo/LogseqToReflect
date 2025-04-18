from .base import ContentProcessor
import re

ADMONITION_MAP = {
    "IMPORTANT": ("‼️", "##"),
    "WARNING": ("⚠️", "##"),
    "TIP": ("💡", "##"),
    "NOTE": ("ℹ️", "##"),
}


class AdmonitionProcessor(ContentProcessor):
    """Convert LogSeq admonition blocks to Reflect blockquote format."""

    def process(self, content):
        lines = content.split("\n")
        new_lines = []
        i = 0
        changed = False
        while i < len(lines):
            line = lines[i]
            # Detect admonition start (allow any leading whitespace, optional dash)
            m = re.match(r"^(\s*-\s*)?#\+BEGIN_([A-Z]+)", line)
            if m and m.group(2) in ADMONITION_MAP:
                typ = m.group(2)
                emoji, heading = ADMONITION_MAP[typ]
                list_prefix = m.group(1) or ""
                block = []
                i += 1
                while i < len(lines):
                    block_line = lines[i].lstrip()
                    if re.match(rf"^#\+END_{typ}", block_line):
                        break
                    block.append(block_line)
                    i += 1
                if block:
                    heading_line = block[0].strip() if block else ""
                    body_lines = block[1:] if len(block) > 1 else []
                    admon = f"> {heading} {emoji} {heading_line}".rstrip()
                    if list_prefix:
                        new_lines.append(f"{list_prefix}{admon}")
                        # For continuation, replace the last '- ' in the prefix with two spaces
                        if "- " in list_prefix:
                            continuation = list_prefix[::-1].replace(" -", "  ", 1)[
                                ::-1
                            ]
                        else:
                            continuation = list_prefix + "  "
                        for body in body_lines:
                            body = body.strip()
                            if body:
                                new_lines.append(f"{continuation}> _{body}_")
                    else:
                        new_lines.append(admon)
                        for body in body_lines:
                            body = body.strip()
                            if body:
                                new_lines.append(f"> _{body}_")
                        # Add a blank line after non-list admonitions unless next line is blank or end of file
                        next_line = lines[i + 1] if i + 1 < len(lines) else ""
                        if next_line.strip() != "":
                            new_lines.append("")
                    changed = True
                i += 1
                continue
            new_lines.append(line)
            i += 1
        new_content = "\n".join(new_lines)
        return new_content, changed
