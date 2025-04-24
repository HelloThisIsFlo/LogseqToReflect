import pytest
import os
from src.processors.base import ContentProcessor
from src.processors.date_header import DateHeaderProcessor
from src.processors.task_cleaner import TaskCleaner
from src.processors.link_processor import LinkProcessor
from src.processors.properties_processor import PropertiesProcessor
from src.processors.block_references import (
    BlockReferencesCleaner,
    BlockReferencesReplacer,
)
from src.processors.page_title import PageTitleProcessor
from src.processors.indented_bullet_points import IndentedBulletPointsProcessor
from src.processors.empty_content_cleaner import EmptyContentCleaner
from src.processors.wikilink import WikiLinkProcessor
import tempfile
from src.file_handlers.directory_walker import DirectoryWalker
from src.processors.ordered_list_processor import OrderedListProcessor
from src.processors.arrows_processor import ArrowsProcessor
from src.processors.admonition_processor import AdmonitionProcessor
from src.processors.tag_to_backlink import TagToBacklinkProcessor
import shutil


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

    def test_convert_cancelled_tasks(self):
        processor = TaskCleaner()
        content = "- CANCELLED Task 1\n- CANCELED Task 2"
        new_content, changed = processor.process(content)
        assert changed is True
        expected = "- [x] ~~Task 1~~\n- [x] ~~Task 2~~"
        assert new_content == expected

    def test_convert_waiting_tasks(self):
        processor = TaskCleaner()
        content = "- WAITING Task 3"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == "- [ ] Task 3"

    def test_tasks_in_headings(self):
        processor = TaskCleaner()
        content = "## TODO First task\n### DONE Second task\n# WAITING Third task\n#### CANCELED Final task"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "## First task" in new_content
        assert "### Second task" in new_content
        assert "# Third task" in new_content
        assert "#### Final task" in new_content

    def test_tasks_in_headings_with_bullets(self):
        processor = TaskCleaner()
        content = "- ## TODO First task\n- ### DONE Second task\n- # WAITING Third task\n- #### CANCELED Final task"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "- ## First task" in new_content
        assert "- ### Second task" in new_content
        assert "- # Third task" in new_content
        assert "- #### Final task" in new_content


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

    def test_remove_inline_properties(self):
        processor = LinkProcessor()
        content = (
            "- collapsed:: true\n  Some content\n- collapsed:: true Some other content"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert "collapsed::" not in new_content
        assert "- Some content\n- Some other content" == new_content

    def test_remove_inline_properties_more_complex_with_other_properties(self):
        processor = LinkProcessor()
        content = """
- ## Hello
	- ## Hi
		- ### How are you?
            - collapsed:: true
              #+BEGIN_NOTE
              This note is collapsed
              #+END_NOTE
            - collapsed:: true
              ```shell
              this code block is collapsed
              ```
            - collapsed:: true
              > [💭]([[wondering]]) This is a collapsed quote
        """

        new_content, changed = processor.process(content)
        assert changed is True
        assert "collapsed::" not in new_content

        # Check that specific content elements are present in the output
        assert "- ## Hello" in new_content
        assert "- ## Hi" in new_content
        assert "- ### How are you?" in new_content
        assert "#+BEGIN_NOTE" in new_content
        assert "This note is collapsed" in new_content
        assert "```shell" in new_content
        assert "this code block is collapsed" in new_content
        assert "> [💭]([[wondering]])" in new_content
        assert "This is a collapsed quote" in new_content

    def test_no_change_when_no_properties(self):
        processor = LinkProcessor()
        content = "Regular text without properties"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content

    def test_remove_filters_lines(self):
        processor = PropertiesProcessor()
        content = 'Text before\nfilters:: {"hello": true}\nText after'
        new_content, changed = processor.process(content)
        assert changed is True
        assert "filters::" not in new_content
        assert "Text before\nText after" == new_content


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
        # Create test uppercase, types, and lowercase config files
        self.uppercase_path = tmp_path / "uppercase.txt"
        self.types_path = tmp_path / "types.txt"
        self.lowercase_path = tmp_path / "lowercase.txt"
        self.uppercase_path.write_text("AWS\nIAM\nCLI\n")
        self.types_path.write_text("jira\nrepo\nproject\nmeeting\n")
        self.lowercase_path.write_text(
            """a
an
the
and
but
or
for
nor
as
at
by
for
from
in
into
near
of
on
onto
to
with
is
"""
        )

    def processor(self, filename):
        return PageTitleProcessor(
            filename,
            uppercase_path=str(self.uppercase_path),
            types_path=str(self.types_path),
            lowercase_path=str(self.lowercase_path),
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

    def test_preserve_existing_title(self):
        processor = self.processor("new_page.md")
        content = "# Old Title\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# New Page\n")
        # We now preserve the existing heading instead of replacing it
        assert "# Old Title" in new_content
        # The title from the filename should come first, followed by the original title
        assert new_content.index("# New Page") < new_content.index("# Old Title")

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

    def test_url_encoded_filename_decodes_title(self):
        processor = self.processor(
            "This is a test%3A With some %22quoted text%22 it should be converted.md"
        )
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        # The title should be decoded and title-cased
        assert new_content.startswith(
            '# This is a Test: With Some "Quoted Text" It Should Be Converted\n\n'
        )

    def test_backlinks_in_filename_are_removed(self):
        processor = self.processor(
            "jira___with [[some backlink]] in title and [[topic___Another One]].md"
        )
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith(
            "# With Some Backlink in Title and Topic Another One\n\n"
        )

    def test_preserves_h1_heading(self):
        processor = self.processor("page_with_h1.md")
        content = "# This H1 heading should be preserved\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        # The title from filename should be present
        assert "# Page with H1" in new_content
        # The original H1 heading should also still be present
        assert "# This H1 heading should be preserved" in new_content
        # The original H1 heading should come after the title from the filename
        assert new_content.index("# Page with H1") < new_content.index(
            "# This H1 heading should be preserved"
        )

    def test_preserves_h1_heading_with_type(self):
        processor = self.processor("repo___page_with_h1.md")
        content = "# This H1 heading should be preserved\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        # The title from filename should be present
        assert "# Page with H1" in new_content
        # The type tag should be added
        assert "#repo" in new_content
        # The original H1 heading should still be present
        assert "# This H1 heading should be preserved" in new_content
        # The order should be: title, type tag, original heading
        title_pos = new_content.index("# Page with H1")
        type_pos = new_content.index("#repo")
        heading_pos = new_content.index("# This H1 heading should be preserved")
        assert title_pos < type_pos < heading_pos


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

    def test_preserve_indentation_for_headings_with_tasks(self):
        processor = IndentedBulletPointsProcessor()
        content = "## Main section\n- Regular bullet\n- ## Task in heading (h2)\n\t- # Nested task heading (h1)\n\t\t- ### Third level task (h3)\n\t\t\t- #### Fourth level task (h4)\n\t\t\t\t- ##### Fifth level task (h5)\n\t\t\t\t\t- ###### Sixth level task (h6)"
        new_content, changed = processor.process(content)
        assert (
            changed is False
        )  # Should not change the indentation of headings with tasks
        assert content == new_content

    def test_complex_hierarchy_indentation(self):
        processor = IndentedBulletPointsProcessor()
        content = (
            "## [[What I've done today]]\n"
            "\t- [[jira/Implement Tracing Support in Core Platform]]\n"
            "\t\t- Started mapping out the different request flow\n"
            "\t\t\t- Had some very nice **breakthroughs**! 😃\n"
            "\t\t\t\t- #### What works:\n"
            "\t\t\t\t  background-color:: green\n"
            "\t\t\t\t\t- Service A\n"
            "\t\t\t\t\t\t- Everything works ✅\n"
            "\t\t\t\t\t- Service B\n"
            "\t\t\t\t\t\t- **Caveat:** Client actually does 2 calls\n"
            "\t\t\t\t\t\t\t- The calls\n"
            "\t\t\t\t\t\t\t\t- `fetchMetadata`\n"
            "\t\t\t\t\t\t\t\t- `getResponse`\n"
            "\t\t\t\t\t\t- That's why we get 2 [[dt/trace id]]s ...\n"
            "\t\t\t\t\t\t\t- ... but the second [[dt/trace id]] has **all the info we need** 🎉\n"
            "\t\t\t\t\t- `resolveData`\n"
            "\t\t\t\t\t\t- This is what's actually called by the internal `fetch_dataset` method\n"
            "\t\t\t\t- #### What doesn't work:\n"
            "\t\t\t\t  background-color:: red\n"
            "\t\t\t\t\t- The fallback path via `get_fallback_stream?`\n"
        )
        expected = (
            "## [[What I've done today]]\n"
            "- [[jira/Implement Tracing Support in Core Platform]]\n"
            "\t- Started mapping out the different request flow\n"
            "\t\t- Had some very nice **breakthroughs**! 😃\n"
            "\t\t\t- #### What works:\n"
            "\t\t\t  background-color:: green\n"
            "\t\t\t\t- Service A\n"
            "\t\t\t\t\t- Everything works ✅\n"
            "\t\t\t\t- Service B\n"
            "\t\t\t\t\t- **Caveat:** Client actually does 2 calls\n"
            "\t\t\t\t\t\t- The calls\n"
            "\t\t\t\t\t\t\t- `fetchMetadata`\n"
            "\t\t\t\t\t\t\t- `getResponse`\n"
            "\t\t\t\t\t- That's why we get 2 [[dt/trace id]]s ...\n"
            "\t\t\t\t\t\t- ... but the second [[dt/trace id]] has **all the info we need** 🎉\n"
            "\t\t\t\t- `resolveData`\n"
            "\t\t\t\t\t- This is what's actually called by the internal `fetch_dataset` method\n"
            "\t\t\t- #### What doesn't work:\n"
            "\t\t\t  background-color:: red\n"
            "\t\t\t\t- The fallback path via `get_fallback_stream?`\n"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == expected

    def test_bullet_with_heading_and_children(self):
        processor = IndentedBulletPointsProcessor()
        content = (
            "- ### [[Flexible Work Policy]]\n"
            "\t- There's an internal policy that allows short-term remote work\n"
            "\t- Typical allowance:\n"
            "\t\t- 1 week flexible\n"
            "\t\t- 2 weeks during designated periods\n"
            "\t- #### Process\n"
            "\t\t- Request must be submitted 30 days ahead\n"
            "\t\t- Requires approval and standard HR documentation\n"
        )
        expected = (
            "- ### [[Flexible Work Policy]]\n"
            "\t- There's an internal policy that allows short-term remote work\n"
            "\t- Typical allowance:\n"
            "\t\t- 1 week flexible\n"
            "\t\t- 2 weeks during designated periods\n"
            "\t- #### Process\n"
            "\t\t- Request must be submitted 30 days ahead\n"
            "\t\t- Requires approval and standard HR documentation\n"
        )
        new_content, changed = processor.process(content)
        assert changed is False  # No change should be made
        assert new_content == expected


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

    def test_preserve_inline_tag_capitalization(self):
        # Simulate TagToBacklinkProcessor having found 'Insight' and 'Follow-up' as tags
        TagToBacklinkProcessor.found_tags.clear()
        TagToBacklinkProcessor.found_tags.update({"Insight", "Follow-up", "mytag"})
        processor = self.processor()
        content = "- this is a test [[Insight]]\n- I'm wondering XYZ [[Follow-up]]\n- unrelated [[Some Page]]\n- #MyTag"
        # Simulate tag to backlink conversion for hashtag
        content = content.replace("#MyTag", "[[mytag]]")
        new_content, changed = processor.process(content)
        # Inline tags and hashtag tags should be lowercased
        assert "[[insight]]" in new_content
        assert "[[follow-up]]" in new_content
        assert "[[mytag]]" in new_content
        # Non-tag wikilinks should be formatted as usual
        assert "[[Some Page]]" in new_content

    def test_does_not_reformat_already_slash_tagged(self):
        processor = self.processor()
        content = "- this is a test [[insight]]\n- another [[follow-up]]"
        new_content, changed = processor.process(content)
        # Should be unchanged
        assert new_content == content


class TestBlockReferencesReplacer:
    """Tests for the BlockReferencesReplacer class"""

    def test_collect_and_replace_block_references(self, tmpdir):
        # Create sample files with block IDs and references in 'pages'
        pages_dir = tmpdir.mkdir("pages")
        page1_content = """# Page 1
- This is a test block
  id:: 67a45c2e-529c-4831-b069-dd6f8e8d1234
- Another block
"""
        page1_path = pages_dir.join("page1.md")
        page1_path.write(page1_content)

        page2_content = """# Page 2
- Reference to block: ((67a45c2e-529c-4831-b069-dd6f8e8d1234))
- Normal text
"""
        page2_path = pages_dir.join("page2.md")
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
        # Create sample files with multiple block IDs and references in 'pages'
        pages_dir = tmpdir.mkdir("pages")
        blocks_content = """# Blocks
- First block
  id:: aaaa1111-2222-3333-4444-555566667777
- Second block
  id:: bbbb1111-2222-3333-4444-555566667777
- Third block with nested content
  id:: cccc1111-2222-3333-4444-555566667777
  - Nested item
"""
        blocks_path = pages_dir.join("blocks.md")
        blocks_path.write(blocks_content)

        references_content = """# References
- First reference: ((aaaa1111-2222-3333-4444-555566667777))
- Second reference: ((bbbb1111-2222-3333-4444-555566667777))
- Combined references: ((aaaa1111-2222-3333-4444-555566667777)) and ((cccc1111-2222-3333-4444-555566667777))
"""
        references_path = pages_dir.join("references.md")
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
        # Create a file with a reference to a non-existent block in 'pages'
        pages_dir = tmpdir.mkdir("pages")
        content = """# Missing Reference
- Reference to non-existent block: ((12345678-1234-1234-1234-123456789012))
"""
        file_path = pages_dir.join("missing.md")
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
        # Create sample files with block IDs and embedded references in 'pages'
        pages_dir = tmpdir.mkdir("pages")
        page1_content = """# Page 1
- This is a test block
  id:: abcd1234-5678-90ab-cdef-1234567890ab
- Another block
"""
        page1_path = pages_dir.join("page1.md")
        page1_path.write(page1_content)

        page2_content = """# Page 2
- Regular reference: ((abcd1234-5678-90ab-cdef-1234567890ab))
- Embedded reference: {{embed ((abcd1234-5678-90ab-cdef-1234567890ab))}}
- Normal text
"""
        page2_path = pages_dir.join("page2.md")
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

    def test_ignore_nested_journals_and_pages(self, tmpdir):
        from src.file_handlers.directory_walker import DirectoryWalker

        # Create direct 'pages' and nested 'journals' under a subdirectory
        pages_dir = tmpdir.mkdir("pages")
        page_content = (
            """# Direct Page\n- Block\n  id:: 12345678-1234-1234-1234-1234567890ab\n"""
        )
        page_path = pages_dir.join("page.md")
        page_path.write(page_content)

        # Create a nested 'journals' directory
        nested_journals = (
            tmpdir.mkdir("logseq")
            .mkdir("version-files")
            .mkdir("incoming")
            .mkdir("journals")
        )
        nested_journal_content = """# Nested Journal\n- Block\n  id:: abcdabcd-abcd-abcd-abcd-abcdabcdabcd\n"""
        nested_journal_path = nested_journals.join("journal.md")
        nested_journal_path.write(nested_journal_content)

        # Create a direct 'journals' directory
        journals_dir = tmpdir.mkdir("journals")
        journal_content = """# Direct Journal\n- Block\n  id:: 87654321-4321-4321-4321-0987654321ab\n"""
        journal_path = journals_dir.join("journal.md")
        journal_path.write(journal_content)

        # Check DirectoryWalker only finds direct children
        walker = DirectoryWalker(str(tmpdir), str(tmpdir), dry_run=True)
        found_journals = walker.find_directories("journals")
        found_pages = walker.find_directories("pages")
        assert set(found_journals) == {str(journals_dir)}
        assert set(found_pages) == {str(pages_dir)}

        # Check BlockReferencesReplacer only collects from direct children
        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))
        assert (
            "12345678-1234-1234-1234-1234567890ab" in replacer.block_map
        )  # from direct pages
        assert (
            "87654321-4321-4321-4321-0987654321ab" in replacer.block_map
        )  # from direct journals
        assert (
            "abcdabcd-abcd-abcd-abcd-abcdabcdabcd" not in replacer.block_map
        )  # from nested journals

    def test_embed_heading_block_as_bold(self, tmpdir):
        pages_dir = tmpdir.mkdir("pages")
        # Block is a heading
        page1_content = """# Page 1\n## Business Hour Support\n  id:: 6717bc1c-cb7e-449f-8cc7-87261c54ebbd\n"""
        page1_path = pages_dir.join("page1.md")
        page1_path.write(page1_content)

        # Reference it both ways
        page2_content = (
            "# Page 2\n"
            "- Regular reference: ((6717bc1c-cb7e-449f-8cc7-87261c54ebbd))\n"
            "- Embedded reference: {{embed ((6717bc1c-cb7e-449f-8cc7-87261c54ebbd))}}\n"
        )
        page2_path = pages_dir.join("page2.md")
        page2_path.write(page2_content)

        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))
        result, changed = replacer.process(page2_content)
        assert changed is True
        # Both references should be replaced with bolded heading, no #
        assert "**Business Hour Support**" in result
        assert "##" not in result
        assert "((6717bc1c-cb7e-449f-8cc7-87261c54ebbd))" not in result
        assert "{{embed" not in result

    def test_handle_type_prefixed_page_names(self, tmpdir):
        # Create a temporary types.txt file
        config_dir = tmpdir.mkdir("config")
        types_file = config_dir.join("types.txt")
        types_file.write("project\nmeeting\ntype\ntopic\n")

        # Set environment variable to point to our test types file
        import os

        os.environ["LOGSEQ2REFLECT_TYPES_PATH"] = str(types_file)

        # Create sample files with block IDs and references in 'pages'
        pages_dir = tmpdir.mkdir("pages")

        # Create a page with a type/ prefix pattern
        page1_content = """# type/Test Page
- This is a test block in a type-prefixed page
  id:: abcd1234-5678-90ab-cdef-1234567890ab
- Another block
"""
        page1_path = pages_dir.join("type___test_page.md")
        page1_path.write(page1_content)

        # Create another page with a different type/ prefix
        page2_content = """# project/Another Page
- This is a test block in a project-prefixed page
  id:: bbbb1111-2222-3333-4444-555566667777
"""
        page2_path = pages_dir.join("project___another_page.md")
        page2_path.write(page2_content)

        # Create a page that references both blocks
        page3_content = """# References Page
- Regular reference to type page: ((abcd1234-5678-90ab-cdef-1234567890ab))
- Embedded reference to type page: {{embed ((abcd1234-5678-90ab-cdef-1234567890ab))}}
- Regular reference to project page: ((bbbb1111-2222-3333-4444-555566667777))
- Embedded reference to project page: {{embed ((bbbb1111-2222-3333-4444-555566667777))}}
"""
        page3_path = pages_dir.join("references_page.md")
        page3_path.write(page3_content)

        # Initialize and collect blocks
        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))

        # Verify the blocks were collected correctly
        assert "abcd1234-5678-90ab-cdef-1234567890ab" in replacer.block_map
        text1, page_name1 = replacer.block_map["abcd1234-5678-90ab-cdef-1234567890ab"]
        assert text1 == "This is a test block in a type-prefixed page"
        assert page_name1 == "type/Test Page"

        assert "bbbb1111-2222-3333-4444-555566667777" in replacer.block_map
        text2, page_name2 = replacer.block_map["bbbb1111-2222-3333-4444-555566667777"]
        assert text2 == "This is a test block in a project-prefixed page"
        assert page_name2 == "project/Another Page"

        # Test processing the references
        result, changed = replacer.process(page3_content)
        assert changed is True

        # For type/Test Page, the type should be removed in the links
        assert "[[Test Page]]" in result
        assert "[[type/Test Page]]" not in result

        # For project/Another Page, the project should be removed in the links
        assert "[[Another Page]]" in result
        assert "[[project/Another Page]]" not in result

        # Clean up environment variable
        del os.environ["LOGSEQ2REFLECT_TYPES_PATH"]

    def test_url_encoded_filenames_in_references(self, tmpdir):
        # Create a temporary page with URL-encoded characters in the filename
        pages_dir = tmpdir.mkdir("pages")
        page1_content = """# This is a test: With some "quoted text"
- This is a test block with special chars
  id:: abcd1234-5678-90ab-cdef-1234567890ef
- Another block
"""
        # Use URL-encoded filename
        page1_path = pages_dir.join("This is a test%3A With some %22quoted text%22.md")
        page1_path.write(page1_content)

        # Create a page that references the block
        page2_content = """# Reference Page
- Reference to URL-encoded page: ((abcd1234-5678-90ab-cdef-1234567890ef))
- Embedded reference: {{embed ((abcd1234-5678-90ab-cdef-1234567890ef))}}
"""
        page2_path = pages_dir.join("reference_page.md")
        page2_path.write(page2_content)

        # Initialize and collect blocks
        replacer = BlockReferencesReplacer()
        replacer.collect_blocks(str(tmpdir))

        # Verify the block was collected
        assert "abcd1234-5678-90ab-cdef-1234567890ef" in replacer.block_map
        text, page_name = replacer.block_map["abcd1234-5678-90ab-cdef-1234567890ef"]

        # Check that the page name is URL-decoded
        assert page_name == 'This is a test: With some "quoted text"'
        assert "%" not in page_name

        # Test replacing in content
        result, changed = replacer.process(page2_content)
        assert changed is True

        # Check that references are properly decoded in the output
        assert (
            'Reference to URL-encoded page: _This is a test block with special chars ([[This is a test: With some "quoted text"]])_'
            in result
        )
        assert (
            'Embedded reference: _This is a test block with special chars ([[This is a test: With some "quoted text"]])_'
            in result
        )
        assert "%3A" not in result
        assert "%22" not in result


