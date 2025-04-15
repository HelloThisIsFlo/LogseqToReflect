from .base import ContentProcessor
import re


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

    def _title_case(self, text):
        words = text.split()
        if not words:
            return ""
        result = [words[0].capitalize()]
        for word in words[1:-1] if len(words) > 1 else []:
            if word.lower() in self.lowercase_words:
                result.append(word.lower())
            else:
                result.append(word.capitalize())
        if len(words) > 1:
            result.append(words[-1].capitalize())
        return " ".join(result)

    def _capitalize_with_slash_rules(self, text):
        if "/" in text:
            parts = text.split("/")
            last_part_words = last_part = parts[-1].split(" ")
            last_part_title_cased = []
            if last_part_words:
                last_part_title_cased.append(last_part_words[0].capitalize())
                for word in last_part_words[1:-1] if len(last_part_words) > 1 else []:
                    if word.lower() in self.lowercase_words:
                        last_part_title_cased.append(word.lower())
                    else:
                        last_part_title_cased.append(word.capitalize())
                if len(last_part_words) > 1:
                    last_part_title_cased.append(last_part_words[-1].capitalize())
            formatted_last_part = " ".join(last_part_title_cased)
            parts = [p.lower() for p in parts[:-1]] + [formatted_last_part]
            return "/".join(parts)
        else:
            words = text.split(" ")
            if not words:
                return ""
            result = [words[0].capitalize()]
            for word in words[1:-1] if len(words) > 1 else []:
                if word.lower() in self.lowercase_words:
                    result.append(word.lower())
                else:
                    result.append(word.capitalize())
            if len(words) > 1:
                result.append(words[-1].capitalize())
            return " ".join(result)

    def _format_wikilink(self, match):
        link_text = match.group(1)
        formatted_text = self._capitalize_with_slash_rules(link_text)
        return f"[[{formatted_text}]]"

    def process(self, content):
        new_content = re.sub(r"\[\[(.*?)\]\]", self._format_wikilink, content)
        return new_content, new_content != content
