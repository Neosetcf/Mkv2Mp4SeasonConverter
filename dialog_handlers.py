from imports import lazy_import, lazy_QtWidgets, lazy_json
from ignored_folders_dialog import IgnoredFoldersDialog

QtWidgets = lazy_QtWidgets()
json_module = lazy_json()

class DialogHandlers:
    def __init__(self, layout, processing_controls, config):
        self.layout = layout
        self.processing_controls = processing_controls
        self.config = config
        self.selected_file_type = "mp4"  # Default file type
        self.ignored_folders = self.config.get("ignored_folders", [])  # Load from config

        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI elements for dialog handling."""
        self.output_format_combo = QtWidgets.QComboBox()
        self.output_format_combo.addItems(["mp4", "mkv", "avi"])
        self.output_format_combo.currentTextChanged.connect(self.set_selected_file_type)
        self.layout.addWidget(self.output_format_combo)

        self.ignored_folders_button = QtWidgets.QPushButton("Manage Ignored Folders")
        self.ignored_folders_button.clicked.connect(self.manage_ignored_folders)
        self.layout.addWidget(self.ignored_folders_button)

    def set_selected_file_type(self, text):
        """Sets the selected file type."""
        self.selected_file_type = text
        print(f"Selected file type: {self.selected_file_type}")

    def manage_ignored_folders(self):
        """Opens a dialog to manage ignored folders."""
        dialog = IgnoredFoldersDialog(self.ignored_folders, self.config)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.ignored_folders = dialog.ignored_folders
            self.save_ignored_folders()

    def save_ignored_folders(self):
        """Saves the ignored folders to the config."""
        self.config["ignored_folders"] = self.ignored_folders
        with open("config.json", "w") as f:
            json_module.dump(self.config, f, indent=4)
