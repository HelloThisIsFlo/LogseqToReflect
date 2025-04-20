from .base import ContentProcessor
import re
import os
from ..utils import find_markdown_files
from typing import Dict, Tuple, List, Optional, Match, Pattern


# Common patterns used for block references
class BlockReferencePatterns:
    # Standard UUID pattern (accepts both 7 and 8 character first segment)
    UUID_PATTERN = r"[a-f0-9]{7,8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"

    # Block reference patterns
    BLOCK_REF = r"\(\({UUID}\)\)"
    EMBED_REF = r"\{\{embed\s+\(\({UUID}\)\)\}\}"
    EMBED_GENERIC = r"\{\{embed\s+.*?\}\}"
    BEGIN_END_BLOCK = r"#\+BEGIN_\w+.*?#\+END_\w+"
    QUERY_BLOCK = r"^\s*-?\s*\{\{query.*?\}\}.*$"

    # ID extraction pattern
    ID_PATTERN = r"^(\s*.*?)id::\s*([a-f0-9-]+)(.*)$"

    @classmethod
    def get_block_ref_pattern(cls) -> Pattern:
        """Get compiled regex for block references"""
        pattern = cls.BLOCK_REF.replace("{UUID}", cls.UUID_PATTERN)
        return re.compile(pattern)

    @classmethod
    def get_embed_ref_pattern(cls) -> Pattern:
        """Get compiled regex for embedded block references"""
        pattern = cls.EMBED_REF.replace("{UUID}", cls.UUID_PATTERN)
        return re.compile(pattern)

    @classmethod
    def get_id_pattern(cls) -> Pattern:
        """Get compiled regex for block ID extraction"""
        return re.compile(cls.ID_PATTERN)


class BlockReferencesCleaner(ContentProcessor):
    """Clean up LogSeq block references"""

    def process(self, content: str) -> Tuple[str, bool]:
        original_content = content
        new_content = content

        # Remove block references
        new_content = BlockReferencePatterns.get_block_ref_pattern().sub(
            "", new_content
        )

        # Remove embedded block references
        new_content = BlockReferencePatterns.get_embed_ref_pattern().sub(
            "", new_content
        )

        # Special case: handle any leftover {{embed ...}} patterns
        new_content = re.sub(BlockReferencePatterns.EMBED_GENERIC, "", new_content)

        # Remove #+BEGIN_SRC...#+END_SRC and #+BEGIN_QUERY...#+END_QUERY blocks only (allow leading whitespace)
        new_content = re.sub(
            r"^\s*#\+BEGIN_SRC.*?^\s*#\+END_SRC",
            "",
            new_content,
            flags=re.DOTALL | re.MULTILINE,
        )
        new_content = re.sub(
            r"^\s*#\+BEGIN_QUERY.*?^\s*#\+END_QUERY",
            "",
            new_content,
            flags=re.DOTALL | re.MULTILINE,
        )

        # Remove query blocks - match the entire line containing a query
        new_content = re.sub(
            BlockReferencePatterns.QUERY_BLOCK, "", new_content, flags=re.MULTILINE
        )

        return new_content, new_content != original_content


