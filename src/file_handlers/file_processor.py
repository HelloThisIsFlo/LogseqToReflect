import os

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
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return content_changed, True
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False
