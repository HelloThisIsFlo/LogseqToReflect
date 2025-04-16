import pytest
import os
import tempfile
import shutil
from src.file_handlers.directory_walker import DirectoryWalker


@pytest.fixture
def test_workspace():
    """Create a temporary workspace with test files"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create journals directory
    journals_dir = os.path.join(temp_dir, "journals")
    os.makedirs(journals_dir, exist_ok=True)

    # Create pages directory
    pages_dir = os.path.join(temp_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    # Create some journal files
    with open(os.path.join(journals_dir, "2023_01_01.md"), "w") as f:
        f.write("Journal content\n- TODO Task 1\n- DONE Task 2")

    with open(os.path.join(journals_dir, "2023_01_02.md"), "w") as f:
        f.write(
            "More journal content\n:LOGBOOK:\nLogbook content\n:END:\n- DOING Task 3"
        )

    # Create some page files
    with open(os.path.join(pages_dir, "test_page.md"), "w") as f:
        f.write("alias:: Test Alias\nPage content\n- TODO Task 1")

    with open(os.path.join(pages_dir, "another_page.md"), "w") as f:
        f.write(
            "id:: abcd1234-5678-90ab-cdef-1234567890ab\nMore page content\n- DONE Task 2"
        )

    # Create a nested directory structure
    nested_dir = os.path.join(temp_dir, "nested")
    os.makedirs(nested_dir, exist_ok=True)

    nested_journals = os.path.join(nested_dir, "journals")
    os.makedirs(nested_journals, exist_ok=True)

    with open(os.path.join(nested_journals, "2023_01_03.md"), "w") as f:
        f.write("Nested journal content")

    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def output_dir():
    """Create a temporary output directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestDirectoryWalker:
    """Tests for the DirectoryWalker class"""

    def test_init(self, test_workspace, output_dir):
        walker = DirectoryWalker(test_workspace, output_dir, dry_run=True)
        assert walker.workspace == os.path.abspath(test_workspace)
        assert walker.output_dir == output_dir
        assert walker.dry_run is True

        # Check processors are initialized
        assert walker.journal_processor is not None
        assert walker.page_processor is not None

    def test_find_directories(self, test_workspace, output_dir):
        walker = DirectoryWalker(test_workspace, output_dir)

        # Find journal directories
        journal_dirs = walker.find_directories("journals")
        assert len(journal_dirs) == 1
        assert os.path.join(test_workspace, "journals") in journal_dirs

        # Find pages directories
        page_dirs = walker.find_directories("pages")
        assert len(page_dirs) == 1
        assert os.path.join(test_workspace, "pages") in page_dirs

        # Find non-existent directories
        assert len(walker.find_directories("nonexistent")) == 0

    def test_process_journal_directory_dry_run(self, test_workspace, output_dir):
        walker = DirectoryWalker(test_workspace, output_dir, dry_run=True)
        journal_dir = os.path.join(test_workspace, "journals")

        # Process in dry run mode
        total_files, content_changed, renamed = walker.process_journal_directory(
            journal_dir
        )

        # Check counts
        assert total_files == 2
        assert content_changed == 2  # Both files would be changed
        assert renamed == 2  # Both files would be renamed

        # Check no files are created in dry run mode
        output_journal_dir = os.path.join(output_dir, "journals")
        assert not os.path.exists(output_journal_dir)

    def test_process_journal_directory(self, test_workspace, output_dir):
        walker = DirectoryWalker(test_workspace, output_dir, dry_run=False)
        journal_dir = os.path.join(test_workspace, "journals")

        # Process journal directory
        total_files, content_changed, renamed = walker.process_journal_directory(
            journal_dir
        )

        # Check counts
        assert total_files == 2
        assert content_changed == 2
        assert renamed == 2

        # Check files are created
        output_journal_dir = os.path.join(output_dir, "journals")
        assert os.path.exists(output_journal_dir)
        assert os.path.exists(os.path.join(output_journal_dir, "2023-01-01.md"))
        assert os.path.exists(os.path.join(output_journal_dir, "2023-01-02.md"))

        # Check content is transformed
        with open(os.path.join(output_journal_dir, "2023-01-01.md"), "r") as f:
            content = f.read()
            assert "# Sun, January 1st, 2023" in content
            assert "- [ ] Task 1" in content
            assert "- [x] Task 2" in content

    def test_process_pages_directory_dry_run(self, test_workspace, output_dir):
        walker = DirectoryWalker(test_workspace, output_dir, dry_run=True)
        pages_dir = os.path.join(test_workspace, "pages")

        # Process in dry run mode
        total_files, content_changed = walker.process_pages_directory(pages_dir)

        # Check counts
        assert total_files == 2
        assert content_changed == 2  # Both files would be changed

        # Check no files are created in dry run mode
        output_pages_dir = os.path.join(output_dir, "pages")
        assert not os.path.exists(output_pages_dir)

    def test_process_pages_directory(self, test_workspace, output_dir):
        walker = DirectoryWalker(test_workspace, output_dir, dry_run=False)
        pages_dir = os.path.join(test_workspace, "pages")

        # Process pages directory
        total_files, content_changed = walker.process_pages_directory(pages_dir)

        # Check counts
        assert total_files == 2
        assert content_changed == 2

        # Check files are created
        output_pages_dir = os.path.join(output_dir, "pages")
        assert os.path.exists(output_pages_dir)
        assert os.path.exists(os.path.join(output_pages_dir, "test_page.md"))
        assert os.path.exists(os.path.join(output_pages_dir, "another_page.md"))

        # Check content is transformed
        with open(os.path.join(output_pages_dir, "test_page.md"), "r") as f:
            content = f.read()
            assert "# Test Page // Test Alias" in content
            assert "- [ ] Task 1" in content
            assert "alias::" not in content

        with open(os.path.join(output_pages_dir, "another_page.md"), "r") as f:
            content = f.read()
            assert "# Another Page" in content
            assert "- [x] Task 2" in content
            assert "id::" not in content
