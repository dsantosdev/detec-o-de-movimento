import cv2
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
                a = bytes.find(b'\xff\xd8')
                b = bytes.find(b'\xff\xd9')
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
