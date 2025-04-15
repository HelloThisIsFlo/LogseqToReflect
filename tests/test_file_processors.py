import pytest
import os
import tempfile
import shutil
from src.file_handlers.file_processor import FileProcessor
from src.file_handlers.journal_file_processor import JournalFileProcessor
from src.file_handlers.page_file_processor import PageFileProcessor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestFileProcessor:
    """Tests for the base FileProcessor class"""

    def test_init_with_dry_run(self):
        processor = FileProcessor(dry_run=True)
        assert processor.dry_run is True

    def test_init_without_dry_run(self):
        processor = FileProcessor(dry_run=False)
        assert processor.dry_run is False

    def test_get_processors(self):
        processor = FileProcessor()
        assert processor.get_processors() == []


class TestJournalFileProcessor:
    """Tests for the JournalFileProcessor class"""

    def test_init(self):
        processor = JournalFileProcessor(dry_run=True)
        assert processor.dry_run is True

        processor = JournalFileProcessor(dry_run=False)
        assert processor.dry_run is False

    def test_get_processors(self):
        processor = JournalFileProcessor()
        processors = processor.get_processors()
        assert len(processors) == 6
        # Check processor types without being too strict about order
        processor_types = {type(p).__name__ for p in processors}
        assert processor_types == {
            "TaskCleaner",
            "LinkProcessor",
            "BlockReferencesCleaner",
            "EmptyContentCleaner",
            "IndentedBulletPointsProcessor",
            "WikiLinkProcessor",
        }

    def test_extract_date_from_filename_valid(self):
        processor = JournalFileProcessor()
        date_parts = processor.extract_date_from_filename("2023_01_15.md")
        assert date_parts == ("2023", "01", "15")

    def test_extract_date_from_filename_invalid(self):
        processor = JournalFileProcessor()

        # Not matching pattern
        assert processor.extract_date_from_filename("not_a_date.md") is None

        # Wrong separator
        assert processor.extract_date_from_filename("2023-01-15.md") is None

        # Missing extension
        assert processor.extract_date_from_filename("2023_01_15") is None

    def test_process_file(self, temp_dir):
        # Create a test file
        input_path = os.path.join(temp_dir, "2023_01_15.md")
        with open(input_path, "w") as f:
            f.write("Some journal content\n- TODO Task 1\n- DONE Task 2")

        processor = JournalFileProcessor(dry_run=False)
        content_changed, file_renamed = processor.process_file(input_path, temp_dir)

        assert content_changed is True
        assert file_renamed is True

        # Check the new file exists
        new_file_path = os.path.join(temp_dir, "2023-01-15.md")
        assert os.path.exists(new_file_path)

        # Verify content was transformed
        with open(new_file_path, "r") as f:
            content = f.read()

        assert "# Sun, January 15th, 2023" in content
        assert "- [ ] Task 1" in content
        assert "- [x] Task 2" in content


class TestPageFileProcessor:
    """Tests for the PageFileProcessor class"""

    def test_init(self):
        processor = PageFileProcessor(dry_run=True)
        assert processor.dry_run is True

        processor = PageFileProcessor(dry_run=False)
        assert processor.dry_run is False

    def test_get_processors(self):
        processor = PageFileProcessor()
        processors = processor.get_processors()
        assert len(processors) == 6
        # Check processor types without being too strict about order
        processor_types = {type(p).__name__ for p in processors}
        assert processor_types == {
            "TaskCleaner",
            "LinkProcessor",
            "BlockReferencesCleaner",
            "EmptyContentCleaner",
            "IndentedBulletPointsProcessor",
            "WikiLinkProcessor",
        }

    def test_process_file(self, temp_dir):
        # Create a test file
        input_path = os.path.join(temp_dir, "test_page.md")
        output_path = os.path.join(temp_dir, "output/test_page.md")

        with open(input_path, "w") as f:
            f.write(
                "alias:: Test Alias\nSome page content\n- TODO Task 1\n- DONE Task 2"
            )

        processor = PageFileProcessor(dry_run=False)
        content_changed, success = processor.process_file(input_path, output_path)

        assert content_changed is True
        assert success is True

        # Check the output file exists
        assert os.path.exists(output_path)

        # Verify content was transformed
        with open(output_path, "r") as f:
            content = f.read()

        assert "# Test Page // Test Alias" in content
        assert "- [ ] Task 1" in content
        assert "- [x] Task 2" in content
        assert "alias::" not in content
