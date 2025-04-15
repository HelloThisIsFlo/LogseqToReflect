import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import importlib.util
import re


@pytest.fixture
def test_logseq_workspace():
    """Create a temporary LogSeq workspace with journals and pages"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Create directory structure
    journals_dir = os.path.join(temp_dir, "journals")
    os.makedirs(journals_dir, exist_ok=True)

    pages_dir = os.path.join(temp_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    # Create journal files with different formats and features to test
    with open(os.path.join(journals_dir, "2023_01_01.md"), "w") as f:
        f.write("- This is a journal entry\n- TODO Task 1\n- DONE Task 2\n")

    with open(os.path.join(journals_dir, "2023_02_14.md"), "w") as f:
        f.write(
            "- Valentine's day\n:LOGBOOK:\nCLOCK: [2023-02-14 Tue 09:00:00]--[2023-02-14 Tue 10:00:00] =>  01:00:00\n:END:\n- DOING Working on project\n"
        )

    # Create page files with different formats and features to test
    with open(os.path.join(pages_dir, "project_notes.md"), "w") as f:
        f.write(
            "alias:: Project Documentation, Notes/Project\n- This is a page with project notes\n- TODO Implement feature\n- ((abcd1234-5678-90ab-cdef-1234567890ab))\n- collapsed:: true\n"
        )

    with open(os.path.join(pages_dir, "meeting___notes.md"), "w") as f:
        f.write(
            "id:: abcd1234-5678-90ab-cdef-1234567890ab\n- Meeting notes\n- DONE Review project timeline\n- {{query (and (todo todo) (page \"Project\"))}}\n#+BEGIN_SRC python\nprint('hello world')\n#+END_SRC\n"
        )

    # Return the path to the workspace
    yield temp_dir

    # Clean up
    shutil.rmtree(temp_dir)


def test_end_to_end_conversion(test_logseq_workspace, monkeypatch):
    """Test the end-to-end conversion process using the main function"""
    # Set up the output directory
    output_dir = os.path.join(os.path.dirname(test_logseq_workspace), "output_reflect")

    # Mock sys.argv
    test_args = [
        "logseq_to_reflect_converter.py",
        "--workspace",
        test_logseq_workspace,
        "--output-dir",
        output_dir,
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Import the module containing the main function
    spec = importlib.util.spec_from_file_location(
        "converter",
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "src",
            "logseq_to_reflect_converter.py",
        ),
    )
    converter_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter_module)

    # Run the main function
    converter_module.main()

    # Verify output directory structure
    assert os.path.exists(output_dir)
    assert os.path.exists(os.path.join(output_dir, "journals"))
    assert os.path.exists(os.path.join(output_dir, "pages"))

    # Check journal files
    journal_files = os.listdir(os.path.join(output_dir, "journals"))
    assert "2023-01-01.md" in journal_files
    assert "2023-02-14.md" in journal_files

    # Check page files
    page_files = os.listdir(os.path.join(output_dir, "pages"))
    assert "project_notes.md" in page_files
    assert "meeting___notes.md" in page_files

    # Verify journal content transformations
    with open(os.path.join(output_dir, "journals", "2023-01-01.md"), "r") as f:
        content = f.read()
        assert "# Sun, January 1st, 2023" in content
        assert "- [ ] Task 1" in content
        assert "- [x] Task 2" in content

    with open(os.path.join(output_dir, "journals", "2023-02-14.md"), "r") as f:
        content = f.read()
        assert "# Tue, February 14th, 2023" in content
        assert ":LOGBOOK:" not in content
        assert "- [ ] Working on project" in content

    # Verify page content transformations
    with open(os.path.join(output_dir, "pages", "project_notes.md"), "r") as f:
        content = f.read()
        assert "# Project Notes // Project Documentation // Notes/Project" in content
        assert "- [ ] Implement feature" in content
        assert "((abcd1234-5678-90ab-cdef-1234567890ab))" not in content
        assert "collapsed:: true" not in content

    with open(os.path.join(output_dir, "pages", "meeting___notes.md"), "r") as f:
        content = f.read()
        assert "# meeting/Notes" in content
        assert "id::" not in content
        assert "- [x] Review project timeline" in content
        assert "{{query" not in content
        assert "#+BEGIN_SRC" not in content
        assert "#+END_SRC" not in content

    # Clean up
    shutil.rmtree(output_dir)


def test_dry_run_mode(test_logseq_workspace, monkeypatch, capsys):
    """Test the dry run mode doesn't create files but shows what would be done"""
    # Set up the output directory
    output_dir = os.path.join(os.path.dirname(test_logseq_workspace), "output_reflect")

    # Clean up output directory if it exists from previous runs
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Mock sys.argv
    test_args = [
        "logseq_to_reflect_converter.py",
        "--workspace",
        test_logseq_workspace,
        "--output-dir",
        output_dir,
        "--dry-run",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Import the module containing the main function
    spec = importlib.util.spec_from_file_location(
        "converter",
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "src",
            "logseq_to_reflect_converter.py",
        ),
    )
    converter_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter_module)

    # Run the main function
    converter_module.main()

    # Check output contains dry run messages
    captured = capsys.readouterr()
    output = captured.out

    assert "Dry run: True" in output
    assert "Would save to" in output
    assert "Would update content" in output
    assert "Run without --dry-run to apply these changes" in output

    # Verify no files were created
    assert not os.path.exists(output_dir)


