import os
import re
import shutil
import sys
import configparser
import ffmpeg
from enum import Enum
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QMessageBox, QFileDialog, QScrollArea, QFrame, QDialog, QComboBox, QFormLayout,
    QCheckBox, QSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt

class Verbosity(Enum):
    SILENT = 0
    DESTINATION = 1
    NORMAL = 2
    VERBOSE = 3

class Config:
    COMPLETED_DIR_NAME = "Completed"
    CONVERTED_DIR_NAME = "CONVERTED_MKV"
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".renameMkv")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.ini")
    CONVERTED_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Anime", "CONVERTED_MKV")

    def __init__(self):
        os.makedirs(Config.CONVERTED_DIR, exist_ok=True)
        os.makedirs(Config.CONFIG_DIR, exist_ok=True)

    def save_settings(self, settings):
        try:
            config = configparser.ConfigParser()
            config["paths"] = settings
            config["config"] = {"converted_dir": Config.CONVERTED_DIR}
            with open(Config.CONFIG_FILE, "w") as configfile:
                config.write(configfile)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def load_settings(self):
        try:
            config = configparser.ConfigParser()
            if os.path.exists(Config.CONFIG_FILE):
                config.read(Config.CONFIG_FILE)
                if "paths" in config:
                    settings = dict(config.items("paths"))
                    if "config" in config:
                        Config.CONVERTED_DIR = config.get("config", "converted_dir")
                    return settings
            return {}
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}

config = Config()

def is_folder_empty(folder_path, verbosity=Verbosity.NORMAL):
    is_empty = not any(os.scandir(folder_path))
    if verbosity.value >= Verbosity.VERBOSE.value:
        print(f"[VERBOSE] Checking if folder '{folder_path}' is empty: {is_empty}")
    return is_empty

def get_mkv_filenames(target_folder, verbosity=Verbosity.NORMAL):
    filenames = {os.path.splitext(f)[0] for f in os.listdir(target_folder) if f.endswith(".mkv")}
    if verbosity.value >= Verbosity.VERBOSE.value:
        print(f"[VERBOSE] MKV filenames in '{target_folder}': {filenames}")
    return filenames

def extract_episode_number(file_path, verbosity=Verbosity.NORMAL):
    filename = os.path.basename(file_path)
    if filename.startswith("media"):
        folder_name = os.path.basename(os.path.dirname(file_path))
        match = re.search(r"(\d+)", folder_name)
        if match:
            return match.group(1)
        else:
            if verbosity.value >= Verbosity.NORMAL.value:
                print(f"[NORMAL] Could not extract episode number from folder name: {folder_name}")
            return None
    patterns = [r"E(\d+)", r"(\d+)\.", r"\[(\d+)\]", r"(\d+)(?!.*\d)"]
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)
    if verbosity.value >= Verbosity.NORMAL.value:
        print(f"[NORMAL] Could not extract episode number from: {file_path}")
    return None

def extract_season_number(target_folder, verbosity=Verbosity.NORMAL):
    try:
        match = re.search(r"Season\s*(\d+)|S(\d+)|(\d+)\s*season", target_folder, re.IGNORECASE)
        if match:
            season_number = next(group for group in match.groups() if group is not None)
            if verbosity.value >= Verbosity.VERBOSE.value:
                print(f"[VERBOSE] Extracted season number from '{target_folder}': {season_number}")
            return season_number
        return "1"
    except Exception as e:
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Error extracting season number: {e}")
        return "1"

def remove_m3u8_folder(m3u8_folder_path, verbosity=Verbosity.NORMAL):
    try:
        shutil.rmtree(m3u8_folder_path)
        if verbosity.value >= Verbosity.VERBOSE.value:
            print(f"[VERBOSE] Removed m3u8 folder: {m3u8_folder_path}")
    except Exception as e:
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Error removing m3u8 folder: {e}")

def is_valid_directory(path):
    return path and os.path.exists(path) and os.path.isdir(path)

