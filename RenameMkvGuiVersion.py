#--- this version requires you to do pip install ffmpeg-python
#--- you also need to do pip install psutil

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox
import configparser
import ffmpeg
from enum import Enum

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

def convert_mkv_to_mp4(mkv_file, converted_dir, verbosity=Verbosity.NORMAL):
    output_filename = os.path.splitext(os.path.basename(mkv_file))[0] + ".mp4"
    output_file = os.path.join(converted_dir, output_filename)
    encoders = [
        {'c:v': 'libx264', 'c:a': 'aac'},
        {'c:v': 'libx265', 'c:a': 'aac'},
        {'c:v': 'libvpx-vp9', 'c:a': 'libopus'},
        {'c:v': 'libaom-av1', 'c:a': 'libopus'},
        {'c:v': 'copy', 'c:a': 'copy'},
    ]
    for encoder_options in encoders:
        try:
            input_stream = ffmpeg.input(mkv_file)
            output_stream = input_stream.output(output_file, loglevel='error', **encoder_options)
            output_stream.run(overwrite_output=True)
            if verbosity.value >= Verbosity.VERBOSE.value:
                print(f"[VERBOSE] Converted: {mkv_file} to {output_file} using options: {encoder_options}")
            return output_file
        except ffmpeg.Error as e:
            if verbosity.value >= Verbosity.NORMAL.value:
                print(f"[NORMAL] ffmpeg failed for {mkv_file} with options {encoder_options}: {e.stderr.decode()}")
        except Exception as e:
            if verbosity.value >= Verbosity.NORMAL.value:
                print(f"[NORMAL] Error converting {mkv_file} with options {encoder_options}: {e}")
    if verbosity.value >= Verbosity.NORMAL.value:
        print(f"[NORMAL] Failed to convert {mkv_file} with all encoder options.")
    return None

def get_saved_paths(settings):
    starting_dir = settings.get("starting_dir")
    storage_location = settings.get("storage_location")
    ignored_folders_str = settings.get("ignored_folders", "")
    ignored_folders = ignored_folders_str.split(";") if ignored_folders_str else []
    return starting_dir, storage_location, ignored_folders

def validate_and_prompt(path, title):
    while path is None or not is_valid_directory(path):
        path = filedialog.askdirectory(title=title)
        if not path:
            exit()
    return path

def process_directory_item(item_path, base_dir, season_number, verbosity=Verbosity.NORMAL):
    if os.path.isdir(item_path):
        process_directory(item_path, base_dir, verbosity)
    elif item_path.endswith((".mkv", ".mp4")):
        process_mkv_file(item_path, base_dir, season_number, verbosity)
    elif item_path.endswith(".m3u8"):
        m3u8_name = os.path.splitext(os.path.basename(item_path))[0]
        key_path = os.path.join(os.path.dirname(item_path), "media.key")
        output_path = os.path.join(os.path.dirname(item_path), f"{m3u8_name}.mp4")
        if os.path.exists(key_path):
            try:
                with open(key_path, "rb") as key_file:
                    key_data = key_file.read()
                if fuse_ts_files(item_path, key_data, output_path, verbosity):
                    new_output_path = os.path.join(os.path.dirname(os.path.dirname(item_path)), os.path.basename(output_path))
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
                new_output_path = os.path.join(os.path.dirname(os.path.dirname(item_path)), os.path.basename(output_path))
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

def process_mkv_file(file_path, base_dir, season_number, verbosity=Verbosity.NORMAL):
    renamed_file = rename_mkv(file_path, season_number, verbosity)
    if renamed_file:
        move_mkv(renamed_file, base_dir, verbosity)
        return True
    return False

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
                print(f"[NORMAL] FFmpeg error with options {options}: {e.stderr.decode()}")
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

def delete_m3u8_folders_gui():
    directory = filedialog.askdirectory(title="Select Directory to Process")
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
    messagebox.showinfo("Deletion Complete", "All .m3u8 folders have been deleted.")

def process_directory_gui():
    directory = filedialog.askdirectory(title="Select Directory to Process")
    if not directory:
        return
    def process_m3u8_files(root_dir):
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".m3u8"):
                    m3u8_path = os.path.join(root, file)
                    file_name_without_ext = os.path.splitext(file)[0]
                    if file == "media.m3u8":
                        dir_name = os.path.basename(root)
                        if dir_name.endswith(".m3u8"):
                            dir_name = dir_name[:-5]
                        output_file_name = dir_name + ".mp4"
                    else:
                        output_file_name = file_name_without_ext + ".mp4"
                    output_file = os.path.join(root, output_file_name)
                    key_file = os.path.join(root, "media.key")
                    if os.path.exists(key_file):
                        try:
                            with open(key_file, "rb") as f:
                                key_data = f.read()
                            if fuse_ts_files(m3u8_path, key_data, output_file, Verbosity.NORMAL):
                                print(f"Successfully processed: {m3u8_path}")
                                parent_dir = os.path.dirname(root)
                                shutil.move(output_file, os.path.join(parent_dir, output_file_name))
                                print(f"Moved {output_file_name} to {parent_dir}")
                            else:
                                print(f"Failed to process: {m3u8_path}")
                        except FileNotFoundError:
                            print(f"Key file not found: {key_file}")
                        except Exception as e:
                            print(f"An error occurred processing {m3u8_path}: {e}")
                    else:
                        if fuse_ts_files(m3u8_path, None, output_file, Verbosity.NORMAL):
                            print(f"Successfully processed: {m3u8_path} (No key file found, assuming unencrypted)")
                            parent_dir = os.path.dirname(root)
                            shutil.move(output_file, os.path.join(parent_dir, output_file_name))
                            print(f"Moved {output_file_name} to {parent_dir}")
                        else:
                            print(f"Failed to process: {m3u8_path}")
    process_m3u8_files(directory)
    messagebox.showinfo("Processing Complete", "All m3u8 files have been processed.")

