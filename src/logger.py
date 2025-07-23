import logging
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
