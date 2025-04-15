import os
from .file_processor import FileProcessor
from ..processors import (
    LinkProcessor,
    BlockReferencesCleaner,
    BlockReferencesReplacer,
    TaskCleaner,
    EmptyContentCleaner,
    IndentedBulletPointsProcessor,
    PageTitleProcessor,
    WikiLinkProcessor,
)
from typing import Optional


class PageFileProcessor(FileProcessor):
    """Process page files with task formatting and link preservation"""

    def __init__(
        self,
        block_references_replacer: Optional[BlockReferencesReplacer] = None,
        dry_run: bool = False,
    ):
        self.block_references_replacer = block_references_replacer
        processors = [LinkProcessor()]
        if self.block_references_replacer:
            processors.append(self.block_references_replacer)
        else:
            processors.append(BlockReferencesCleaner())
        processors.extend(
            [
                TaskCleaner(),
                EmptyContentCleaner(),
                IndentedBulletPointsProcessor(),
                WikiLinkProcessor(),
            ]
        )
        super().__init__(processors, dry_run)

    def process_file(self, file_path: str, output_path: str) -> tuple[bool, bool]:
        """
        Process a page file, add a page title, and write the result to output_path.
        Returns:
            Tuple of (content_changed, success)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Add PageTitleProcessor with the correct filename at the start
            title_processor = PageTitleProcessor(os.path.basename(file_path))
            new_content, content_changed = title_processor.process(content)
            new_content, changed = self.pipeline.process(new_content)
            content_changed = content_changed or changed
            if self.dry_run:
                if content_changed:
                    print(f"Would update content in {file_path}")
                print(f"Would save to {output_path}")
                return content_changed, True
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return content_changed, True
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False
