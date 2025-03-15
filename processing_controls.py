from imports import lazy_import, lazy_QtWidgets, lazy_QtCore, lazy_json
from utils import create_ui_element

QtCore = lazy_QtCore()
QtWidgets = lazy_QtWidgets()
json_module = lazy_json()

class ProcessingControls:
    def __init__(self, layout, config, db_handler, main_window):
        self.layout = layout
        self.config = config
        self.db_handler = db_handler
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        """Creates and arranges UI components."""
        self.progress_bar = create_ui_element("QProgressBar")
        self.start_button = create_ui_element("QPushButton", text="Start Processing")
        self.cancel_button = create_ui_element("QPushButton", text="Cancel")
        self.current_cpu_label = create_ui_element("QLabel", text="Current CPU Usage: 0%")

        # Output Name Pattern
        output_name_layout = create_ui_element("QHBoxLayout")
        self.output_name_entry = create_ui_element("QLineEdit", text="{filename}_converted")
        output_name_layout.addWidget(create_ui_element("QLabel", text="Output Name Pattern:"))
        output_name_layout.addWidget(self.output_name_entry)

        # CPU Limit Controls
        cpu_limit_layout = create_ui_element("QHBoxLayout")
        self.cpu_limit_entry = create_ui_element("QLineEdit", text=str(self.config.get("max_cpu_percent", 80)))
        self.cpu_limit_button = create_ui_element("QPushButton", text="Set CPU Limit")

        cpu_limit_layout.addWidget(create_ui_element("QLabel", text="CPU Limit (%):"))
        cpu_limit_layout.addWidget(self.cpu_limit_entry)
        cpu_limit_layout.addWidget(self.cpu_limit_button)

        # Adding components to layout
        self.layout.addLayout(output_name_layout) # add this line
        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.cancel_button)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.current_cpu_label)
        self.layout.addLayout(cpu_limit_layout)

        # Connecting signals
        self.cpu_limit_button.clicked.connect(self.set_cpu_limit)
        self.cancel_button.clicked.connect(self.cancel_processing)

    def set_cpu_limit(self):
        """Updates CPU limit in configuration."""
        try:
            limit = int(self.cpu_limit_entry.text())
            if 1 <= limit <= 100:
                self.config["max_cpu_percent"] = limit
                with open("config.json", "w") as f:
                    json_module.dump(self.config, f, indent=4)
            else:
                create_ui_element("QMessageBox").warning(self.main_window, "Invalid Input", "CPU limit must be between 1 and 100.")
        except ValueError:
            create_ui_element("QMessageBox").warning(self.main_window, "Invalid Input", "Please enter a valid number.")

    def cancel_processing(self):
        """Stops the processing worker safely."""
        if hasattr(self.main_window.processing_handler, 'worker') and self.main_window.processing_handler.worker:
            self.main_window.processing_handler.worker.stop()
