import os
from .journal_file_processor import JournalFileProcessor
from .page_file_processor import PageFileProcessor
from typing import Optional
from ..processors.block_references import BlockReferencesReplacer
from ..utils import find_markdown_files


class DirectoryWalker:
    """Class for walking directories and processing files"""

    def __init__(
        self,
        workspace: str,
        output_dir: str,
        dry_run: bool = False,
        block_references_replacer: Optional[BlockReferencesReplacer] = None,
    ):
        self.workspace = os.path.abspath(workspace)
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.journal_processor = JournalFileProcessor(
            block_references_replacer, dry_run
        )
        self.page_processor = PageFileProcessor(block_references_replacer, dry_run)

    def find_directories(self, dir_name: str) -> list[str]:
        result = []
        for root, dirs, _ in os.walk(self.workspace):
            if dir_name in dirs:
                result.append(os.path.join(root, dir_name))
        return result

    def process_journal_directory(self, journal_dir: str) -> tuple[int, int, int]:
        """
        Process all markdown files in a journal directory and its subdirectories.
        Returns: (total_files, content_changed, renamed)
        """
        rel_path = os.path.relpath(journal_dir, self.workspace)
        output_journal_dir = os.path.join(self.output_dir, rel_path)
        if not self.dry_run:
            os.makedirs(output_journal_dir, exist_ok=True)
        total_files = 0
        content_changed = 0
        renamed = 0
        print(f"Processing journal directory: {journal_dir}")
        print(f"Output directory: {output_journal_dir}")
        for file_path in find_markdown_files(journal_dir):
            # Compute output root for each file
            relative_root = os.path.relpath(os.path.dirname(file_path), journal_dir)
            output_root = os.path.join(output_journal_dir, relative_root)
            content_change, file_renamed = self.journal_processor.process_file(
                file_path, output_root
            )
            total_files += 1
            if content_change:
                content_changed += 1
            if file_renamed:
                renamed += 1
        return total_files, content_changed, renamed

    def process_pages_directory(self, pages_dir: str) -> tuple[int, int]:
        """
        Process all markdown files in a pages directory and its subdirectories.
        Returns: (total_files, content_changed)
        """
        rel_path = os.path.relpath(pages_dir, self.workspace)
        output_pages_dir = os.path.join(self.output_dir, rel_path)
        if not self.dry_run:
            os.makedirs(output_pages_dir, exist_ok=True)
        total_files = 0
        content_changed = 0
        print(f"Processing pages directory: {pages_dir}")
        print(f"Output directory: {output_pages_dir}")
        for file_path in find_markdown_files(pages_dir):
            relative_root = os.path.relpath(os.path.dirname(file_path), pages_dir)
            output_root = os.path.join(output_pages_dir, relative_root)
            output_path = os.path.join(output_root, os.path.basename(file_path))
            content_change, _ = self.page_processor.process_file(file_path, output_path)
            total_files += 1
            if content_change:
                content_changed += 1
        return total_files, content_changed
