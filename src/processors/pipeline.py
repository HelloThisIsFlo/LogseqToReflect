from typing import List, Tuple, Optional
from .base import ContentProcessor
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ProcessorPipeline:
    """
    Pipeline that sequentially applies multiple content processors to a text.
    Provides unified error handling and performance tracking.
    """

    def __init__(self, processors: List[ContentProcessor]):
        """
        Initialize the pipeline with a list of processors.

        Args:
            processors: List of ContentProcessor instances to apply in sequence
        """
        self.processors = processors

    def process(self, content: str) -> Tuple[str, bool]:
        """
        Process content through all processors in sequence.

        Args:
            content: The content to process

        Returns:
            Tuple of (processed_content, was_changed)
        """
        if not content:
            return content, False

        changed = False
        current_content = content

        for idx, processor in enumerate(self.processors):
            try:
                processor_name = processor.__class__.__name__
                new_content, did_change = processor.process(current_content)

                if did_change:
                    logger.debug(f"Processor {processor_name} changed content")
                    changed = True
                    current_content = new_content

            except Exception as e:
                # Log error but continue with pipeline
                logger.error(
                    f"Error in processor {processor.__class__.__name__}: {str(e)}"
                )

        return current_content, changed