def run_gui():
    settings = config.load_settings()
    starting_dir, storage_location, ignored_folders = get_saved_paths(settings)

    def select_starting_directory():
        nonlocal starting_dir
        starting_dir = filedialog.askdirectory(title="Select Starting Directory")
        if starting_dir:
            starting_dir_entry.delete(0, tk.END)
            starting_dir_entry.insert(0, starting_dir)

    def select_storage_location():
        nonlocal storage_location
        storage_location = filedialog.askdirectory(title="Select Storage Location")
        if storage_location:
            storage_location_entry.delete(0, tk.END)
            storage_location_entry.insert(0, storage_location)

    def select_converted_directory():
        Config.CONVERTED_DIR = filedialog.askdirectory(title="Select Converted Directory")
        if Config.CONVERTED_DIR:
            converted_dir_entry.delete(0, tk.END)
            converted_dir_entry.insert(0, Config.CONVERTED_DIR)

    def add_ignored_folder():
        ignored_folder = filedialog.askdirectory(title="Select Ignored Folder")
        if ignored_folder:
            folder_name = os.path.basename(ignored_folder)
            if folder_name not in ignored_folders:
                ignored_folders.append(folder_name)
                ignored_folders_list.insert(tk.END, folder_name)

    def remove_ignored_folder():
        selected_index = ignored_folders_list.curselection()
        if selected_index:
            ignored_folders.pop(selected_index[0])
            ignored_folders_list.delete(selected_index[0])

    def start_processing():
        nonlocal starting_dir, storage_location, ignored_folders
        starting_dir = starting_dir_entry.get()
        storage_location = storage_location_entry.get()
        settings["starting_dir"] = starting_dir
        settings["storage_location"] = storage_location
        settings["ignored_folders"] = ";".join(ignored_folders)
        config.save_settings(settings)

        process_selected_directory(starting_dir, storage_location, ignored_folders, Verbosity.NORMAL)
        messagebox.showinfo("Processing Complete", "MKV files have been processed.")

    def fuse_ts_files_gui():
        m3u8_file = filedialog.askopenfilename(title="Select m3u8 File", filetypes=[("m3u8 files", "*.m3u8")])
        if not m3u8_file:
            return

        key_file = filedialog.askopenfilename(title="Select Key File", filetypes=[("key files", "*.key")])
        if not key_file:
            return

        output_file = os.path.splitext(m3u8_file)[0] + ".mp4"

        try:
            with open(key_file, "rb") as f:
                key_data = f.read()

            if fuse_ts_files(m3u8_file, key_data, output_file, Verbosity.NORMAL):
                messagebox.showinfo("Fusion Complete", f"TS files fused to: {output_file}")
            else:
                messagebox.showerror("Fusion Failed", "Failed to fuse TS files.")
        except FileNotFoundError:
            messagebox.showerror("Key File Error", "Key file not found.")

    root = tk.Tk()
    root.title("MKV Renamer and Mover")

    starting_dir_label = tk.Label(root, text="Starting Directory:")
    starting_dir_label.pack()
    starting_dir_entry = tk.Entry(root, width=50)
    starting_dir_entry.pack()
    if starting_dir:
        starting_dir_entry.insert(0, starting_dir)
    starting_dir_button = tk.Button(root, text="Browse", command=select_starting_directory)
    starting_dir_button.pack()

    storage_location_label = tk.Label(root, text="Storage Location:")
    storage_location_label.pack()
    storage_location_entry = tk.Entry(root, width=50)
    storage_location_entry.pack()
    if storage_location:
        storage_location_entry.insert(0, storage_location)
    storage_location_button = tk.Button(root, text="Browse", command=select_storage_location)
    storage_location_button.pack()

    converted_dir_label = tk.Label(root, text="Converted Directory:")
    converted_dir_label.pack()
    converted_dir_entry = tk.Entry(root, width=50)
    converted_dir_entry.pack()
    if Config.CONVERTED_DIR:
        converted_dir_entry.insert(0, Config.CONVERTED_DIR)
    converted_dir_button = tk.Button(root, text="Browse", command=select_converted_directory)
    converted_dir_button.pack()

    ignored_folders_label = tk.Label(root, text="Ignored Folders:")
    ignored_folders_label.pack()
    ignored_folders_list = Listbox(root, width=50, selectmode=tk.SINGLE)
    for folder in ignored_folders:
        ignored_folders_list.insert(tk.END, folder)
    ignored_folders_list.pack()
    add_ignored_button = tk.Button(root, text="Add Ignored Folder", command=add_ignored_folder)
    add_ignored_button.pack()
    remove_ignored_button = tk.Button(root, text="Remove Selected Folder", command=remove_ignored_folder)
    remove_ignored_button.pack()

    start_button = tk.Button(root, text="Start Processing", command=start_processing)
    start_button.pack(pady=20)

    fuse_button = tk.Button(root, text="Fuse TS Files", command=fuse_ts_files_gui)
    fuse_button.pack(pady=10)

    manual_ts_button = tk.Button(root, text="Process TS Directory", command=process_directory_gui)
    manual_ts_button.pack(pady=20)

    delete_folders_button = tk.Button(root, text="Delete .m3u8 Folders", command=delete_m3u8_folders_gui)
    delete_folders_button.pack(pady=10)

    root.mainloop()

def main():
    run_gui()

if __name__ == "__main__":
    main()
