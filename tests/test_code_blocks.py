import pytest
import os
import tempfile
import re
from src.processors.indented_bullet_points import IndentedBulletPointsProcessor
from src.file_handlers.page_file_processor import PageFileProcessor


class TestCodeBlocks:
    """Tests for code blocks processing, especially handling comments with # symbol"""

    def test_hash_comments_in_code_blocks_preserve_indentation(self):
        """Test that hash comments in code blocks preserve their indentation"""
        processor = IndentedBulletPointsProcessor()

        content = """
## Code Example
```python
# This is a comment
def example():
    # Indented comment
    return "Hello"
```"""

        result, changed = processor.process(content)

        # The content should not be changed as code blocks should be preserved
        assert changed is False
        assert result == content

    def test_nested_code_blocks_preserve_indentation(self):
        """Test that nested code blocks under bullet points preserve indentation"""
        processor = IndentedBulletPointsProcessor()

        content = """
- This is a bullet point
  - Nested bullet
    ```python
    # Comment at level 0
    def example():
        # Indented comment
        return "Hello"
    ```"""

        result, changed = processor.process(content)

        # We want to make sure the indented content and hash comments are preserved
        assert "    # Comment at level 0" in result
        assert "        # Indented comment" in result

    def test_deep_nested_code_blocks_with_hash_comments(self):
        """Test a deeply nested code block with hash comments as in the bug report"""
        processor = IndentedBulletPointsProcessor()

        # This replicates the example from edge cases.md
        content = """- Now under a deep nested hierarchy
  - Level 2
    - Level 3
      - Level 4
        - Level 5
          - Level 6
            - Level 7
              - Level 8
              	- ```
                  print("Hello, world!")
                  # Some comment with intended indentation
                  #                  some other comment with lots of spaces
                  ```"""

        result, changed = processor.process(content)

        # In the result, we should still have the properly indented hash comments
        assert "# Some comment with intended indentation" in result
        assert "#                  some other comment with lots of spaces" in result

    def test_full_pipeline_with_code_blocks(self):
        """Test the full pipeline with code blocks to ensure hashtags are not mistaken for headings"""
        # Use the full page file processor that includes all processors
        processor = PageFileProcessor()

        content = """
## Code Example

```python
# This is a comment
def example():
    # Indented comment
    return "Hello"
```

- Now under a deep nested hierarchy
  - Level 2
    - Level 3
      - Level 4
        - Level 5
          - Level 6
            - Level 7
              - Level 8
              	- ```
                  print("Hello, world!")
                  # Some comment with intended indentation
                  #                  some other comment with lots of spaces
                  ```
"""

        # Use a temporary directory for the test files
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "test_code_block_temp.md")
            output_file = os.path.join(temp_dir, "test_code_block_temp_output.md")

            # Write the test content
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Process the file
            changed, success = processor.process_file(input_file, output_file)
            assert success is True

            # Read the processed content
            with open(output_file, "r", encoding="utf-8") as f:
                result = f.read()
                print("\nFull result content:")
                print(result)

            # Verify that the indentation is preserved by looking at specific patterns
            # First code block - simple case
            assert "# This is a comment" in result
            assert "    # Indented comment" in result

            # Second code block - find all code blocks and analyze the one with "Hello, world!"
            code_blocks = re.findall(r"```(?:\w*\n)?([^`]+?)```", result, re.DOTALL)
            assert (
                len(code_blocks) >= 2
            ), f"Expected at least 2 code blocks, found {len(code_blocks)}"

            # Find the code block that contains our test case
            nested_block = None
            for block in code_blocks:
                if 'print("Hello, world!")' in block:
                    nested_block = block
                    break

            assert (
                nested_block is not None
            ), "Could not find code block with 'Hello, world!'"
            print(f"\nFound nested code block:\n{nested_block}")

            # Check that the comment lines have proper indentation
            comment_lines = [
                line
                for line in nested_block.split("\n")
                if line.strip().startswith("#")
            ]
            print(f"\nComment lines: {comment_lines}")

            # Check that the indentation before the hash symbol is preserved
            assert any(
                line.lstrip().startswith("#") and line != line.lstrip()
                for line in comment_lines
            ), "No indented comment line found"

            # Check that the "some other comment" line has multiple spaces preserved
            assert any(
                "some other comment with lots of spaces" in line
                for line in comment_lines
            ), "Comment text with spaces not preserved"

            # Check that the spaces inside the second comment are preserved
            spaces_preserved_line = [
                line for line in comment_lines if "some other comment" in line
            ][0]
            # Extract the text between the # and "some"
            spaces_before_some = spaces_preserved_line.split("#")[1].split("some")[0]
            # Verify there are multiple spaces (more than 5) before "some"
            assert (
                len(spaces_before_some) > 5
            ), f"Not enough spaces preserved before 'some' in '{spaces_preserved_line}'"
