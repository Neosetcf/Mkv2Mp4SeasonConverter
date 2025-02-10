import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import configparser
import subprocess
import multiprocessing

# --- Configuration and Constants ---
CONFIG_DIR = os.path.expanduser("~/RenameMkv")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.ini")
CONVERTED_DIR_NAME = "CONVERTED_MKV"
COMPLETED_DIR_NAME = "Completed"

# Verbosity Levels:
SILENT = 0
DESTINATION = 1
NORMAL = 2
VERBOSE = 3

# --- Helper Functions ---

def is_folder_empty(folder_path, verbosity=NORMAL):
    is_empty = not any(os.scandir(folder_path))
    if verbosity >= VERBOSE:
        print(f"[VERBOSE] Checking if folder '{folder_path}' is empty: {is_empty}")
    return is_empty

def get_mkv_filenames(target_folder, verbosity=NORMAL):
    filenames = {os.path.splitext(f)[0] for f in os.listdir(target_folder) if f.endswith(".mkv")}
    if verbosity >= VERBOSE:
        print(f"[VERBOSE] MKV filenames in '{target_folder}': {filenames}")
    return filenames

def extract_season_number(target_folder, verbosity=NORMAL):
    try:
        match = re.search(r"Season\s*(\d+)", target_folder, re.IGNORECASE)
        if match:
            season_number = match.group(1)
            if verbosity >= VERBOSE:
                print(f"[VERBOSE] Extracted season number from '{target_folder}': {season_number}")
            return season_number

        match = re.search(r"S(\d+)", target_folder, re.IGNORECASE)
        if match:
            season_number = match.group(1)
            if verbosity >= VERBOSE:
                print(f"[VERBOSE] Extracted season number from '{target_folder}': {season_number}")
            return season_number

        if verbosity >= VERBOSE:
            print(f"[VERBOSE] No season number found in '{target_folder}'")
        return None
    except Exception as e:
        if verbosity >= NORMAL:
            print(f"[NORMAL] Error extracting season number: {e}")
        return None

def remove_m3u8_folder(m3u8_folder_path, verbosity=NORMAL):
    try:
        shutil.rmtree(m3u8_folder_path)
        if verbosity >= VERBOSE:
            print(f"[VERBOSE] Removed m3u8 folder: {m3u8_folder_path}")
    except Exception as e:
        if verbosity >= NORMAL:
            print(f"[NORMAL] Error removing m3u8 folder: {e}")

def is_valid_directory(path):
    if path is None:  # Explicitly check for None
        return False
    return os.path.exists(path) and os.path.isdir(path)

def rename_mkv(file_path, season_number, verbosity=NORMAL):
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
            episode_number = str(float(episode_number))
            episode_number = episode_number.rstrip('0').rstrip('.') if '.' in episode_number else episode_number
        except ValueError:
            pass

        if season_number is None:
            season_number = "1"

        new_filename = f"S{season_number}E{episode_number}.mkv"
        new_filepath = os.path.join(os.path.dirname(file_path), new_filename)

        counter = 1
        while os.path.exists(new_filepath):
            new_filename = f"S{season_number}E{episode_number}_{counter}.mkv"
            new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
            counter += 1

        os.rename(file_path, new_filepath)

        if verbosity >= VERBOSE:
            print(f"[VERBOSE] Renamed: {file_path} to {new_filepath}")
        return new_filepath

    except Exception as e:
        if verbosity >= NORMAL:
            print(f"[NORMAL] Error renaming '{file_path}': {e}")
        return None

def move_mkv(file_path, base_dir, verbosity=NORMAL):
    try:
        relative_path = os.path.relpath(file_path, base_dir)
        completed_dir = os.path.join(base_dir, COMPLETED_DIR_NAME, os.path.dirname(relative_path))
        final_destination = os.path.join(completed_dir, os.path.basename(file_path))

        os.makedirs(completed_dir, exist_ok=True)
        shutil.move(file_path, final_destination)

        if verbosity >= DESTINATION:
            print(f"[DESTINATION] Moved and Renamed: {file_path} to {final_destination}")

        return True
    except OSError as e:
        if verbosity >= NORMAL:
            print(f"[NORMAL] Error moving '{file_path}': {e}")
        return False
    except Exception as e:
        if verbosity >= NORMAL:
            print(f"[NORMAL] Error moving '{file_path}': {e}")
        return False

def process_directory_item(item_path, base_dir, season_number, mkv_files_present, verbosity=NORMAL):
    if os.path.isdir(item_path):
        process_directory(item_path, base_dir, mkv_files_present, verbosity)
    elif item_path.endswith((".mkv", ".mp4")):
        return process_mkv_file(item_path, base_dir, season_number, mkv_files_present, verbosity)
    return None

