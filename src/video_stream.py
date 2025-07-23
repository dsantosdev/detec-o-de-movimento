import cv2
import numpy as np
import threading
from logger import get_logger
from PIL import Image, ImageTk

class VideoStream:
    def __init__(self, label, url):
        self.label = label
        self.url = url
        self.logger = get_logger()
        self.running = False
        self.frame = None

    def start(self):
        self.running = True
        threading.Thread(target=self.update, daemon=True).start()
        self.logger.info("Video stream started")

    def update(self):
        try:
            cap = cv2.VideoCapture(self.url)
            if not cap.isOpened():
                self.logger.error(f"Failed to open video stream: {self.url}")
                self.running = False
                return
            while self.running:
                ret, frame = cap.read()
                if ret:
                    self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(self.frame)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.label.configure(image=imgtk)
                    self.label.image = imgtk
                else:
                    self.logger.warning("No frame received from stream")
            cap.release()
        except Exception as e:
            self.logger.error(f"Error in video stream: {e}")
            self.running = False
        finally:
            if 'cap' in locals():
                cap.release()

    def stop(self):
        self.running = False
        self.logger.info("Video stream stopped")