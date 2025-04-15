from typing import List
from .base import ContentProcessor


class ProcessorPipeline:
    def __init__(self, processors: List[ContentProcessor]):
        self.processors = processors

    def process(self, content: str) -> (str, bool):
        changed = False
        for processor in self.processors:
            content, did_change = processor.process(content)
            changed = changed or did_change
        return content, changed
