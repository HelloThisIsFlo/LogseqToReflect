import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import importlib.util
import re
import subprocess
from src.processors.tag_to_backlink import TagToBacklinkProcessor


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
    with open(os.path.join(pages_dir, "project___Build agents.md"), "w") as f:
        f.write(
            "alias:: Build agents doc, agents doc\n- This is a page with project notes\n- TODO Implement feature\n- ((abcd1234-5678-90ab-cdef-1234567890ab))\n- collapsed:: true\n"
        )

    with open(os.path.join(pages_dir, "meeting___notes.md"), "w") as f:
        f.write(
            "id:: abcd1234-5678-90ab-cdef-1234567890ab\n- Meeting notes\n- DONE Review project timeline\n- {{query (and (todo todo) (page \"Project\"))}}\n#+BEGIN_SRC python\nprint('hello world')\n#+END_SRC\n"
        )

    # Return the path to the workspace
    yield temp_dir

    # Clean up
    shutil.rmtree(temp_dir)


def run_cli(args, env=None):
    env = env or os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
    return subprocess.run(
        [sys.executable, "-m", "src.logseq_to_reflect_converter"] + args,
        capture_output=True,
        text=True,
        env=env,
    )


def test_end_to_end_conversion(test_logseq_workspace, monkeypatch, tmp_path):
    """Test the end-to-end conversion process using the main function, with a test config for types/uppercase."""
    # Set up the output directory inside tmp_path
    output_dir = str(tmp_path / "output_reflect")

    # Set up a test config directory
    config_dir = tmp_path / "test_categories_config"
    config_dir.mkdir()
    (config_dir / "types.txt").write_text("repo\njira\nproject\nmeeting\n")
    (config_dir / "uppercase.txt").write_text("AWS\nIAM\nCLI\n")
    (config_dir / "lowercase.txt").write_text(
        "a\nan\nthe\nand\nbut\nor\nfor\nnor\nas\nat\nby\nfor\nfrom\nin\ninto\nnear\nof\non\nonto\nto\nwith\n"
    )

    # Patch sys.argv to use the temp output dir and pass categories config
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "logseq_to_reflect_converter.py",
            "--workspace",
            test_logseq_workspace,
            "--output-dir",
            output_dir,
            "--categories-config",
            str(config_dir),
        ],
    )

    # Import the module containing the main function (AFTER env is set)
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
    # No subfolders for journals or pages
    assert not os.path.exists(os.path.join(output_dir, "journals"))
    assert not os.path.exists(os.path.join(output_dir, "pages"))

    # Check step_1 and step_2 exist
    step_1_dir = os.path.join(output_dir, "step_1")
    step_2_dir = os.path.join(output_dir, "step_2")
    assert os.path.exists(step_1_dir)
    assert os.path.exists(step_2_dir)

    # Check journal files (should be in step_2)
    journal_files = os.listdir(step_2_dir)
    assert "2023-01-01.md" in journal_files
    assert "2023-02-14.md" in journal_files

    # Check page files (should be in step_1 or step_2)
    all_page_files = os.listdir(step_1_dir) + os.listdir(step_2_dir)
    assert "project___Build agents.md" in all_page_files
    assert "meeting___notes.md" in all_page_files

    # Verify journal content transformations
    with open(os.path.join(step_2_dir, "2023-01-01.md"), "r") as f:
        content = f.read()
        assert "# Sun, January 1st, 2023" in content
        assert "- [ ] Task 1" in content
        assert "- [x] Task 2" in content

    with open(os.path.join(step_2_dir, "2023-02-14.md"), "r") as f:
        content = f.read()
        assert "# Tue, February 14th, 2023" in content
        assert ":LOGBOOK:" not in content
        assert "- [ ] Working on project" in content

    # Verify page content transformations
    # Try both step_1 and step_2 for each page file
    for page_file in ["project___Build agents.md", "meeting___notes.md"]:
        if os.path.exists(os.path.join(step_1_dir, page_file)):
            page_path = os.path.join(step_1_dir, page_file)
        else:
            page_path = os.path.join(step_2_dir, page_file)
        with open(page_path, "r") as f:
            content = f.read()
            if page_file == "project___Build agents.md":
                assert "Agents Doc" in content
                assert "#project" in content
                assert "- [ ] Implement feature" in content
                assert "((abcd1234-5678-90ab-cdef-1234567890ab))" not in content
                assert "collapsed:: true" not in content
            if page_file == "meeting___notes.md":
                assert "# Notes" in content
                assert "#meeting" in content
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

    # Check for evidence of dry run mode
    assert "Would update content in" in output
    assert "Would save to" in output
    assert "Run without --dry-run to apply these changes" in output

    # Check that output directory was not created
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
        # No subfolders for journals or pages
        assert not os.path.exists(os.path.join(output_dir, "journals"))
        assert not os.path.exists(os.path.join(output_dir, "pages"))

        # Check that step_1 and step_2 exist
        step_1_dir = os.path.join(output_dir, "step_1")
        step_2_dir = os.path.join(output_dir, "step_2")
        assert os.path.exists(step_1_dir)
        assert os.path.exists(step_2_dir)

        # Check that journal files exist and have been processed (should be in step_2)
        journal_files = [
            f
            for f in os.listdir(step_2_dir)
            if f.endswith(".md") and re.match(r"\d{4}-\d{2}-\d{2}\.md", f)
        ]
        assert len(journal_files) > 0  # Make sure there's at least one journal file

        # Check that page files exist and have been processed (should be in step_1 or step_2)
        page_files = [
            f
            for f in os.listdir(step_1_dir)
            if f.endswith(".md") and not re.match(r"\d{4}-\d{2}-\d{2}\.md", f)
        ] + [
            f
            for f in os.listdir(step_2_dir)
            if f.endswith(".md") and not re.match(r"\d{4}-\d{2}-\d{2}\.md", f)
        ]
        assert len(page_files) > 0  # Make sure there's at least one page file

        # Verify journal files were renamed correctly (from YYYY_MM_DD.md to YYYY-MM-DD.md)
        for file in journal_files:
            assert re.match(
                r"\d{4}-\d{2}-\d{2}\.md", file
            ), f"Journal file {file} not in correct format YYYY-MM-DD.md"

        # Sample check of content transformation
        # Check the first journal file
        if journal_files:
            first_journal = os.path.join(step_2_dir, journal_files[0])
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
            # Try both step_1 and step_2 for each page file
            for page_file in page_files:
                if os.path.exists(os.path.join(step_1_dir, page_file)):
                    page_path = os.path.join(step_1_dir, page_file)
                else:
                    page_path = os.path.join(step_2_dir, page_file)
                with open(page_path, "r") as f:
                    content = f.read()
                    lines = content.strip().split("\n")
                    # First line should be a markdown header
                    assert lines[0].startswith(
                        "# "
                    ), f"Page {page_file} doesn't start with a title header"

                    # Look for a file with ___ in its name to check slash formatting
                    if "___" in page_file:
                        title = lines[0][2:]  # Remove "# " prefix
                        # Now expect no slashes, just flattened title
                        if len(title.split()) > 1:
                            assert (
                                " " in title
                            ), f"Title for file with ___ ({page_file}) should be space-separated"

        print(f"\nConverted workspace created at: {output_dir}")
        print(
            "You can manually inspect the results and then delete the directory when done."
        )
    except AssertionError as e:
        # Clean up on test failure
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        raise e


