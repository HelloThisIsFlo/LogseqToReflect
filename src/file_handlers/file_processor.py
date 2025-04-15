import os
from src.processors.pipeline import ProcessorPipeline
from typing import List
from src.processors.base import ContentProcessor


class FileProcessor:
    """Base class for file processors, handling file I/O and delegating content processing to a ProcessorPipeline."""

    def __init__(self, processors: List[ContentProcessor], dry_run: bool = False):
        self.pipeline = ProcessorPipeline(processors)
        self.dry_run = dry_run

    def process_file(self, file_path: str, output_path: str) -> tuple[bool, bool]:
        """
        Process a file and write the result to output_path.
        Returns:
            Tuple of (content_changed, success)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content, content_changed = self.pipeline.process(content)
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
