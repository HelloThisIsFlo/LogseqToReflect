import pytest
from src.processors.image_processor import ImageProcessor


class TestImageProcessor:
    """Tests for the ImageProcessor class"""

    def test_convert_image_with_attributes(self):
        """Test converting an image with attributes."""
        processor = ImageProcessor()
        content = "- ![Display Text](../assets/IMG_1667_1705397197654_0_1705397341304_0.jpg){:height 325, :width 423}"
        expected = "- [[logseq-import-missing-asset]]: `IMG_1667_1705397197654_0_1705397341304_0.jpg`"

        new_content, changed = processor.process(content)

        assert changed is True
        assert new_content == expected

    def test_convert_simple_image(self):
        """Test converting a simple image without attributes."""
        processor = ImageProcessor()
        content = "![Some Alt Text](../assets/simple_image.jpg)"
        expected = "[[logseq-import-missing-asset]]: `simple_image.jpg`"

        new_content, changed = processor.process(content)

        assert changed is True
        assert new_content == expected

    def test_convert_image_in_paragraph(self):
        """Test converting an image within a paragraph."""
        processor = ImageProcessor()
        content = "This is a paragraph with an image ![Alt](../assets/image.jpg) in the middle."
        expected = "This is a paragraph with an image [[logseq-import-missing-asset]]: `image.jpg` in the middle."

        new_content, changed = processor.process(content)

        assert changed is True
        assert new_content == expected

    def test_convert_multiple_images(self):
        """Test converting multiple images in the same content."""
        processor = ImageProcessor()
        content = """
- First image: ![Alt1](../assets/img1.jpg)
- Second image: ![Alt2](../assets/img2.png){:width 500}
"""
        expected = """
- First image: [[logseq-import-missing-asset]]: `img1.jpg`
- Second image: [[logseq-import-missing-asset]]: `img2.png`
"""

        new_content, changed = processor.process(content)

        assert changed is True
        assert new_content == expected

    def test_no_change_when_no_images(self):
        """Test that content without images is not changed."""
        processor = ImageProcessor()
        content = "This is regular text without any images."

        new_content, changed = processor.process(content)

        assert changed is False
        assert new_content == content

    def test_convert_image_in_nested_list(self):
        """Test converting an image in a nested list."""
        processor = ImageProcessor()
        content = """
- Top level item
  - Nested item with image ![Alt](../assets/nested.jpg)
    - More nesting
"""
        expected = """
- Top level item
  - Nested item with image [[logseq-import-missing-asset]]: `nested.jpg`
    - More nesting
"""

        new_content, changed = processor.process(content)

        assert changed is True
        assert new_content == expected

    def test_convert_image_in_code_blocks_and_backticks(self):
        """Test that images inside code blocks are also processed."""
        processor = ImageProcessor()
        content = """
```markdown
This is a code block with ![Alt](../assets/image.jpg)
```

And some text with `inline code with ![Alt2](../assets/image2.jpg)`
"""
        expected = """
```markdown
This is a code block with [[logseq-import-missing-asset]]: `image.jpg`
```

And some text with `inline code with [[logseq-import-missing-asset]]: `image2.jpg``
"""

        new_content, changed = processor.process(content)

        assert changed is True
        assert new_content == expected

    def test_different_alt_text_and_filename(self):
        """Test that the processor extracts the filename from the URL, not the alt text."""
        processor = ImageProcessor()
        content = "![image.png](../assets/real_image_name.png)"
        expected = "[[logseq-import-missing-asset]]: `real_image_name.png`"

        new_content, changed = processor.process(content)

        assert changed is True
        assert new_content == expected
