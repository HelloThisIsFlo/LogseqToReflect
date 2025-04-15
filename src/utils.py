import datetime
from typing import Iterator


class DateFormatter:
    """Helper class for formatting dates"""

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
    DAY_SUFFIXES = {1: "st", 2: "nd", 3: "rd", 21: "st", 22: "nd", 23: "rd", 31: "st"}

    @staticmethod
    def get_day_suffix(day):
        return DateFormatter.DAY_SUFFIXES.get(day, "th")

    @staticmethod
    def get_weekday_name(date_obj):
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return weekday_names[date_obj.weekday()]

    @staticmethod
    def format_date_for_header(year, month, day):
        try:
            date_obj = datetime.date(int(year), int(month), int(day))
            weekday = DateFormatter.get_weekday_name(date_obj)
            month_name = DateFormatter.MONTH_NAMES[int(month)]
            day_with_suffix = f"{int(day)}{DateFormatter.get_day_suffix(int(day))}"
            return f"{weekday}, {month_name} {day_with_suffix}, {year}"
        except ValueError as e:
            print(f"Error formatting date {year}-{month}-{day}: {e}")
            return None


def find_markdown_files(root_dir: str) -> Iterator[str]:
    """
    Yield all .md file paths under the given directory, recursively.
    """
    import os

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(".md"):
                yield os.path.join(root, file)
