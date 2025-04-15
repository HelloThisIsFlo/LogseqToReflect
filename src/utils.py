import datetime
import os
import logging
from typing import Iterator, Optional, List, Dict, Union, Callable

# Configure logging
logger = logging.getLogger(__name__)


class DateFormatter:
    """Helper class for formatting dates"""

    # Month name mapping
    MONTH_NAMES: Dict[int, str] = {
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

    # Day suffix mapping
    DAY_SUFFIXES: Dict[int, str] = {
        1: "st",
        2: "nd",
        3: "rd",
        21: "st",
        22: "nd",
        23: "rd",
        31: "st",
    }

    # Weekday names
    WEEKDAY_NAMES: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    @staticmethod
    def get_day_suffix(day: int) -> str:
        """Get the appropriate suffix for a day number (st, nd, rd, th)"""
        return DateFormatter.DAY_SUFFIXES.get(day, "th")

    @staticmethod
    def get_weekday_name(date_obj: datetime.date) -> str:
        """Get the abbreviated weekday name for a date object"""
        return DateFormatter.WEEKDAY_NAMES[date_obj.weekday()]

    @staticmethod
    def format_date_for_header(
        year: Union[str, int], month: Union[str, int], day: Union[str, int]
    ) -> Optional[str]:
        """
        Format a date for use in a header.

        Args:
            year: Year as string or int
            month: Month as string or int
            day: Day as string or int

        Returns:
            Formatted date string or None if error
        """
        try:
            # Convert to integers
            year_int = int(year)
            month_int = int(month)
            day_int = int(day)

            # Create date object
            date_obj = datetime.date(year_int, month_int, day_int)

            # Format components
            weekday = DateFormatter.get_weekday_name(date_obj)
            month_name = DateFormatter.MONTH_NAMES[month_int]
            day_with_suffix = f"{day_int}{DateFormatter.get_day_suffix(day_int)}"

            # Combine into final format
            return f"{weekday}, {month_name} {day_with_suffix}, {year_int}"
        except ValueError as e:
            logger.error(f"Error formatting date {year}-{month}-{day}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error formatting date: {e}")
            return None


def find_markdown_files(root_dir: str) -> Iterator[str]:
    """
    Yield all .md file paths under the given directory, recursively.

    Args:
        root_dir: Directory to search

    Yields:
        Paths to all Markdown files found
    """
    try:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(".md"):
                    yield os.path.join(root, file)
    except Exception as e:
        logger.error(f"Error finding markdown files in {root_dir}: {e}")


def safe_read_file(file_path: str) -> Optional[str]:
    """
    Safely read a file with error handling.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string, or None if error
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


def safe_write_file(file_path: str, content: str) -> bool:
    """
    Safely write content to a file with error handling.

    Args:
        file_path: Path to write to
        content: Content to write

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Write the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return False


def ensure_directory(dir_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Directory path to ensure exists

    Returns:
        True if successful or directory already exists, False on error
    """
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {dir_path}: {e}")
        return False
