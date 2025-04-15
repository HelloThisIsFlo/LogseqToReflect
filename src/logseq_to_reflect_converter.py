#!/usr/bin/env python3
import re
import os
import datetime
import argparse
import shutil
from pathlib import Path
from abc import ABC, abstractmethod


class DateFormatter:
    """Helper class for formatting dates"""

    # Mapping of month numbers to names
    MONTH_NAMES = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    # Mapping of day suffixes
    DAY_SUFFIXES = {1: "st", 2: "nd", 3: "rd", 21: "st", 22: "nd", 23: "rd", 31: "st"}

    @staticmethod
    def get_day_suffix(day):
        """Return the appropriate suffix for a day number."""
        return DateFormatter.DAY_SUFFIXES.get(day, "th")

    @staticmethod
    def get_weekday_name(date_obj):
        """Return the abbreviated weekday name."""
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return weekday_names[date_obj.weekday()]

    @staticmethod
    def format_date_for_header(year, month, day):
        """Format the date as 'Mon, April 14th, 2025'."""
        try:
            date_obj = datetime.date(int(year), int(month), int(day))
            weekday = DateFormatter.get_weekday_name(date_obj)
            month_name = DateFormatter.MONTH_NAMES[int(month)]
            day_with_suffix = f"{int(day)}{DateFormatter.get_day_suffix(int(day))}"
            return f"{weekday}, {month_name} {day_with_suffix}, {year}"
        except ValueError as e:
            print(f"Error formatting date {year}-{month}-{day}: {e}")
            return None


class ContentProcessor(ABC):
    """Base class for content processors"""

    @abstractmethod
    def process(self, content):
        """
        Process the content and return a tuple of (new_content, changed).
        """
        pass


class DateHeaderProcessor(ContentProcessor):
    """Add a date header to the content"""

    def __init__(self, formatted_date):
        self.formatted_date = formatted_date

    def process(self, content):
        first_line = content.strip().split("\n")[0] if content.strip() else ""
        if not first_line.startswith("# "):
            return f"# {self.formatted_date}\n\n{content}", True
        return content, False


class TaskCleaner(ContentProcessor):
    """Clean up tasks in LogSeq format for Reflect"""

    def process(self, content):
        # Remove LOGBOOK sections
        new_content = re.sub(r"\s+:LOGBOOK:.*?:END:", "", content, flags=re.DOTALL)

        # Replace task markers
        new_content = re.sub(r"- TODO ", "- [ ] ", new_content)
        new_content = re.sub(r"- DONE ", "- [x] ", new_content)
        new_content = re.sub(r"- DOING ", "- [ ] ", new_content)

        return new_content, new_content != content


class LinkProcessor(ContentProcessor):
    """Process LogSeq links for Reflect compatibility"""

    def process(self, content):
        # Remove LogSeq block IDs
        new_content = re.sub(
            r"id:: [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
            "",
            content,
        )

        # Remove LogSeq properties like collapsed:: true
        new_content = re.sub(r"\s+[a-z]+:: (?:true|false)", "", new_content)

        return new_content, new_content != content


class BlockReferencesCleaner(ContentProcessor):
    """Clean up LogSeq block references"""

    def process(self, content):
        # Remove block references ((block-id))
        new_content = re.sub(
            r"\(\([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\)\)",
            "",
            content,
        )

        # Remove #+BEGIN_... #+END_... blocks
        new_content = re.sub(
            r"#\+BEGIN_\w+.*?#\+END_\w+", "", new_content, flags=re.DOTALL
        )

        # Remove query blocks - match the entire line containing a query
        new_content = re.sub(
            r"^\s*-?\s*{{query.*?}}.*$", "", new_content, flags=re.MULTILINE
        )

        return new_content, new_content != content


