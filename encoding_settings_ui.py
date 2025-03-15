from imports import lazy_import

QtWidgets = lazy_import("PyQt5.QtWidgets")

class EncodingSettingsUI:
    def __init__(self, parent_layout):
        self.video_codec_label = QtWidgets.QLabel("Video Codec:")
        self.video_codec_combobox = QtWidgets.QComboBox()
        self.video_codec_combobox.addItems(["libx264", "libx265", "vp9", "av1"])

        self.audio_codec_label = QtWidgets.QLabel("Audio Codec:")
        self.audio_codec_combobox = QtWidgets.QComboBox()
        self.audio_codec_combobox.addItems(["aac", "mp3", "opus"])

        self.video_bitrate_label = QtWidgets.QLabel("Video Bitrate:")
        self.video_bitrate_lineedit = QtWidgets.QLineEdit("2000k")

        self.audio_bitrate_label = QtWidgets.QLabel("Audio Bitrate:")
        self.audio_bitrate_lineedit = QtWidgets.QLineEdit("192k")

        self.preset_label = QtWidgets.QLabel("Preset:")
        self.preset_combobox = QtWidgets.QComboBox()
        self.preset_combobox.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])

        # Add widgets to the layout
        parent_layout.addWidget(self.video_codec_label)
        parent_layout.addWidget(self.video_codec_combobox)
        parent_layout.addWidget(self.audio_codec_label)
        parent_layout.addWidget(self.audio_codec_combobox)
        parent_layout.addWidget(self.video_bitrate_label)
        parent_layout.addWidget(self.video_bitrate_lineedit)
        parent_layout.addWidget(self.audio_bitrate_label)
        parent_layout.addWidget(self.audio_bitrate_lineedit)
        parent_layout.addWidget(self.preset_label)
        parent_layout.addWidget(self.preset_combobox)

    def get_settings(self):
        return {
            "video_codec": self.video_codec_combobox.currentText(),
            "audio_codec": self.audio_codec_combobox.currentText(),
            "video_bitrate": self.video_bitrate_lineedit.text(),
            "audio_bitrate": self.audio_bitrate_lineedit.text(),
            "preset": self.preset_combobox.currentText()
        }
