from config import IP_FOLDER_MAPPING
import socket

def get_folder_number():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return IP_FOLDER_MAPPING.get(ip, "0000")
    except:
        return "0000"
