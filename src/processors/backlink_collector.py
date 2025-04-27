from .base import ContentProcessor
import re
import os
from typing import Set, Dict, Optional


class BacklinkCollector(ContentProcessor):
    """
    Collects all backlinks found during processing and can write them to a file.
    Dates are stored in YYYY/MM/DD format instead of their formatted representation.
    """

    # Collection of all backlinks found across processing
    found_backlinks: Set[str] = set()

    # Dictionary to map formatted dates back to YYYY/MM/DD format
    date_backlinks: Dict[str, str] = {}

    def __init__(self):
        # Pattern to detect backlinks
        self.backlink_pattern = re.compile(r"\[\[(.*?)\]\]")

        # Pattern to detect if a backlink is a date
        self.date_pattern = re.compile(r"^(\d{4})[\s\-](\d{2})[\s\-](\d{2})$")

        # Pattern to detect formatted dates (e.g. "Thu, April 17th, 2025")
        self.formatted_date_pattern = re.compile(
            r"^([A-Za-z]{3}), ([A-Za-z]+) (\d{1,2})(?:st|nd|rd|th), (\d{4})$"
        )

    @classmethod
    def collect_dates_from_workspace(cls, workspace_path: str) -> None:
        """
        Pre-collect dates from journal files in the workspace to build the date mapping.

        Args:
            workspace_path: Path to the LogSeq workspace
        """
        # Check for journal directories
        journals_dir = os.path.join(workspace_path, "journals")
        if not os.path.isdir(journals_dir):
            return

        # Process all journal files
        for file_name in os.listdir(journals_dir):
            if not file_name.endswith(".md"):
                continue

            # Try to extract date from filename
            # Look for patterns like YYYY_MM_DD.md or YYYY-MM-DD.md
            date_match = re.match(r"(\d{4})[_\-](\d{2})[_\-](\d{2})\.md", file_name)
            if date_match:
                year, month, day = date_match.groups()
                from ..utils import DateFormatter

                # Store in YYYY/MM/DD format
                standardized_date = f"{year}/{month}/{day}"

                # Get the formatted version
                formatted_date = DateFormatter.format_date_for_header(year, month, day)
                if formatted_date:
                    cls.date_backlinks[formatted_date] = standardized_date

    def process(self, content: str):
        """
        Extract all backlinks from content and add them to the collection.
        This doesn't modify the content.
        """
        # Find all backlinks in the content
        for match in self.backlink_pattern.finditer(content):
            backlink = match.group(1)

            # Check if this is a date in YYYY-MM-DD or YYYY MM DD format
            date_match = self.date_pattern.match(backlink)
            if date_match:
                year, month, day = date_match.groups()
                # Store as YYYY/MM/DD format
                standardized_date = f"{year}/{month}/{day}"
                BacklinkCollector.found_backlinks.add(standardized_date)

                # Also record the mapping from formatted to standardized
                from ..utils import DateFormatter

                formatted_date = DateFormatter.format_date_for_header(year, month, day)
                if formatted_date:
                    BacklinkCollector.date_backlinks[formatted_date] = standardized_date
            # Check if this is a formatted date (e.g., "Thu, April 17th, 2025")
            elif self.formatted_date_pattern.match(backlink):
                # This is a formatted date, check if we have its standardized form
                if backlink in BacklinkCollector.date_backlinks:
                    standardized_date = BacklinkCollector.date_backlinks[backlink]
                    BacklinkCollector.found_backlinks.add(standardized_date)
                else:
                    # Just add it as-is if we don't have a mapping
                    BacklinkCollector.found_backlinks.add(backlink)
            else:
                # Regular backlink
                BacklinkCollector.found_backlinks.add(backlink)

        # Don't modify the content
        return content, False

    @classmethod
    def write_to_file(cls, output_path: str) -> bool:
        """
        Write all collected backlinks to a file, sorted alphabetically.
        For formatted dates, use the YYYY/MM/DD format if available.

        Args:
            output_path: Path to write the backlinks file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Process backlinks, converting formatted dates to YYYY/MM/DD
            processed_backlinks = set()
            for backlink in cls.found_backlinks:
                # If this is a formatted date, use the standardized form
                if backlink in cls.date_backlinks:
                    processed_backlinks.add(cls.date_backlinks[backlink])
                else:
                    processed_backlinks.add(backlink)

            # Write sorted backlinks to file
            with open(output_path, "w", encoding="utf-8") as f:
                for backlink in sorted(processed_backlinks):
                    f.write(f"{backlink}\n")

            return True
        except Exception as e:
            print(f"Error writing backlinks to {output_path}: {e}")
            return False

    @classmethod
    def clear_backlinks(cls):
        """Clear the collection of backlinks"""
        cls.found_backlinks.clear()
        cls.date_backlinks.clear()
