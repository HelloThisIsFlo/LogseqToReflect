import os
import logging
from typing import Tuple, List, Dict, Any
from .directory_walker import DirectoryWalker
from ..processors.block_references import BlockReferencesReplacer

# Configure logging
logger = logging.getLogger(__name__)


class ConversionStats:
    """Tracks statistics for the conversion process"""

    def __init__(self):
        self.journal_files_processed = 0
        self.journal_files_changed = 0
        self.journal_files_renamed = 0
        self.pages_files_processed = 0
        self.pages_files_changed = 0

    def add_journal_stats(self, files: int, changed: int, renamed: int) -> None:
        """Add journal directory processing statistics"""
        self.journal_files_processed += files
        self.journal_files_changed += changed
        self.journal_files_renamed += renamed

    def add_pages_stats(self, files: int, changed: int) -> None:
        """Add pages directory processing statistics"""
        self.pages_files_processed += files
        self.pages_files_changed += changed

    @property
    def total_files(self) -> int:
        """Total number of files processed"""
        return self.journal_files_processed + self.pages_files_processed

    @property
    def total_changed(self) -> int:
        """Total number of files changed"""
        return self.journal_files_changed + self.pages_files_changed

    def __str__(self) -> str:
        """Generate a report of the conversion statistics"""
        return (
            f"  Journal files processed: {self.journal_files_processed}\n"
            f"  Journal files with content changes: {self.journal_files_changed}\n"
            f"  Journal files renamed: {self.journal_files_renamed}\n"
            f"  Pages files processed: {self.pages_files_processed}\n"
            f"  Pages files with content changes: {self.pages_files_changed}\n"
            f"  Total files processed: {self.total_files}\n"
            f"  Total files with changes: {self.total_changed}"
        )


class LogSeqToReflectConverter:
    """Main converter class to convert LogSeq files to Reflect format"""

    def __init__(
        self,
        workspace: str,
        output_dir: str = None,
        dry_run: bool = False,
        categories_config: str = None,
    ):
        """
        Initialize the LogSeq to Reflect converter.

        Args:
            workspace: Path to the LogSeq workspace
            output_dir: Optional custom output directory. If not provided, will create
                       "<workspace> (Reflect format)" in the same parent directory
            dry_run: If True, show what would be changed without making changes
            categories_config: Path to categories config directory (types.txt, uppercase.txt)
        """
        self.workspace = os.path.abspath(workspace)
        self.output_dir = self._determine_output_dir(output_dir)
        self.dry_run = dry_run
        self.stats = ConversionStats()
        self.categories_config = categories_config

        # Initialize processors and walker
        self.block_references_replacer = BlockReferencesReplacer()
        self.walker = DirectoryWalker(
            workspace,
            self.output_dir,
            dry_run,
            self.block_references_replacer,
            categories_config=self.categories_config,
        )

    def _determine_output_dir(self, output_dir: str = None) -> str:
        """Determine the output directory path"""
        if output_dir is None:
            workspace_name = os.path.basename(self.workspace)
            parent_dir = os.path.dirname(self.workspace)
            return os.path.join(parent_dir, f"{workspace_name} (Reflect format)")
        else:
            return os.path.abspath(output_dir)

    def _process_journal_directories(self, journal_dirs: List[str]) -> None:
        """Process all journal directories"""
        for journal_dir in journal_dirs:
            logger.info(f"Processing journal directory: {journal_dir}")
            files, changed, renamed = self.walker.process_journal_directory(journal_dir)
            self.stats.add_journal_stats(files, changed, renamed)

    def _process_pages_directories(self, pages_dirs: List[str]) -> None:
        """Process all pages directories"""
        for pages_dir in pages_dirs:
            logger.info(f"Processing pages directory: {pages_dir}")
            files, changed = self.walker.process_pages_directory(pages_dir)
            self.stats.add_pages_stats(files, changed)

    def run(self) -> ConversionStats:
        """
        Run the conversion process for the LogSeq workspace.

        Returns:
            ConversionStats object with conversion statistics
        """
        logger.info(f"Converting LogSeq workspace: {self.workspace}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Dry run: {self.dry_run}")

        # Create output directory if needed
        if not self.dry_run:
            os.makedirs(self.output_dir, exist_ok=True)

        # Collect block references from all files
        self.block_references_replacer.collect_blocks(self.workspace)

        # Find directories to process
        journals_dirs = self.walker.find_directories("journals")
        pages_dirs = self.walker.find_directories("pages")

        # Report what we found
        if journals_dirs:
            logger.info(f"Found {len(journals_dirs)} journal directories")
        else:
            logger.info("No journal directories found")

        if pages_dirs:
            logger.info(f"Found {len(pages_dirs)} pages directories")
        else:
            logger.info("No pages directories found")

        # Process all directories
        self._process_journal_directories(journals_dirs)
        self._process_pages_directories(pages_dirs)

        # Return stats for reporting
        return self.stats


def main():
    """Command-line entry point"""
    import argparse

    # Configure logging for command-line use
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert LogSeq files for use in Reflect."
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root directory (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        help='Output directory (default: workspace name + " (Reflect format)")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--categories-config",
        help="Path to categories config directory (containing types.txt and uppercase.txt)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate workspace
    if not os.path.isdir(args.workspace):
        logger.error(f"Error: {args.workspace} is not a valid directory")
        return

    # Run the conversion
    converter = LogSeqToReflectConverter(
        workspace=args.workspace,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        categories_config=args.categories_config,
    )
    stats = converter.run()

    # Print statistics
    print("\nConversion Statistics:")
    print(stats)

    if args.dry_run:
        print("\nRun without --dry-run to apply these changes.")


__all__ = ["main"]
