import logging

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Change to INFO or WARNING as needed
    format='[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("domain_manager.log"),  # Logs to a file
        logging.StreamHandler()  # Logs to the console
    ]
)

# Create a logger instance for importing into other modules
logger = logging.getLogger("domain_manager")
