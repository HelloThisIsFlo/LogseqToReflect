import os
import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional, Iterator

from .journal_file_processor import JournalFileProcessor
from .page_file_processor import PageFileProcessor
from ..processors.block_references import BlockReferencesReplacer
from ..utils import find_markdown_files

# Configure logging
logger = logging.getLogger(__name__)


class DirectoryWalker:
    """Class for walking directories and processing files"""

    def __init__(
        self,
        workspace: str,
        output_dir: str,
        dry_run: bool = False,
        block_references_replacer: Optional[BlockReferencesReplacer] = None,
        categories_config: str = None,
    ):
        """
        Initialize DirectoryWalker for processing LogSeq files.

        Args:
            workspace: The root LogSeq workspace directory
            output_dir: The output directory for converted files
            dry_run: If True, don't actually write any files
            block_references_replacer: Optional block references processor
            categories_config: Optional categories configuration
        """
        self.workspace = os.path.abspath(workspace)
        self.output_dir = output_dir
        self.dry_run = dry_run
        self.journal_processor = JournalFileProcessor(
            block_references_replacer, dry_run, categories_config=categories_config
        )
        self.page_processor = PageFileProcessor(
            block_references_replacer, dry_run, categories_config=categories_config
        )
        # Always use step_1 and step_2 subdirectories under the output dir
        self.step_1_dir = os.path.join(self.output_dir, "step_1")
        self.step_2_dir = os.path.join(self.output_dir, "step_2")

    def find_directories(self, dir_name: str) -> List[str]:
        """
        Find all directories with the given name that are direct children of the workspace.

        Args:
            dir_name: Name of directory to find (e.g., "journals", "pages")

        Returns:
            List of absolute paths to matching directories
        """
        result = []
        try:
            # Only look for direct children
            candidate = os.path.join(self.workspace, dir_name)
            if os.path.isdir(candidate):
                result.append(candidate)
        except Exception as e:
            logger.error(f"Error finding directories '{dir_name}': {e}")

        return result

    def _ensure_output_directory(self, output_path: str) -> bool:
        """
        Ensure the output directory exists.

        Args:
            output_path: The directory path to create

        Returns:
            True if successful or dry run, False on failure
        """
        if self.dry_run:
            return True

        try:
            os.makedirs(output_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create output directory {output_path}: {e}")
            return False

    def _has_aliases(self, file_path: str) -> bool:
        """
        Check if a file has aliases (triple underscores in filename).

        Args:
            file_path: Path to the file to check

        Returns:
            True if file has aliases, False otherwise
        """
        filename = os.path.basename(file_path)
        if "___" in filename:
            return True

        # Also check if file content has an alias property
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if re.search(r"alias::", content):
                return True
        except Exception:
            pass

        return False

    def _get_output_dir_for_file(self, file_path: str) -> str:
        """
        Determine the appropriate output directory for a file.

        Args:
            file_path: Path to the file to check

        Returns:
            Path to the appropriate output directory (step_1 or step_2)
        """
        if self._has_aliases(file_path):
            return self.step_1_dir
        else:
            return self.step_2_dir

    def process_journal_directory(self, journal_dir: str) -> Tuple[int, int, int]:
        """
        Process all markdown files in a journal directory and its subdirectories.

        Args:
            journal_dir: Path to the journal directory

        Returns:
            Tuple of (total_files, content_changed, renamed)
        """
        # Ensure both output directories exist
        if not self._ensure_output_directory(
            self.step_1_dir
        ) or not self._ensure_output_directory(self.step_2_dir):
            return 0, 0, 0
        total_files = 0
        content_changed = 0
        renamed = 0
        logger.info(f"Processing journal directory: {journal_dir}")
        logger.info(f"Output step_1 directory: {self.step_1_dir}")
        logger.info(f"Output step_2 directory: {self.step_2_dir}")
        try:
            for file_path in find_markdown_files(journal_dir):
                # Journals always go to step_2
                output_root = self.step_2_dir
                try:
                    content_change, file_renamed = self.journal_processor.process_file(
                        file_path, output_root
                    )
                    total_files += 1
                    if content_change:
                        content_changed += 1
                    if file_renamed:
                        renamed += 1
                except Exception as e:
                    logger.error(f"Error processing journal file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error walking journal directory {journal_dir}: {e}")
        return total_files, content_changed, renamed

    def process_pages_directory(self, pages_dir: str) -> Tuple[int, int]:
        """
        Process all markdown files in a pages directory and its subdirectories.

        Args:
            pages_dir: Path to the pages directory

        Returns:
            Tuple of (total_files, content_changed)
        """
        # Ensure both output directories exist
        if not self._ensure_output_directory(
            self.step_1_dir
        ) or not self._ensure_output_directory(self.step_2_dir):
            return 0, 0
        total_files = 0
        content_changed = 0
        logger.info(f"Processing pages directory: {pages_dir}")
        logger.info(f"Output step_1 directory: {self.step_1_dir}")
        logger.info(f"Output step_2 directory: {self.step_2_dir}")
        try:
            for file_path in find_markdown_files(pages_dir):
                output_dir = self._get_output_dir_for_file(file_path)
                output_path = os.path.join(output_dir, os.path.basename(file_path))
                try:
                    if not self.dry_run:
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    content_change, _ = self.page_processor.process_file(
                        file_path, output_path
                    )
                    total_files += 1
                    if content_change:
                        content_changed += 1
                except Exception as e:
                    logger.error(f"Error processing page file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error walking pages directory {pages_dir}: {e}")
        return total_files, content_changed
