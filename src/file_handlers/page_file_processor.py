import os
from .file_processor import FileProcessor
from ..processors import (
    LinkProcessor,
    PropertiesProcessor,
    BlockReferencesCleaner,
    BlockReferencesReplacer,
    TaskCleaner,
    EmptyContentCleaner,
    IndentedBulletPointsProcessor,
    PageTitleProcessor,
    WikiLinkProcessor,
    AdmonitionProcessor,
    TagToBacklinkProcessor,
    CodeBlockProcessor,
    HeadingProcessor,
    FirstContentIndentationProcessor,
    ImageProcessor,
)
from ..processors.ordered_list_processor import OrderedListProcessor
from ..processors.arrows_processor import ArrowsProcessor
from ..processors.empty_line_processor import EmptyLineBetweenBulletsProcessor
from ..processors.backlink_collector import BacklinkCollector
from typing import Optional


class PageFileProcessor(FileProcessor):
    """Process page files with task formatting and link preservation"""

    def __init__(
        self,
        block_references_replacer: Optional[BlockReferencesReplacer] = None,
        dry_run: bool = False,
        categories_config: str = None,
    ):
        self.block_references_replacer = block_references_replacer
        self.categories_config = categories_config
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
                AdmonitionProcessor(),
                EmptyContentCleaner(),
                CodeBlockProcessor(),
                IndentedBulletPointsProcessor(),
                HeadingProcessor(),
                TagToBacklinkProcessor(categories_config=categories_config),
                (
                    WikiLinkProcessor(categories_config=categories_config)
                    if categories_config
                    else WikiLinkProcessor()
                ),
                BacklinkCollector(),
                ArrowsProcessor(),
                EmptyLineBetweenBulletsProcessor(),
                FirstContentIndentationProcessor(),
                ImageProcessor(),
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
            if self.categories_config:
                uppercase_path = os.path.join(self.categories_config, "uppercase.txt")
                types_path = os.path.join(self.categories_config, "types.txt")
                lowercase_path = os.path.join(self.categories_config, "lowercase.txt")
                title_processor = PageTitleProcessor(
                    os.path.basename(file_path),
                    uppercase_path=uppercase_path,
                    types_path=types_path,
                    lowercase_path=lowercase_path,
                )
            else:
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
