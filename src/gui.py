import tkinter as tk
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
