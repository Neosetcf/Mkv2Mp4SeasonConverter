from imports import lazy_import

json = lazy_import("json")
logging = lazy_import("logging")
QtWidgets = lazy_import("PyQt5.QtWidgets")
psutil = lazy_import("psutil")
os = lazy_import("os")

def load_config(config_file="config.json"):
    """Loads application configuration from a JSON file.
    Creates a default config if it doesn't exist.
    """
    default_config = {
        "source_dir": "",
        "destination_folder": "",
        "log_file": "app.log",
        "db_file": "app.db",
        "max_cpu_percent": 80,
        "hardware_acceleration": None,
        "ignored_folders": [],
        "video_codec": "libx264",
        "audio_codec": "aac",
        "video_bitrate": "2000k",
        "audio_bitrate": "192k",
        "preset": "medium"
    }
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"Config file '{config_file}' not found. Creating default.")
        try:
            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=4)
            return default_config
        except Exception as e:
            logging.error(f"Error creating default config: {e}")
            return default_config
    except json.JSONDecodeError:
        logging.error(f"Error decoding config file '{config_file}'.")
        return default_config
    return default_config

def save_config(config, config_file="config.json"):
    """Saves the updated configuration to a file."""
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        logging.info("Configuration saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save config: {e}")

def setup_logging(log_file="app.log"):
    """Sets up logging with file and console handlers."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def create_ui_element(element_type, **kwargs):
    """Dynamically creates a PyQt UI element."""
    if QtWidgets:
        return getattr(QtWidgets, element_type)(**kwargs)
    return None

def get_cpu_percent():
    """Returns the current CPU usage percentage."""
    return psutil.cpu_percent(interval=0.1)

def get_output_path(input_file, source_folder, destination_folder, output_format, output_name):
    """Generates the output file path."""
    relative_path = os.path.relpath(input_file, source_folder)
    output_filename = os.path.splitext(os.path.basename(input_file))[0]
    if output_name:
        output_filename = output_name
    output_filename += "." + output_format
    output_path = os.path.join(destination_folder, relative_path)
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, output_filename)
