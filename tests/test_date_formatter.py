import pytest
from src.logseq_to_reflect_converter import DateFormatter
import datetime


def test_get_day_suffix():
    """Test the get_day_suffix method for various day numbers"""
    assert DateFormatter.get_day_suffix(1) == "st"
    assert DateFormatter.get_day_suffix(2) == "nd"
    assert DateFormatter.get_day_suffix(3) == "rd"
    assert DateFormatter.get_day_suffix(4) == "th"
    assert DateFormatter.get_day_suffix(11) == "th"
    assert DateFormatter.get_day_suffix(21) == "st"
    assert DateFormatter.get_day_suffix(22) == "nd"
    assert DateFormatter.get_day_suffix(23) == "rd"
    assert DateFormatter.get_day_suffix(30) == "th"
    assert DateFormatter.get_day_suffix(31) == "st"


def test_get_weekday_name():
    """Test the get_weekday_name method for all weekdays"""
    weekdays = [
        (datetime.date(2023, 1, 2), "Mon"),  # Monday
        (datetime.date(2023, 1, 3), "Tue"),  # Tuesday
        (datetime.date(2023, 1, 4), "Wed"),  # Wednesday
        (datetime.date(2023, 1, 5), "Thu"),  # Thursday
        (datetime.date(2023, 1, 6), "Fri"),  # Friday
        (datetime.date(2023, 1, 7), "Sat"),  # Saturday
        (datetime.date(2023, 1, 8), "Sun"),  # Sunday
    ]

    for date_obj, expected_name in weekdays:
        assert DateFormatter.get_weekday_name(date_obj) == expected_name


def test_format_date_for_header():
    """Test the format_date_for_header method for various dates"""
    test_cases = [
        (("2023", "01", "01"), "Sun, January 1st, 2023"),
        (("2023", "02", "02"), "Thu, February 2nd, 2023"),
        (("2023", "03", "03"), "Fri, March 3rd, 2023"),
        (("2023", "04", "04"), "Tue, April 4th, 2023"),
        (("2023", "05", "11"), "Thu, May 11th, 2023"),
        (("2023", "06", "21"), "Wed, June 21st, 2023"),
        (("2023", "07", "22"), "Sat, July 22nd, 2023"),
        (("2023", "08", "23"), "Wed, August 23rd, 2023"),
        (("2023", "09", "30"), "Sat, September 30th, 2023"),
        (("2023", "10", "31"), "Tue, October 31st, 2023"),
    ]

    for date_parts, expected_format in test_cases:
        year, month, day = date_parts
        assert DateFormatter.format_date_for_header(year, month, day) == expected_format


def test_format_date_invalid():
    """Test the format_date_for_header method with invalid date"""
    # Invalid date (February 30th)
    assert DateFormatter.format_date_for_header("2023", "02", "30") is None
