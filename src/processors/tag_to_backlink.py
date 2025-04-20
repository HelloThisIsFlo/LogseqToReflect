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
    TAG_PATTERN = re.compile(r"(?<!\\w)#([a-zA-Z0-9\-_]+)")

    def __init__(self, categories_config: str = None):
        if categories_config:
            types_path = os.path.join(categories_config, "types.txt")
            self.types = load_types(types_path)
        else:
            self.types = load_types()

    def process(self, content):
        changed = False

        def replacer(match):
            tag = match.group(1)
            tag_lower = tag.lower()
            if tag_lower in self.types:
                return f"#{tag}"  # Leave as-is
            TagToBacklinkProcessor.found_tags.add(tag_lower)
            nonlocal changed
            changed = True
            return f"[[/{tag_lower}/]]"

        new_content = self.TAG_PATTERN.sub(replacer, content)
        return new_content, changed
