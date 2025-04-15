import pytest
import os
import tempfile
import shutil
import io
import sys
from src.file_handlers.logseq_to_reflect_converter import LogSeqToReflectConverter


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

    yield temp_dir
    shutil.rmtree(temp_dir)


class TestLogSeqToReflectConverter:
    """Tests for the LogSeqToReflectConverter class"""

    def test_init_with_default_output_dir(self, test_workspace):
        # Initialize with default output directory
        converter = LogSeqToReflectConverter(
            workspace=test_workspace,
        )

        # Check default output directory name
        workspace_name = os.path.basename(test_workspace)
        parent_dir = os.path.dirname(test_workspace)
        expected_output_dir = os.path.join(
            parent_dir, f"{workspace_name} (Reflect format)"
        )

        assert converter.workspace == os.path.abspath(test_workspace)
        assert converter.output_dir == expected_output_dir
        assert converter.dry_run is False

        # Check walker is initialized
        assert converter.walker is not None

    def test_init_with_custom_output_dir(self, test_workspace):
        # Create a custom output directory
        custom_output = os.path.join(os.path.dirname(test_workspace), "custom_output")

        # Initialize with custom output directory
        converter = LogSeqToReflectConverter(
            workspace=test_workspace, output_dir=custom_output, dry_run=True
        )

        assert converter.workspace == os.path.abspath(test_workspace)
        assert converter.output_dir == os.path.abspath(custom_output)
        assert converter.dry_run is True

    def test_run_dry_run(self, test_workspace, capsys):
        # Initialize converter with dry run mode
        converter = LogSeqToReflectConverter(workspace=test_workspace, dry_run=True)

        # Run conversion
        stats = converter.run()

        # Check output
        captured = capsys.readouterr()
        output = captured.out

        # Verify operation was performed in dry run mode
        assert "Would update content in" in output
        assert "Would save to" in output

        # Verify the stats
        assert stats.journal_files_processed > 0
        assert stats.pages_files_processed > 0

        # No output directory should have been created
        expected_output_dir = os.path.join(
            os.path.dirname(test_workspace),
            f"{os.path.basename(test_workspace)} (Reflect format)",
        )
        assert not os.path.exists(expected_output_dir)

    def test_run(self, test_workspace):
        # Set up a custom output directory to avoid cluttering the file system
        output_dir = os.path.join(
            os.path.dirname(test_workspace), "test_converter_output"
        )

        # Make sure the output directory doesn't exist
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        # Initialize converter
        converter = LogSeqToReflectConverter(
            workspace=test_workspace, output_dir=output_dir
        )

        # Run conversion
        stats = converter.run()

        # Verify results
        assert os.path.exists(output_dir)
        assert os.path.exists(os.path.join(output_dir, "journals"))
        assert os.path.exists(os.path.join(output_dir, "pages"))

        # Check journal files were converted
        assert os.path.exists(os.path.join(output_dir, "journals", "2023-01-01.md"))
        assert os.path.exists(os.path.join(output_dir, "journals", "2023-01-02.md"))

        # Check page files were converted
        assert os.path.exists(os.path.join(output_dir, "pages", "test_page.md"))
        assert os.path.exists(os.path.join(output_dir, "pages", "another_page.md"))

        # Check stats
        assert stats.journal_files_processed == 2
        assert stats.pages_files_processed == 2
        assert stats.total_files == 4

        # Clean up
        shutil.rmtree(output_dir)
