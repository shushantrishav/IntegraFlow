# backend/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Get the current date to append to log files (e.g., 'backend-2025-07-03.log')
current_date = datetime.now().strftime("%Y-%m-%d")
log_filename = f"logs/backend-{current_date}.log"

# Logger setup
logger = logging.getLogger("vectorshift-backend")
logger.setLevel(logging.INFO)

# Define a consistent formatter for log messages
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"  # Log timestamp format
)

# Console handler: outputs logs to the console with INFO level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Rotating file handler: keeps up to 3 backup log files, each with max size of 5MB
file_handler = RotatingFileHandler(log_filename, maxBytes=5 * 1024 * 1024, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Attach both handlers (console and file) to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