class TestOrderedListProcessor:
    """Tests for the OrderedListProcessor class"""

    def test_convert_ordered_list_property(self):
        processor = OrderedListProcessor()
        content = (
            "- Ordered subitem one\n"
            "  logseq.order-list-type:: number\n"
            "- Ordered subitem two\n"
            "  logseq.order-list-type:: number\n"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        expected = "1. Ordered subitem one\n" "1. Ordered subitem two\n"
        assert new_content == expected

    def test_no_change_without_order_property(self):
        processor = OrderedListProcessor()
        content = "- Simple bullet\n- Another bullet\n"
        new_content, changed = processor.process(content)
        assert changed is False
        assert new_content == content


class TestPropertiesProcessor:
    """Tests for the PropertiesProcessor class, including background-color highlighting and property removal."""

    def test_remove_filters_lines(self):
        processor = PropertiesProcessor()
        content = 'Text before\nfilters:: {"hello": true}\nText after'
        new_content, changed = processor.process(content)
        assert changed is True
        assert "filters::" not in new_content
        assert "Text before\nText after" == new_content

    def test_highlight_bullet_with_background_color(self):
        processor = PropertiesProcessor()
        content = (
            "- [[Super Important Topic]] that should be highlighted\n"
            "  background-color:: yellow\n"
            "- Another point\n"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert "==[[Super Important Topic]] that should be highlighted==" in new_content
        assert "background-color:: yellow" not in new_content
        assert "- Another point" in new_content

    def test_highlight_bullet_with_different_background_color(self):
        processor = PropertiesProcessor()
        content = (
            "- [[Another Highlighted Point]]\n"
            "  background-color:: blue\n"
            "- Not highlighted\n"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert "==[[Another Highlighted Point]]==" in new_content
        assert "background-color:: blue" not in new_content
        assert "- Not highlighted" in new_content

    def test_extra_properties_are_deleted(self):
        processor = PropertiesProcessor()
        content = (
            "- Task with inline properties\n"
            "  priority:: high\n"
            "  background-color:: yellow\n"
            "  id:: 1234-5678\n"
            "- Another point\n"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert "priority::" not in new_content
        assert "id::" not in new_content
        assert "background-color:: yellow" not in new_content
        assert "==Task with inline properties==" in new_content
        assert "- Another point" in new_content

    def test_single_blank_line_after_title(self):
        processor = PropertiesProcessor()
        # Simulate a file with a title and extra blank lines
        content = "# Hello Hi How Are You // Testing\n\n\nThis is a test page with multiple underscores."
        new_content, changed = processor.process(content)
        # There should be exactly one blank line between the title and the next line
        lines = new_content.split("\n")
        # Find the title line
        for idx, line in enumerate(lines):
            if line.startswith("# "):
                # The next line should be blank, and the one after should not
                assert lines[idx + 1] == ""
                assert lines[idx + 2] != ""
                break

    def test_highlight_bullet_heading_with_background_color(self):
        processor = PropertiesProcessor()
        content = (
            "- #### Highlighted Title in bullet list\n" "  background-color:: yellow\n"
        )
        new_content, changed = processor.process(content)
        assert changed is True
        assert "- #### ==Highlighted Title in bullet list==" in new_content
        assert "background-color:: yellow" not in new_content


class TestArrowsProcessor:
    """Tests for the ArrowsProcessor class."""

    def test_replace_arrows(self):
        processor = ArrowsProcessor()
        content = "This is an arrow -> and another => in the text."
        new_content, changed = processor.process(content)
        assert changed is True
        assert "->" not in new_content
        assert "=>" not in new_content
        assert new_content.count("→") == 2
        assert new_content == "This is an arrow → and another → in the text."

    def test_no_arrows(self):
        processor = ArrowsProcessor()
        content = "No arrows here."
        new_content, changed = processor.process(content)
        assert changed is False
        assert new_content == content

    def test_multiple_arrows(self):
        processor = ArrowsProcessor()
        content = "a -> b => c -> d => e"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == "a → b → c → d → e"

    def test_replace_left_arrows(self):
        processor = ArrowsProcessor()
        content = "<- left arrow and <= less or equal"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "<-" not in new_content
        assert "<=" not in new_content
        assert new_content.count("←") == 2
        assert new_content == "← left arrow and ← less or equal"

    def test_mixed_arrows(self):
        processor = ArrowsProcessor()
        content = "<- a -> b <= c => d"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content == "← a → b ← c → d"


class TestAdmonitionProcessor:
    """Tests for the AdmonitionProcessor class"""

    @pytest.mark.parametrize(
        "typ, emoji, heading, marker",
        [
            ("IMPORTANT", "‼️", "##", "IMPORTANT"),
            ("WARNING", "⚠️", "##", "WARNING"),
            ("TIP", "💡", "##", "TIP"),
            ("NOTE", "ℹ️", "##", "NOTE"),
        ],
    )
    def test_top_level_admonition(self, typ, emoji, heading, marker):
        content = f"""
#+BEGIN_{marker}
This is a {typ.lower()} heading
Extra info line
#+END_{marker}
""".strip()
        processor = AdmonitionProcessor()
        new_content, changed = processor.process(content)
        assert changed is True
        lines = new_content.split("\n")
        if typ == "WARNING":
            assert lines[0] == f"> {heading} {emoji} This is a {typ.lower()} heading"
            assert lines[1] == f"> _Extra info line_"
        else:
            assert lines[0] == f"> {heading} {emoji} This is a {typ.lower()} heading"
            assert lines[1] == f"> _Extra info line_"

    @pytest.mark.parametrize(
        "typ, emoji, heading, marker",
        [
            ("IMPORTANT", "‼️", "##", "IMPORTANT"),
            ("WARNING", "⚠️", "##", "WARNING"),
            ("TIP", "💡", "##", "TIP"),
            ("NOTE", "ℹ️", "##", "NOTE"),
        ],
    )
    def test_indented_admonition(self, typ, emoji, heading, marker):
        content = f"""
- #+BEGIN_{marker}
  {typ.title()} block heading
  More details
  #+END_{marker}
""".strip()
        processor = AdmonitionProcessor()
        new_content, changed = processor.process(content)
        assert changed is True
        lines = new_content.split("\n")
        prefix = "- "
        continuation = prefix.replace("- ", "  ")
        if typ == "WARNING":
            assert (
                lines[0] == f"{prefix}> {heading} {emoji} {typ.title()} block heading"
            )
            assert lines[1] == f"{continuation}> _More details_"
        else:
            assert (
                lines[0] == f"{prefix}> {heading} {emoji} {typ.title()} block heading"
            )
            assert lines[1] == f"{continuation}> _More details_"

    def test_multiple_admonitions(self):
        content = """
#+BEGIN_IMPORTANT
First
#+END_IMPORTANT
#+BEGIN_TIP
Second
#+END_TIP
""".strip()
        processor = AdmonitionProcessor()
        new_content, changed = processor.process(content)
        assert changed is True
        assert "> ## ‼️ First" in new_content
        assert "> ## 💡 Second" in new_content

    def test_admonition_with_no_body(self):
        content = """
#+BEGIN_NOTE
Just a heading
#+END_NOTE
""".strip()
        processor = AdmonitionProcessor()
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("> ## ℹ️ Just a heading")
        assert "_" not in new_content or new_content.endswith("_")

    def test_non_admonition_content_untouched(self):
        content = "Regular content\n- Not an admonition block"
        processor = AdmonitionProcessor()
        new_content, changed = processor.process(content)
        assert changed is False
        assert new_content == content


class TestTagToBacklinkProcessor:
    @pytest.fixture(autouse=True)
    def clear_found_tags(self):
        TagToBacklinkProcessor.found_tags.clear()

    def test_single_tag(self):
        processor = TagToBacklinkProcessor()
        content = "This is a test #Tag"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "This is a test [[tag]]" == new_content
        assert "tag" in TagToBacklinkProcessor.found_tags

    def test_multiple_tags(self):
        processor = TagToBacklinkProcessor()
        content = "This has #Multiple #tAGs in it"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "This has [[multiple]] [[tags]] in it" == new_content
        assert "multiple" in TagToBacklinkProcessor.found_tags
        assert "tags" in TagToBacklinkProcessor.found_tags

    def test_no_tags(self):
        processor = TagToBacklinkProcessor()
        content = "No tags here."
        new_content, changed = processor.process(content)
        assert changed is False
        assert new_content == content
        assert not any(tag in content for tag in TagToBacklinkProcessor.found_tags)

    def test_tag_with_underscore_and_dash(self):
        processor = TagToBacklinkProcessor()
        content = "Complex tags #with_underscore and #with-dash"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "Complex tags [[with_underscore]] and [[with-dash]]" == new_content

    def test_does_not_convert_tags_in_code_blocks(self):
        processor = TagToBacklinkProcessor()
        content = (
            "Some text #tag1\n"
            "```python\n#notatag\nprint('hello #tag2')\n```\n"
            "More text #tag3\n"
            "~~~\n#alsonotatag\n~~~\n"
            "End #tag4"
        )
        new_content, changed = processor.process(content)
        # Only tags outside code blocks should be converted
        assert "[[tag1]]" in new_content
        assert "[[tag3]]" in new_content
        assert "[[tag4]]" in new_content
        assert "#notatag" in new_content
        assert "#alsonotatag" in new_content
        assert "#tag2" in new_content  # inside code block, should not be converted

    def test_does_not_convert_tags_in_links_or_urls(self):
        processor = TagToBacklinkProcessor()
        content = (
            "A link: [see here](#notatag)\n"
            "A URL: https://example.com/#notatag\n"
            "In text: #tag1 and text #tag2\n"
            "At start: #tag3\n"
            "No space:foo#notatag\n"
            "With space: foo #tag4"
        )
        new_content, changed = processor.process(content)
        # Only tags with space or start of line should be converted
        assert "[[tag1]]" in new_content
        assert "[[tag2]]" in new_content
        assert "[[tag3]]" in new_content
        assert "[[tag4]]" in new_content
        assert "#notatag" in new_content  # in link, url, or no space


class TestHeadingProcessor:
    """Tests for the HeadingProcessor class"""

    def test_puts_first_heading_in_bullet(self):
        from src.processors.heading_processor import HeadingProcessor

        processor = HeadingProcessor()
        content = "# Page Title\n\n## First Heading\nSome content\n### Subheading"
        new_content, changed = processor.process(content)
        assert changed is True
        assert (
            "# Page Title\n\n- ## First Heading\nSome content\n### Subheading"
            == new_content
        )

    def test_ignores_already_bulleted_heading(self):
        from src.processors.heading_processor import HeadingProcessor

        processor = HeadingProcessor()
        content = "# Page Title\n\n- ## First Heading\nSome content\n### Subheading"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content

    def test_handles_type_tag(self):
        from src.processors.heading_processor import HeadingProcessor

        processor = HeadingProcessor()
        content = "# Page Title\n\n#type\n\n## First Heading\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert (
            "# Page Title\n\n#type\n\n- ## First Heading\nSome content" == new_content
        )

    def test_only_affects_first_heading(self):
        from src.processors.heading_processor import HeadingProcessor

        processor = HeadingProcessor()
        content = "# Page Title\n\n- ## First Heading\nSome content\n## Second Heading"
        new_content, changed = processor.process(content)
        assert changed is False
        # Second heading should remain unbulleted
        assert (
            "# Page Title\n\n- ## First Heading\nSome content\n## Second Heading"
            == new_content
        )


@pytest.fixture(autouse=True, scope="session")
def clean_test_output():
    output_dir = "tests/full_test_workspace (Reflect format)/step_2/"
    if os.path.exists(output_dir):
        for fname in os.listdir(output_dir):
            if fname.startswith("tag") and fname.endswith(".md"):
                os.remove(os.path.join(output_dir, fname))
    yield
    # Optionally, clean up again after tests
    if os.path.exists(output_dir):
        for fname in os.listdir(output_dir):
            if fname.startswith("tag") and fname.endswith(".md"):
                os.remove(os.path.join(output_dir, fname))
