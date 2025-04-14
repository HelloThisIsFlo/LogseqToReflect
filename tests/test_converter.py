import pytest
import os
import tempfile
import shutil
import re
from src.logseq_to_reflect_converter import LogSeqToReflectConverter

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
        f.write("More journal content\n:LOGBOOK:\nLogbook content\n:END:\n- DOING Task 3")
    
    # Create some page files
    with open(os.path.join(pages_dir, "test_page.md"), "w") as f:
        f.write("alias:: Test Alias\nPage content\n- TODO Task 1")
    
    with open(os.path.join(pages_dir, "another_page.md"), "w") as f:
        f.write("id:: abcd1234-5678-90ab-cdef-1234567890ab\nMore page content\n- DONE Task 2")
    
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
        expected_output_dir = os.path.join(parent_dir, f"{workspace_name} (Reflect format)")
        
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
            workspace=test_workspace,
            output_dir=custom_output,
            dry_run=True
        )
        
        assert converter.workspace == os.path.abspath(test_workspace)
        assert converter.output_dir == os.path.abspath(custom_output)
        assert converter.dry_run is True
    
    def test_run_dry_run(self, test_workspace, capsys):
        # Initialize converter with dry run mode
        converter = LogSeqToReflectConverter(
            workspace=test_workspace,
            dry_run=True
        )
        
        # Run conversion
        converter.run()
        
        # Check output
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify dry run messages
        assert "Dry run: True" in output
        assert "Found 1 journal directories" in output
        assert "Found 1 pages directories" in output
        assert "Journal files processed: 2" in output
        assert "Pages files processed: 2" in output
        assert "Would save to" in output  # Check for a different dry run indicator message
        
        # Check no files are created in dry run mode
        output_dir = converter.output_dir
        assert not os.path.exists(output_dir) or os.listdir(output_dir) == []
    
    def test_run(self, test_workspace):
        # Initialize converter
        converter = LogSeqToReflectConverter(
            workspace=test_workspace,
            dry_run=False
        )
        
        # Run conversion
        converter.run()
        
        # Check output directory is created
        output_dir = converter.output_dir
        assert os.path.exists(output_dir)
        
        # Check journal files are processed
        output_journals_dir = os.path.join(output_dir, "journals")
        assert os.path.exists(output_journals_dir)
        assert os.path.exists(os.path.join(output_journals_dir, "2023-01-01.md"))
        assert os.path.exists(os.path.join(output_journals_dir, "2023-01-02.md"))
        
        # Check content of converted journal files
        with open(os.path.join(output_journals_dir, "2023-01-01.md"), "r") as f:
            content = f.read()
            assert "# Sun, January 1st, 2023" in content
            assert "- [ ] Task 1" in content
            assert "- [x] Task 2" in content
        
        # Check page files are processed
        output_pages_dir = os.path.join(output_dir, "pages")
        assert os.path.exists(output_pages_dir)
        assert os.path.exists(os.path.join(output_pages_dir, "test_page.md"))
        assert os.path.exists(os.path.join(output_pages_dir, "another_page.md"))
        
        # Check content of converted page files
        with open(os.path.join(output_pages_dir, "test_page.md"), "r") as f:
            content = f.read()
            assert "# Test Page // Test Alias" in content
            assert "- [ ] Task 1" in content
            assert "alias::" not in content 