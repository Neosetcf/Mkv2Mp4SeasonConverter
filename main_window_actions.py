from imports import lazy_import
from ignored_folders_dialog import IgnoredFoldersDialog
from utils import save_config

QtWidgets = lazy_import("PyQt5.QtWidgets")

class MainWindowActions:
    def __init__(self, main_window):
        self.main_window = main_window

    def browse_source_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self.main_window, "Select Source Folder")
        if folder:
            self.main_window.source_folder_entry.setText(folder)
            self.main_window.config["source_dir"] = folder
            save_config(self.main_window.config)

    def browse_destination_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self.main_window, "Select Destination Folder")
        if folder:
            self.main_window.destination_folder_entry.setText(folder)
            self.main_window.config["destination_folder"] = folder
            save_config(self.main_window.config)

    def update_ignored_folders_list(self):
        self.main_window.ignored_folders_list.clear()
        for folder in self.main_window.config.get("ignored_folders", []):
            self.main_window.ignored_folders_list.addItem(folder)

    def manage_ignored_folders(self):
        print(f"manage_ignored_folders called. self is: {self}")
        dialog = IgnoredFoldersDialog(self.main_window.config, self.main_window)
        dialog.exec_()
        print("Before update_ignored_folders_list")
        self.update_ignored_folders_list()
        print("After update_ignored_folders_list")
        save_config(self.main_window.config)

    def start_processing(self):
        from processor_handler import ProcessingHandler
        from db_operations import DatabaseOperations

        db_handler = DatabaseOperations(self.main_window.config)

        self.main_window.start_button.setEnabled(False)

        processor = ProcessingHandler(
            self.main_window,
            self.main_window.source_folder_entry,
            self.main_window.destination_folder_entry,
            self.main_window.output_format_combobox.currentText(),
            self.main_window.output_name_entry,
            self.main_window.progress_bar,
            self.main_window.start_button,
            self.main_window.current_cpu_label,
            self.main_window.config.get("ignored_folders", []),
            self.main_window.config,
            db_handler
        )
        processor.start()
