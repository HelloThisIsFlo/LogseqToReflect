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
        1: "January", 2: "February", 3: "March",
        4: "April", 5: "May", 6: "June",
        7: "July", 8: "August", 9: "September",
        10: "October", 11: "November", 12: "December"
    }

    # Mapping of day suffixes
    DAY_SUFFIXES = {
        1: "st", 2: "nd", 3: "rd", 21: "st", 22: "nd", 23: "rd", 31: "st"
    }

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
        first_line = content.strip().split('\n')[0] if content.strip() else ""
        if not first_line.startswith("# "):
            return f"# {self.formatted_date}\n\n{content}", True
        return content, False

class TaskCleaner(ContentProcessor):
    """Clean up tasks in LogSeq format for Reflect"""
    
    def process(self, content):
        # Remove LOGBOOK sections
        new_content = re.sub(r'\s+:LOGBOOK:.*?:END:', '', content, flags=re.DOTALL)
        
        # Replace task markers
        new_content = re.sub(r'- TODO ', '- [ ] ', new_content)
        new_content = re.sub(r'- DONE ', '- [x] ', new_content)
        new_content = re.sub(r'- DOING ', '- [ ] ', new_content)
        
        return new_content, new_content != content

class LinkProcessor(ContentProcessor):
    """Process LogSeq links for Reflect compatibility"""
    
    def process(self, content):
        # Remove LogSeq block IDs
        new_content = re.sub(r'id:: [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '', content)
        
        # Remove LogSeq properties like collapsed:: true
        new_content = re.sub(r'\s+[a-z]+:: (?:true|false)', '', new_content)
        
        return new_content, new_content != content

class BlockReferencesCleaner(ContentProcessor):
    """Clean up LogSeq block references"""
    
    def process(self, content):
        # Remove block references ((block-id))
        new_content = re.sub(r'\(\([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\)\)', '', content)
        
        # Remove #+BEGIN_... #+END_... blocks
        new_content = re.sub(r'#\+BEGIN_\w+.*?#\+END_\w+', '', new_content, flags=re.DOTALL)
        
        # Remove query blocks and other special blocks
        new_content = re.sub(r'{{query.*?}}', '', new_content, flags=re.DOTALL)
        
        return new_content, new_content != content

class PageTitleProcessor(ContentProcessor):
    """Process page titles according to the specified rules"""
    
    def __init__(self, filename):
        self.filename = filename
        # Words that should be lowercase in title case
        self.lowercase_words = {
            'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 
            'as', 'at', 'by', 'for', 'from', 'in', 'into', 
            'near', 'of', 'on', 'onto', 'to', 'with'
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
        
        return ' '.join(result)
    
    def _format_title_from_filename(self):
        """Format the title based on the filename without the extension"""
        base_name = os.path.splitext(self.filename)[0]
        
        # Check if the filename has double underscores
        if '___' in base_name:
            # Split by double underscores
            parts = base_name.split('___')
            
            # Capitalize only the last part
            parts = [p for p in parts[:-1]] + [parts[-1].capitalize()]
            
            # Join with slashes
            return f"# {'/'.join(parts)}"
        else:
            # Simple filename - apply title case
            if base_name:
                # Replace underscores with spaces and apply title case
                text = base_name.replace('_', ' ')
                base_name = self._title_case(text)
            return f"# {base_name}"
    
    def _capitalize_with_slash_rules(self, text):
        """Apply capitalization rules, handling slash-separated text specially"""
        if '/' in text:
            parts = text.split('/')
            # Capitalize only the last part
            parts = [p for p in parts[:-1]] + [parts[-1].capitalize()]
            return '/'.join(parts)
        else:
            # Apply title case
            return self._title_case(text)
    
    def _extract_alias(self, content):
        """Extract the alias from the content if it exists"""
        alias_match = re.search(r'alias:: (.*?)($|\n)', content)
        if alias_match:
            return alias_match.group(1).strip(), alias_match.start(), alias_match.end()
        return None, -1, -1
    
    def process(self, content):
        title = self._format_title_from_filename()
        
        # Check for alias near the start
        alias_text, alias_start, alias_end = self._extract_alias(content)
        
        if alias_text:
            # Split multiple aliases
            aliases = [a.strip() for a in alias_text.split(',')]
            
            # Capitalize each alias and add to title
            for alias in aliases:
                capitalized_alias = self._capitalize_with_slash_rules(alias)
                title = f"{title} // {capitalized_alias}"
            
            # Remove the alias line from the content
            content = content[:alias_start] + content[alias_end:]
        
        # Check if the content already has a title
        first_line = content.strip().split('\n')[0] if content.strip() else ""
        if first_line.startswith("# "):
            # Replace the existing title
            lines = content.split('\n')
            lines[0] = title
            new_content = '\n'.join(lines)
        else:
            # Add the title at the beginning
            new_content = f"{title}\n\n{content.strip()}"
        
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
            with open(file_path, 'r', encoding='utf-8') as f:
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
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return content_changed, True
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False

class JournalFileProcessor(FileProcessor):
    """Process journal files with date headers and task formatting"""
    
    def __init__(self, dry_run=False):
        super().__init__(dry_run)
    
    def get_processors(self):
        """Get list of processors for journal files."""
        return [
            TaskCleaner(),
            LinkProcessor(),
            BlockReferencesCleaner()
        ]
    
    def extract_date_from_filename(self, filename):
        """Extract date components from filename in format YYYY_MM_DD.md."""
        match = re.match(r'(\d{4})_(\d{2})_(\d{2})\.md', filename)
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
            with open(file_path, 'r', encoding='utf-8') as f:
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
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return content_changed, True
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False, False

class PageFileProcessor(FileProcessor):
    """Process page files with task formatting and link preservation"""
    
    def __init__(self, dry_run=False):
        super().__init__(dry_run)
    
    def get_processors(self):
        """Get list of processors for page files."""
        return [
            TaskCleaner(),
            LinkProcessor(),
            BlockReferencesCleaner()
        ]
    
    def process_file(self, file_path, output_path):
        """
        Process a page file and format the title according to specified rules.
        
        Returns:
            Tuple of (content_changed, success)
        """
        try:
            filename = os.path.basename(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply common processors
            content_changed = False
            for processor in self.get_processors():
                new_content, changed = processor.process(content)
                content = new_content
                content_changed = content_changed or changed
            
            # Apply page title processor
            title_processor = PageTitleProcessor(filename)
            new_content, changed = title_processor.process(content)
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
                with open(output_path, 'w', encoding='utf-8') as f:
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
                if file.lower().endswith('.md'):
                    file_path = os.path.join(root, file)
                    content_change, file_renamed = self.journal_processor.process_file(file_path, output_root)
                    
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
                if file.lower().endswith('.md'):
                    file_path = os.path.join(root, file)
                    output_path = os.path.join(output_root, file)
                    content_change, _ = self.page_processor.process_file(file_path, output_path)
                    
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
            self.output_dir = os.path.join(parent_dir, f"{workspace_name} (Reflect format)")
        else:
            self.output_dir = os.path.abspath(output_dir)
        
        self.dry_run = dry_run
        
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
        
        # Process journal directories
        journal_dirs = self.walker.find_directories('journals')
        if not journal_dirs:
            print("No journal directories found")
            return
        
        print(f"Found {len(journal_dirs)} journal directories")
        
        total_journal_files = 0
        total_journal_content_changed = 0
        total_journal_renamed = 0
        
        for journal_dir in journal_dirs:
            files, content_changed, renamed = self.walker.process_journal_directory(journal_dir)
            total_journal_files += files
            total_journal_content_changed += content_changed
            total_journal_renamed += renamed
        
        # Process pages directories
        pages_dirs = self.walker.find_directories('pages')
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
    parser = argparse.ArgumentParser(description='Convert LogSeq files for use in Reflect.')
    parser.add_argument('--workspace', default='.', help='Workspace root directory (default: current directory)')
    parser.add_argument('--output-dir', help='Output directory (default: workspace name + " (Reflect format)")')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.workspace):
        print(f"Error: {args.workspace} is not a valid directory")
        return
    
    converter = LogSeqToReflectConverter(
        workspace=args.workspace,
        output_dir=args.output_dir,
        dry_run=args.dry_run
    )
    
    converter.run()
    
    if args.dry_run:
        print("\nRun without --dry-run to apply these changes.")

if __name__ == "__main__":
    main() 