from .base import ContentProcessor
import os
import re

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


def load_lowercase_words(lowercase_path=None):
    if lowercase_path is None:
        # Default path
        CATEGORIES_DIR = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "..", "categories_config"
        )
        lowercase_path = os.path.join(CATEGORIES_DIR, "lowercase.txt")
    try:
        with open(lowercase_path, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except Exception as e:
        raise RuntimeError(
            f"Could not load lowercase words from {lowercase_path}: {e}. Please provide a valid lowercase.txt file."
        )


class PageTitleProcessor(ContentProcessor):
    """Process page titles according to the specified rules"""

    def __init__(
        self,
        filename,
        uppercase_path=UPPERCASE_PATH,
        types_path=TYPES_PATH,
        lowercase_path=None,
    ):
        self.filename = filename
        self.uppercase_terms = load_uppercase_terms(uppercase_path)
        self.types = load_types(types_path)
        self.lowercase_words = load_lowercase_words(lowercase_path)

    def _title_case(self, text):
        """Apply proper title case to text"""
        words = text.split()
        if not words:
            return ""
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
        return " ".join(result)

    def _maybe_uppercase(self, word, is_first=False, is_last=False):
        # Always uppercase if in the list, else title/lowercase as before
        if word.upper() in self.uppercase_terms:
            return word.upper()
        if not is_first and word.lower() in self.lowercase_words and not is_last:
            return word.lower()
        return word.capitalize()

    def _format_title_from_filename(self):
        """Format the title based on the filename without the extension, flattening any hierarchy"""
        base_name = os.path.splitext(self.filename)[0]
        parts = re.split(r"___|/|_", base_name)
        parts = [p.strip() for p in parts if p.strip()]
        type_found, parts = self._extract_type(parts)
        flat_name = " ".join(parts)
        flat_name = re.sub(r"\s+", " ", flat_name).strip()
        flat_name = self._title_case(flat_name)
        return f"# {flat_name}", type_found

    def _extract_type(self, parts):
        # Remove all occurrences of any type (case-insensitive)
        found_type = None
        filtered_parts = []
        for part in parts:
            if part.lower() in self.types:
                if not found_type:
                    found_type = part
                continue
            filtered_parts.append(part)
        return found_type, filtered_parts

    def _capitalize_with_slash_rules(self, text):
        """Apply capitalization rules, handling slash-separated text specially"""
        if "/" in text:
            parts = text.split("/")
            parts = [p for p in parts[:-1]] + [parts[-1].capitalize()]
            return "/".join(parts)
        else:
            return self._title_case(text)

    def _flatten_and_title_case(self, text):
        """Flatten any hierarchy and apply title case (for aliases and titles)"""
        flat = text.replace("___", " ").replace("/", " ").replace("_", " ")
        flat = re.sub(r"\s+", " ", flat).strip()
        return self._title_case(flat)

    def _extract_alias(self, content):
        """Extract the alias from the content if it exists"""
        alias_match = re.search(r"alias:: (.*?)($|\n)", content)
        if alias_match:
            return alias_match.group(1).strip(), alias_match.start(), alias_match.end()
        return None, -1, -1

    def process(self, content):
        # Remove leading blank lines from content
        content = content.lstrip("\n")
        title, type_found = self._format_title_from_filename()
        main_title = title[2:].strip()  # Remove '# '
        alias_text, alias_start, alias_end = self._extract_alias(content)
        if alias_text:
            aliases = [a.strip() for a in alias_text.split(",")]
            unique_aliases = []
            for alias in aliases:
                # Remove type from alias as well
                alias_parts = re.split(r"___|/|_", alias)
                alias_parts = [p.strip() for p in alias_parts if p.strip()]
                _, alias_parts = self._extract_type(alias_parts)
                flattened_alias = self._title_case(" ".join(alias_parts))
                if (
                    flattened_alias != main_title
                    and flattened_alias not in unique_aliases
                ):
                    unique_aliases.append(flattened_alias)
            for alias in unique_aliases:
                title = f"{title} // {alias}"
            content = content[:alias_start] + content[alias_end:]
        # Insert #<type> tag if type_found
        type_tag_line = f"#{type_found.lower()}" if type_found else None
        first_line = content.strip().split("\n")[0] if content.strip() else ""
        if first_line.startswith("# "):
            lines = content.split("\n")
            lines[0] = title
            # Remove any blank lines after the title
            while len(lines) > 1 and lines[1].strip() == "":
                lines.pop(1)
            if type_tag_line:
                # Insert type tag after exactly one blank line
                lines.insert(1, "")
                lines.insert(2, type_tag_line)
                # Remove any extra blank lines after the tag
                while len(lines) > 3 and lines[3].strip() == "":
                    lines.pop(3)
            new_content = "\n".join(lines)
        else:
            # Always exactly one blank line after title, and after tag if present
            new_content = f"{title}\n\n"
            if type_tag_line:
                new_content += f"{type_tag_line}\n\n"
            new_content += f"{content.strip()}"
        return new_content, new_content != content
