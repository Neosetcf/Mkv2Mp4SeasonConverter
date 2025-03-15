from imports import lazy_import, lazy_QtWidgets
from utils import create_ui_element

QtWidgets = lazy_QtWidgets()

class FolderSelector:
    def __init__(self, layout, config):
        self.layout = layout
        self.config = config

        # Create UI Elements
        self.source_folder_entry, self.source_folder_button = self.create_folder_entry("Source Folder:", "source_dir")
        self.destination_folder_entry, self.destination_folder_button = self.create_folder_entry("Destination Folder:", "destination_dir") #Modified

    def setup_ui(self):
        # The UI setup is already done in the constructor
        pass

    def create_folder_entry(self, label_text, config_key):
        """Helper to create a labeled folder entry with a selection button."""
        layout = create_ui_element("QHBoxLayout")
        entry = create_ui_element("QLineEdit", text=self.config.get(config_key, ""))
        button = create_ui_element("QPushButton", text=f"Select {label_text}")

        button.clicked.connect(lambda: self.select_folder(entry, config_key))
        layout.addWidget(create_ui_element("QLabel", text=label_text))
        layout.addWidget(entry)
        layout.addWidget(button)
        self.layout.addLayout(layout)

        return entry, button # Modified

    def select_folder(self, entry_widget, config_key):
        """Handles folder selection and updates the config."""
        folder = QtWidgets.QFileDialog.getExistingDirectory(None, f"Select {config_key.replace('_', ' ').title()}")
        if folder:
            entry_widget.setText(folder)
            self.config[config_key] = folder
