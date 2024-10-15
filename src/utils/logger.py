import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Get the project root directory
project_root = Path(__file__).resolve().parent.parent.parent


# Configure the logger
log_file_path = Path(project_root, 'logs', "domain_manager.log")

logging.basicConfig(
    level=logging.INFO,  # Change to INFO or WARNING as needed
    format='[%(asctime)s][%(name)s][%(levelname)s][%(filename)s:%(lineno)d][%(funcName)s] %(message)s',
    handlers=[
        RotatingFileHandler(filename=log_file_path, maxBytes=1e9, backupCount=8),  # Log rotation when the file becomes 1GB
        logging.StreamHandler()  # Logs to the console
    ]
)


# Create a logger instance for importing into other modules
logger = logging.getLogger("domain_manager")