def rename_mkv(file_path, season_number, verbosity=Verbosity.NORMAL):
    try:
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        if re.match(r"^S\d+E\d+(\.\d+)?\.mkv$", os.path.basename(file_path), re.IGNORECASE):
            return None
        episode_match = re.search(r"E(\d+(?:\.\d+)?)|Ep(\d+(?:\.\d+)?)|Episode(\d+(?:\.\d+)?)|(\d+(?:\.\d+))", file_name, re.IGNORECASE)
        episode_number = episode_match.group(1) or episode_match.group(2) or episode_match.group(3) or episode_match.group(4) if episode_match else file_name
        if episode_number is None:
            print(f"Warning: Could not extract episode number from '{file_path}'. Skipping rename.")
            return None
        try:
            episode_number = str(float(episode_number)).rstrip('0').rstrip('.')
        except ValueError:
            pass
        season_number = season_number or "1"
        new_filename = f"S{season_number}E{episode_number}.mkv"
        new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
        counter = 1
        while os.path.exists(new_filepath):
            new_filename = f"S{season_number}E{episode_number}_{counter}.mkv"
            new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
            counter += 1
        os.rename(file_path, new_filepath)
        if verbosity.value >= Verbosity.VERBOSE.value:
            print(f"[VERBOSE] Renamed: {file_path} to {new_filepath}")
        return new_filepath
    except Exception as e:
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Error renaming '{file_path}': {e}")
        return None

def move_mkv(file_path, base_dir, verbosity=Verbosity.NORMAL):
    try:
        relative_path = os.path.relpath(file_path, base_dir)
        completed_dir = os.path.join(base_dir, Config.COMPLETED_DIR_NAME, os.path.dirname(relative_path))
        final_destination = os.path.join(completed_dir, os.path.basename(file_path))
        os.makedirs(completed_dir, exist_ok=True)
        shutil.move(file_path, final_destination)
        if verbosity.value >= Verbosity.DESTINATION.value:
            print(f"[DESTINATION] Moved and Renamed: {file_path} to {final_destination}")
        return True
    except OSError as e:
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Error moving '{file_path}': {e}")
        return False
    except Exception as e:
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Error moving '{file_path}': {e}")
        return False

def convert_video(input_file, output_file, verbosity=Verbosity.NORMAL):
    """
    Converts a video file to another format using ffmpeg.
    """
    try:
        # Use ffmpeg to convert the file
        (
            ffmpeg
            .input(input_file)
            .output(output_file, vcodec='copy', acodec='copy')  # Copy streams without re-encoding
            .run(overwrite_output=True)
        )

        if verbosity.value >= Verbosity.VERBOSE.value:
            print(f"[VERBOSE] Converted {input_file} to {output_file}")

        return output_file
    except ffmpeg.Error as e:
        if verbosity.value >= Verbosity.NORMAL.value:
            error_message = e.stderr.decode() if e.stderr else "Unknown error (no stderr output)"
            print(f"[NORMAL] FFmpeg error: {error_message}")
        return None
    except Exception as e:
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Error converting {input_file}: {e}")
        return None

def process_mkv_file(file_path, base_dir, season_number, verbosity=Verbosity.NORMAL):
    renamed_file = rename_mkv(file_path, season_number, verbosity)
    if renamed_file:
        # Move the renamed .mkv file
        move_success = move_mkv(renamed_file, base_dir, verbosity)
        if move_success:
            # Convert the .mkv file to .mp4
            output_file = os.path.join(Config.CONVERTED_DIR, os.path.basename(renamed_file).replace(".mkv", ".mp4"))
            converted_file = convert_video(renamed_file, output_file, verbosity)
            if converted_file:
                print(f"[SUCCESS] Converted {renamed_file} to {converted_file}")
            else:
                print(f"[ERROR] Failed to convert {renamed_file} to .mp4")
        return True
    return False

