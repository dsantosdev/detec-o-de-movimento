import os
import subprocess

# Define the base path
BASE_PATH = r"C:\_Python\detecção-de-movimento"

# Define the structure and file contents
structure = {
    "src": {
        "__init__.py": "# Empty __init__.py to make src a package",
        "main.py": """import tkinter as tk
from gui import MainGUI
from folder_monitor import FolderMonitor
from config import BASE_PATH, IP_FOLDER_MAPPING
from logger import setup_logger
import socket
import os

def get_folder_from_ip():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return IP_FOLDER_MAPPING.get(ip, "0000")
    except:
        return "0000"

def main():
    logger = setup_logger()
    logger.info("Starting application")
    
    folder_number = get_folder_from_ip()
    monitor_path = os.path.join(BASE_PATH, folder_number)
    logger.info(f"Monitoring folder: {monitor_path}")
    
    root = tk.Tk()
    app = MainGUI(root)
    monitor = FolderMonitor(monitor_path, app.show_interface)
    monitor.start()
    
    logger.info("Application initialized")
    root.mainloop()

if __name__ == "__main__":
    main()
""",
        "gui.py": """import tkinter as tk
from PIL import Image, ImageTk
from video_stream import VideoStream
from logger import get_logger
import cv2
import numpy as np

class MainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Motion Detection")
        self.logger = get_logger()
        self.is_fullscreen = False
        self.stream = None
        
        self.video_label = tk.Label(self.root)
        self.video_label.pack(pady=10)
        
        self.thumbnail_label = tk.Label(self.root)
        self.thumbnail_label.place(relx=0.8, rely=0.1, anchor="ne")
        self.thumbnail_label.bind("<Button-1>", self.toggle_thumbnail)
        
        self.close_button = tk.Button(self.root, text="Close Image", command=self.close_thumbnail)
        self.close_button.place(relx=0.8, rely=0.15, anchor="ne")
        self.close_button.place_forget()
        
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)
        buttons = [
            "Sem motivo aparente",
            "Evento devido à...",
            "Inibir detecções por...",
            "Escolher motivo",
            "Pausar por 1 minuto"
        ]
        for text in buttons:
            tk.Button(self.button_frame, text=text, command=lambda t=text: self.button_action(t)).pack(side=tk.LEFT, padx=5)
        
        self.log_window = None
        self.root.bind("<Control-F12>", self.toggle_log_window)
        
        self.root.withdraw()

    def button_action(self, text):
        self.logger.info(f"Button clicked: {text}")

    def show_interface(self, image_path):
        self.logger.info(f"Showing interface for image: {image_path}")
        self.root.deiconify()
        if self.stream is None:
            self.stream = VideoStream(self.video_label, "http://your_video_stream_url")
            self.stream.start()
        self.load_thumbnail(image_path)

    def load_thumbnail(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((100, 100))
            self.thumbnail = ImageTk.PhotoImage(img)
            self.thumbnail_label.configure(image=self.thumbnail)
            self.thumbnail_label.image = self.thumbnail
            self.full_image = ImageTk.PhotoImage(Image.open(image_path))
            self.logger.info(f"Thumbnail loaded: {image_path}")
        except Exception as e:
            self.logger.error(f"Error loading thumbnail: {e}")

    def toggle_thumbnail(self, event):
        if not self.is_fullscreen:
            self.video_label.configure(image=self.full_image)
            self.close_button.place(relx=0.5, rely=0.5, anchor="center")
            self.is_fullscreen = True
            self.logger.info("Thumbnail expanded to fullscreen")
        else:
            self.video_label.configure(image='')
            self.close_button.place_forget()
            self.is_fullscreen = False
            self.logger.info("Thumbnail minimized")

    def close_thumbnail(self):
        self.thumbnail_label.configure(image='')
        self.close_button.place_forget()
        self.is_fullscreen = False
        self.logger.info("Thumbnail closed")

    def toggle_log_window(self, event):
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = tk.Toplevel(self.root)
            self.log_window.title("Log Window")
            text = tk.Text(self.log_window, height=20, width=80)
            text.pack(padx=10, pady=10)
            with open("logs/app.log", "r") as f:
                lines = f.readlines()[-100:]
                text.insert(tk.END, "".join(lines))
            text.config(state="disabled")
            self.logger.info("Log window opened")
        else:
            self.log_window.destroy()
            self.logger.info("Log window closed")
""",
        "video_stream.py": """import cv2
import numpy as np
import urllib.request
import threading
from logger import get_logger

class VideoStream:
    def __init__(self, label, url):
        self.label = label
        self.url = url
        self.logger = get_logger()
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.update, daemon=True).start()
        self.logger.info("Video stream started")

    def update(self):
        try:
            stream = urllib.request.urlopen(self.url)
            bytes = bytes()
            while self.running:
                bytes += stream.read(1024)
                a = bytes.find(b'\\xff\\xd8')
                b = bytes.find(b'\\xff\\xd9')
                if a != -1 and b != -1:
                    jpg = bytes[a:b+2]
                    bytes = bytes[b+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img = ImageTk.PhotoImage(img)
                    self.label.configure(image=img)
                    self.label.image = img
        except Exception as e:
            self.logger.error(f"Error in video stream: {e}")
            self.running = False

    def stop(self):
        self.running = False
        self.logger.info("Video stream stopped")
""",
        "folder_monitor.py": """from watchdog.observers import Observer
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
""",
        "logger.py": """import logging
import os

def setup_logger():
    logger = logging.getLogger("MotionDetection")
    logger.setLevel(logging.INFO)
    os.makedirs("logs", exist_ok=True)
    handler = logging.FileHandler("logs/app.log")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def get_logger():
    return logging.getLogger("MotionDetection")
""",
        "config.py": """BASE_PATH = r"\\\\srvftp\\monitoramento\\FTP"

IP_FOLDER_MAPPING = {
    "192.9.100.100": "0000",
    "192.9.100.102": "0001",
    "192.9.100.106": "0002",
    "192.9.100.109": "0003",
    "192.9.100.114": "0004",
    "192.9.100.118": "0005",
    "192.9.100.123": "0006"
}
""",
        "ip_mapping.py": """from config import IP_FOLDER_MAPPING
import socket

def get_folder_number():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return IP_FOLDER_MAPPING.get(ip, "0000")
    except:
        return "0000"
"""
    },
    "logs": {
        "app.log": ""
    },
    "requirements.txt": """pillow
opencv-python
watchdog
"""
}

def create_structure(base_path, structure):
    # Create base directory if it doesn't exist
    os.makedirs(base_path, exist_ok=True)
    
    # Create virtual environment
    venv_path = os.path.join(base_path, ".venv")
    subprocess.run(["python", "-m", "venv", venv_path], check=True)
    print(f"Created virtual environment: {venv_path}")

    def create_files(path, items):
        for name, content in items.items():
            full_path = os.path.join(path, name)
            if isinstance(content, dict):  # It's a directory
                os.makedirs(full_path, exist_ok=True)
                create_files(full_path, content)
            else:  # It's a file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Created file: {full_path}")

    create_files(base_path, structure)
    print("Directory structure and files created successfully!")

if __name__ == "__main__":
    create_structure(BASE_PATH, structure)