class BlockReferencesReplacer(ContentProcessor):
    """
    Replace LogSeq block references with their actual content and a link to the source page.
    """

    def __init__(self):
        # Dictionary to store block IDs and their associated text and page names
        # Format: {block_id: (text, page_name)}
        self.block_map: Dict[str, Tuple[str, str]] = {}
        # Load type definitions if available
        self.types = self._load_types()

    def _load_types(self) -> set:
        """Load type definitions from the types.txt file if it exists"""
        try:
            categories_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "..", "categories_config"
            )
            types_path = os.environ.get(
                "LOGSEQ2REFLECT_TYPES_PATH", os.path.join(categories_dir, "types.txt")
            )
            with open(types_path, "r", encoding="utf-8") as f:
                return set(line.strip().lower() for line in f if line.strip())
        except Exception:
            return set()

    def _is_direct_child(self, parent: str, child: str) -> bool:
        """Return True if 'child' is an immediate subdirectory of 'parent'"""
        parent = os.path.abspath(parent)
        child = os.path.abspath(child)
        return os.path.dirname(child) == parent

    def collect_blocks(self, workspace_path: str) -> None:
        """Scan only 'journals' and 'pages' directories that are direct children of the workspace for block IDs and their text"""
        for subdir in ("journals", "pages"):
            dir_path = os.path.join(workspace_path, subdir)
            if os.path.isdir(dir_path) and self._is_direct_child(
                workspace_path, dir_path
            ):
                for file_path in find_markdown_files(dir_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        page_name = self._extract_page_name(file_path, content)
                        self._extract_block_ids(content, page_name)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")

    def _extract_page_name(self, file_path: str, content: str) -> str:
        """Extract the page name from the file path or content"""
        # First try to get the title from the content (first heading)
        title_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # If no title found, use the file name without extension
        base_name = os.path.basename(file_path)
        base_name = os.path.splitext(base_name)[0]
        return base_name.replace("_", " ")

    def _format_page_name_for_link(self, page_name: str) -> str:
        """Format the page name for use in a link, removing type prefixes if present"""
        if not self.types:
            return page_name

        # Replace backlinks with their content - e.g., [[some text]] becomes "some text"
        # This matches how page titles are formatted when backlinks are in the filename
        page_name = re.sub(r"\[\[(.*?)\]\]", r"\1", page_name)

        # Case 1: Check if the page_name has a slash format (type/Title)
        if "/" in page_name:
            parts = page_name.split("/", 1)
            if len(parts) == 2 and parts[0].lower() in self.types:
                # Return just the title part without the type prefix
                return parts[1].strip()

        # Case 2: Check if the page name starts with a type word followed by space
        # This handles cases like "Jira Title" -> "Title"
        words = page_name.split(None, 1)  # Split by whitespace, max 1 split
        if len(words) >= 2 and words[0].lower() in self.types:
            return words[1].strip()

        return page_name

    def _extract_block_ids(self, content: str, page_name: str) -> None:
        """Extract all block IDs and their associated text from the content"""
        id_pattern = BlockReferencePatterns.get_id_pattern()
        lines = content.split("\n")

        for i, line in enumerate(lines):
            match = id_pattern.search(line)
            if match:
                block_id = match.group(2).strip()
                if not self._is_valid_block_id(block_id):
                    continue

                clean_text = self._extract_block_text(lines, i, match)
                self.block_map[block_id] = (clean_text, page_name)

    def _extract_block_text(self, lines: List[str], index: int, match: Match) -> str:
        """Extract the text associated with a block ID"""
        # Get the text from the line with ID
        line_text = match.group(1).strip()

        # If the line only contains the ID and no other text,
        # look upwards for the nearest non-empty, non-property, non-id line
        if not line_text:
            i = index - 1
            while i >= 0:
                prev_line = lines[i].strip()
                # Skip empty lines and property/id lines
                if (
                    prev_line
                    and not prev_line.startswith("id::")
                    and "::" not in prev_line
                ):
                    line_text = prev_line
                    break
                i -= 1

        # Clean up the text (remove leading/trailing whitespace, bullet points, etc.)
        clean_text = re.sub(r"^\s*-\s*", "", line_text).strip()

        # Convert LogSeq task markers to Reflect format if present
        if clean_text.startswith("TODO "):
            clean_text = "[ ] " + clean_text[5:]
        elif clean_text.startswith("DONE "):
            clean_text = "[x] " + clean_text[5:]
        elif clean_text.startswith("DOING "):
            clean_text = "[ ] " + clean_text[6:]

        # If we still have no content, try to get it from the beginning of the current line
        if not clean_text and match.group(1):
            clean_text = re.sub(r"^\s*-\s*", "", match.group(1)).strip()

        # If the block is a heading (starts with one or more #), bold it and remove the # symbols
        if clean_text.startswith("#"):
            # Remove all leading # and whitespace, then bold
            heading_text = clean_text.lstrip("# ").strip()
            clean_text = f"**{heading_text}**"

        return clean_text

    def _is_valid_block_id(self, block_id: str) -> bool:
        """Check if the block ID matches the expected UUID format"""
        return bool(
            re.match(
                r"^[a-f0-9]{7,8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
                block_id,
            )
        )

    def _replace_embedded_references(self, content: str) -> str:
        """Replace embedded block references while preserving indentation and formatting (optimized)"""
        lines = content.split("\n")
        modified = False
        # Precompile the embed pattern to extract block_ids
        embed_pattern = re.compile(
            r"\{\{embed\s+\(\(([a-f0-9\-]{7,8}-[a-f0-9\-]{4}-[a-f0-9\-]{4}-[a-f0-9\-]{4}-[a-f0-9\-]{12})\)\)\}\}"
        )

        for i, line in enumerate(lines):
            match = embed_pattern.search(line)
            if match:
                block_id = match.group(1)
                if block_id in self.block_map:
                    text, page_name = self.block_map[block_id]
                    # Format page name for the link
                    formatted_page_name = self._format_page_name_for_link(page_name)
                    modified = True
                    # Extract indentation and context
                    indent_ws = line[
                        : len(line) - len(line.lstrip())
                    ]  # Use original whitespace (tabs or spaces)
                    before_embed = line[: match.start()]
                    after_embed = line[match.end() :]
                    line_content = line.lstrip()
                    is_bullet = line_content.startswith("- ")

                    # Format the replacement line preserving context
                    if before_embed.strip():
                        # Preserve existing line content
                        lines[i] = (
                            f"{before_embed}_{text} ([[{formatted_page_name}]])_{after_embed}"
                        )
                    else:
                        # No text before the embed, just indentation
                        if is_bullet:
                            # Preserve the bullet point
                            lines[i] = (
                                f"{indent_ws}- _{text} ([[{formatted_page_name}]])_{after_embed}"
                            )
                        else:
                            # Just add the content
                            lines[i] = (
                                f"{indent_ws}_{text} ([[{formatted_page_name}]])_{after_embed}"
                            )
        return "\n".join(lines) if modified else content

    def _replace_regular_references(self, content: str) -> str:
        """Replace regular ((block-id)) references"""
        for block_id, (text, page_name) in self.block_map.items():
            pattern = r"\(\(" + re.escape(block_id) + r"\)\)"
            formatted_page_name = self._format_page_name_for_link(page_name)
            content = re.sub(pattern, f"_{text} ([[{formatted_page_name}]])_", content)
        return content

    def _clean_orphaned_references(self, content: str) -> str:
        """Clean up any orphaned references not found in the block map"""
        if not self.block_map:
            # Remove regular references
            content = BlockReferencePatterns.get_block_ref_pattern().sub("", content)

            # Remove embedded references
            content = BlockReferencePatterns.get_embed_ref_pattern().sub("", content)

        # Clean up common patterns regardless
        # Only remove #+BEGIN_SRC...#+END_SRC and #+BEGIN_QUERY...#+END_QUERY blocks (allow leading whitespace)
        content = re.sub(
            r"^\s*#\+BEGIN_SRC.*?^\s*#\+END_SRC",
            "",
            content,
            flags=re.DOTALL | re.MULTILINE,
        )
        content = re.sub(
            r"^\s*#\+BEGIN_QUERY.*?^\s*#\+END_QUERY",
            "",
            content,
            flags=re.DOTALL | re.MULTILINE,
        )
        content = re.sub(
            BlockReferencePatterns.QUERY_BLOCK, "", content, flags=re.MULTILINE
        )
        content = re.sub(BlockReferencePatterns.EMBED_GENERIC, "", content)

        return content

    def process(self, content: str) -> Tuple[str, bool]:
        """Replace block references with their actual content and a link to the source page"""
        original_content = content

        # Process embedded references first (they may contain regular references)
        content = self._replace_embedded_references(content)

        # Process regular references
        content = self._replace_regular_references(content)

        # Clean up any orphaned references
        content = self._clean_orphaned_references(content)

        return content, content != original_content
