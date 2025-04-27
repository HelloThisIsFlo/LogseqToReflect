import pyperclip
from datetime import datetime, timedelta

# Read from clipboard
clipboard_content = pyperclip.paste()

# Parse dates
files = [line.strip() for line in clipboard_content.splitlines() if line.strip()]
dates = sorted(datetime.strptime(f.replace(".md", ""), "%Y-%m-%d") for f in files)

# Check for gaps
for i in range(1, len(dates)):
    if dates[i] - dates[i - 1] != timedelta(days=1):
        print(
            f"Gap between {dates[i-1].date()} and {dates[i].date()} ({(dates[i] - dates[i-1]).days - 1} missing days)"
        )
