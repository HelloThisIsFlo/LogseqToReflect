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

class PageFileProcessor(FileProcessor):
    """Process page files with task formatting and link preservation"""
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

    def process_file(self, file_path, output_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            processors = self.get_processors()
            # Add PageTitleProcessor with the correct filename at the start
            processors.insert(0, PageTitleProcessor(os.path.basename(file_path)))
            content_changed = False
            for processor in processors:
                content, changed = processor.process(content)
                if changed:
                    content_changed = True
            if self.dry_run:
                if content_changed:
                    print(f"Would update content in {file_path}")
                print(f"Would save to {output_path}")
                return content_changed, True
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return content_changed, True
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False
