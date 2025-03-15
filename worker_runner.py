from imports import lazy_import, lazy_logging, lazy_QtCore, lazy_threading  # modified

ffmpeg = lazy_import("ffmpeg")
logging = lazy_logging()
QtCore = lazy_QtCore()
os = lazy_import("os")  # Lazily import os
threading = lazy_threading()  # added

class WorkerRunner(QtCore.QRunnable):
    def __init__(self, worker, db_handler):
        super().__init__()
        self.worker = worker
        self.db_handler = db_handler
        self.lock = threading.Lock()  # Ensures thread safety for DB operations

    def run(self):
        threads = []  # Initialize threads as an empty list
        for i, file_path in enumerate(self.worker.files):
            if not self.worker.running:
                break
            thread = threading.Thread(target=self.process_and_store, args=(file_path, i))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        self.worker.finished.emit()

    def process_and_store(self, file_path, index):
        output_file = self.get_output_path(file_path)
        if self.process_file(file_path, output_file):
            with self.lock:
                self.db_handler.add_processed_file(file_path, output_file)
        self.worker.progress.emit(index + 1)

    def get_output_path(self, input_file):
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        output_name = self.worker.output_name_pattern.replace("{filename}", file_name)
        return f"{self.worker.destination_dir}/{output_name}.{self.worker.output_format}"

    def process_file(self, input_file, output_file):
        try:
            hwaccel = self.worker.config.get("hardware_acceleration")
            input_stream = ffmpeg.input(input_file)
            output_args = {'c:v': 'libx264'}
            if hwaccel:
                output_args['hwaccel'] = hwaccel

            output_stream = input_stream.output(output_file, **output_args).overwrite_output()
            output_stream.run()
            return True
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logging.error(f"FFmpeg error for {input_file}: {error_msg}")
        except Exception as e:
            logging.error(f"Error processing {input_file}: {e}")
        return False
