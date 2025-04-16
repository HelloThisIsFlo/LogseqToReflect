import sys
import os
from src.utils import find_markdown_files
from src.processors.page_title import PageTitleProcessor
from collections import defaultdict

# List of known collection/type categories (case-insensitive, title-cased for output)
COLLECTION_TYPE_CATEGORIES = {
    "Repo",
    "Jira",
    "Course",
    "Env",
    "Vdi",
}


def title_case(s):
    # Title-case but preserve all-uppercase acronyms (e.g., AWS, IAM)
    return " ".join([w if w.isupper() else w.capitalize() for w in s.split()])


def build_hierarchy(titles):
    tree = {}
    for title in titles:
        # Remove leading '# ' and split by ' //', then by '/'
        main_title = title.lstrip("# ").split(" //")[0].strip()
        parts = [part.strip() for part in main_title.split("/")]
        # Title-case all parts
        parts = [title_case(part) for part in parts]
        node = tree
        for part in parts:
            if part not in node:
                node[part] = {}
            node = node[part]
    return tree


def print_hierarchy(node, indent=0, file=None):
    for key in sorted(node.keys(), key=lambda s: s.lower()):
        line = f"{'  ' * indent}- {key}"
        print(line)
        if file:
            file.write(line + "\n")
        print_hierarchy(node[key], indent + 1, file)


def group_archetypes(tree):
    collection_type = {}
    disambiguation = {}
    for key in tree:
        # Case-insensitive match for collection/type
        if title_case(key) in COLLECTION_TYPE_CATEGORIES:
            collection_type[key] = tree[key]
        else:
            disambiguation[key] = tree[key]
    return collection_type, disambiguation


def list_disambiguated_pages(workspace_dir):
    print(f"Scanning for files with triple underscores (___) in: {workspace_dir}\n")
    found = False
    results = []
    print(f"{'Filename':<60} | Would-be Title")
    print("-" * 90)
    for file_path in find_markdown_files(workspace_dir):
        filename = os.path.basename(file_path)
        if "___" in filename:
            found = True
            processor = PageTitleProcessor(filename)
            title = processor._format_title_from_filename()
            results.append((filename, title))
    if not found:
        print("No files with triple underscores found.")
    else:
        # Print the table
        for filename, title in results:
            print(f"{filename:<60} | {title}")
        # Write sorted titles to file
        output_file = os.path.join(os.getcwd(), "disambiguated_titles.txt")
        sorted_titles = sorted([title for _, title in results], key=lambda t: t.lower())
        with open(output_file, "w", encoding="utf-8") as f:
            for title in sorted_titles:
                f.write(f"{title}\n")
            # Build and write archetype hierarchies
            tree = build_hierarchy(sorted_titles)
            collection_type, disambiguation = group_archetypes(tree)
            # Print and write Collection/Type
            print("\nCollection/Type Categories:")
            f.write("\nCollection/Type Categories:\n\n")
            print_hierarchy(collection_type, file=f)
            # Print and write Disambiguation
            print("\nDisambiguation Categories:")
            f.write("\nDisambiguation Categories:\n\n")
            print_hierarchy(disambiguation, file=f)
        # Also print archetypes to stdout
        print("\nCollection/Type Categories:")
        print_hierarchy(collection_type)
        print("\nDisambiguation Categories:")
        print_hierarchy(disambiguation)
        print(
            f"\nWrote sorted would-be titles and archetype hierarchies to: {output_file}"
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.list_disambiguated_pages <workspace_dir>")
        sys.exit(1)
    workspace_dir = sys.argv[1]
    list_disambiguated_pages(workspace_dir)
