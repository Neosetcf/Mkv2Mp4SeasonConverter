from imports import lazy_sqlite3, lazy_logging

sqlite3 = lazy_sqlite3()
logging = lazy_logging()

class DatabaseHandler:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self.connection.execute("PRAGMA journal_mode=WAL;")  # Enable Write-Ahead Logging
            return True
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            return False

    def create_tables(self):
        try:
            with self.connection as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processed_files (
                        filepath TEXT PRIMARY KEY,
                        output_path TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_filepath ON processed_files (filepath)")
                logging.info("Database tables created or already exist.")
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")

    def add_processed_file(self, file_path, output_path):
        try:
            with self.connection as conn:
                conn.execute("INSERT OR REPLACE INTO processed_files (filepath, output_path) VALUES (?, ?)",
                             (file_path, output_path))
                logging.info(f"Added processed file: {file_path}")
        except sqlite3.Error as e:
            logging.error(f"Database error adding file: {e}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
