import os
import re
from ..utils import DateFormatter
from .file_processor import FileProcessor
from ..processors import (
    LinkProcessor,
    PropertiesProcessor,
    BlockReferencesCleaner,
    BlockReferencesReplacer,
    TaskCleaner,
    EmptyContentCleaner,
    IndentedBulletPointsProcessor,
    WikiLinkProcessor,
    DateHeaderProcessor,
)
from ..processors.ordered_list_processor import OrderedListProcessor
from ..processors.arrows_processor import ArrowsProcessor
from typing import Optional


class JournalFileProcessor(FileProcessor):
    """Process journal files with date headers and task formatting"""

    def __init__(
        self,
        block_references_replacer: Optional[BlockReferencesReplacer] = None,
        dry_run: bool = False,
        categories_config: str = None,  # Accept for compatibility
    ):
        self.block_references_replacer = block_references_replacer
        processors = [LinkProcessor()]
        processors.append(PropertiesProcessor())
        processors.append(OrderedListProcessor())
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
                ArrowsProcessor(),
            ]
        )
        super().__init__(processors, dry_run)

    def extract_date_from_filename(
        self, filename: str
    ) -> Optional[tuple[str, str, str]]:
        match = re.match(r"(\d{4})_(\d{2})_(\d{2})\.md", filename)
        if not match:
            return None
        return match.groups()

    def process_file(self, file_path: str, output_dir: str) -> tuple[bool, bool]:
        """
        Process a journal file, add a date header, and write the result to output_dir.
        Returns:
            Tuple of (content_changed, success)
        """
        filename = os.path.basename(file_path)
        date_parts = self.extract_date_from_filename(filename)
        if not date_parts:
            print(f"Skipping {filename} - doesn't match expected format YYYY_MM_DD.md")
            return False, False

        year, month, day = date_parts
        formatted_date = DateFormatter.format_date_for_header(year, month, day)
        if not formatted_date:
            return False, False

        new_filename = f"{year}-{month}-{day}.md"
        output_path = os.path.join(output_dir, new_filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content, content_changed = self.pipeline.process(content)
            date_processor = DateHeaderProcessor(formatted_date)
            new_content, changed = date_processor.process(new_content)
            content_changed = content_changed or changed
            if self.dry_run:
                if content_changed:
                    print(f"Would update content in {file_path}")
                print(f"Would save to {output_path} (renamed from {filename})")
                return content_changed, True
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return content_changed, True
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False
