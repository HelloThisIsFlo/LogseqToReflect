from .base import ContentProcessor
import re
import os

CATEGORIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "categories_config"
)
TYPES_PATH = os.environ.get(
    "LOGSEQ2REFLECT_TYPES_PATH", os.path.join(CATEGORIES_DIR, "types.txt")
)


def load_types(types_path=TYPES_PATH):
    try:
        with open(types_path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except Exception:
        return set()


class TagToBacklinkProcessor(ContentProcessor):
    """
    Replace #tag with [[tag]] (lowercase) and collect unique tags, skipping type tags.
    """

    found_tags = set()
    TAG_PATTERN = re.compile(r"(^|\s)#([a-zA-Z0-9\-_]+)")

    def __init__(self, categories_config: str = None):
        if categories_config:
            types_path = os.path.join(categories_config, "types.txt")
            self.types = load_types(types_path)
        else:
            self.types = load_types()

    def process(self, content):
        changed = False
        # Split content into code and non-code blocks
        code_block_pattern = re.compile(r"(\n?)(```|~~~)(.*?)(\2)(.*?)(\2)", re.DOTALL)
        # We'll use a simpler approach: split on fenced code blocks
        fenced_pattern = re.compile(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)", re.MULTILINE)
        parts = fenced_pattern.split(content)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 1 and (part.startswith("```") or part.startswith("~~~")):
                # This is a code block, leave untouched
                result.append(part)
            else:
                # This is normal text, apply tag conversion
                def replacer(match):
                    prefix = match.group(1)
                    tag = match.group(2)
                    tag_lower = tag.lower()
                    if tag_lower in self.types:
                        return f"{prefix}#{tag}"  # Leave as-is
                    TagToBacklinkProcessor.found_tags.add(tag_lower)
                    nonlocal changed
                    changed = True
                    return f"{prefix}[[/{tag_lower}/]]"

                result.append(self.TAG_PATTERN.sub(replacer, part))
        new_content = "".join(result)
        return new_content, changed
