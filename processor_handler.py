from imports import lazy_import, lazy_logging, lazy_QtCore, lazy_threading, lazy_json
from worker import AsyncWorker
from file_scanner import FileScanner
from processing_initializer import ProcessingInitializer

QtWidgets = lazy_import("PyQt5.QtWidgets")
QtGui = lazy_import("PyQt5.QtGui")
QtCore = lazy_QtCore()
logging = lazy_logging()
json_module = lazy_json()

class ProcessingHandler:
    def __init__(self, window, source_folder_entry, destination_folder_entry, output_format, output_name_entry, progress_bar, start_button, current_cpu_label, ignored_folders, config, db_handler):
        self.window = window
        self.source_folder_entry = source_folder_entry
        self.destination_folder_entry = destination_folder_entry
        self.output_format = output_format
        self.output_name_entry = output_name_entry
        self.progress_bar = progress_bar
        self.start_button = start_button
        self.current_cpu_label = current_cpu_label
        self.ignored_folders = ignored_folders
        self.config = config
        self.db_handler = db_handler
        self.threadpool = QtCore.QThreadPool()
        self.worker = None

    def start(self):
        """Starts the processing workflow after validation."""
        print(f"ProcessingHandler selected_file_type: {self.output_format}")
        if not self.output_format:
            QtWidgets.QMessageBox.warning(self.window, "Error", "Please select an output format.")
            return

        source_folder = self.source_folder_entry.text()
        files = list(FileScanner(source_folder, self.ignored_folders).scan())

        if not files:
            logging.warning("No files found for processing.")
            return

        if not self.initialize_processing(files):
            return
        self.files = files

        encoding_settings = self.window.encoding_settings_ui.get_settings()

        # Update config
        self.config["video_codec"] = encoding_settings["video_codec"]
        self.config["audio_codec"] = encoding_settings["audio_codec"]
        self.config["video_bitrate"] = encoding_settings["video_bitrate"]
        self.config["audio_bitrate"] = encoding_settings["audio_bitrate"]
        self.config["preset"] = encoding_settings["preset"]

        self.worker = AsyncWorker(
            source_folder, files, self.config.get("max_cpu_percent", 100), self.output_format, self.output_name_entry.text(), self.config
        )
        print(f"self.worker in start: {self.worker}")
        self.launch_worker(source_folder, files)

        # Removed worker runner and threadpool
        self.worker.run()
        self.worker.finished.connect(self.on_processing_complete)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.cpu_update.connect(lambda cpu: self.current_cpu_label.setText(f"Current CPU Usage: {cpu:.2f}%"))

    def initialize_processing(self, files):
        """Handles input validation and UI initialization."""
        initializer = ProcessingInitializer(
            self.source_folder_entry,
            self.destination_folder_entry,
            self.output_format,
            self.output_name_entry,
            self.progress_bar,
            self.start_button,
        )
        return initializer.initialize(files)

    def launch_worker(self, source_folder, files):
        print(f"self.worker in launch_worker: {self.worker}")
        # removed worker runner and threadpool
        # worker_runner = WorkerRunner(self.worker, self.db_handler)
        # self.threadpool.start(worker_runner)
        # removed connect calls
        # self.worker.finished.connect(self.on_processing_complete)
        # self.worker.progress.connect(self.progress_bar.setValue)
        # self.worker.cpu_update.connect(lambda cpu: self.current_cpu_label.setText(f"Current CPU Usage: {cpu:.2f}%"))

    def on_processing_complete(self):
        """Handles post-processing cleanup and UI updates."""
        self.start_button.setEnabled(True)
        logging.info("Processing complete.")
        self.save_config()

    def save_config(self):
        """Saves the updated configuration to a file."""
        try:
            with open("config.json", "w") as f:
                json_module.dump(self.config, f, indent=4)
            logging.info("Configuration saved successfully.")
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
