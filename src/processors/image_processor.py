from .base import ContentProcessor
import re
import os


class ImageProcessor(ContentProcessor):
    """Process LogSeq image links for Reflect compatibility"""

    def __init__(self):
        # Regular expression to match both patterns:
        # 1. With attributes: ![IMG_1667...jpg](../assets/IMG_1667...jpg){:height 325, :width 423}
        # 2. Without attributes: ![IMG_1667...jpg](../assets/IMG_1667...jpg)
        self.image_pattern = re.compile(r"!\[([^\]]+)\]\(([^)]+)\)(?:\{[^}]*\})?")

    def process(self, content):
        """
        Process content by converting image markdown syntax to the desired format.

        Args:
            content: The content string to process

        Returns:
            Tuple of (new_content, changed)
        """
        if not content:
            return content, False

        # Check if there are any images in the content
        if not self.image_pattern.search(content):
            return content, False

        def replace_image(match):
            # Extract the filename from the URL path
            image_url = match.group(2)  # This is the URL path
            # Get the base filename without the directory path
            image_filename = os.path.basename(image_url)
            return f"[[logseq-import-missing-asset]]: `{image_filename}`"

        new_content = self.image_pattern.sub(replace_image, content)

        return new_content, new_content != content
