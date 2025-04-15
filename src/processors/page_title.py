from .base import ContentProcessor
import os
import re

class PageTitleProcessor(ContentProcessor):
    """Process page titles according to the specified rules"""
    def __init__(self, filename):
        self.filename = filename
        # Words that should be lowercase in title case
        self.lowercase_words = {
            "a", "an", "the", "and", "but", "or", "for", "nor", "as", "at", "by", "for", "from", "in", "into", "near", "of", "on", "onto", "to", "with",
        }

    def _title_case(self, text):
        """Apply proper title case to text"""
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

    def _format_title_from_filename(self):
        """Format the title based on the filename without the extension"""
        base_name = os.path.splitext(self.filename)[0]
        if "___" in base_name:
            parts = base_name.split("___")
            parts = [p for p in parts[:-1]] + [parts[-1].capitalize()]
            return f"# {'/'.join(parts)}"
        else:
            if base_name:
                text = base_name.replace("_", " ")
                base_name = self._title_case(text)
            return f"# {base_name}"

    def _capitalize_with_slash_rules(self, text):
        """Apply capitalization rules, handling slash-separated text specially"""
        if "/" in text:
            parts = text.split("/")
            parts = [p for p in parts[:-1]] + [parts[-1].capitalize()]
            return "/".join(parts)
        else:
            return self._title_case(text)

    def _extract_alias(self, content):
        """Extract the alias from the content if it exists"""
        alias_match = re.search(r"alias:: (.*?)($|\n)", content)
        if alias_match:
            return alias_match.group(1).strip(), alias_match.start(), alias_match.end()
        return None, -1, -1

    def process(self, content):
        title = self._format_title_from_filename()
        alias_text, alias_start, alias_end = self._extract_alias(content)
        if alias_text:
            aliases = [a.strip() for a in alias_text.split(",")]
            for alias in aliases:
                capitalized_alias = self._capitalize_with_slash_rules(alias)
                title = f"{title} // {capitalized_alias}"
            content = content[:alias_start] + content[alias_end:]
        first_line = content.strip().split("\n")[0] if content.strip() else ""
        if first_line.startswith("# "):
            lines = content.split("\n")
            lines[0] = title
            new_content = "\n".join(lines)
        else:
            new_content = f"{title}\n\n{content.strip()}"
        return new_content, new_content != content