def process_directory_item(item_path, base_dir, season_number, verbosity=Verbosity.NORMAL):
    if os.path.isdir(item_path):
        process_directory(item_path, base_dir, verbosity)
    elif item_path.endswith((".mkv", ".mp4")):
        process_mkv_file(item_path, base_dir, season_number, verbosity)
    elif item_path.endswith(".m3u8"):
        dir_name = os.path.basename(os.path.dirname(item_path))  # Get the folder name (e.g., "12.m3u8")

        # Extract the episode number from the folder name
        episode_number = None
        if dir_name.endswith(".m3u8"):
            episode_number = dir_name[:-5]  # Remove ".m3u8" to get the episode number

        # If episode_number is not extracted, fall back to the folder name
        if not episode_number:
            episode_number = dir_name

        # Construct the output file name
        output_file_name = f"S{season_number}E{episode_number}.mp4"
        output_path = os.path.join(os.path.dirname(item_path), output_file_name)

        key_path = os.path.join(os.path.dirname(item_path), "media.key")
        if os.path.exists(key_path):
            try:
                with open(key_path, "rb") as key_file:
                    key_data = key_file.read()
                if fuse_ts_files(item_path, key_data, output_path, verbosity):
                    new_output_path = os.path.join(os.path.dirname(os.path.dirname(item_path)), output_file_name)
                    try:
                        shutil.move(output_path, new_output_path)
                        if verbosity.value >= Verbosity.VERBOSE.value:
                            print(f"[VERBOSE] Moved fused file to: {new_output_path}")
                        process_mkv_file(new_output_path, base_dir, season_number, verbosity)
                    except Exception as move_err:
                        if verbosity.value >= Verbosity.NORMAL.value:
                            print(f"[NORMAL] Error moving fused file: {move_err}")
                else:
                    if verbosity.value >= Verbosity.NORMAL.value:
                        print(f"[NORMAL] Failed to fuse ts files from {item_path}")
            except FileNotFoundError:
                if verbosity.value >= Verbosity.NORMAL.value:
                    print(f"[NORMAL] media.key not found in {os.path.dirname(item_path)}")
        else:
            if fuse_ts_files(item_path, None, output_path, verbosity):
                new_output_path = os.path.join(os.path.dirname(os.path.dirname(item_path)), output_file_name)
                try:
                    shutil.move(output_path, new_output_path)
                    if verbosity.value >= Verbosity.VERBOSE.value:
                        print(f"[VERBOSE] Moved fused file to: {new_output_path}")
                    process_mkv_file(new_output_path, base_dir, season_number, verbosity)
                except Exception as move_err:
                    if verbosity.value >= Verbosity.NORMAL.value:
                        print(f"[NORMAL] Error moving fused file: {move_err}")
            else:
                if verbosity.value >= Verbosity.NORMAL.value:
                    print(f"[NORMAL] Failed to fuse ts files from {item_path}")

def process_directory(directory_path, base_dir, verbosity=Verbosity.NORMAL):
    if os.path.basename(directory_path).lower() == Config.COMPLETED_DIR_NAME.lower():
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Skipping directory: {directory_path} (Folder named 'Completed')")
        return
    for item in os.listdir(directory_path):
        full_item_path = os.path.join(directory_path, item)
        process_directory_item(full_item_path, base_dir, extract_season_number(full_item_path, verbosity), verbosity)

def process_m3u8_directory(item_path, mkv_files_present, verbosity=Verbosity.NORMAL):
    m3u8_base_name = os.path.splitext(os.path.basename(item_path))[0]
    if m3u8_base_name in mkv_files_present:
        remove_m3u8_folder(item_path, verbosity)
    else:
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Skipped removing m3u8 folder: {item_path} (No matching .mkv file)")

def fuse_ts_files(m3u8_file, key_data, output_file, verbosity=Verbosity.NORMAL):
    encoding_options = [
        {'c:v': 'copy', 'c:a': 'copy', 'bsf:a': 'aac_adtstoasc'},
        {'c:v': 'libx264', 'c:a': 'aac', 'bsf:a': 'aac_adtstoasc'},
        {'c:v': 'libx265', 'c:a': 'aac', 'bsf:a': 'aac_adtstoasc'},
        {'c:v': 'libvpx-vp9', 'c:a': 'libopus'},
        {'c:v': 'libaom-av1', 'c:a': 'libopus'}
    ]
    for options in encoding_options:
        try:
            if not output_file.lower().endswith(".mp4"):
                output_file = os.path.splitext(output_file)[0] + ".mp4"
            input_stream = ffmpeg.input(m3u8_file, format='hls', allowed_extensions='ALL')
            output_stream = input_stream.output(output_file, **options)
            output_stream.run(overwrite_output=True)
            if verbosity.value >= Verbosity.VERBOSE.value:
                print(f"[VERBOSE] Fused and converted TS files to: {output_file} with options: {options}")
            return True
        except ffmpeg.Error as e:
            if verbosity.value >= Verbosity.NORMAL.value:
                error_message = e.stderr.decode() if e.stderr else "Unknown error (no stderr output)"
                print(f"[NORMAL] FFmpeg error with options {options}: {error_message}")
        except FileNotFoundError:
            if verbosity.value >= Verbosity.NORMAL.value:
                print("Error: FFmpeg executable not found. Make sure it's in your PATH.")
            return False
        except Exception as e:
            if verbosity.value >= Verbosity.NORMAL.value:
                print(f"An unexpected error occurred: {e}")
            return False
    if verbosity.value >= Verbosity.NORMAL.value:
        print(f"[NORMAL] Failed to fuse and convert .ts files into: {output_file} with all encoding options.")
    return False

