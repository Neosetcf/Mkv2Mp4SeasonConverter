from imports import lazy_import, lazy_QtWidgets
from utils import create_ui_element

QtWidgets = lazy_QtWidgets()

class ProcessingInitializer:
    def __init__(self, source_folder_entry, destination_folder_entry, output_format, output_name_entry, progress_bar, start_button):
        self.source_folder_entry = source_folder_entry
        self.destination_folder_entry = destination_folder_entry
        self.output_format = output_format
        self.output_name_entry = output_name_entry
        self.progress_bar = progress_bar
        self.start_button = start_button

    def initialize(self, files):
        """Validates inputs and initializes processing."""
        if not self.validate_input(self.source_folder_entry.text(), "Please select a source folder."):
            return False

        if not self.validate_input(self.destination_folder_entry.text(), "Please select a destination folder."):
            return False

        if not self.validate_input(self.output_format, "Please select an output format."):
            return False

        if not self.validate_input(self.output_name_entry.text(), "Please enter an output name pattern."):
            return False

        self.setup_progress_bar(len(files))
        self.start_button.setEnabled(False)
        return True

    def validate_input(self, value, error_message):
        """Helper method to validate inputs."""
        if not value:
            create_ui_element("QMessageBox").warning(None, "Error", error_message)
            return False
        return True

    def setup_progress_bar(self, file_count):
        """Initializes progress bar settings."""
        self.progress_bar.setMaximum(file_count)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
