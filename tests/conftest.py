import pytest
import os
import tempfile
import shutil


@pytest.fixture
def shared_temp_dir():
    """Create a temporary directory for tests that is shared across multiple test modules"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def shared_test_workspace(shared_temp_dir):
    """Create a shared test workspace with LogSeq structure"""
    # Create directory structure
    journals_dir = os.path.join(shared_temp_dir, "journals")
    os.makedirs(journals_dir, exist_ok=True)

    pages_dir = os.path.join(shared_temp_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    # Create test files from the test_files directory
    test_files_dir = os.path.join(os.path.dirname(__file__), "test_files")

    # Copy journal files
    journal_files_dir = os.path.join(test_files_dir, "journals")
    if os.path.exists(journal_files_dir):
        for filename in os.listdir(journal_files_dir):
            if filename.endswith(".md"):
                source = os.path.join(journal_files_dir, filename)
                dest = os.path.join(journals_dir, filename)
                shutil.copy2(source, dest)

    # Copy page files
    page_files_dir = os.path.join(test_files_dir, "pages")
    if os.path.exists(page_files_dir):
        for filename in os.listdir(page_files_dir):
            if filename.endswith(".md"):
                source = os.path.join(page_files_dir, filename)
                dest = os.path.join(pages_dir, filename)
                shutil.copy2(source, dest)

    return shared_temp_dir


@pytest.fixture(autouse=True, scope="session")
def clean_tag_files():
    for step in ["step_1", "step_2"]:
        output_dir = f"tests/full_test_workspace (Reflect format)/{step}/"
        if os.path.exists(output_dir):
            for fname in os.listdir(output_dir):
                if fname.startswith("tag") and fname.endswith(".md"):
                    os.remove(os.path.join(output_dir, fname))
    yield
    # Clean up again after the session
    for step in ["step_1", "step_2"]:
        output_dir = f"tests/full_test_workspace (Reflect format)/{step}/"
        if os.path.exists(output_dir):
            for fname in os.listdir(output_dir):
                if fname.startswith("tag") and fname.endswith(".md"):
                    os.remove(os.path.join(output_dir, fname))