class BlockReferencesReplacer(ContentProcessor):
    """
    Replace LogSeq block references with their actual content and a link to the source page.

    This processor:
    1. Collects all block IDs and their associated text from all files
    2. Replaces block references ((block-id)) with the actual content and a link to the source page
    """

    def __init__(self):
        # Dictionary to store block IDs and their associated text and page names
        # Format: {block_id: (text, page_name)}
        self.block_map = {}

    def collect_blocks(self, workspace_path):
        """Scan all files in the workspace to collect block IDs and their text"""
        print("Collecting block IDs and content...")

        # Find all markdown files in the workspace
        md_files = []
        for root, _, files in os.walk(workspace_path):
            for file in files:
                if file.lower().endswith(".md"):
                    md_files.append(os.path.join(root, file))

        # Process each file to extract block IDs and content
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract the page name (either from the file name or from the content)
                page_name = self._extract_page_name(file_path, content)

                # Find all block IDs and their associated text
                self._extract_block_ids(content, page_name)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        print(f"Collected {len(self.block_map)} block references")

    def _extract_page_name(self, file_path, content):
        """Extract the page name from the file path or content"""
        # First try to get the title from the content (first heading)
        title_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # If no title found, use the file name without extension
        base_name = os.path.basename(file_path)
        base_name = os.path.splitext(base_name)[0]

        # Clean up the name (replace underscores with spaces, etc.)
        return base_name.replace("_", " ")

    def _extract_block_ids(self, content, page_name):
        """Extract all block IDs and their associated text from the content"""
        # Find all lines with block IDs
        block_id_pattern = r"(.*?)id::\s*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})(.*)$"

        lines = content.split("\n")
        for i, line in enumerate(lines):
            match = re.search(block_id_pattern, line)
            if match:
                block_id = match.group(2).strip()

                # Get the text from the previous line if this is just an ID line
                # Otherwise use the current line's text without the ID part
                line_text = match.group(1).strip()

                # If the line only contains the ID and no other text,
                # look at the previous line for the content
                if not line_text and i > 0:
                    line_text = lines[i - 1].strip()

                # Clean up the text (remove leading/trailing whitespace, bullet points, etc.)
                clean_text = re.sub(r"^\s*-\s*", "", line_text).strip()

                # If we still have no content, try to get it from the beginning of the current line
                if not clean_text and match.group(1):
                    # Extract content before "id::"
                    clean_text = re.sub(r"^\s*-\s*", "", match.group(1)).strip()

                # Store the block ID, text, and page name
                self.block_map[block_id] = (clean_text, page_name)

    def process(self, content):
        """Replace block references with their actual content and a link to the source page"""
        original_content = content

        # Find all block references in the content
        reference_pattern = (
            r"\(\(([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\)\)"
        )

        # Check if there are any references at all
        has_references = re.search(reference_pattern, content) is not None

        # Remove #+BEGIN_... #+END_... blocks
        content = re.sub(r"#\+BEGIN_\w+.*?#\+END_\w+", "", content, flags=re.DOTALL)

        # Remove query blocks - match the entire line containing a query
        content = re.sub(r"^\s*-?\s*{{query.*?}}.*$", "", content, flags=re.MULTILINE)

        # If no references found after cleaning blocks, return early
        if not has_references:
            return content, original_content != content

        # If we have no block map but there are references, we'll still remove them
        if not self.block_map:
            content = re.sub(reference_pattern, "", content)
            return content, original_content != content

        # Count replacements to determine if content changed
        replacements_made = 0

        def replace_reference(match):
            nonlocal replacements_made
            block_id = match.group(1)
            if block_id in self.block_map:
                text, page_name = self.block_map[block_id]
                replacements_made += 1
                return f"{text} ([[{page_name}]])"
            replacements_made += 1
            return ""  # If the block ID is not found, remove the reference

        content = re.sub(reference_pattern, replace_reference, content)

        return content, original_content != content


