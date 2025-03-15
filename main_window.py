from imports import lazy_import
from encoding_settings_ui import EncodingSettingsUI
from main_window_actions import MainWindowActions
from utils import load_config

QtWidgets = lazy_import("PyQt5.QtWidgets")
QtCore = lazy_import("PyQt5.QtCore")
QtGui = lazy_import("PyQt5.QtGui")
os = lazy_import("os")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Converter")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Load config
        self.config = load_config()

        # Source Folder
        self.source_folder_label = QtWidgets.QLabel("Source Folder:")
        self.source_folder_entry = QtWidgets.QLineEdit(self.config.get("source_dir", ""))
        self.source_folder_button = QtWidgets.QPushButton("Browse")
        self.source_folder_button.clicked.connect(self.browse_source_folder)

        source_layout = QtWidgets.QHBoxLayout()
        source_layout.addWidget(self.source_folder_entry)
        source_layout.addWidget(self.source_folder_button)

        self.layout.addWidget(self.source_folder_label)
        self.layout.addLayout(source_layout)

        # Destination Folder
        self.destination_folder_label = QtWidgets.QLabel("Destination Folder:")
        self.destination_folder_entry = QtWidgets.QLineEdit(self.config.get("destination_folder", ""))
        self.destination_folder_button = QtWidgets.QPushButton("Browse")
        self.destination_folder_button.clicked.connect(self.browse_destination_folder)

        destination_layout = QtWidgets.QHBoxLayout()
        destination_layout.addWidget(self.destination_folder_entry)
        destination_layout.addWidget(self.destination_folder_button)

        self.layout.addWidget(self.destination_folder_label)
        self.layout.addLayout(destination_layout)

        # Ignored Folders
        self.ignored_folders_label = QtWidgets.QLabel("Ignored Folders:")
        self.ignored_folders_list = QtWidgets.QListWidget()
        self.ignored_folders_button = QtWidgets.QPushButton("Manage Ignored Folders")
        self.ignored_folders_button.clicked.connect(self.manage_ignored_folders)

        self.layout.addWidget(self.ignored_folders_label)
        self.layout.addWidget(self.ignored_folders_list)
        self.layout.addWidget(self.ignored_folders_button)

        self.actions = MainWindowActions(self)
        print(f"self.actions is of type: {type(self.actions)}")

        self.update_ignored_folders_list()

        # Output Format
        self.output_format_label = QtWidgets.QLabel("Output Format:")
        self.output_format_combobox = QtWidgets.QComboBox()
        self.output_format_combobox.addItems(["mp4", "avi", "mkv", "webm"])

        self.layout.addWidget(self.output_format_label)
        self.layout.addWidget(self.output_format_combobox)

        # Output Name
        self.output_name_label = QtWidgets.QLabel("Output Name:")
        self.output_name_entry = QtWidgets.QLineEdit()

        self.layout.addWidget(self.output_name_label)
        self.layout.addWidget(self.output_name_entry)

        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.layout.addWidget(self.progress_bar)

        # Start Button
        self.start_button = QtWidgets.QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_processing)
        self.layout.addWidget(self.start_button)

        # Current CPU Usage Label
        self.current_cpu_label = QtWidgets.QLabel("Current CPU Usage: 0.00%")
        self.layout.addWidget(self.current_cpu_label)

        # Encoding Settings UI
        self.encoding_settings_ui = EncodingSettingsUI(self.layout)

    def browse_source_folder(self):
        self.actions.browse_source_folder()

    def browse_destination_folder(self):
        self.actions.browse_destination_folder()

    def update_ignored_folders_list(self):
        if hasattr(self.actions, "update_ignored_folders_list"):
            self.actions.update_ignored_folders_list()
        else:
            print("Error: self.actions does not have update_ignored_folders_list")

    def manage_ignored_folders(self):
        self.actions.manage_ignored_folders()

    def start_processing(self):
        self.actions.start_processing()
