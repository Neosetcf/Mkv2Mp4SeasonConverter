from imports import lazy_os

os = lazy_os()

class FileScanner:
    def __init__(self, source_dir, ignored_folders=None):
        self.source_dir = source_dir
        self.ignored_folders = ignored_folders or []

    def scan(self):
        """Recursively scans the source directory for files."""
        for root, dirs, files in os.walk(self.source_dir):
            # Remove ignored folders from dirs to prevent traversal
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in self.ignored_folders]

            for file in files:
                yield os.path.join(root, file)

if __name__ == '__main__':
    # Add Test code here.
    scanner = FileScanner(".")
    for f in scanner.scan():
        print(f)
