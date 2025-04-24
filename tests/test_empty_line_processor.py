import pytest
from src.processors.empty_line_processor import EmptyLineBetweenBulletsProcessor


class TestEmptyLineBetweenBulletsProcessor:
    def test_removes_empty_lines_between_bullets(self):
        processor = EmptyLineBetweenBulletsProcessor()
        content = """# Title

- First bullet

- Second bullet

- Third bullet"""

        expected = """# Title

- First bullet
- Second bullet
- Third bullet"""

        result, changed = processor.process(content)
        assert result == expected
        assert changed is True

    def test_preserves_empty_lines_within_bullets(self):
        processor = EmptyLineBetweenBulletsProcessor()
        content = """# Title

- First bullet
  with multiple lines

  and a paragraph break

- Second bullet"""

        expected = """# Title

- First bullet
  with multiple lines

  and a paragraph break
- Second bullet"""

        result, changed = processor.process(content)
        if result != expected:
            print("EXPECTED:")
            print(repr(expected))
            print("ACTUAL:")
            print(repr(result))
        assert result == expected
        assert changed is True

    def test_preserves_empty_lines_in_code_blocks(self):
        processor = EmptyLineBetweenBulletsProcessor()
        content = """# Title

- First bullet
  ```python
  def hello():

      print("Hello world")

  ```

- Second bullet"""

        expected = """# Title

- First bullet
  ```python
  def hello():

      print("Hello world")

  ```
- Second bullet"""

        result, changed = processor.process(content)
        assert result == expected
        assert changed is True

    def test_preserves_empty_lines_after_title_and_tags(self):
        processor = EmptyLineBetweenBulletsProcessor()
        content = """# Title

#tag

- First bullet

- Second bullet"""

        expected = """# Title

#tag

- First bullet
- Second bullet"""

        result, changed = processor.process(content)
        assert result == expected
        assert changed is True

    def test_handles_complex_nested_structure(self):
        processor = EmptyLineBetweenBulletsProcessor()
        content = """# Complex Document

- First level bullet

  - Second level bullet

    - Third level bullet

- Another first level

  With content

  - Second level again

    With its own content
"""

        expected = """# Complex Document

- First level bullet
  - Second level bullet
    - Third level bullet
- Another first level

  With content
  - Second level again

    With its own content
"""

        result, changed = processor.process(content)
        assert result == expected
        assert changed is True

    def test_no_changes_needed(self):
        processor = EmptyLineBetweenBulletsProcessor()
        content = """# Title

- First bullet
- Second bullet
- Third bullet"""

        result, changed = processor.process(content)
        assert result == content
        assert changed is False
