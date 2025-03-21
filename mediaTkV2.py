import os
import re
import shutil
import sys
import configparser
import ffmpeg
from enum import Enum
from tkinter import (
    Tk, Label, Entry, Button, Listbox, Scrollbar, messagebox, filedialog, simpledialog, Toplevel, Checkbutton,
    Spinbox, StringVar, IntVar, OptionMenu, Frame
)

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

class DirectorySelectionDialog(simpledialog.Dialog):
    def __init__(self, parent, starting_dir, storage_location, converted_dir):
        self.starting_dir = starting_dir
        self.storage_location = storage_location
        self.converted_dir = converted_dir
        super().__init__(parent, "Directory Selection")

    def body(self, master):
        Label(master, text="Starting Directory:").grid(row=0, column=0, sticky="w")
        self.starting_dir_entry = Entry(master, width=50)
        self.starting_dir_entry.insert(0, self.starting_dir)
        self.starting_dir_entry.grid(row=0, column=1)
        Button(master, text="Browse", command=lambda: self.select_directory(self.starting_dir_entry)).grid(row=0, column=2)

        Label(master, text="Storage Location:").grid(row=1, column=0, sticky="w")
        self.storage_location_entry = Entry(master, width=50)
        self.storage_location_entry.insert(0, self.storage_location)
        self.storage_location_entry.grid(row=1, column=1)
        Button(master, text="Browse", command=lambda: self.select_directory(self.storage_location_entry)).grid(row=1, column=2)

        Label(master, text="Converted Directory:").grid(row=2, column=0, sticky="w")
        self.converted_dir_entry = Entry(master, width=50)
        self.converted_dir_entry.insert(0, self.converted_dir)
        self.converted_dir_entry.grid(row=2, column=1)
        Button(master, text="Browse", command=lambda: self.select_directory(self.converted_dir_entry)).grid(row=2, column=2)

        return self.starting_dir_entry

    def select_directory(self, entry_widget):
        """Opens a dialog to select a directory and updates the entry widget."""
        directory = filedialog.askdirectory()
        if directory:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, directory)

    def apply(self):
        """Saves the selected directories."""
        self.starting_dir = self.starting_dir_entry.get()
        self.storage_location = self.storage_location_entry.get()
        self.converted_dir = self.converted_dir_entry.get()

    def get_directories(self):
        """Returns the selected directories."""
        return self.starting_dir, self.storage_location, self.converted_dir

class ManageIgnoredFoldersDialog(simpledialog.Dialog):
    def __init__(self, parent, ignored_folders):
        self.ignored_folders = ignored_folders
        super().__init__(parent, "Manage Ignored Folders")

    def body(self, master):
        self.ignored_folders_list = Listbox(master, width=50, height=10)
        self.ignored_folders_list.grid(row=0, column=0, columnspan=2)
        for folder in self.ignored_folders:
            self.ignored_folders_list.insert("end", folder)

        Button(master, text="Add Folder", command=self.add_ignored_folder).grid(row=1, column=0)
        Button(master, text="Remove Folder", command=self.remove_ignored_folder).grid(row=1, column=1)

        return self.ignored_folders_list

    def add_ignored_folder(self):
        """Opens a dialog to add a folder to the ignored list."""
        folder = filedialog.askdirectory()
        if folder:
            folder_name = os.path.basename(folder)
            if folder_name not in self.ignored_folders_list.get(0, "end"):
                self.ignored_folders_list.insert("end", folder_name)

    def remove_ignored_folder(self):
        """Removes the selected folder from the ignored list."""
        selected = self.ignored_folders_list.curselection()
        if selected:
            self.ignored_folders_list.delete(selected)

    def apply(self):
        """Saves the updated list of ignored folders."""
        self.ignored_folders = list(self.ignored_folders_list.get(0, "end"))

    def get_ignored_folders(self):
        """Returns the updated list of ignored folders."""
        return self.ignored_folders

