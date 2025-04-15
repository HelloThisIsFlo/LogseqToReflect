from ..utils import DateFormatter
from .base import ContentProcessor


class DateHeaderProcessor(ContentProcessor):
    """Add a date header to the content"""

    def __init__(self, formatted_date):
        self.formatted_date = formatted_date

    def process(self, content):
        first_line = content.strip().split("\n")[0] if content.strip() else ""
        if not first_line.startswith("# "):
            return f"# {self.formatted_date}\n\n{content}", True
        return content, False