def process_directory(item_path, base_dir, mkv_files_present, verbosity=NORMAL):
    if item_path.endswith(".m3u8"):
        process_m3u8_directory(item_path, mkv_files_present, verbosity)
    elif os.path.basename(item_path).lower() == COMPLETED_DIR_NAME.lower():
        if verbosity >= NORMAL:
            print(f"[NORMAL] Skipping directory: {item_path} (Folder named 'Completed')")
        return

def process_m3u8_directory(item_path, mkv_files_present, verbosity=NORMAL):
    m3u8_base_name = os.path.splitext(os.path.basename(item_path))[0]
    if m3u8_base_name in mkv_files_present:
        remove_m3u8_folder(item_path, verbosity)
    else:
        if verbosity >= NORMAL:
            print(f"[NORMAL] Skipped removing m3u8 folder: {item_path} (No matching .mkv file)")

def process_mkv_file(item_path, base_dir, season_number, mkv_files_present, verbosity=NORMAL):
    new_filepath = rename_mkv(item_path, season_number, verbosity)

    if new_filepath is None and re.match(r"^S\d+E\d+(\.\d+)?\.mkv$", os.path.basename(item_path), re.IGNORECASE):
        new_filepath = item_path
        if move_mkv(new_filepath, base_dir, verbosity):
            m3u8_file_path = os.path.join(os.path.dirname(item_path), f"{os.path.splitext(os.path.basename(item_path))[0]}.m3u8")
            if os.path.exists(m3u8_file_path):
                try:
                    os.remove(m3u8_file_path)
                    if verbosity >= VERBOSE:
                        print(f"[VERBOSE] Removed m3u8 file: {m3u8_file_path}")
                except Exception as e:
                    if verbosity >= NORMAL:
                        print(f"[NORMAL] Error removing m3u8 file: {e}")
            return new_filepath
    elif new_filepath:
        if move_mkv(new_filepath, base_dir, verbosity):
            m3u8_file_path = os.path.join(os.path.dirname(item_path), f"{os.path.splitext(os.path.basename(item_path))[0]}.m3u8")
            if os.path.exists(m3u8_file_path):
                try:
                    os.remove(m3u8_file_path)
                    if verbosity >= VERBOSE:
                        print(f"[VERBOSE] Removed m3u8 file: {m3u8_file_path}")
                except Exception as e:
                    if verbosity >= NORMAL:
                        print(f"[NORMAL] Error removing m3u8 file: {e}")
            return new_filepath
    return None

def convert_mkv_to_mp4(mkv_file, converted_dir, base_dir, verbosity=NORMAL):
    output_file = os.path.splitext(mkv_file)[0] + ".mp4"
    temp_output_file = os.path.join(converted_dir, os.path.basename(output_file))

    if os.path.exists(temp_output_file):
        if verbosity >= NORMAL:
            print(f"[NORMAL] Skipping: {mkv_file} (MP4 file already exists)")
        return temp_output_file

    command = ["ffmpeg", "-i", mkv_file, "-codec", "copy", temp_output_file]
    try:
        subprocess.run(command, check=True)
        if verbosity >= VERBOSE:
            print(f"[VERBOSE] Converted: {mkv_file} to {temp_output_file}")
        return temp_output_file

    except subprocess.CalledProcessError as e:
        if verbosity >= NORMAL:
            print(f"[NORMAL] Error converting {mkv_file}: {e}")
        return None

def process_conversion_folder(folder_path, converted_dir, base_dir, verbosity=NORMAL):
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    results = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".mkv"):
                mkv_file = os.path.join(root, file)
                results.append(pool.apply_async(convert_and_move, (mkv_file, converted_dir, base_dir, verbosity)))

    pool.close()
    pool.join()

    for result in results:
        try:
            result.get()
        except Exception as e:
            print(f"[ERROR] Multiprocessing error: {e}")

def convert_and_move(mkv_file, converted_dir, base_dir, verbosity):
    converted_file = convert_mkv_to_mp4(mkv_file, converted_dir, base_dir, verbosity)
    if converted_file:
        try:
            relative_path = os.path.relpath(converted_file, converted_dir)
            original_relative_path = os.path.relpath(os.path.dirname(mkv_file), base_dir)
            if original_relative_path.lower().startswith(COMPLETED_DIR_NAME.lower()):
                original_relative_path = original_relative_path[len(COMPLETED_DIR_NAME):].lstrip(os.sep)
            final_destination = os.path.join(base_dir, COMPLETED_DIR_NAME, original_relative_path, os.path.basename(converted_file))
            os.makedirs(os.path.dirname(final_destination), exist_ok=True)
            shutil.move(converted_file, final_destination)
            if verbosity >= DESTINATION:
                print(f"[DESTINATION] Moved: {converted_file} to {final_destination}")
        except ValueError as e:
            print(f"[ERROR] Error calculating relative path: {e}")

def process_all_subfolders(key_directory, base_dir, verbosity=NORMAL):
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    results = []

    for item in os.listdir(key_directory):
        item_path = os.path.join(key_directory, item)
        results.append(pool.apply_async(_process_item_helper, (item_path, base_dir, verbosity)))

    pool.close()
    pool.join()

    for result in results:
        try:
            result.get()
        except Exception as e:
            print(f"[ERROR] Multiprocessing error in process_all_subfolders: {e}")

