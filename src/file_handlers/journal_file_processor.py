import os
import re
from ..utils import DateFormatter
from .file_processor import FileProcessor
from ..processors import (
    LinkProcessor,
    BlockReferencesCleaner,
    BlockReferencesReplacer,
    TaskCleaner,
    EmptyContentCleaner,
    IndentedBulletPointsProcessor,
    WikiLinkProcessor,
    DateHeaderProcessor,
)

class JournalFileProcessor(FileProcessor):
    """Process journal files with date headers and task formatting"""
    def __init__(self, dry_run=False):
        super().__init__(dry_run)
        self.block_references_replacer = None

    def get_processors(self):
        processors = [LinkProcessor()]
        if self.block_references_replacer:
            processors.append(self.block_references_replacer)
        else:
            processors.append(BlockReferencesCleaner())
        processors.extend([
            TaskCleaner(),
            EmptyContentCleaner(),
            IndentedBulletPointsProcessor(),
            WikiLinkProcessor(),
        ])
        return processors

    def extract_date_from_filename(self, filename):
        match = re.match(r"(\d{4})_(\d{2})_(\d{2})\.md", filename)
        if not match:
            return None
        return match.groups()

    def process_file(self, file_path, output_dir):
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
            content_changed = False
            for processor in self.get_processors():
                new_content, changed = processor.process(content)
                content = new_content
                content_changed = content_changed or changed
            date_processor = DateHeaderProcessor(formatted_date)
            new_content, changed = date_processor.process(content)
            content = new_content
            content_changed = content_changed or changed
            if self.dry_run:
                if content_changed:
                    print(f"Would update content in {file_path}")
                print(f"Would save to {output_path} (renamed from {filename})")
                return content_changed, True
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return content_changed, True
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False
