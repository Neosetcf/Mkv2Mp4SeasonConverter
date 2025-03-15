from utils import create_ui_element
from imports import lazy_import

QtWidgets = lazy_import("PyQt5.QtWidgets")

class OutputSettings:
    def __init__(self, layout):
        self.layout = layout
        self.setup_ui()

    def setup_ui(self):
        """Creates UI elements for output settings."""
        # Removed output name pattern code
        # output_name_layout = create_ui_element("QHBoxLayout")
        # self.output_name_entry = create_ui_element("QLineEdit", text="{filename}_converted")

        # output_name_layout.addWidget(create_ui_element("QLabel", text="Output Name Pattern:"))
        # output_name_layout.addWidget(self.output_name_entry)
        # self.layout.addLayout(output_name_layout)
        pass # added pass so the function does not error out.