class EmptyContentCleaner(ContentProcessor):
    """Clean up empty lines and empty bullet points left after content removal"""

    def process(self, content):
        lines = content.split("\n")
        new_lines = []

        for i, line in enumerate(lines):
            # Skip empty bullet points (just "- " with possible whitespace)
            if re.match(r"^\s*-\s*$", line):
                continue

            # Add non-empty lines or lines that aren't just whitespace after a task
            # BUT preserve empty lines between sections (before headings)
            if (
                i > 0
                and not line.strip()
                and re.match(r"^\s*-\s*\[[ x]\]", lines[i - 1])
            ):
                # Check if this empty line is followed by a heading
                if i < len(lines) - 1 and lines[i + 1].strip().startswith("#"):
                    new_lines.append(line)
                continue

            new_lines.append(line)

        new_content = "\n".join(new_lines)
        return new_content, new_content != content


class IndentedBulletPointsProcessor(ContentProcessor):
    """
    Process indented bullet points with tabs and convert them to a format compatible with Reflect.

    This processor:
    1. Removes one level of tab indentation from bullet points directly under headings
    2. Preserves the hierarchical structure of nested bullet points
    3. Ensures proper indentation levels are maintained throughout bullet hierarchies

    Example transformation:
    ```
    ## Heading
        - Top level bullet under heading (indented with tabs in LogSeq)
            - Second level bullet
                - Third level bullet
    ```

    becomes:

    ```
    ## Heading
    - Top level bullet under heading
        - Second level bullet
            - Third level bullet
    ```
    """

    def process(self, content):
        lines = content.split("\n")
        new_lines = []
        current_section = None

        for i, line in enumerate(lines):
            # Check if line is a heading (starts with #)
            if line.strip().startswith("#"):
                current_section = line
                new_lines.append(line)
                continue

            # Count leading tabs to determine indentation level
            leading_tabs = 0
            for char in line:
                if char == "\t":
                    leading_tabs += 1
                else:
                    break

            # Check if this is a bullet point (after tabs there's "- ")
            trimmed_line = line.lstrip("\t")
            is_bullet = trimmed_line.startswith("- ")

            if is_bullet:
                # Handle indentation levels based on bullet hierarchy
                if current_section is not None and leading_tabs == 1:
                    # Top level bullet under a section heading - remove the leading tab
                    new_lines.append(trimmed_line)
                elif leading_tabs > 0:
                    # Keep proper indentation for nested bullets, preserving hierarchy
                    # but reduce level by 1 for top-level bullets
                    indentation = "\t" * (leading_tabs - 1)
                    new_lines.append(f"{indentation}{trimmed_line}")
                else:
                    # Already a top-level bullet without indentation
                    new_lines.append(line)
            else:
                # Not a bullet point, keep as is
                new_lines.append(line)

                # If we have a non-empty, non-heading, non-bullet line,
                # reset the current section (we're no longer directly under a heading)
                if line.strip() and not line.strip().startswith("#"):
                    current_section = None

        new_content = "\n".join(new_lines)
        return new_content, new_content != content