def get_saved_paths(settings):
    """
    Retrieves the saved paths (starting directory, storage location, and ignored folders) from the settings.
    """
    starting_dir = settings.get("starting_dir")
    storage_location = settings.get("storage_location")
    ignored_folders_str = settings.get("ignored_folders", "")
    ignored_folders = ignored_folders_str.split(";") if ignored_folders_str else []
    return starting_dir, storage_location, ignored_folders

def process_selected_directory(starting_dir, storage_location, ignored_folders, verbosity=Verbosity.NORMAL):
    if not is_valid_directory(starting_dir):
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Invalid starting directory: {starting_dir}")
        return
    if not is_valid_directory(storage_location):
        if verbosity.value >= Verbosity.NORMAL.value:
            print(f"[NORMAL] Invalid storage location: {storage_location}")
        return
    if not os.path.exists(os.path.join(starting_dir, Config.COMPLETED_DIR_NAME)):
        os.makedirs(os.path.join(starting_dir, Config.COMPLETED_DIR_NAME))
    for item in os.listdir(starting_dir):
        item_path = os.path.join(starting_dir, item)
        if os.path.isdir(item_path) and item in ignored_folders:
            if verbosity.value >= Verbosity.NORMAL.value:
                print(f"[NORMAL] Skipping ignored folder: {item_path}")
            continue
        process_directory(item_path, starting_dir, verbosity)

class VideoFormatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Video Formats")
        self.setModal(True)

        # Create layout
        layout = QFormLayout(self)

        # Input format dropdown
        self.input_format = QComboBox()
        self.input_format.addItems(["mkv", "mp4", "avi", "mov", "flv", "wmv"])
        layout.addRow("Input Format:", self.input_format)

        # Output format dropdown
        self.output_format = QComboBox()
        self.output_format.addItems(["mp4", "mkv", "avi", "mov", "flv", "wmv"])
        layout.addRow("Output Format:", self.output_format)

        # OK and Cancel buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

    def get_formats(self):
        return self.input_format.currentText(), self.output_format.currentText()

