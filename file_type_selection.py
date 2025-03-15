from imports import lazy_import, lazy_QtWidgets, lazy_QtCore

QtWidgets = lazy_QtWidgets()
QtCore = lazy_QtCore()

class FileTypeSelectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Output Format")
        self.setGeometry(100, 100, 300, 200)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.create_radio_buttons()
        self.create_buttons()

    def create_radio_buttons(self):
        """Creates radio buttons for file type selection."""
        self.radio_group = QtWidgets.QButtonGroup()
        self.mp4_radio = QtWidgets.QRadioButton("mp4")
        self.avi_radio = QtWidgets.QRadioButton("avi")
        self.mkv_radio = QtWidgets.QRadioButton("mkv")

        self.radio_group.addButton(self.mp4_radio)
        self.radio_group.addButton(self.avi_radio)
        self.radio_group.addButton(self.mkv_radio)

        self.layout.addWidget(self.mp4_radio)
        self.layout.addWidget(self.avi_radio)
        self.layout.addWidget(self.mkv_radio)

        self.mp4_radio.setChecked(True) # Set default selection

    def create_buttons(self):
        """Creates OK and Cancel buttons."""
        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("OK")
        cancel_button = QtWidgets.QPushButton("Cancel")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        self.layout.addLayout(button_layout)

    def get_selected_file_type(self):
        """Returns the selected file type."""
        if self.mp4_radio.isChecked():
            return "mp4"
        elif self.avi_radio.isChecked():
            return "avi"
        elif self.mkv_radio.isChecked():
            return "mkv"
        else:
            return None