class PageTitleProcessor(ContentProcessor):
    """Process page titles according to the specified rules"""

    def __init__(self, filename):
        self.filename = filename
        # Words that should be lowercase in title case
        self.lowercase_words = {
            "a",
            "an",
            "the",
            "and",
            "but",
            "or",
            "for",
            "nor",
            "as",
            "at",
            "by",
            "for",
            "from",
            "in",
            "into",
            "near",
            "of",
            "on",
            "onto",
            "to",
            "with",
        }

    def _title_case(self, text):
        """Apply proper title case to text"""
        words = text.split()

        # Handle empty strings
        if not words:
            return ""

        # Always capitalize first and last word
        result = [words[0].capitalize()]

        # Apply rules to middle words
        for word in words[1:-1] if len(words) > 1 else []:
            if word.lower() in self.lowercase_words:
                result.append(word.lower())
            else:
                result.append(word.capitalize())

        # Add last word if it exists (and it's not the only word)
        if len(words) > 1:
            result.append(words[-1].capitalize())

        return " ".join(result)

    def _format_title_from_filename(self):
        """Format the title based on the filename without the extension"""
        base_name = os.path.splitext(self.filename)[0]

        # Check if the filename has double underscores
        if "___" in base_name:
            # Split by double underscores
            parts = base_name.split("___")

            # Capitalize only the last part
            parts = [p for p in parts[:-1]] + [parts[-1].capitalize()]

            # Join with slashes
            return f"# {'/'.join(parts)}"
        else:
            # Simple filename - apply title case
            if base_name:
                # Replace underscores with spaces and apply title case
                text = base_name.replace("_", " ")
                base_name = self._title_case(text)
            return f"# {base_name}"

    def _capitalize_with_slash_rules(self, text):
        """Apply capitalization rules, handling slash-separated text specially"""
        if "/" in text:
            parts = text.split("/")
            # Capitalize only the last part
            parts = [p for p in parts[:-1]] + [parts[-1].capitalize()]
            return "/".join(parts)
        else:
            # Apply title case
            return self._title_case(text)

    def _extract_alias(self, content):
        """Extract the alias from the content if it exists"""
        alias_match = re.search(r"alias:: (.*?)($|\n)", content)
        if alias_match:
            return alias_match.group(1).strip(), alias_match.start(), alias_match.end()
        return None, -1, -1

    def process(self, content):
        title = self._format_title_from_filename()

        # Check for alias near the start
        alias_text, alias_start, alias_end = self._extract_alias(content)

        if alias_text:
            # Split multiple aliases
            aliases = [a.strip() for a in alias_text.split(",")]

            # Capitalize each alias and add to title
            for alias in aliases:
                capitalized_alias = self._capitalize_with_slash_rules(alias)
                title = f"{title} // {capitalized_alias}"

            # Remove the alias line from the content
            content = content[:alias_start] + content[alias_end:]

        # Check if the content already has a title
        first_line = content.strip().split("\n")[0] if content.strip() else ""
        if first_line.startswith("# "):
            # Replace the existing title
            lines = content.split("\n")
            lines[0] = title
            new_content = "\n".join(lines)
        else:
            # Add the title at the beginning
            new_content = f"{title}\n\n{content.strip()}"

        return new_content, new_content != content


class WikiLinkProcessor(ContentProcessor):
    """Process wikilinks using the same formatting rules as page titles"""

    def __init__(self):
        # Words that should be lowercase in title case
        self.lowercase_words = {
            "a",
            "an",
            "the",
            "and",
            "but",
            "or",
            "for",
            "nor",
            "as",
            "at",
            "by",
            "for",
            "from",
            "in",
            "into",
            "near",
            "of",
            "on",
            "onto",
            "to",
            "with",
        }

    def _title_case(self, text):
        """Apply proper title case to text"""
        words = text.split()

        # Handle empty strings
        if not words:
            return ""

        # Always capitalize first and last word
        result = [words[0].capitalize()]

        # Apply rules to middle words
        for word in words[1:-1] if len(words) > 1 else []:
            if word.lower() in self.lowercase_words:
                result.append(word.lower())
            else:
                result.append(word.capitalize())

        # Add last word if it exists (and it's not the only word)
        if len(words) > 1:
            result.append(words[-1].capitalize())

        return " ".join(result)

    def _capitalize_with_slash_rules(self, text):
        """Apply capitalization rules, handling slash-separated text specially"""
        if "/" in text:
            parts = text.split("/")
            # Capitalize only the last part after applying title case to it
            # Note: We don't replace underscores with spaces for wikilinks
            last_part_words = last_part = parts[-1].split(" ")
            last_part_title_cased = []

            # Apply title case to the last part, word by word
            if last_part_words:
                # First word is always capitalized
                last_part_title_cased.append(last_part_words[0].capitalize())

                # Middle words follow lowercase word rules
                for word in last_part_words[1:-1] if len(last_part_words) > 1 else []:
                    if word.lower() in self.lowercase_words:
                        last_part_title_cased.append(word.lower())
                    else:
                        last_part_title_cased.append(word.capitalize())

                # Last word is always capitalized
                if len(last_part_words) > 1:
                    last_part_title_cased.append(last_part_words[-1].capitalize())

            formatted_last_part = " ".join(last_part_title_cased)

            # Keep paths lowercase, capitalize only the last part
            parts = [p.lower() for p in parts[:-1]] + [formatted_last_part]
            return "/".join(parts)
        else:
            # For regular text (no slashes), apply title case
            # Split by spaces for title casing but preserve underscores
            words = text.split(" ")

            # Handle empty strings
            if not words:
                return ""

            # Always capitalize first and last word
            result = [words[0].capitalize()]

            # Apply rules to middle words
            for word in words[1:-1] if len(words) > 1 else []:
                if word.lower() in self.lowercase_words:
                    result.append(word.lower())
                else:
                    result.append(word.capitalize())

            # Add last word if it exists (and it's not the only word)
            if len(words) > 1:
                result.append(words[-1].capitalize())

            return " ".join(result)

    def _format_wikilink(self, match):
        """Format the wikilink content according to the rules"""
        link_text = match.group(1)
        formatted_text = self._capitalize_with_slash_rules(link_text)
        return f"[[{formatted_text}]]"

    def process(self, content):
        # Find all wikilinks and format them
        new_content = re.sub(r"\[\[(.*?)\]\]", self._format_wikilink, content)
        return new_content, new_content != content