class ManageIgnoredFoldersDialog(QDialog):
    def __init__(self, ignored_folders, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Ignored Folders")
        self.setModal(True)

        # Create layout
        layout = QVBoxLayout(self)

        # Ignored Folders List
        self.ignored_folders_list = QListWidget()
        self.ignored_folders_list.addItems(ignored_folders)
        layout.addWidget(self.ignored_folders_list)

        # Add Ignored Folder Button
        self.add_button = QPushButton("Add Ignored Folder")
        self.add_button.clicked.connect(self.add_ignored_folder)
        layout.addWidget(self.add_button)

        # Remove Selected Folder Button
        self.remove_button = QPushButton("Remove Selected Folder")
        self.remove_button.clicked.connect(self.remove_ignored_folder)
        layout.addWidget(self.remove_button)

        # Close Button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

    def add_ignored_folder(self):
        """Opens a dialog to add a folder to the ignored list."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Ignore")
        if folder:
            folder_name = os.path.basename(folder)
            if folder_name not in [self.ignored_folders_list.item(i).text() for i in range(self.ignored_folders_list.count())]:
                self.ignored_folders_list.addItem(folder_name)

    def remove_ignored_folder(self):
        """Removes the selected folder from the ignored list."""
        selected_item = self.ignored_folders_list.currentItem()
        if selected_item:
            self.ignored_folders_list.takeItem(self.ignored_folders_list.row(selected_item))

    def get_ignored_folders(self):
        """Returns the updated list of ignored folders."""
        return [self.ignored_folders_list.item(i).text() for i in range(self.ignored_folders_list.count())]

class DirectorySelectionDialog(QDialog):
    def __init__(self, starting_dir, storage_location, converted_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Directory Selection")
        self.setModal(True)

        # Create layout
        layout = QFormLayout(self)

        # Starting Directory
        self.starting_dir_label = QLabel("Starting Directory:")
        self.starting_dir_entry = QLineEdit()
        self.starting_dir_entry.setText(starting_dir)
        self.starting_dir_button = QPushButton("Browse")
        self.starting_dir_button.clicked.connect(lambda: self.select_directory(self.starting_dir_entry))
        layout.addRow(self.starting_dir_label, self.starting_dir_entry)
        layout.addRow(self.starting_dir_button)

        # Storage Location
        self.storage_location_label = QLabel("Storage Location:")
        self.storage_location_entry = QLineEdit()
        self.storage_location_entry.setText(storage_location)
        self.storage_location_button = QPushButton("Browse")
        self.storage_location_button.clicked.connect(lambda: self.select_directory(self.storage_location_entry))
        layout.addRow(self.storage_location_label, self.storage_location_entry)
        layout.addRow(self.storage_location_button)

        # Converted Directory
        self.converted_dir_label = QLabel("Converted Directory:")
        self.converted_dir_entry = QLineEdit()
        self.converted_dir_entry.setText(converted_dir)
        self.converted_dir_button = QPushButton("Browse")
        self.converted_dir_button.clicked.connect(lambda: self.select_directory(self.converted_dir_entry))
        layout.addRow(self.converted_dir_label, self.converted_dir_entry)
        layout.addRow(self.converted_dir_button)

        # OK and Cancel Buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

    def select_directory(self, entry_widget):
        """Opens a dialog to select a directory and updates the entry widget."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            entry_widget.setText(directory)

    def get_directories(self):
        """Returns the selected directories."""
        return (
            self.starting_dir_entry.text(),
            self.storage_location_entry.text(),
            self.converted_dir_entry.text()
        )

class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setModal(True)

        # Create layout
        layout = QVBoxLayout(self)

        # Verbosity Level
        self.verbosity_label = QLabel("Verbosity Level:")
        self.verbosity_combo = QComboBox()
        self.verbosity_combo.addItems(["Silent", "Destination", "Normal", "Verbose"])
        layout.addWidget(self.verbosity_label)
        layout.addWidget(self.verbosity_combo)

        # File Deletion Options
        self.delete_originals_checkbox = QCheckBox("Delete Original Files After Processing")
        layout.addWidget(self.delete_originals_checkbox)

        # Custom FFmpeg Arguments
        self.ffmpeg_args_label = QLabel("Custom FFmpeg Arguments:")
        self.ffmpeg_args_entry = QLineEdit()
        self.ffmpeg_args_entry.setPlaceholderText("e.g., -c:v libx264 -crf 23 -preset fast")
        layout.addWidget(self.ffmpeg_args_label)
        layout.addWidget(self.ffmpeg_args_entry)

        # Batch Size Control
        self.batch_size_label = QLabel("Batch Size (Files to Process at Once):")
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(1, 100)
        self.batch_size_spinbox.setValue(10)
        layout.addWidget(self.batch_size_label)
        layout.addWidget(self.batch_size_spinbox)

        # File Overwrite Options
        self.overwrite_checkbox = QCheckBox("Overwrite Existing Files")
        layout.addWidget(self.overwrite_checkbox)

        # Custom Output Directory
        self.output_dir_button = QPushButton("Select Custom Output Directory")
        self.output_dir_button.clicked.connect(self.select_output_directory)
        layout.addWidget(self.output_dir_button)

        # File Filtering Options
        self.filter_button = QPushButton("Set File Filters")
        self.filter_button.clicked.connect(self.set_file_filters)
        layout.addWidget(self.filter_button)

        # Custom Naming Patterns
        self.naming_pattern_button = QPushButton("Set Custom Naming Patterns")
        self.naming_pattern_button.clicked.connect(self.set_naming_patterns)
        layout.addWidget(self.naming_pattern_button)

        # Error Handling Options
        self.error_handling_button = QPushButton("Set Error Handling Preferences")
        self.error_handling_button.clicked.connect(self.set_error_handling)
        layout.addWidget(self.error_handling_button)

        # Preview Changes
        self.preview_button = QPushButton("Preview Changes")
        self.preview_button.clicked.connect(self.preview_changes)
        layout.addWidget(self.preview_button)

        # Fuse TS Files Button
        self.fuse_button = QPushButton("Fuse TS Files")
        self.fuse_button.clicked.connect(self.fuse_ts_files_gui)
        layout.addWidget(self.fuse_button)

        # Process TS Directory Button
        self.process_ts_button = QPushButton("Process TS Directory")
        self.process_ts_button.clicked.connect(self.process_ts_directory_gui)
        layout.addWidget(self.process_ts_button)

        # Delete .m3u8 Folders Button
        self.delete_folders_button = QPushButton("Delete .m3u8 Folders")
        self.delete_folders_button.clicked.connect(self.delete_m3u8_folders_gui)
        layout.addWidget(self.delete_folders_button)

        # Convert Video Formats Button
        self.convert_formats_button = QPushButton("Convert Video Formats")
        self.convert_formats_button.clicked.connect(self.convert_video_formats)
        layout.addWidget(self.convert_formats_button)

        # Save Settings Button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)

    def select_output_directory(self):
        """Opens a dialog to select a custom output directory."""
        output_dir = QFileDialog.getExistingDirectory(self, "Select Custom Output Directory")
        if output_dir:
            self.output_dir = output_dir
            QMessageBox.information(self, "Output Directory Set", f"Output directory set to: {output_dir}")

    def set_file_filters(self):
        """Opens a dialog to set file filters."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Set File Filters")
        layout = QFormLayout(dialog)

        # File Size Filter
        self.size_filter_checkbox = QCheckBox("Filter by File Size")
        self.size_filter_min = QLineEdit()
        self.size_filter_min.setPlaceholderText("Min size (MB)")
        self.size_filter_max = QLineEdit()
        self.size_filter_max.setPlaceholderText("Max size (MB)")
        layout.addRow(self.size_filter_checkbox)
        layout.addRow("Min Size (MB):", self.size_filter_min)
        layout.addRow("Max Size (MB):", self.size_filter_max)

        # File Extension Filter
        self.extension_filter_checkbox = QCheckBox("Filter by File Extension")
        self.extension_filter_entry = QLineEdit()
        self.extension_filter_entry.setPlaceholderText("e.g., .mkv, .mp4")
        layout.addRow(self.extension_filter_checkbox)
        layout.addRow("Extensions:", self.extension_filter_entry)

        # Date Modified Filter
        self.date_filter_checkbox = QCheckBox("Filter by Date Modified")
        self.date_filter_start = QDateEdit()
        self.date_filter_start.setCalendarPopup(True)
        self.date_filter_end = QDateEdit()
        self.date_filter_end.setCalendarPopup(True)
        layout.addRow(self.date_filter_checkbox)
        layout.addRow("Start Date:", self.date_filter_start)
        layout.addRow("End Date:", self.date_filter_end)

        # Save Filters Button
        save_button = QPushButton("Save Filters")
        save_button.clicked.connect(dialog.accept)
        layout.addRow(save_button)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Filters Set", "File filters have been applied.")

    def set_naming_patterns(self):
        """Opens a dialog to set custom naming patterns."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Custom Naming Patterns")
        layout = QFormLayout(dialog)

        # Naming Pattern Entry
        self.naming_pattern_entry = QLineEdit()
        self.naming_pattern_entry.setPlaceholderText("e.g., S{season}E{episode}.mkv")
        layout.addRow("Naming Pattern:", self.naming_pattern_entry)

        # Save Pattern Button
        save_button = QPushButton("Save Pattern")
        save_button.clicked.connect(dialog.accept)
        layout.addRow(save_button)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Pattern Set", "Custom naming pattern has been applied.")

    def set_error_handling(self):
        """Opens a dialog to set error handling preferences."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Error Handling Preferences")
        layout = QFormLayout(dialog)

        # Error Handling Options
        self.error_handling_combo = QComboBox()
        self.error_handling_combo.addItems(["Skip", "Retry", "Abort"])
        layout.addRow("On Error:", self.error_handling_combo)

        # Save Preferences Button
        save_button = QPushButton("Save Preferences")
        save_button.clicked.connect(dialog.accept)
        layout.addRow(save_button)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Preferences Set", "Error handling preferences have been applied.")

    def preview_changes(self):
        """Opens a dialog to preview changes."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Preview Changes")
        layout = QVBoxLayout(dialog)

        # Preview List
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)

        # Populate Preview List
        starting_dir = self.parent().starting_dir_entry.text()
        if is_valid_directory(starting_dir):
            for root, _, files in os.walk(starting_dir):
                for file in files:
                    if file.endswith(".mkv"):
                        self.preview_list.addItem(f"Rename: {file} -> S01E01.mkv")

        # Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def fuse_ts_files_gui(self):
        """Handles the GUI for fusing TS files."""
        m3u8_file, _ = QFileDialog.getOpenFileName(self, "Select m3u8 File", "", "m3u8 files (*.m3u8)")
        if not m3u8_file:
            return

        key_file, _ = QFileDialog.getOpenFileName(self, "Select Key File", "", "key files (*.key)")
        if not key_file:
            return

        output_file = os.path.splitext(m3u8_file)[0] + ".mp4"

        try:
            with open(key_file, "rb") as f:
                key_data = f.read()

            if fuse_ts_files(m3u8_file, key_data, output_file, self.get_verbosity_level()):
                QMessageBox.information(self, "Fusion Complete", f"TS files fused to: {output_file}")
            else:
                QMessageBox.critical(self, "Fusion Failed", "Failed to fuse TS files.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Key File Error", "Key file not found.")

    def process_ts_directory_gui(self):
        """Handles the GUI for processing a directory of TS files."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Process")
        if not directory:
            return

        verbosity = self.get_verbosity_level()
        delete_originals = self.should_delete_originals()

        def process_m3u8_files(root_dir):
            for root, dirs, files in os.walk(root_dir):
                for file in files:
                    if file.endswith(".m3u8"):
                        m3u8_path = os.path.join(root, file)
                        dir_name = os.path.basename(root)

                        # Extract episode number
                        episode_number = dir_name[:-5] if dir_name.endswith(".m3u8") else dir_name

                        # Construct output file name
                        output_file_name = f"S1E{episode_number}.mp4"
                        output_file = os.path.join(root, output_file_name)

                        # Check for key file
                        key_file = os.path.join(root, "media.key")
                        if os.path.exists(key_file):
                            try:
                                with open(key_file, "rb") as f:
                                    key_data = f.read()
                                if fuse_ts_files(m3u8_path, key_data, output_file, verbosity):
                                    print(f"Successfully processed: {m3u8_path}")
                                    parent_dir = os.path.dirname(root)
                                    shutil.move(output_file, os.path.join(parent_dir, output_file_name))
                                    print(f"Moved {output_file_name} to {parent_dir}")
                                    if delete_originals:
                                        shutil.rmtree(root)
                                        print(f"Deleted original folder: {root}")
                                else:
                                    print(f"Failed to process: {m3u8_path}")
                            except FileNotFoundError:
                                print(f"Key file not found: {key_file}")
                            except Exception as e:
                                print(f"An error occurred processing {m3u8_path}: {e}")
                        else:
                            if fuse_ts_files(m3u8_path, None, output_file, verbosity):
                                print(f"Successfully processed: {m3u8_path} (No key file found, assuming unencrypted)")
                                parent_dir = os.path.dirname(root)
                                shutil.move(output_file, os.path.join(parent_dir, output_file_name))
                                print(f"Moved {output_file_name} to {parent_dir}")
                                if delete_originals:
                                    shutil.rmtree(root)
                                    print(f"Deleted original folder: {root}")
                            else:
                                print(f"Failed to process: {m3u8_path}")

        process_m3u8_files(directory)
        QMessageBox.information(self, "Processing Complete", "All m3u8 files have been processed.")

    def delete_m3u8_folders_gui(self):
        """Handles the GUI for deleting .m3u8 folders."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Process")
        if not directory:
            return

        def delete_m3u8_folders(root_dir):
            for root, dirs, files in os.walk(root_dir, topdown=False):
                for dir_name in dirs:
                    full_dir_path = os.path.join(root, dir_name)
                    if dir_name.endswith(".m3u8"):
                        try:
                            shutil.rmtree(full_dir_path)
                            print(f"Deleted folder: {full_dir_path}")
                        except Exception as e:
                            print(f"Error deleting {full_dir_path}: {e}")

        delete_m3u8_folders(directory)
        QMessageBox.information(self, "Deletion Complete", "All .m3u8 folders have been deleted.")

    def convert_video_formats(self):
        """Handles the GUI for converting video formats."""
        dialog = VideoFormatDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            input_format, output_format = dialog.get_formats()
            QMessageBox.information(self, "Formats Selected", f"Input Format: {input_format}\nOutput Format: {output_format}")

            # Process all files with the selected input format
            starting_dir = self.parent().starting_dir_entry.text()
            if not is_valid_directory(starting_dir):
                QMessageBox.critical(self, "Error", "Invalid starting directory.")
                return

            for root, _, files in os.walk(starting_dir):
                for file in files:
                    if file.endswith(f".{input_format}"):
                        input_file = os.path.join(root, file)
                        output_file = os.path.join(root, os.path.splitext(file)[0] + f".{output_format}")
                        if convert_video(input_file, output_file, self.get_verbosity_level()):
                            print(f"[SUCCESS] Converted {input_file} to {output_file}")
                            if self.should_delete_originals():
                                os.remove(input_file)
                                print(f"[INFO] Deleted original file: {input_file}")
                        else:
                            print(f"[ERROR] Failed to convert {input_file} to {output_file}")

            QMessageBox.information(self, "Conversion Complete", "All video files have been converted.")

    def save_settings(self):
        """Saves the advanced settings to the config file."""
        settings = {
            "verbosity": self.verbosity_combo.currentText(),
            "delete_originals": str(self.should_delete_originals()),
            "ffmpeg_args": self.get_custom_ffmpeg_args(),
            "batch_size": str(self.get_batch_size()),
            "overwrite_files": str(self.should_overwrite_files()),
        }
        config.save_settings(settings)
        QMessageBox.information(self, "Settings Saved", "Advanced settings have been saved.")

    def get_verbosity_level(self):
        """Returns the selected verbosity level as a Verbosity enum."""
        verbosity_text = self.verbosity_combo.currentText()
        if verbosity_text == "Silent":
            return Verbosity.SILENT
        elif verbosity_text == "Destination":
            return Verbosity.DESTINATION
        elif verbosity_text == "Normal":
            return Verbosity.NORMAL
        elif verbosity_text == "Verbose":
            return Verbosity.VERBOSE
        return Verbosity.NORMAL

    def should_delete_originals(self):
        """Returns whether the user wants to delete original files after processing."""
        return self.delete_originals_checkbox.isChecked()

    def get_custom_ffmpeg_args(self):
        """Returns the custom FFmpeg arguments entered by the user."""
        return self.ffmpeg_args_entry.text()

    def get_batch_size(self):
        """Returns the batch size selected by the user."""
        return self.batch_size_spinbox.value()

    def should_overwrite_files(self):
        """Returns whether the user wants to overwrite existing files."""
        return self.overwrite_checkbox.isChecked()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MKV Renamer and Mover")
        self.setGeometry(100, 100, 800, 600)

        # Load settings
        self.settings = config.load_settings()
        self.starting_dir, self.storage_location, self.ignored_folders = get_saved_paths(self.settings)

        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Directory Selection Button
        self.directory_button = QPushButton("Select Directories")
        self.directory_button.clicked.connect(self.select_directories)
        scroll_layout.addWidget(self.directory_button)

        # Manage Ignored Folders Button
        self.manage_ignored_button = QPushButton("Manage Ignored Folders")
        self.manage_ignored_button.clicked.connect(self.manage_ignored_folders)
        scroll_layout.addWidget(self.manage_ignored_button)

        # Start Processing Button
        self.start_button = QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_processing)
        scroll_layout.addWidget(self.start_button)

        # Advanced Settings Button
        self.advanced_settings_button = QPushButton("Advanced Settings")
        self.advanced_settings_button.clicked.connect(self.open_advanced_settings)
        scroll_layout.addWidget(self.advanced_settings_button)

    def select_directories(self):
        """Opens a dialog to select directories."""
        dialog = DirectorySelectionDialog(
            self.starting_dir,
            self.storage_location,
            Config.CONVERTED_DIR,
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.starting_dir, self.storage_location, Config.CONVERTED_DIR = dialog.get_directories()

    def manage_ignored_folders(self):
        """Opens a dialog to manage ignored folders."""
        dialog = ManageIgnoredFoldersDialog(self.ignored_folders, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.ignored_folders = dialog.get_ignored_folders()

    def start_processing(self):
        """Starts the processing of files."""
        self.settings["starting_dir"] = self.starting_dir
        self.settings["storage_location"] = self.storage_location
        self.settings["ignored_folders"] = ";".join(self.ignored_folders)
        config.save_settings(self.settings)

        process_selected_directory(self.starting_dir, self.storage_location, self.ignored_folders, Verbosity.NORMAL)
        QMessageBox.information(self, "Processing Complete", "MKV files have been processed.")

    def open_advanced_settings(self):
        """Opens the advanced settings dialog."""
        dialog = AdvancedSettingsDialog(self)
        dialog.exec()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
