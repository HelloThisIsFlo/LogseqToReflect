import os
from .directory_walker import DirectoryWalker
from ..processors.block_references import BlockReferencesReplacer

class LogSeqToReflectConverter:
    """Main converter class to convert LogSeq files to Reflect format"""
    def __init__(self, workspace, output_dir=None, dry_run=False):
        self.workspace = os.path.abspath(workspace)
        if output_dir is None:
            workspace_name = os.path.basename(workspace)
            parent_dir = os.path.dirname(workspace)
            self.output_dir = os.path.join(parent_dir, f"{workspace_name} (Reflect format)")
        else:
            self.output_dir = os.path.abspath(output_dir)
        self.dry_run = dry_run
        self.block_references_replacer = BlockReferencesReplacer()
        self.walker = DirectoryWalker(workspace, self.output_dir, dry_run)

    def run(self):
        print(f"Converting LogSeq workspace: {self.workspace}")
        print(f"Output directory: {self.output_dir}")
        print(f"Dry run: {self.dry_run}")
        if not self.dry_run:
            os.makedirs(self.output_dir, exist_ok=True)
        self.block_references_replacer.collect_blocks(self.workspace)
        self.walker.journal_processor.block_references_replacer = self.block_references_replacer
        self.walker.page_processor.block_references_replacer = self.block_references_replacer
        journals_dirs = self.walker.find_directories("journals")
        pages_dirs = self.walker.find_directories("pages")
        if journals_dirs:
            print(f"Found {len(journals_dirs)} journal directories")
        else:
            print("No journal directories found")
        if pages_dirs:
            print(f"Found {len(pages_dirs)} pages directories")
        else:
            print("No pages directories found")
        total_journal_files = total_journal_content_changed = total_journal_renamed = 0
        total_pages_files = total_pages_content_changed = 0
        for journal_dir in journals_dirs:
            files, changed, renamed = self.walker.process_journal_directory(journal_dir)
            total_journal_files += files
            total_journal_content_changed += changed
            total_journal_renamed += renamed
        for pages_dir in pages_dirs:
            files, changed = self.walker.process_pages_directory(pages_dir)
            total_pages_files += files
            total_pages_content_changed += changed
        print(f"  Journal files processed: {total_journal_files}")
        print(f"  Journal files with content changes: {total_journal_content_changed}")
        print(f"  Journal files renamed: {total_journal_renamed}")
        if pages_dirs:
            print(f"  Pages files processed: {total_pages_files}")
            print(f"  Pages files with content changes: {total_pages_content_changed}")
        total_files = total_journal_files + total_pages_files
        total_changes = total_journal_content_changed + total_pages_content_changed
        print(f"  Total files processed: {total_files}")
        print(f"  Total files with changes: {total_changes}")

def main():
    import argparse
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
    args = parser.parse_args()
    if not os.path.isdir(args.workspace):
        print(f"Error: {args.workspace} is not a valid directory")
        return
    converter = LogSeqToReflectConverter(
        workspace=args.workspace, output_dir=args.output_dir, dry_run=args.dry_run
    )
    converter.run()
    if args.dry_run:
        print("\nRun without --dry-run to apply these changes.")

__all__ = ["main"]