class FileProcessor:
    """Base class for file processors"""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run

    def get_processors(self):
        """Get list of content processors for this file type."""
        return []

    def process_file(self, file_path, output_path):
        """
        Process a file and write the result to output_path.

        Returns:
            Tuple of (content_changed, success)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply processors
            content_changed = False
            for processor in self.get_processors():
                new_content, changed = processor.process(content)
                content = new_content
                content_changed = content_changed or changed

            if self.dry_run:
                if content_changed:
                    print(f"Would update content in {file_path}")
                print(f"Would save to {output_path}")
                return content_changed, True
            else:
                # Make sure the output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Write the content to the output file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return content_changed, True

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False


class JournalFileProcessor(FileProcessor):
    """Process journal files with date headers and task formatting"""

    def __init__(self, dry_run=False):
        super().__init__(dry_run)
        self.block_references_replacer = None

    def get_processors(self):
        """Get list of processors for journal files."""
        processors = [
            LinkProcessor(),  # Process links first
        ]

        # Add the block references replacer or cleaner
        if self.block_references_replacer:
            processors.append(self.block_references_replacer)
        else:
            processors.append(BlockReferencesCleaner())

        # Add the remaining processors in order
        processors.extend(
            [
                TaskCleaner(),
                EmptyContentCleaner(),
                IndentedBulletPointsProcessor(),
                WikiLinkProcessor(),
            ]
        )

        return processors

    def extract_date_from_filename(self, filename):
        """Extract date components from filename in format YYYY_MM_DD.md."""
        match = re.match(r"(\d{4})_(\d{2})_(\d{2})\.md", filename)
        if not match:
            return None
        return match.groups()

    def process_file(self, file_path, output_dir):
        """
        Process a journal file.

        Returns:
            Tuple of (content_changed, file_renamed)
        """
        filename = os.path.basename(file_path)

        # Extract date from filename
        date_parts = self.extract_date_from_filename(filename)
        if not date_parts:
            print(f"Skipping {filename} - doesn't match expected format YYYY_MM_DD.md")
            return False, False

        year, month, day = date_parts
        formatted_date = DateFormatter.format_date_for_header(year, month, day)
        if not formatted_date:
            return False, False

        # Generate the new filename
        new_filename = f"{year}-{month}-{day}.md"
        output_path = os.path.join(output_dir, new_filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply common processors
            content_changed = False
            for processor in self.get_processors():
                new_content, changed = processor.process(content)
                content = new_content
                content_changed = content_changed or changed

            # Add date header
            date_processor = DateHeaderProcessor(formatted_date)
            new_content, changed = date_processor.process(content)
            content = new_content
            content_changed = content_changed or changed

            if self.dry_run:
                if content_changed:
                    print(f"Would update content in {file_path}")
                print(f"Would save to {output_path} (renamed from {filename})")
                return content_changed, True
            else:
                # Write the content to the output file
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return content_changed, True

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False


class PageFileProcessor(FileProcessor):
    """Process page files with task formatting and link preservation"""

    def __init__(self, dry_run=False):
        super().__init__(dry_run)
        self.block_references_replacer = None

    def get_processors(self):
        """Get list of processors for page files."""
        processors = [
            LinkProcessor(),  # Process links first
        ]

        # Add the block references replacer or cleaner
        if self.block_references_replacer:
            processors.append(self.block_references_replacer)
        else:
            processors.append(BlockReferencesCleaner())

        # Add the remaining processors in order
        processors.extend(
            [
                TaskCleaner(),
                EmptyContentCleaner(),
                IndentedBulletPointsProcessor(),
                WikiLinkProcessor(),
            ]
        )

        return processors

    def process_file(self, file_path, output_path):
        """
        Process a page file and format the title according to specified rules.

        Returns:
            Tuple of (content_changed, success)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get base processors
            processors = self.get_processors()

            # Add PageTitleProcessor first, which needs the filename
            filename = os.path.basename(file_path)
            processors.insert(0, PageTitleProcessor(filename))

            # Run all processors
            content_changed = False
            for processor in processors:
                content, changed = processor.process(content)
                if changed:
                    content_changed = True

            if self.dry_run:
                if content_changed:
                    print(f"Would update content in {file_path}")
                print(f"Would save to {output_path}")
                return content_changed, True
            else:
                # Make sure the output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Write the content to the output file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return content_changed, True

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False


