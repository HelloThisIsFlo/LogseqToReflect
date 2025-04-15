from .base import ContentProcessor
import re
import os
from ..utils import find_markdown_files
from typing import Dict, Tuple


class BlockReferencesCleaner(ContentProcessor):
    """Clean up LogSeq block references"""

    def process(self, content):
        original_content = content

        # Remove block references ((block-id))
        new_content = re.sub(
            r"\(\([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\)\)",
            "",
            content,
        )

        # Remove embedded block references {{embed ((block-id))}}
        new_content = re.sub(
            r"\{\{embed\s+\(\([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\)\)\}\}",
            "",
            new_content,
        )

        # Special case: handle any leftover {{embed ...}} patterns
        new_content = re.sub(r"\{\{embed\s+.*?\}\}", "", new_content)

        # Remove #+BEGIN_... #+END_... blocks
        new_content = re.sub(
            r"#\+BEGIN_\w+.*?#\+END_\w+", "", new_content, flags=re.DOTALL
        )

        # Remove query blocks - match the entire line containing a query
        new_content = re.sub(
            r"^\s*-?\s*\{\{query.*?\}\}.*$", "", new_content, flags=re.MULTILINE
        )

        return new_content, new_content != original_content


class BlockReferencesReplacer(ContentProcessor):
    """
    Replace LogSeq block references with their actual content and a link to the source page.

    This processor:
    1. Collects all block IDs and their associated text from all files
    2. Replaces block references ((block-id)) with the actual content and a link to the source page
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
                # Only print errors, not every file processed
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
        # Clean up the name (replace underscores with spaces, etc.)
        return base_name.replace("_", " ")

    def _extract_block_ids(self, content: str, page_name: str) -> None:
        """Extract all block IDs and their associated text from the content"""
        block_id_pattern = r"^(\s*.*?)id::\s*([a-f0-9-]+)(.*)$"
        lines = content.split("\n")
        for i, line in enumerate(lines):
            match = re.search(block_id_pattern, line)
            if match:
                block_id = match.group(2).strip()
                if not self._is_valid_block_id(block_id):
                    continue
                clean_text = self._extract_block_text(lines, i, match)
                self.block_map[block_id] = (clean_text, page_name)

    def _extract_block_text(self, lines: list, index: int, match: re.Match) -> str:
        """Extract the text associated with a block ID"""
        block_id = match.group(2).strip()
        # Get the text from the previous line if this is just an ID line
        line_text = match.group(1).strip()
        # If the line only contains the ID and no other text,
        # look at the previous line for the content
        if not line_text and index > 0:
            line_text = lines[index - 1].strip()
        # Clean up the text (remove leading/trailing whitespace, bullet points, etc.)
        clean_text = re.sub(r"^\s*-\s*", "", line_text).strip()
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

    def process(self, content: str) -> Tuple[str, bool]:
        """Replace block references with their actual content and a link to the source page"""
        original_content = content
        # Print debug info
        print("Processing content with BlockReferencesReplacer")
        # First, we need to identify all embedded references and process them before regular references
        # This prevents issues where regular references inside embedded tags get replaced first
        for block_id, (text, page_name) in self.block_map.items():
            # Look for embedded references line by line to preserve indentation
            lines = content.split("\n")
            modified_lines = False
            for i, line in enumerate(lines):
                # Match "{{embed ((block-id))}}" pattern
                embed_pattern = r"\{\{embed\s+\(\(" + re.escape(block_id) + r"\)\)\}\}"
                embed_match = re.search(embed_pattern, line)
                if embed_match:
                    print(f"Found embedded reference to {block_id}")
                    # Extract indentation from the beginning of the line
                    indentation = len(line) - len(line.lstrip())
                    indent_spaces = " " * indentation
                    # Get the text before and after the embedded reference
                    before_embed = line[: embed_match.start()]
                    after_embed = line[embed_match.end() :]
                    # Check if this is a bullet point line (starts with "- " after indentation)
                    line_content = line.lstrip()
                    is_bullet = line_content.startswith("- ")
                    # If the line has content before the embed, preserve it
                    # Otherwise use bullet point format if it's a bullet point line
                    if before_embed.strip():
                        # Preserve existing line content around the embed
                        lines[i] = (
                            f"{before_embed}_{text} ([[{page_name}]])_{after_embed}"
                        )
                    else:
                        # No text before the embed, just indentation
                        if is_bullet:
                            # If it's a bullet point, preserve the bullet
                            lines[i] = (
                                f"{indent_spaces}- _{text} ([[{page_name}]])_{after_embed}"
                            )
                        else:
                            # Not a bullet point, just add the content
                            lines[i] = (
                                f"{indent_spaces}_{text} ([[{page_name}]])_{after_embed}"
                            )
                    modified_lines = True
            # Reconstruct the content only if modifications were made
            if modified_lines:
                content = "\n".join(lines)
        # Process regular block references after handling all embedded references
        for block_id, (text, page_name) in self.block_map.items():
            # Check for regular references
            pattern = r"\(\(" + re.escape(block_id) + r"\)\)"
            if re.search(pattern, content):
                print(f"Found regular reference to {block_id}")
            # Replace regular references to this block ID with italicized content + page link
            content = re.sub(pattern, f"_{text} ([[{page_name}]])_", content)
        # If no block IDs in the map but there are still references, clean them up
        if not self.block_map:
            # Remove regular references with updated pattern to match both 7 and 8 character first segments
            content = re.sub(
                r"\(\([a-f0-9]{7,8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\)\)",
                "",
                content,
            )
            # Remove embedded references with updated pattern, preserving surrounding text
            content = re.sub(
                r"\{\{embed\s+\(\([a-f0-9]{7,8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\)\)\}\}",
                "",
                content,
            )
        # Remove #+BEGIN_... #+END_... blocks
        content = re.sub(r"#\+BEGIN_\w+.*?#\+END_\w+", "", content, flags=re.DOTALL)
        # Remove query blocks - match the entire line containing a query
        content = re.sub(
            r"^\s*-?\s*\{\{query.*?\}\}.*$", "", content, flags=re.MULTILINE
        )
        # Special case: handle any leftover {{embed ...}} patterns
        content = re.sub(r"\{\{embed\s+.*?\}\}", "", content)
        return content, content != original_content
