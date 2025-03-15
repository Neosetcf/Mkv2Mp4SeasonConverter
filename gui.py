from imports import lazy_logging, lazy_sys, lazy_io, lazy_import, lazy_QtWidgets, lazy_os
from utils import setup_logging, load_config

class FilteredStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.ignored_messages = [
            "kf.i18n: KLocalizedString: Using an empty domain, fix the code."
        ]

    def write(self, message):
        sys_module = lazy_sys()
        if not any(ignored in message for ignored in self.ignored_messages):
            self.original_stderr.write(message)

    def flush(self):
        self.original_stderr.flush()

def main():
    logging_module = lazy_logging()
    sys_module = lazy_sys()
    io_module = lazy_io()
    QtWidgets = lazy_QtWidgets()
    os_module = lazy_os()

    try:
        config = load_config()
        setup_logging(config.get("log_file", "app.log"))

        current_dir = os_module.path.dirname(os_module.path.abspath(__file__))
        sys_module.path.insert(0, current_dir)

        db_handler = lazy_import("database").DatabaseHandler(config.get("db_file", "app.db"))
        if db_handler.connect():
            db_handler.create_tables()

        sys_module.stderr = FilteredStderr(sys_module.stderr)

        app = QtWidgets.QApplication(sys_module.argv)
        window = lazy_import("main_window").MainWindow()
        window.show()
        app.exec()

    except Exception as e:
        if logging_module:
            logging_module.critical(f"Unhandled exception in main: {e}")
        else:
            print(f"Unhandled exception in main: {e}")

if __name__ == "__main__":
    main()