class DirectoryWalker:
    """Class for walking directories and processing files"""

    def __init__(self, workspace, output_dir, dry_run=False):
        self.workspace = os.path.abspath(workspace)
        self.output_dir = output_dir
        self.dry_run = dry_run

        # Initialize file processors
        self.journal_processor = JournalFileProcessor(dry_run)
        self.page_processor = PageFileProcessor(dry_run)

    def find_directories(self, dir_name):
        """Find all directories with the given name in the workspace."""
        result = []

        for root, dirs, _ in os.walk(self.workspace):
            if dir_name in dirs:
                result.append(os.path.join(root, dir_name))

        return result

    def process_journal_directory(self, journal_dir):
        """
        Process all journal files in a directory.

        Returns:
            Tuple of (total_files, content_changed, renamed)
        """
        # Determine the relative path and create output directory
        rel_path = os.path.relpath(journal_dir, self.workspace)
        output_journal_dir = os.path.join(self.output_dir, rel_path)

        if not self.dry_run:
            os.makedirs(output_journal_dir, exist_ok=True)

        total_files = 0
        content_changed = 0
        renamed = 0

        print(f"Processing journal directory: {journal_dir}")
        print(f"Output directory: {output_journal_dir}")

        for root, _, files in os.walk(journal_dir):
            relative_root = os.path.relpath(root, journal_dir)
            output_root = os.path.join(output_journal_dir, relative_root)

            if not self.dry_run:
                os.makedirs(output_root, exist_ok=True)

            for file in files:
                if file.lower().endswith(".md"):
                    file_path = os.path.join(root, file)
                    content_change, file_renamed = self.journal_processor.process_file(
                        file_path, output_root
                    )

                    total_files += 1
                    if content_change:
                        content_changed += 1
                    if file_renamed:
                        renamed += 1

        return total_files, content_changed, renamed

    def process_pages_directory(self, pages_dir):
        """
        Process all page files in a directory.

        Returns:
            Tuple of (total_files, content_changed)
        """
        # Determine the relative path and create output directory
        rel_path = os.path.relpath(pages_dir, self.workspace)
        output_pages_dir = os.path.join(self.output_dir, rel_path)

        if not self.dry_run:
            os.makedirs(output_pages_dir, exist_ok=True)

        total_files = 0
        content_changed = 0

        print(f"Processing pages directory: {pages_dir}")
        print(f"Output directory: {output_pages_dir}")

        for root, _, files in os.walk(pages_dir):
            relative_root = os.path.relpath(root, pages_dir)
            output_root = os.path.join(output_pages_dir, relative_root)

            if not self.dry_run:
                os.makedirs(output_root, exist_ok=True)

            for file in files:
                if file.lower().endswith(".md"):
                    file_path = os.path.join(root, file)
                    output_path = os.path.join(output_root, file)
                    content_change, _ = self.page_processor.process_file(
                        file_path, output_path
                    )

                    total_files += 1
                    if content_change:
                        content_changed += 1

        return total_files, content_changed


