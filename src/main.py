import tkinter as tk
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
