from config import BASE_PATH, IP_FOLDER_MAPPING
import tkinter as tk
from PIL import Image, ImageTk
from video_stream import VideoStream
from logger import get_logger
import os
import re
import requests
from requests.auth import HTTPBasicAuth
from queue import Queue
import socket
import threading
import time

class MainGUI:
    processing_lock = False  # Inicia desbloqueado

    def __init__(self, root):
        self.root = root
        self.root.title("Motion Detection")
        self.logger = get_logger()
        self.is_fullscreen = False
        self.stream = None
        self.camera_map = {}
        self.image_queue = Queue()
        self.current_image = None
        self.current_camera_number = None
        
        self.root.attributes('-topmost', True)
        self.metadata_label = tk.Label(self.root, text="", font=("Arial", 12), bg="black", fg="white")
        self.metadata_label.pack(side=tk.TOP, fill=tk.X)
        self.video_label = tk.Label(self.root)
        self.video_label.place(relx=0.5, rely=0.5, anchor="center", width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
        self.video_label.lower()
        self.image_label = tk.Label(self.root)
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")
        self.image_label.lower()
        self.thumbnail_label = tk.Label(self.root)
        self.thumbnail_label.place(relx=0.9, rely=0.098, anchor="nw")
        self.thumbnail_label.bind("<Button-1>", self.toggle_thumbnail)
        self.thumbnail_label.lift()
        self.button_frame = tk.Frame(self.root)
        self.button_frame.place(relx=0.5, rely=1.0, anchor="s")
        self.button_frame.lift()
        buttons = ["Sem motivo aparente", "Evento devido à...", "Inibir detecções por...", "Escolher motivo", "Pausar por 1 minuto"]
        for text in buttons:
            if text == "Sem motivo aparente":
                tk.Button(self.button_frame, text=text, command=self.handle_no_reason).pack(side=tk.LEFT, padx=5, pady=5)
            else:
                tk.Button(self.button_frame, text=text, command=lambda t=text: self.button_action(t)).pack(side=tk.LEFT, padx=5, pady=5)
        self.log_window = None
        self.root.bind("<Control-F12>", self.toggle_log_window)
        self.root.withdraw()
        self.start_monitoring()

    def button_action(self, text):
        self.logger.info(f"Button clicked: {text}")

    def handle_no_reason(self):
        if self.current_image and os.path.exists(self.current_image):
            os.remove(self.current_image)
            self.logger.info(f"Deleted image: {self.current_image}")
            MainGUI.processing_lock = False
            if not self.image_queue.empty():
                self.current_image = self.image_queue.get()
                filename = os.path.basename(self.current_image)
                match = re.match(r"(\d{8}-\d{6})_([\d.]+)_(.+)_(\d{4})\.jpg", filename)
                if match:
                    camera_name = match.group(3)
                    self.current_camera_number = self.camera_map.get(camera_name, "0")
                    if self.stream:
                        self.stream.stop()
                    self.stream = VideoStream(self.video_label, f"http://admin:@Dm1n@localhost/mjpegstream.cgi?camera={self.current_camera_number}")
                    self.stream.start()
                    self.load_thumbnail(self.current_image)
                self.logger.info(f"Updated video and thumbnail for: {self.current_image}")
            else:
                self.current_image = None
                self.logger.info("No more images")
            MainGUI.processing_lock = True

    def fetch_camera_names(self):
        try:
            response = requests.get("http://localhost/camerasnomes.cgi", auth=HTTPBasicAuth("admin", "@Dm1n"))
            response.raise_for_status()
            pairs = response.text.split("&")
            for pair in pairs:
                if "=" in pair:
                    number, name = pair.split("=")
                    camera_name = name.split(".")[0] if "." in name else name
                    self.camera_map[camera_name] = number
                    self.logger.info(f"Parsed camera: {camera_name} = {number}")
        except Exception as e:
            self.logger.error(f"Error fetching API data: {e}")

    def start_monitoring(self):
        self.fetch_camera_names()
        self.initialize_first_image()
        threading.Thread(target=self.monitor_folder, daemon=True).start()
        self.root.deiconify()

    def initialize_first_image(self):
        ip = socket.gethostbyname(socket.gethostname())
        folder_map = IP_FOLDER_MAPPING
        folder = folder_map.get(ip, "0000")
        image_folder = os.path.join(BASE_PATH, folder)
        if os.path.exists(image_folder):
            images = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png'))]
            def sort_key(image):
                has_def = "[ DEF ]" in os.path.basename(image)
                return (not has_def, os.path.getmtime(image))
            images.sort(key=sort_key)
            if images:
                self.current_image = images[0]
                match = re.match(r"(\d{8}-\d{6})_([\d.]+)_(.+)_(\d{4})\.jpg", os.path.basename(self.current_image))
                if match:
                    camera_name = match.group(3)
                    self.current_camera_number = self.camera_map.get(camera_name, "0")
                    self.stream = VideoStream(self.video_label, f"http://admin:@Dm1n@localhost/mjpegstream.cgi?camera={self.current_camera_number}")
                    self.stream.start()
                self.load_thumbnail(self.current_image)
                self.toggle_thumbnail(None)  # Expande o thumbnail automaticamente
                self.logger.info(f"Initialized with: {self.current_image}")

    def monitor_folder(self):
        ip = socket.gethostbyname(socket.gethostname())
        folder_map = IP_FOLDER_MAPPING
        folder = folder_map.get(ip, "0000")
        image_folder = os.path.join(BASE_PATH, folder)
        last_files = set()
        
        while True:
            if os.path.exists(image_folder) and MainGUI.processing_lock:
                current_files = set(os.listdir(image_folder))
                new_files = [f for f in current_files if f.endswith(('.jpg', '.png')) and f not in last_files]
                if new_files:
                    images = [os.path.join(image_folder, f) for f in new_files]
                    def sort_key(image):
                        has_def = "[ DEF ]" in os.path.basename(image)
                        return (not has_def, os.path.getmtime(image))
                    images.sort(key=sort_key)
                    for image in images:
                        self.image_queue.put(image)
                        self.logger.info(f"New image detected: {image}")
                last_files = current_files
            time.sleep(1)

    def show_interface(self, image_path):
        self.logger.info(f"Showing interface for: {image_path}")
        self.root.deiconify()
        self.root.attributes('-fullscreen', True)
        self.load_thumbnail(image_path)

    def load_thumbnail(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((100, 100))
            self.thumbnail = ImageTk.PhotoImage(img)
            self.thumbnail_label.configure(image=self.thumbnail)
            self.thumbnail_label.image = self.thumbnail  # Mantém referência
            full_img = Image.open(image_path).resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.Resampling.LANCZOS)
            self.full_image = ImageTk.PhotoImage(full_img)
            self.is_fullscreen = False
            self.logger.info(f"Thumbnail loaded: {image_path}")
            filename = os.path.basename(image_path)
            match = re.match(r"(\d{8}-\d{6})_([\d.]+)_(.+)_(\d{4})\.jpg", filename)
            if match:
                date_time = match.group(1).replace("-", " ")
                ip = match.group(2)
                camera_name = match.group(3)
                metadata = f"{camera_name} - {ip} | {date_time[:4]}-{date_time[4:6]}-{date_time[6:11]}:{date_time[11:13]}:{date_time[13:]}"
                self.metadata_label.configure(text=metadata)
                self.logger.info(f"Metadata displayed: {metadata}")
            else:
                self.metadata_label.configure(text="Unknown Camera - Unknown IP | Unknown Date")
                self.logger.warning(f"Could not parse: {filename}")
        except Exception as e:
            self.logger.error(f"Error loading thumbnail: {e}")
            self.metadata_label.configure(text="Error loading image")

    def toggle_thumbnail(self, event):
        if not self.is_fullscreen and self.thumbnail:
            self.image_label.configure(image=self.full_image)
            self.image_label.place(relx=0.5, rely=0.5, anchor="center", width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
            self.image_label.lift()
            self.image_label.bind("<Button-1>", self.toggle_thumbnail)
            self.button_frame.lift()
            self.is_fullscreen = True
            self.logger.info("Thumbnail expanded")
        elif self.is_fullscreen:
            self.image_label.configure(image='')
            self.image_label.place(relx=0.5, rely=0.5, anchor="center")
            self.video_label.lift()
            self.thumbnail_label.lift()
            self.button_frame.lift()
            self.image_label.unbind("<Button-1>")
            self.is_fullscreen = False
            self.logger.info("Thumbnail minimized")

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