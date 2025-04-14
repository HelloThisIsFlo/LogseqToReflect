import pytest
from src.logseq_to_reflect_converter import (
    ContentProcessor, 
    DateHeaderProcessor, 
    TaskCleaner, 
    LinkProcessor, 
    BlockReferencesCleaner, 
    PageTitleProcessor,
    IndentedBulletPointsProcessor
)

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

class TestPageTitleProcessor:
    """Tests for the PageTitleProcessor class"""
    
    def test_format_simple_filename(self):
        processor = PageTitleProcessor("simple_page.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# Simple Page\n\n")
    
    def test_format_filename_with_underscores(self):
        processor = PageTitleProcessor("my_awesome_page.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# My Awesome Page\n\n")
    
    def test_format_filename_with_triple_underscores(self):
        processor = PageTitleProcessor("folder___page.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# folder/Page\n\n")
    
    def test_title_case_rules(self):
        processor = PageTitleProcessor("the_importance_of_a_good_title.md")
        content = "Some content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# The Importance of a Good Title\n\n")
    
    def test_aliases_formatting(self):
        processor = PageTitleProcessor("page.md")
        content = "alias:: first alias, second/alias\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "# Page // First Alias // second/Alias\n\n" in new_content
        assert "alias::" not in new_content
    
    def test_replace_existing_title(self):
        processor = PageTitleProcessor("new_page.md")
        content = "# Old Title\nSome content"
        new_content, changed = processor.process(content)
        assert changed is True
        assert new_content.startswith("# New Page\n")
        assert "Old Title" not in new_content

class TestIndentedBulletPointsProcessor:
    """Tests for the IndentedBulletPointsProcessor class"""
    
    def test_remove_tabs_from_bullet_points(self):
        processor = IndentedBulletPointsProcessor()
        content = "## [[Project Status]]\n\t- Working on [[Feature X]] with [[John Doe]]\n\t- Need to check reference\n\t- Also see [[page/documentation]]"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "## [[Project Status]]\n- Working on [[Feature X]] with [[John Doe]]\n- Need to check reference\n- Also see [[page/documentation]]" == new_content
    
    def test_no_change_when_no_indented_bullets(self):
        processor = IndentedBulletPointsProcessor()
        content = "## Regular heading\n- Regular bullet point\n- Another bullet point"
        new_content, changed = processor.process(content)
        assert changed is False
        assert content == new_content
    
    def test_mixed_indented_and_regular_bullets(self):
        processor = IndentedBulletPointsProcessor()
        content = "## Mixed content\n- Regular bullet\n\t- Indented bullet\n- Another regular bullet"
        new_content, changed = processor.process(content)
        assert changed is True
        assert "## Mixed content\n- Regular bullet\n- Indented bullet\n- Another regular bullet" == new_content 