class LogSeqToReflectConverter:
    """Main converter class to convert LogSeq files to Reflect format"""

    def __init__(self, workspace, output_dir=None, dry_run=False):
        """
        Initialize the converter.

        Args:
            workspace: Path to the LogSeq workspace
            output_dir: Path to the output directory. If None, will be '{workspace} (Reflect format)'
            dry_run: Whether to perform a dry run without making actual changes
        """
        self.workspace = os.path.abspath(workspace)

        if output_dir is None:
            workspace_name = os.path.basename(workspace)
            parent_dir = os.path.dirname(workspace)
            self.output_dir = os.path.join(
                parent_dir, f"{workspace_name} (Reflect format)"
            )
        else:
            self.output_dir = os.path.abspath(output_dir)

        self.dry_run = dry_run

        # Create the block references replacer
        self.block_references_replacer = BlockReferencesReplacer()

        # Create the directory walker
        self.walker = DirectoryWalker(workspace, self.output_dir, dry_run)

    def run(self):
        """Run the conversion process"""
        print(f"Converting LogSeq workspace: {self.workspace}")
        print(f"Output directory: {self.output_dir}")
        print(f"Dry run: {self.dry_run}")

        if not self.dry_run:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)

        # First, collect all block references from all files
        self.block_references_replacer.collect_blocks(self.workspace)

        # Update the file processors with the block references replacer
        self.walker.journal_processor.block_references_replacer = (
            self.block_references_replacer
        )
        self.walker.page_processor.block_references_replacer = (
            self.block_references_replacer
        )

        # Process journal directories
        journal_dirs = self.walker.find_directories("journals")
        if not journal_dirs:
            print("No journal directories found")
            return

        print(f"Found {len(journal_dirs)} journal directories")

        total_journal_files = 0
        total_journal_content_changed = 0
        total_journal_renamed = 0

        for journal_dir in journal_dirs:
            files, content_changed, renamed = self.walker.process_journal_directory(
                journal_dir
            )
            total_journal_files += files
            total_journal_content_changed += content_changed
            total_journal_renamed += renamed

        # Process pages directories
        pages_dirs = self.walker.find_directories("pages")
        total_pages_files = 0
        total_pages_content_changed = 0

        if pages_dirs:
            print(f"Found {len(pages_dirs)} pages directories")

            for pages_dir in pages_dirs:
                files, content_changed = self.walker.process_pages_directory(pages_dir)
                total_pages_files += files
                total_pages_content_changed += content_changed

        print(f"\nSummary:")
        print(f"  Journal files processed: {total_journal_files}")
        print(f"  Journal files with content changes: {total_journal_content_changed}")
        print(f"  Journal files renamed: {total_journal_renamed}")

        if pages_dirs:
            print(f"  Pages files processed: {total_pages_files}")
            print(f"  Pages files with content changes: {total_pages_content_changed}")

        total_files = total_journal_files + total_pages_files
        total_changes = total_journal_content_changed + total_pages_content_changed
        print(f"  Total files processed: {total_files}")
        print(f"  Total files with changes: {total_changes}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert LogSeq files for use in Reflect."
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root directory (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        help='Output directory (default: workspace name + " (Reflect format)")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.workspace):
        print(f"Error: {args.workspace} is not a valid directory")
        return

    converter = LogSeqToReflectConverter(
        workspace=args.workspace, output_dir=args.output_dir, dry_run=args.dry_run
    )

    converter.run()

    if args.dry_run:
        print("\nRun without --dry-run to apply these changes.")


if __name__ == "__main__":
    main()
