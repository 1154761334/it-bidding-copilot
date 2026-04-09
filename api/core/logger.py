import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Ensure log directory exists
LOG_DIR = "/root/it-bidding-copilot/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "server.log")

# Configure logging
logger = logging.getLogger("it_bidding_copilot")
logger.setLevel(logging.INFO)

# Create handlers
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
console_handler = logging.StreamHandler(sys.stdout)

# Create formatters and add them to handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_logger(name=None):
    if name:
        return logging.getLogger(f"it_bidding_copilot.{name}")
    return logger
