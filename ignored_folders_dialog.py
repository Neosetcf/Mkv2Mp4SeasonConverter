from imports import lazy_import, lazy_QtWidgets, lazy_json
from utils import save_config #import save_config

QtWidgets = lazy_QtWidgets()
json_module = lazy_json()

class IgnoredFoldersDialog(QtWidgets.QDialog):
    def __init__(self, config, parent=None): #add parent
        super().__init__(parent) #add parent
        self.setWindowTitle("Manage Ignored Folders")
        self.config = config
        self.ignored_folders = self.config.get("ignored_folders", []) #get ignored folders from config

        self.setup_ui()

    def setup_ui(self):
        """Sets up the UI elements for the dialog."""
        layout = QtWidgets.QVBoxLayout()
        self.list_widget = QtWidgets.QListWidget()
        for folder in self.ignored_folders:
            self.list_widget.addItem(folder)

        add_button = QtWidgets.QPushButton("Add Folder")
        add_button.clicked.connect(self.add_folder)

        remove_button = QtWidgets.QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)

        layout.addWidget(self.list_widget)
        layout.addLayout(button_layout)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_and_save) #change accept to accept and save
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def add_folder(self):
        """Adds a folder to the ignored folders list."""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder to Ignore")
        if folder:
            self.ignored_folders.append(folder)
            self.list_widget.addItem(folder)

    def remove_selected(self):
        """Removes the selected folder from the ignored folders list."""
        selected_items = self.list_widget.selectedItems()
        for item in selected_items:
            self.ignored_folders.remove(item.text())
            self.list_widget.takeItem(self.list_widget.row(item))

    def accept_and_save(self):
        """Accepts the dialog and saves the updated ignored folders to config."""
        self.config["ignored_folders"] = self.ignored_folders
        save_config(self.config)
        self.accept()
