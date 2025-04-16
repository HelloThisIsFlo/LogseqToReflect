import pytest
import os
from src.processors.base import ContentProcessor
from src.processors.date_header import DateHeaderProcessor
from src.processors.task_cleaner import TaskCleaner
from src.processors.link_processor import LinkProcessor
from src.processors.block_references import (
    BlockReferencesCleaner,
    BlockReferencesReplacer,
)
from src.processors.page_title import PageTitleProcessor
from src.processors.indented_bullet_points import IndentedBulletPointsProcessor
from src.processors.empty_content_cleaner import EmptyContentCleaner
from src.processors.wikilink import WikiLinkProcessor
import tempfile


class TestDateHeaderProcessor:
    """Tests for the DateHeaderProcessor class"""

    def test_add_date_header_to_empty_content(self):
        processor = DateHeaderProcessor("Mon, January 1st, 2023")
        content = ""
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == "# Mon, January 1st, 2023\n\n"

    def test_add_date_header_to_content_without_header(self):
        processor = DateHeaderProcessor("Mon, January 1st, 2023")
        content = "Some content\nMore lines"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == "# Mon, January 1st, 2023\n\nSome content\nMore lines"

    def test_date_header_not_added_when_already_exists(self):
        processor = DateHeaderProcessor("Mon, January 1st, 2023")
        content = "# Existing header\nSome content"
        new_content, changed = processor.process(content)
        assert changed is False
        assert new_content == content


class TestTaskCleaner:
    """Tests for the TaskCleaner class"""

    def test_clean_logbook_sections(self):
        processor = TaskCleaner()
        content = "Text before\n:LOGBOOK:\nSome logbook content\n:END:\nText after"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "LOGBOOK" not in new_content
        assert "Text before\nText after" == new_content

    def test_replace_todo_markers(self):
        processor = TaskCleaner()
        content = "- TODO Task 1\n- DONE Task 2\n- DOING Task 3"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "- [ ] Task 1\n- [x] Task 2\n- [ ] Task 3" == new_content

    def test_no_change_when_no_tasks(self):
        processor = TaskCleaner()
        content = "Regular text without tasks"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content


class TestLinkProcessor:
    """Tests for the LinkProcessor class"""

    def test_remove_block_ids(self):
        processor = LinkProcessor()
        content = "Text before\nid:: abcd1234-5678-90ab-cdef-1234567890ab\nText after"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "id::" not in new_content
        assert "Text before\n\nText after" == new_content

    def test_remove_properties(self):
        processor = LinkProcessor()
        content = "Text before\ncollapsed:: true\nText after"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "collapsed::" not in new_content
        assert "Text before\nText after" == new_content

    def test_no_change_when_no_properties(self):
        processor = LinkProcessor()
        content = "Regular text without properties"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content


class TestBlockReferencesCleaner:
    """Tests for the BlockReferencesCleaner class"""

    def test_remove_block_references(self):
        processor = BlockReferencesCleaner()
        content = "Text with a reference ((abcd1234-5678-90ab-cdef-1234567890ab)) in the middle"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "((" not in new_content
        assert "Text with a reference  in the middle" == new_content

    def test_remove_embedded_block_references(self):
        processor = BlockReferencesCleaner()
        content = "Text with an embedded reference {{embed ((abcd1234-5678-90ab-cdef-1234567890ab))}} in the middle"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "{{embed" not in new_content
        assert "((" not in new_content
        assert "Text with an embedded reference  in the middle" == new_content

    def test_remove_code_blocks(self):
        processor = BlockReferencesCleaner()
        content = "Text before\n#+BEGIN_SRC python\ndef hello():\n    print('Hello')\n#+END_SRC\nText after"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "#+BEGIN_SRC" not in new_content
        assert "#+END_SRC" not in new_content
        assert "Text before\n\nText after" == new_content

    def test_remove_query_blocks(self):
        processor = BlockReferencesCleaner()
        content = "Text before\n{{query something}}\nText after"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "{{query" not in new_content
        assert "Text before\n\nText after" == new_content

    def test_no_change_when_no_blocks(self):
        processor = BlockReferencesCleaner()
        content = "Regular text without blocks"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content