def test_full_workspace_conversion(monkeypatch):
    """
    Test running the converter on the full_test_workspace.
    This test runs the converter on the real test workspace and verifies basic outputs.
    """
    # Get path to the full test workspace
    full_test_workspace = os.path.join(os.path.dirname(__file__), "full_test_workspace")
    output_dir = full_test_workspace + " (Reflect format)"

    # Mock sys.argv
    test_args = [
        "logseq_to_reflect_converter.py",
        "--workspace",
        full_test_workspace,
        "--output-dir",
        output_dir,
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Import the module containing the main function
    spec = importlib.util.spec_from_file_location(
        "converter",
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "src",
            "logseq_to_reflect_converter.py",
        ),
    )
    converter_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter_module)

    # Run the main function
    converter_module.main()

    try:
        # Verify output directory structure was created
        assert os.path.exists(output_dir)
        assert os.path.exists(os.path.join(output_dir, "journals"))
        assert os.path.exists(os.path.join(output_dir, "pages"))

        # Check that journal files exist and have been processed
        journal_files = os.listdir(os.path.join(output_dir, "journals"))
        assert len(journal_files) > 0  # Make sure there's at least one journal file

        # Check that page files exist and have been processed
        page_files = os.listdir(os.path.join(output_dir, "pages"))
        assert len(page_files) > 0  # Make sure there's at least one page file

        # Verify journal files were renamed correctly (from YYYY_MM_DD.md to YYYY-MM-DD.md)
        for file in journal_files:
            assert re.match(
                r"\d{4}-\d{2}-\d{2}\.md", file
            ), f"Journal file {file} not in correct format YYYY-MM-DD.md"

        # Sample check of content transformation
        # Check the first journal file
        if journal_files:
            first_journal = os.path.join(output_dir, "journals", journal_files[0])
            with open(first_journal, "r") as f:
                content = f.read()
                # Should have a date header
                assert re.search(
                    r"# \w{3}, \w+ \d+\w{2}, \d{4}", content
                ), "Date header not found in journal file"
                # Check task transformations if they exist
                if "TODO" in content or "DONE" in content:
                    assert "TODO" not in content, "TODO marker not transformed"
                    assert "DONE" not in content, "DONE marker not transformed"

        # Check page title formatting
        if page_files:
            first_page = os.path.join(output_dir, "pages", page_files[0])
            with open(first_page, "r") as f:
                content = f.read()
                lines = content.strip().split("\n")
                # First line should be a markdown header
                assert lines[0].startswith(
                    "# "
                ), "Page doesn't start with a title header"

                # Look for a file with ___ in its name to check slash formatting
                special_format_files = [f for f in page_files if "___" in f]
                if special_format_files:
                    special_page = os.path.join(
                        output_dir, "pages", special_format_files[0]
                    )
                    with open(special_page, "r") as f:
                        content = f.read()
                        lines = content.strip().split("\n")
                        title = lines[0][2:]  # Remove "# " prefix
                        assert (
                            "/" in title
                        ), f"Title for file with ___ ({special_format_files[0]}) doesn't contain expected slash format"

        print(f"\nConverted workspace created at: {output_dir}")
        print(
            "You can manually inspect the results and then delete the directory when done."
        )
    except AssertionError as e:
        # Clean up on test failure
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        raise e
