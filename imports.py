import importlib

def lazy_import(module_name):
    """Dynamically imports a module with error handling."""
    try:
        return importlib.import_module(module_name)
    except ImportError as e: # Catch the actual exception
        raise ImportError(f"Error: Could not import module '{module_name}': {e}") # Raise it again

def lazy_os():
    return lazy_import("os")

def lazy_sys():
    return lazy_import("sys")

def lazy_io():
    return lazy_import("io")

def lazy_json():
    return lazy_import("json")

def lazy_sqlite3():
    return lazy_import("sqlite3")

def lazy_logging():
    return lazy_import("logging")

def lazy_ffmpeg():
    return lazy_import("ffmpeg")

def lazy_time():
    return lazy_import("time")

def lazy_QtWidgets():
    return lazy_import("PyQt5.QtWidgets")

def lazy_QtCore():
    return lazy_import("PyQt5.QtCore")

def lazy_QtGui():
    return lazy_import("PyQt5.QtGui")

def lazy_psutil():
    return lazy_import("psutil")

def lazy_threading():
    return lazy_import("threading")
