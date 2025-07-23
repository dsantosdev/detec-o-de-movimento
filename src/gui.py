import tkinter as tk
from PIL import Image, ImageTk
from video_stream import VideoStream
from logger import get_logger
import cv2
import numpy as np
import re
import os
import requests
from requests.auth import HTTPBasicAuth

class MainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Motion Detection")
        self.logger = get_logger()
        self.is_fullscreen = False
        self.stream = None
        self.camera_map = {}  # Store camera name to number mapping
        
        # Set window to always on top
        self.root.attributes('-topmost', True)
        
        # Label for camera metadata (camera name, IP, date/time)
        self.metadata_label = tk.Label(self.root, text="", font=("Arial", 12), bg="black", fg="white")
        self.metadata_label.pack(side=tk.TOP, fill=tk.X)
        
        self.video_label = tk.Label(self.root)
        self.video_label.pack(pady=10)
        
        self.thumbnail_label = tk.Label(self.root)
        self.thumbnail_label.place(relx=0.8, rely=0.1, anchor="ne")
        self.thumbnail_label.bind("<Button-1>", self.toggle_thumbnail)
        
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)  # Fixed at bottom
        buttons = [
            "Sem motivo aparente",
            "Evento devido à...",
            "Inibir detecções por...",
            "Escolher motivo",
            "Pausar por 1 minuto"
        ]
        for text in buttons:
            tk.Button(self.button_frame, text=text, command=lambda t=text: self.button_action(t)).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.log_window = None
        self.root.bind("<Control-F12>", self.toggle_log_window)
        
        self.root.withdraw()

    def button_action(self, text):
        self.logger.info(f"Button clicked: {text}")

    def fetch_camera_names(self):
        try:
            response = requests.get(
                "http://localhost/camerasnomes.cgi",
                auth=HTTPBasicAuth("admin", "@Dm1n")
            )
            response.raise_for_status()
            # Parse response (e.g., "0=ARB [ BAL ] Pátio.ARB [ BAL ] Pátio")
            pairs = response.text.split("&")
            for pair in pairs:
                if "=" in pair:
                    number, name = pair.split("=")
                    # Extract camera name (before the first . if it exists)
                    camera_name = name.split(".")[0] if "." in name else name
                    self.camera_map[camera_name] = number
                    self.logger.info(f"Parsed camera: {camera_name} = {number}")
            print("Stored Camera Map:", self.camera_map)
        except Exception as e:
            print(f"Error fetching API data: {e}")
            self.logger.error(f"Error fetching API data: {e}")

    def show_interface(self, image_path):
        self.logger.info(f"Showing interface for image: {image_path}")
        self.root.deiconify()
        # Set window to full-screen
        self.root.attributes('-fullscreen', True)
        # Fetch camera names
        self.fetch_camera_names()
        # Parse camera name from filename
        filename = os.path.basename(image_path)
        match = re.match(r"(\d{8}-\d{6})_([\d.]+)_(.+)_(\d{4})\.jpg", filename)
        camera_name = match.group(3) if match else "Unknown"
        # Get camera number from map, default to 0 if not found
        camera_number = self.camera_map.get(camera_name, "0")
        # Construct live stream URL
        stream_url = f"http://admin:@Dm1n@localhost/mjpegstream.cgi?camera={camera_number}"
        self.logger.info(f"Using stream URL: {stream_url}")
        if self.stream is None:
            self.stream = VideoStream(self.video_label, stream_url)
            self.stream.start()
        self.load_thumbnail(image_path)

    def load_thumbnail(self, image_path):
        try:
            # Load and display image as thumbnail
            img = Image.open(image_path)
            img.thumbnail((100, 100))
            self.thumbnail = ImageTk.PhotoImage(img)
            self.thumbnail_label.configure(image=self.thumbnail)
            self.thumbnail_label.image = self.thumbnail
            self.full_image = ImageTk.PhotoImage(Image.open(image_path))
            self.is_fullscreen = False
            self.logger.info(f"Thumbnail loaded: {image_path}")
            
            # Parse filename for metadata
            filename = os.path.basename(image_path)
            match = re.match(r"(\d{8}-\d{6})_([\d.]+)_(.+)_(\d{4})\.jpg", filename)
            if match:
                date_time = match.group(1).replace("-", " ")  # e.g., 20250628 214954
                ip = match.group(2)  # e.g., 10.2.236.215
                camera_name = match.group(3)  # e.g., IBI [ SUP ] Depósito
                # Format: Camera Name - IP | Date and Time
                metadata = f"{camera_name} - {ip} | {date_time[:4]}-{date_time[4:6]}-{date_time[6:11]}:{date_time[11:13]}:{date_time[13:]}"
                self.metadata_label.configure(text=metadata)
                self.logger.info(f"Metadata displayed: {metadata}")
            else:
                self.metadata_label.configure(text="Unknown Camera - Unknown IP | Unknown Date")
                self.logger.warning(f"Could not parse metadata from filename: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error loading thumbnail: {e}")
            self.metadata_label.configure(text="Error loading image")

    def toggle_thumbnail(self, event):
        if not self.is_fullscreen:
            self.video_label.configure(image=self.full_image)
            self.thumbnail_label.configure(image='')  # Hide thumbnail
            self.video_label.bind("<Button-1>", self.toggle_thumbnail)  # Bind click to minimize
            self.is_fullscreen = True
            self.logger.info("Thumbnail expanded to full-screen")
        else:
            self.video_label.configure(image='')
            self.thumbnail_label.configure(image=self.thumbnail)  # Show thumbnail again
            self.video_label.unbind("<Button-1>")  # Unbind click
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