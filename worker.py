from imports import lazy_import, lazy_logging, lazy_QtCore, lazy_os, lazy_psutil, lazy_json
from utils import get_output_path
from db_operations import DatabaseOperations

ffmpeg = lazy_import("ffmpeg")
QtCore = lazy_QtCore()
logging = lazy_logging()
os = lazy_os()
psutil = lazy_psutil()
json_module = lazy_json()

class AsyncWorker(QtCore.QObject, QtCore.QRunnable):
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)
    cpu_update = QtCore.pyqtSignal(float)

    def __init__(self, source_folder, files, max_cpu_percent, output_format, output_name, config):
        super().__init__()
        QtCore.QRunnable.__init__(self)
        print("AsyncWorker.__init__ called")
        print(f"AsyncWorker.__init__ output_format: {output_format}")
        self.source_folder = source_folder
        self.files = files
        self.max_cpu_percent = max_cpu_percent
        self.output_format = output_format
        self.output_name = output_name
        self.config = config
        self.db_operations = DatabaseOperations(config)
        self.setAutoDelete(True)

    def run(self):
        """Executes the file conversion process."""
        try:
            total_files = len(self.files)
            for index, file_path in enumerate(self.files):
                self.convert_file(file_path, index, total_files)
                progress_percent = int(((index + 1) / total_files) * 100)
                self.progress.emit(progress_percent)
            self.finished.emit()
        except Exception as e:
            logging.error(f"Error during processing: {e}")
            self.finished.emit()

    def convert_file(self, file_path, index, total_files):
        """Converts a single file using ffmpeg-python."""
        try:
            output_file_path = get_output_path(
                file_path, self.source_folder, self.config["destination_dir"], self.output_format, self.output_name
            )

            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            ffmpeg.input(file_path).output(
                output_file_path,
                vcodec=self.config["video_codec"],
                acodec=self.config["audio_codec"],
                video_bitrate=self.config["video_bitrate"],
                audio_bitrate=self.config["audio_bitrate"],
                preset=self.config["preset"],
            ).run(quiet=True, overwrite_output=True)

            self.db_operations.insert_record(file_path, output_file_path)

        except ffmpeg.Error as e:
            logging.error(f"ffmpeg-python conversion error: {e.stderr.decode()}")
        except Exception as e:
            logging.error(f"Error converting file {file_path}: {e}")

    def update_cpu_usage(self):
        """Updates and emits the current CPU usage."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_update.emit(cpu_percent)
