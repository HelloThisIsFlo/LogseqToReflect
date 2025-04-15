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

        # Remove #+BEGIN_... #+END_... blocks
        new_content = re.sub(
            BlockReferencePatterns.BEGIN_END_BLOCK, "", new_content, flags=re.DOTALL
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

    def collect_blocks(self, workspace_path: str) -> None:
        """Scan all files in the workspace to collect block IDs and their text"""
        for file_path in find_markdown_files(workspace_path):
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
        """Replace embedded block references while preserving indentation and formatting"""
        lines = content.split("\n")
        modified = False

        for i, line in enumerate(lines):
            for block_id, (text, page_name) in self.block_map.items():
                # Create embedding pattern for this specific block ID
                embed_pattern = r"\{\{embed\s+\(\(" + re.escape(block_id) + r"\)\)\}\}"
                embed_match = re.search(embed_pattern, line)

                if embed_match:
                    modified = True
                    # Extract indentation and context
                    indentation = len(line) - len(line.lstrip())
                    indent_spaces = " " * indentation
                    before_embed = line[: embed_match.start()]
                    after_embed = line[embed_match.end() :]
                    line_content = line.lstrip()
                    is_bullet = line_content.startswith("- ")

                    # Format the replacement line preserving context
                    if before_embed.strip():
                        # Preserve existing line content
                        lines[i] = (
                            f"{before_embed}_{text} ([[{page_name}]])_{after_embed}"
                        )
                    else:
                        # No text before the embed, just indentation
                        if is_bullet:
                            # Preserve the bullet point
                            lines[i] = (
                                f"{indent_spaces}- _{text} ([[{page_name}]])_{after_embed}"
                            )
                        else:
                            # Just add the content
                            lines[i] = (
                                f"{indent_spaces}_{text} ([[{page_name}]])_{after_embed}"
                            )
                    break  # Only process one embed per line

        return "\n".join(lines) if modified else content

    def _replace_regular_references(self, content: str) -> str:
        """Replace regular ((block-id)) references"""
        for block_id, (text, page_name) in self.block_map.items():
            pattern = r"\(\(" + re.escape(block_id) + r"\)\)"
            content = re.sub(pattern, f"_{text} ([[{page_name}]])_", content)
        return content

    def _clean_orphaned_references(self, content: str) -> str:
        """Clean up any orphaned references not found in the block map"""
        if not self.block_map:
            # Remove regular references
            content = BlockReferencePatterns.get_block_ref_pattern().sub("", content)

            # Remove embedded references
            content = BlockReferencePatterns.get_embed_ref_pattern().sub("", content)

        # Clean up common patterns regardless
        content = re.sub(
            BlockReferencePatterns.BEGIN_END_BLOCK, "", content, flags=re.DOTALL
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