def _process_item_helper(item_path, base_dir, verbosity):
    if os.path.isdir(item_path):
        if os.path.basename(item_path).lower() != COMPLETED_DIR_NAME.lower():
            if item_path.endswith(".m3u8"):
                process_m3u8_directory(item_path, get_mkv_filenames(os.path.dirname(item_path), verbosity), verbosity)
            else:
                season_number = extract_season_number(item_path, verbosity)
                mkv_files_present = get_mkv_filenames(item_path, verbosity)
                for sub_item in os.listdir(item_path):
                    sub_item_path = os.path.join(item_path, sub_item)
                    process_directory_item(sub_item_path, base_dir, season_number, mkv_files_present, verbosity)
    else:
        process_directory_item(item_path, base_dir, None, get_mkv_filenames(os.path.dirname(item_path), verbosity), verbosity)

def save_settings(settings_file_path, starting_dir, storage_location):
    config = configparser.ConfigParser()
    config['Paths'] = {
        'starting_dir': starting_dir,
        'storage_location': storage_location,
    }

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(settings_file_path, 'w') as configfile:
            config.write(configfile)
        print("Settings saved.")
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings(config_file_path):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    config = configparser.ConfigParser()
    try:
        config.read(config_file_path)
        if 'Paths' in config:
            return config['Paths']
        else:
            return None
    except (FileNotFoundError, configparser.Error):
        return None

def get_saved_paths(settings):
    if settings:
        starting_dir = settings.get("starting_dir")
        storage_location = settings.get("storage_location")

        # Return None for paths that are not found in config
        if not starting_dir or not storage_location:
            return None, None  # Or "", "" if you prefer empty strings
        return starting_dir, storage_location

    return None, None  # Or "", ""

def prompt_for_paths():
    starting_dir = filedialog.askdirectory(title="Select Starting Directory")
    if not starting_dir:
        exit()
    storage_location = filedialog.askdirectory(title="Select Storage Location")
    if not storage_location:
        exit()
    return starting_dir, storage_location

def validate_and_prompt(path, title):
    while path is None or not is_valid_directory(path): #Loop until valid path is given
        path = filedialog.askdirectory(title=title)
        if not path: #If user cancels the dialog
            exit() #Exit the program
    return path

def get_user_paths(settings):
    starting_dir, storage_location = get_saved_paths(settings)

    use_previous_settings = messagebox.askyesno("Settings", "Use previous settings?")

    if use_previous_settings:
        starting_dir = validate_and_prompt(starting_dir, "Select Starting Directory")
        storage_location = validate_and_prompt(storage_location, "Select Storage Location")

        save_settings(CONFIG_FILE, starting_dir, storage_location)
        return starting_dir, storage_location
    else:
        starting_dir, storage_location = prompt_for_paths()
        save_settings(CONFIG_FILE, starting_dir, storage_location)
        return starting_dir, storage_location


def setup_verbosity():
    VERBOSITY = NORMAL

    def set_verbosity(level):
        nonlocal VERBOSITY
        VERBOSITY = level
        print(f"Verbosity level set to: {VERBOSITY}")
        verbosity_window.destroy()

    verbosity_window = tk.Toplevel()
    verbosity_window.title("Verbosity Level")

    tk.Button(verbosity_window, text="Silent", command=lambda: set_verbosity(SILENT)).pack()
    tk.Button(verbosity_window, text="Destination", command=lambda: set_verbosity(DESTINATION)).pack()
    tk.Button(verbosity_window, text="Normal", command=lambda: set_verbosity(NORMAL)).pack()
    tk.Button(verbosity_window, text="Verbose", command=lambda: set_verbosity(VERBOSE)).pack()

    verbosity_window.protocol("WM_DELETE_WINDOW", lambda: set_verbosity(NORMAL))
    verbosity_window.grab_set()
    verbosity_window.wait_window(verbosity_window)
    return VERBOSITY

def process_files(starting_dir, storage_location, base_dir, verbosity):
    try:
        converted_dir = os.path.join(storage_location, CONVERTED_DIR_NAME)
        os.makedirs(converted_dir, exist_ok=True)

        process_all_subfolders(starting_dir, base_dir, verbosity)
        process_conversion_folder(starting_dir, converted_dir, base_dir, verbosity)

        shutil.rmtree(converted_dir)
        #delete_empty_folders(starting_dir)  # If you have this function

        messagebox.showinfo("Finished", "Program finished successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


if __name__ == "__main__":
    settings = load_settings(CONFIG_FILE)
    starting_dir, storage_location = get_user_paths(settings)
    base_dir = starting_dir
    verbosity = setup_verbosity()
    process_files(starting_dir, storage_location, base_dir, verbosity)