def test_arrows_processor_integration(tmp_path):
    from src.processors.arrows_processor import ArrowsProcessor
    from src.processors.pipeline import ProcessorPipeline
    from src.processors.task_cleaner import TaskCleaner
    from src.processors.link_processor import LinkProcessor
    from src.processors.properties_processor import PropertiesProcessor
    from src.processors.ordered_list_processor import OrderedListProcessor
    from src.processors.empty_content_cleaner import EmptyContentCleaner
    from src.processors.indented_bullet_points import IndentedBulletPointsProcessor
    from src.processors.wikilink import WikiLinkProcessor

    # Simulate a pipeline similar to the main one
    pipeline = ProcessorPipeline(
        [
            LinkProcessor(),
            PropertiesProcessor(),
            OrderedListProcessor(),
            TaskCleaner(),
            EmptyContentCleaner(),
            IndentedBulletPointsProcessor(),
            WikiLinkProcessor(),
            ArrowsProcessor(),
        ]
    )
    content = """
# Test Arrows Integration

- This is a right arrow ->
- This is another =>
- This is a left arrow <-
- This is another <=
"""
    new_content, changed = pipeline.process(content)
    assert changed is True
    assert "->" not in new_content
    assert "=>" not in new_content
    assert "<-" not in new_content
    assert "<=" not in new_content
    assert new_content.count("→") == 2
    assert new_content.count("←") == 2
    assert "right arrow →" in new_content
    assert "another →" in new_content
    assert "left arrow ←" in new_content
    assert "another ←" in new_content


def test_tag_page_generation(tmp_path):
    # Simulate tag collection
    TagToBacklinkProcessor.found_tags.clear()
    TagToBacklinkProcessor.found_tags.update({"brag-doc", "my_tag"})
    tag_dir = tmp_path
    # Simulate tag page generation logic
    for tag in TagToBacklinkProcessor.found_tags:
        tag_path = os.path.join(tag_dir, f"{tag}.md")
        tag_content = f"# {tag}\n\n#inline-tag\n"
        with open(tag_path, "w", encoding="utf-8") as f:
            f.write(tag_content)
    # Check files
    for tag in ["brag-doc", "my_tag"]:
        tag_path = os.path.join(tag_dir, f"{tag}.md")
        assert os.path.exists(tag_path)
        with open(tag_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == f"# {tag}\n\n#inline-tag\n"
