from .base import ContentProcessor
import re
from typing import List
import os
from .tag_to_backlink import TagToBacklinkProcessor

# Use environment variables for config paths if set, else default
CATEGORIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "categories_config"
)
UPPERCASE_PATH = os.environ.get(
    "LOGSEQ2REFLECT_UPPERCASE_PATH", os.path.join(CATEGORIES_DIR, "uppercase.txt")
)
TYPES_PATH = os.environ.get(
    "LOGSEQ2REFLECT_TYPES_PATH", os.path.join(CATEGORIES_DIR, "types.txt")
)


def load_uppercase_terms(uppercase_path=UPPERCASE_PATH):
    try:
        with open(uppercase_path, "r", encoding="utf-8") as f:
            return set(line.strip().upper() for line in f if line.strip())
    except Exception:
        return set()


def load_types(types_path=TYPES_PATH):
    try:
        with open(types_path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except Exception:
        return set()


class WikiLinkProcessor(ContentProcessor):
    """Process wikilinks using the same formatting rules as page titles"""

    def __init__(self, categories_config: str = None):
        self.lowercase_words = {
            "a",
            "an",
            "the",
            "and",
            "but",
            "or",
            "for",
            "nor",
            "as",
            "at",
            "by",
            "for",
            "from",
            "in",
            "into",
            "near",
            "of",
            "on",
            "onto",
            "to",
            "with",
        }
        if categories_config:
            uppercase_path = os.path.join(categories_config, "uppercase.txt")
            types_path = os.path.join(categories_config, "types.txt")
            self.uppercase_terms = load_uppercase_terms(uppercase_path)
            self.types = load_types(types_path)
        else:
            self.uppercase_terms = load_uppercase_terms()
            self.types = load_types()

    def _title_case_words(self, words: List[str]) -> List[str]:
        """Apply title case rules to a list of words"""
        if not words:
            return []
        # First word always capitalized (or uppercased if in list)
        result = [
            self._maybe_uppercase(words[0], is_first=True, is_last=(len(words) == 1))
        ]
        for i, word in enumerate(words[1:-1] if len(words) > 1 else []):
            result.append(self._maybe_uppercase(word, is_first=False, is_last=False))
        if len(words) > 1:
            result.append(
                self._maybe_uppercase(words[-1], is_first=False, is_last=True)
            )
        return result

    def _maybe_uppercase(self, word, is_first=False, is_last=False):
        if word.upper() in self.uppercase_terms:
            return word.upper()
        if not is_first and word.lower() in self.lowercase_words and not is_last:
            return word.lower()
        return word.capitalize()

    def _title_case(self, text: str) -> str:
        """Apply title case to a text string"""
        words = text.split()
        return " ".join(self._title_case_words(words))

    def _format_path_with_slashes(self, text: str) -> str:
        """Format text that contains path-like components with slashes"""
        if "/" not in text:
            return self._title_case(text)

        # Split by slash and keep all parts except last in lowercase
        parts = text.split("/")

        # Apply title case to the last part only
        last_part = self._title_case(parts[-1])

        # All parts before the last part should be lowercase
        path_parts = [p.lower() for p in parts[:-1]] + [last_part]

        return "/".join(path_parts)

    def _flatten_and_title_case(self, text: str) -> str:
        parts = re.split(r"___|/|_", text)
        parts = [p.strip() for p in parts if p.strip()]
        # Remove type if present
        parts = [p for p in parts if p.lower() not in self.types]
        flat = " ".join(parts)
        flat = re.sub(r"\s+", " ", flat).strip()
        return self._title_case(flat)

    def _format_wikilink(self, match):
        """Format a wikilink match"""
        link_text = match.group(1)
        # If the text is already a tag (previously was /tag/ format), leave untouched
        found_tags_lower = {t.lower() for t in TagToBacklinkProcessor.found_tags}
        if link_text.lower() in found_tags_lower:
            return f"[[{link_text.lower()}]]"
        formatted_text = self._flatten_and_title_case(link_text)
        return f"[[{formatted_text}]]"

    def process(self, content):
        """Process wikilinks in content"""
        new_content = re.sub(r"\[\[(.*?)\]\]", self._format_wikilink, content)
        return new_content, new_content != content
