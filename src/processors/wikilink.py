from .base import ContentProcessor
import re
from typing import List


class WikiLinkProcessor(ContentProcessor):
    """Process wikilinks using the same formatting rules as page titles"""

    def __init__(self):
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

    def _title_case_words(self, words: List[str]) -> List[str]:
        """Apply title case rules to a list of words"""
        if not words:
            return []

        # First word is always capitalized
        result = [words[0].capitalize()]

        # Middle words follow lowercase rules
        for word in words[1:-1] if len(words) > 1 else []:
            if word.lower() in self.lowercase_words:
                result.append(word.lower())
            else:
                result.append(word.capitalize())

        # Last word is always capitalized
        if len(words) > 1:
            result.append(words[-1].capitalize())

        return result

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
        flat = text.replace("___", " ").replace("/", " ").replace("_", " ")
        flat = re.sub(r"\s+", " ", flat).strip()
        return self._title_case(flat)

    def _format_wikilink(self, match):
        """Format a wikilink match"""
        link_text = match.group(1)
        formatted_text = self._flatten_and_title_case(link_text)
        return f"[[{formatted_text}]]"

    def process(self, content):
        """Process wikilinks in content"""
        new_content = re.sub(r"\[\[(.*?)\]\]", self._format_wikilink, content)
        return new_content, new_content != content