class TestEmptyContentCleaner:
    """Tests for the EmptyContentCleaner class"""

    def test_remove_empty_bullet_points(self):
        processor = EmptyContentCleaner()
        content = "## Section\n- First item\n- \n- Third item"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "- \n" not in new_content
        assert "## Section\n- First item\n- Third item" == new_content

    def test_remove_empty_lines_after_tasks(self):
        processor = EmptyContentCleaner()
        content = (
            "## Tasks\n- [ ] First task\n\n- [x] Second task\n\n## Another Section"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert (
            "## Tasks\n- [ ] First task\n- [x] Second task\n\n## Another Section"
            == new_content
        )

    def test_preserve_empty_lines_before_headings(self):
        processor = EmptyContentCleaner()
        content = "## First Section\n- [ ] Task 1\n\n## Second Section"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content

    def test_preserve_other_empty_lines(self):
        processor = EmptyContentCleaner()
        content = "## First Section\n\n## Second Section"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content


class TestPageTitleProcessor:
    """Tests for the PageTitleProcessor class"""

    @pytest.fixture(autouse=True)
    def setup_test_config(self, tmp_path):
        # Create test uppercase and types config files
        self.uppercase_path = tmp_path / "uppercase.txt"
        self.types_path = tmp_path / "types.txt"
        self.uppercase_path.write_text("AWS\nIAM\nCLI\n")
        self.types_path.write_text("jira\nrepo\nproject\nmeeting\n")

    def processor(self, filename):
        return PageTitleProcessor(
            filename,
            uppercase_path=str(self.uppercase_path),
            types_path=str(self.types_path),
        )

    def test_format_simple_filename(self):
        processor = self.processor("simple_page.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# Simple Page\n\n")

    def test_format_filename_with_underscores(self):
        processor = self.processor("my_awesome_page.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# My Awesome Page\n\n")

    def test_format_filename_with_triple_underscores(self):
        processor = self.processor("folder___page.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# Folder Page\n\n")

    def test_title_case_rules(self):
        processor = self.processor("the_importance_of_a_good_title.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# The Importance of a Good Title\n\n")

    def test_format_filename_with_slashes(self):
        processor = self.processor("aws___iam___role.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# AWS IAM Role\n\n")

    def test_aliases_formatting(self):
        processor = self.processor("page.md")
        content = "alias:: first alias, second/alias\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "# Page // First Alias // Second Alias\n\n" in new_content
        assert "alias::" not in new_content

    def test_replace_existing_title(self):
        processor = self.processor("new_page.md")
        content = "# Old Title\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# New Page\n")
        assert "Old Title" not in new_content

    def test_uppercase_term_in_title(self):
        processor = self.processor("aws___cli___profile.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# AWS CLI Profile\n\n")

    def test_type_removal_and_tag(self):
        processor = self.processor("jira___improve perf on project sentient agents.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        # Should match new output format: blank line between title and tag
        assert new_content.startswith(
            "# Improve Perf on Project Sentient Agents\n\n#jira\n\n"
        )

    def test_uppercase_and_type_in_alias(self):
        processor = self.processor("page.md")
        content = "alias:: aws/cli, repo/hello world\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "# Page // AWS CLI // Hello World\n\n" in new_content

    def test_custom_lowercase_config(self):
        # Create a temporary config directory with a custom lowercase.txt
        with tempfile.TemporaryDirectory() as config_dir:
            lowercase_path = os.path.join(config_dir, "lowercase.txt")
            with open(lowercase_path, "w") as f:
                f.write("foo\nbar\n")
            # 'foo' and 'bar' should be lowercased (except first word), others should be title-cased
            processor = PageTitleProcessor(
                "foo_bar_baz.md", lowercase_path=lowercase_path
            )
            new_content, changed = processor.process("Some content")
            assert changed is True
            # Should be: # Foo bar Baz
            assert new_content.startswith("# Foo bar Baz\n\n")

    def test_exactly_one_blank_line_after_title_and_tag(self):
        # Scenario 1: file with leading blank lines and a type tag
        processor = self.processor("repo___world.md")
        content = "\n\n- hello"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == "# World\n\n#repo\n\n- hello"

        # Scenario 2: file with multiple leading blank lines and no type tag
        processor = self.processor("My___world.md")
        content = "\n\n\n- hello"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == "# My World\n\n- hello"


class TestIndentedBulletPointsProcessor:
    """Tests for the IndentedBulletPointsProcessor class"""

    def test_remove_tabs_from_top_level_bullet_points(self):
        processor = IndentedBulletPointsProcessor()
        content = "## [[Project Status]]\n\t- Working on [[Feature X]] with [[John Doe]]\n\t- Need to check reference\n\t- Also see [[page/documentation]]"
        new_content, changed = processor.process(content)
        assert changed is True
        assert (
            "## [[Project Status]]\n- Working on [[Feature X]] with [[John Doe]]\n- Need to check reference\n- Also see [[page/documentation]]"
            == new_content
        )

    def test_preserve_hierarchy_for_nested_bullet_points(self):
        processor = IndentedBulletPointsProcessor()
        content = "## [[Framework]]\n\t- [[Framework]] is a framework for interfaces\n\t\t- It's a middleware service\n\t\t- It generates interfaces\n\t\t\t- Generates code\n\t- All components use this"
        new_content, changed = processor.process(content)
        assert changed is True
        expected = "## [[Framework]]\n- [[Framework]] is a framework for interfaces\n\t- It's a middleware service\n\t- It generates interfaces\n\t\t- Generates code\n- All components use this"
        assert expected == new_content

    def test_no_change_when_no_indented_bullets(self):
        processor = IndentedBulletPointsProcessor()
        content = "## Regular heading\n- Regular bullet point\n- Another bullet point"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content

    def test_multiple_hierarchical_sections(self):
        processor = IndentedBulletPointsProcessor()
        content = "## First Section\n\t- Top level bullet\n\t\t- Second level\n\t\t\t- Third level\n\n## Second Section\n\t- Another top bullet\n\t\t- Nested bullet"
        new_content, changed = processor.process(content)
        assert changed is True
        expected = "## First Section\n- Top level bullet\n\t- Second level\n\t\t- Third level\n\n## Second Section\n- Another top bullet\n\t- Nested bullet"
        assert expected == new_content


class TestWikiLinkProcessor:
    """Tests for the WikiLinkProcessor class"""

    @pytest.fixture(autouse=True)
    def setup_test_config(self, tmp_path):
        self.uppercase_path = tmp_path / "uppercase.txt"
        self.types_path = tmp_path / "types.txt"
        self.uppercase_path.write_text("AWS\nIAM\nCLI\n")
        self.types_path.write_text("jira\nrepo\nproject\nmeeting\n")

    def processor(self):
        # Patch the processor to use the test config
        class PatchedWikiLinkProcessor(WikiLinkProcessor):
            def __init__(self, uppercase_path, types_path):
                self.lowercase_words = {
                    "a",
                    "an",
                    "the",
                    "and",
                    "but",
                    "or",
                    "for",
                    "nor",
                    "as",
                    "at",
                    "by",
                    "for",
                    "from",
                    "in",
                    "into",
                    "near",
                    "of",
                    "on",
                    "onto",
                    "to",
                    "with",
                }
                self.uppercase_terms = set(
                    line.strip().upper()
                    for line in open(uppercase_path)
                    if line.strip()
                )
                self.types = set(
                    line.strip().lower() for line in open(types_path) if line.strip()
                )

        return PatchedWikiLinkProcessor(str(self.uppercase_path), str(self.types_path))

    def test_format_simple_wikilinks(self):
        processor = self.processor()
        content = "Text with [[simple link]] in the middle"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "Text with [[Simple Link]] in the middle" == new_content

    def test_format_wikilinks_with_underscores(self):
        processor = self.processor()
        content = "Check out [[my_awesome_page]] for more info"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "Check out [[My Awesome Page]] for more info" == new_content

    def test_format_wikilinks_with_slashes(self):
        processor = self.processor()
        content = "Looking at [[aws/iam/group in space]] documentation"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "Looking at [[AWS IAM Group in Space]] documentation" == new_content

    def test_title_case_rules_in_wikilinks(self):
        processor = self.processor()
        content = "See [[the importance of a good title]] page"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "See [[The Importance of a Good Title]] page" == new_content

    def test_multiple_wikilinks_in_content(self):
        processor = self.processor()
        content = "- [[first_link]]\n- [[second/third/important_document]]\n- [[the quick brown fox]]"
        new_content, changed = processor.process(content)
        assert changed is True
        assert (
            "- [[First Link]]\n- [[Second Third Important Document]]\n- [[The Quick Brown Fox]]"
            == new_content
        )

    def test_no_change_when_no_wikilinks(self):
        processor = self.processor()
        content = "Regular text without wikilinks"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content

    def test_wikilink_uppercase_and_type(self):
        processor = self.processor()
        content = (
            "Check out [[aws/cli]] and [[repo/hello world]] and [[jira/issue tracker]]"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert "[[AWS CLI]]" in new_content
        assert "[[Hello World]]" in new_content
        assert "[[Issue Tracker]]" in new_content


class TestBlockReferencesReplacer:
    """Tests for the BlockReferencesReplacer class"""

    def test_collect_and_replace_block_references(self, tmpdir):
        # Create sample files with block IDs and references
        page1_content = """# Page 1
- This is a test block
  id:: 67a45c2e-529c-4831-b069-dd6f8e8d1234
- Another block
"""
        page1_path = tmpdir.join("page1.md")
        page1_path.write(page1_content)

        page2_content = """# Page 2
- Reference to block: ((67a45c2e-529c-4831-b069-dd6f8e8d1234))
- Normal text
"""
        page2_path = tmpdir.join("page2.md")
        page2_path.write(page2_content)

        # Initialize and collect blocks
        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))

        # Verify the block was collected correctly
        assert "67a45c2e-529c-4831-b069-dd6f8e8d1234" in replacer.block_map
        text, page_name = replacer.block_map["67a45c2e-529c-4831-b069-dd6f8e8d1234"]
        assert text == "This is a test block"
        assert page_name == "Page 1"

        # Test replacing in content
        result, changed = replacer.process(page2_content)
        assert changed is True
        assert "This is a test block ([[Page 1]])" in result
        assert "((67a45c2e-529c-4831-b069-dd6f8e8d1234))" not in result

    def test_replace_multiple_references(self, tmpdir):
        # Create sample files with multiple block IDs and references
        blocks_content = """# Blocks
- First block
  id:: aaaa1111-2222-3333-4444-555566667777
- Second block
  id:: bbbb1111-2222-3333-4444-555566667777
- Third block with nested content
  id:: cccc1111-2222-3333-4444-555566667777
  - Nested item
"""
        blocks_path = tmpdir.join("blocks.md")
        blocks_path.write(blocks_content)

        references_content = """# References
- First reference: ((aaaa1111-2222-3333-4444-555566667777))
- Second reference: ((bbbb1111-2222-3333-4444-555566667777))
- Combined references: ((aaaa1111-2222-3333-4444-555566667777)) and ((cccc1111-2222-3333-4444-555566667777))
"""
        references_path = tmpdir.join("references.md")
        references_path.write(references_content)

        # Initialize and collect blocks
        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))

        # Verify blocks were collected
        assert len(replacer.block_map) == 3

        # Test replacing in content
        result, changed = replacer.process(references_content)
        assert changed is True
        assert "First reference: _First block ([[Blocks]])_" in result
        assert "Second reference: _Second block ([[Blocks]])_" in result
        assert (
            "Combined references: _First block ([[Blocks]])_ and _Third block with nested content ([[Blocks]])_"
            in result
        )

    def test_handle_missing_references(self, tmpdir):
        # Create a file with a reference to a non-existent block
        content = """# Missing Reference
- Reference to non-existent block: ((12345678-1234-1234-1234-123456789012))
"""
        file_path = tmpdir.join("missing.md")
        file_path.write(content)

        # Initialize and collect blocks (there are none to collect)
        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))

        # Test replacing in content - should still remove reference even with empty block map
        result, changed = replacer.process(content)

        # Since there are references in the content, the processor should remove them
        assert changed is True
        assert "Reference to non-existent block: " in result
        assert "((12345678-1234-1234-1234-123456789012))" not in result

    def test_handle_embedded_references(self, tmpdir):
        # Create sample files with block IDs and embedded references
        page1_content = """# Page 1
- This is a test block
  id:: abcd1234-5678-90ab-cdef-1234567890ab
- Another block
"""
        page1_path = tmpdir.join("page1.md")
        page1_path.write(page1_content)

        page2_content = """# Page 2
- Regular reference: ((abcd1234-5678-90ab-cdef-1234567890ab))
- Embedded reference: {{embed ((abcd1234-5678-90ab-cdef-1234567890ab))}}
- Normal text
"""
        page2_path = tmpdir.join("page2.md")
        page2_path.write(page2_content)

        # Initialize and collect blocks
        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))

        # Verify the block was collected correctly
        assert "abcd1234-5678-90ab-cdef-1234567890ab" in replacer.block_map
        text, page_name = replacer.block_map["abcd1234-5678-90ab-cdef-1234567890ab"]
        assert text == "This is a test block"
        assert page_name == "Page 1"

        # Test replacing in content
        result, changed = replacer.process(page2_content)
        assert changed is True

        # Check that the regular reference was replaced correctly
        assert "Regular reference: _This is a test block ([[Page 1]])_" in result

        # Check that the embedded reference was also replaced
        # Regular reference is already fixed but let's check if the embedded reference was replaced properly
        assert "{{embed" not in result
        assert "((abcd1234-5678-90ab-cdef-1234567890ab))" not in result

        # The structure with the exact wording depends on implementation, but at minimum:
        assert "Embedded reference:" in result
        assert "This is a test block" in result
        assert "[[Page 1]]" in result
