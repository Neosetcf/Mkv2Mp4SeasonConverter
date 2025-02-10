based off the Mkv2Mp4
this also simply uses both python and FFmpeg

the MKV renaming and conversion program, showing how it interacts with the file structure.

1. Initialization and Setup:

Configuration: The program defines constants for directories and file names, like where settings are saved (CONFIG_DIR, CONFIG_FILE), the names of the "Converted" and "Completed" directories (CONVERTED_DIR_NAME, COMPLETED_DIR_NAME), and verbosity levels.
Helper Functions: Several helper functions are defined for tasks like:
is_folder_empty(): Checks if a folder is empty.
get_mkv_filenames(): Gets all MKV filenames in a directory.
extract_season_number(): Extracts the season number from a folder name.
remove_m3u8_folder(): Removes a folder if it's related to m3u8 playlists.
rename_mkv(): Renames MKV files to "S{Season}E{Episode}.mkv" format.
move_mkv(): Moves MKV files to the "Completed" directory.
process_directory_item(): Processes a single file or directory.
process_directory(): Processes a directory (handles m3u8 folders).
process_m3u8_directory(): Removes m3u8 folders.
process_mkv_file(): Processes an individual MKV file (renaming and moving).
convert_mkv_to_mp4(): Converts an MKV to MP4 using FFmpeg.
process_conversion_folder(): Converts MKVs in the starting directory.
convert_and_move(): Converts and moves a single MKV.
process_all_subfolders(): Recursively processes all subfolders.
_process_item_helper(): A helper function for multiprocessing.
save_settings(): Saves settings to the config file.
load_settings(): Loads settings from the config file.
get_saved_paths(): Gets saved paths from settings.
prompt_for_paths(): Prompts the user for paths.
validate_and_prompt(): Validates and prompts for paths.
get_user_paths(): Gets user paths, prompting if needed.
setup_verbosity(): Sets the verbosity level.
2. Main Execution:

Load Settings: The script loads saved settings (starting directory and storage location) from the config file.
Get User Paths: If no settings are found or the user chooses not to use them, the script prompts the user to select the starting directory and storage location.
Set Verbosity: The user is prompted to choose a verbosity level.
Process Files: The process_files function is called, which initiates the renaming, conversion, and moving process.
3. process_files() Function:

Create Converted Directory: A temporary "Converted" directory is created within the storage location.
Process Subfolders: The process_all_subfolders function is called to handle all subdirectories within the starting directory.
Process Conversion Folder: The process_conversion_folder function is called to convert MKV files directly within the starting directory.
Cleanup: The temporary "Converted" directory is deleted.
4. process_all_subfolders() Function:

This function recursively walks through all subfolders of the starting directory.
For each file or folder:
If it's a directory (and not "Completed"), it either processes m3u8 files or calls process_all_subfolders() again for sub-subdirectories.
If it's an MKV file, it calls process_mkv_file().
5. process_conversion_folder() Function:

This function uses multiprocessing to convert MKV files in the starting directory to MP4 files and store them temporarily in the "Converted" directory.
6. process_mkv_file() Function:

Renames the MKV file using rename_mkv().
Moves the renamed MKV file to the "Completed" directory using move_mkv().
7. convert_mkv_to_mp4() Function:

Uses FFmpeg to convert an MKV file to MP4.
8. convert_and_move() Function:

Converts an MKV to MP4 and moves it to the "Completed" directory.
File Structure Example:

Let's say your starting directory is /path/to/Show:

/path/to/Show/
├── Season 1/
│   ├── Episode 01.mkv
│   ├── Episode 02.mkv
│   └── Extras/
│       └── Bonus Content.mkv
└── Season 2/
    └── Episode 01.mkv
After running the script (and assuming the storage location is the same as the starting directory), the structure will look like this:

/path/to/Show/
├── Season 1/
│   ├── Episode 01.mkv
│   ├── Episode 02.mkv
│   └── Extras/
│       └── Bonus Content.mkv
└── Season 2/
    └── Episode 01.mkv
└── Completed/
    ├── Season 1/
    │   ├── S1E01.mp4
    │   ├── S1E02.mp4
    │   └── Extras/
    │       └── S1EBonus Content.mp4
    └── Season 2/
        └── S2E01.mp4
The original MKV files remain untouched. The converted MP4 files are in the "Completed" directory, mirroring the original folder structure.  The temporary "Converted" directory is deleted after the process is complete. This is the basic flow of the program. 
