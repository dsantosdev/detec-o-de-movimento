from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from logger import get_logger

class FolderMonitor(FileSystemEventHandler):
    def __init__(self, path, callback):
        self.path = path
        self.callback = callback
        self.logger = get_logger()
        self.observer = Observer()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.jpg', '.png')):
            self.logger.info(f"New image detected: {event.src_path}")
            self.callback(event.src_path)

    def start(self):
        self.observer.schedule(self, self.path, recursive=False)
        self.observer.start()
        self.logger.info(f"Started monitoring folder: {self.path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
        self.logger.info("Stopped monitoring folder")
