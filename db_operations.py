from imports import lazy_import

sqlite3 = lazy_import("sqlite3")
logging = lazy_import("logging")

class DatabaseOperations:
    def __init__(self, config):
        self.db_file = config.get("db_file", "app.db")
        self.create_table()

    def create_table(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_file TEXT UNIQUE,
                    output_file TEXT
                )
            """)
            conn.commit()
            conn.close()
            logging.info("Database tables created or already exist.")
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")

    def insert_record(self, input_file, output_file):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO conversions (input_file, output_file) VALUES (?, ?)", (input_file, output_file))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")

    def get_all_records(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversions")
            records = cursor.fetchall()
            conn.close()
            return records
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return []
