import pytest
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path


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

    # Create some page files
    with open(os.path.join(pages_dir, "test_page.md"), "w") as f:
        f.write("alias:: Test Alias\nPage content\n- TODO Task 1")

    yield temp_dir
    shutil.rmtree(temp_dir)


def run_cli(args):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src")
    )
    return subprocess.run(
        [sys.executable, "-m", "src.logseq_to_reflect_converter"] + args,
        capture_output=True,
        text=True,
        env=env,
    )


def test_cli_help():
    """Test the CLI help command"""
    result = run_cli(["--help"])
    assert result.returncode == 0
    assert "Convert LogSeq files for use in Reflect" in result.stdout


def test_cli_invalid_workspace():
    """Test the CLI with an invalid workspace"""
    result = run_cli(["--workspace", "nonexistent_dir"])
    # With updated logging, error messages now go to stderr
    assert "Error: nonexistent_dir is not a valid directory" in result.stderr


def test_cli_dry_run(test_workspace):
    """Test the CLI with dry run mode"""
    output_dir = os.path.join(os.path.dirname(test_workspace), "output")
    result = run_cli(
        [
            "--workspace",
            test_workspace,
            "--output-dir",
            output_dir,
            "--dry-run",
        ]
    )
    assert result.returncode == 0
    # Check for "Dry run: True" in stderr since we now use logger
    assert "Dry run: True" in result.stderr
    assert "Run without --dry-run to apply these changes" in result.stdout

    # Check that no files were created
    assert not os.path.exists(output_dir)