class AdvancedSettingsDialog(simpledialog.Dialog):
    def __init__(self, parent):
        super().__init__(parent, "Advanced Settings")

    def body(self, master):
        Label(master, text="Verbosity Level:").grid(row=0, column=0, sticky="w")
        self.verbosity_var = StringVar(value="Normal")
        OptionMenu(master, self.verbosity_var, "Silent", "Destination", "Normal", "Verbose").grid(row=0, column=1)

        self.delete_originals_var = IntVar(value=0)
        Checkbutton(master, text="Delete Original Files After Processing", variable=self.delete_originals_var).grid(row=1, column=0, columnspan=2, sticky="w")

        Label(master, text="Custom FFmpeg Arguments:").grid(row=2, column=0, sticky="w")
        self.ffmpeg_args_entry = Entry(master, width=50)
        self.ffmpeg_args_entry.grid(row=2, column=1)

        Label(master, text="Batch Size (Files to Process at Once):").grid(row=3, column=0, sticky="w")
        self.batch_size_spinbox = Spinbox(master, from_=1, to=100, width=5)
        self.batch_size_spinbox.grid(row=3, column=1, sticky="w")

        self.overwrite_var = IntVar(value=0)
        Checkbutton(master, text="Overwrite Existing Files", variable=self.overwrite_var).grid(row=4, column=0, columnspan=2, sticky="w")

        return self.ffmpeg_args_entry

    def apply(self):
        """Saves the advanced settings."""
        self.verbosity = self.verbosity_var.get()
        self.delete_originals = self.delete_originals_var.get()
        self.ffmpeg_args = self.ffmpeg_args_entry.get()
        self.batch_size = int(self.batch_size_spinbox.get())
        self.overwrite = self.overwrite_var.get()

    def get_settings(self):
        """Returns the advanced settings."""
        return {
            "verbosity": self.verbosity,
            "delete_originals": self.delete_originals,
            "ffmpeg_args": self.ffmpeg_args,
            "batch_size": self.batch_size,
            "overwrite": self.overwrite,
        }

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("MKV Renamer and Mover")
        self.root.geometry("800x600")

        # Load settings
        self.settings = config.load_settings()
        self.starting_dir, self.storage_location, self.ignored_folders = get_saved_paths(self.settings)

        # Create a central frame
        self.frame = Frame(self.root)
        self.frame.pack(fill="both", expand=True)

        # Directory Selection Button
        self.directory_button = Button(self.frame, text="Select Directories", command=self.select_directories)
        self.directory_button.pack(pady=10)

        # Manage Ignored Folders Button
        self.manage_ignored_button = Button(self.frame, text="Manage Ignored Folders", command=self.manage_ignored_folders)
        self.manage_ignored_button.pack(pady=10)

        # Start Processing Button
        self.start_button = Button(self.frame, text="Start Processing", command=self.start_processing)
        self.start_button.pack(pady=10)

        # Advanced Settings Button
        self.advanced_settings_button = Button(self.frame, text="Advanced Settings", command=self.open_advanced_settings)
        self.advanced_settings_button.pack(pady=10)

    def select_directories(self):
        """Opens a dialog to select directories."""
        dialog = DirectorySelectionDialog(self.root, self.starting_dir, self.storage_location, Config.CONVERTED_DIR)
        if dialog.result:
            self.starting_dir, self.storage_location, Config.CONVERTED_DIR = dialog.get_directories()

    def manage_ignored_folders(self):
        """Opens a dialog to manage ignored folders."""
        dialog = ManageIgnoredFoldersDialog(self.root, self.ignored_folders)
        if dialog.result:
            self.ignored_folders = dialog.get_ignored_folders()

    def start_processing(self):
        """Starts the processing of files."""
        self.settings["starting_dir"] = self.starting_dir
        self.settings["storage_location"] = self.storage_location
        self.settings["ignored_folders"] = ";".join(self.ignored_folders)
        config.save_settings(self.settings)

        process_selected_directory(self.starting_dir, self.storage_location, self.ignored_folders, Verbosity.NORMAL)
        messagebox.showinfo("Processing Complete", "MKV files have been processed.")

    def open_advanced_settings(self):
        """Opens the advanced settings dialog."""
        dialog = AdvancedSettingsDialog(self.root)
        if dialog.result:
            settings = dialog.get_settings()
            print("Advanced Settings:", settings)

def main():
    root = Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
