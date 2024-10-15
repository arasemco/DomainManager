import os
import signal
import dotenv
from threading import Event

from src.managers import ProviderFactory, SubdomainManager, DockerEventListener
from src.utils.logger import logger

# Handle graceful shutdown
stop_signal = Event()

def handle_stop_signal(signum, frame):
    logger.info("Stop signal received. Shutting down immediately...")
    stop_signal.set()


def welcome(provider_name, docker_base_url):
    logger.info("Welcome to Domain Manager!")
    logger.info(f"Provider          : {provider_name}")
    logger.info(f"Docker Base URL   : {docker_base_url}")
    logger.info(f"Domain Name       : {os.getenv('DNM_DOMAIN_NAME', '<not set>')}")
    logger.info(f"Target            : {os.getenv('DNM_TARGET', '<not set>')}")


def main():
    logger.debug("Loading environment variables...")
    # Load environment variables
    if not os.getenv('DNM_DOMAIN_NAME'):
        dotenv.load_dotenv()
    provider_name = os.getenv('DNM_PROVIDER', 'OVH')
    docker_base_url = os.getenv('DNM_DOCKER_BASE_URL', 'unix://var/run/docker.sock')
    welcome(provider_name=provider_name, docker_base_url=docker_base_url)

    # Create instances
    try:
        logger.debug("Creating provider instance...")
        provider = ProviderFactory.get_provider(name=provider_name)
        logger.debug("Creating subdomain manager instance...")
        subdomain_manager = SubdomainManager(provider=provider)
        logger.debug("Creating Docker event listener instance...")
        docker_event_listener = DockerEventListener(subdomain_manager=subdomain_manager, base_url=docker_base_url)
        logger.info("Instances created successfully.")

        # subdomain = 'test'
        # subdomain_manager.add_subdomain(subdomain)
        # subdomain_manager.remove_subdomain(subdomain)
    except Exception as e:
        logger.error(f"Error creating instances: {e}")
        return

    # Start listening for Docker events in the background until the application is running
    try:
        logger.info("Starting Docker event listener...")
        docker_event_listener.listen()
        logger.info("Docker event listener started.")
    except Exception as e:
        logger.error(f"Error starting Docker event listener: {e}")
        return

    # Set up signal handlers
    logger.debug("Setting up signal handlers...")
    signal.signal(signal.SIGTERM, handle_stop_signal)
    signal.signal(signal.SIGINT, handle_stop_signal)

    # Wait for stop signal to stop the application
    logger.info("Waiting for stop signal...")
    stop_signal.wait()
    logger.info("Stop signal received. Docker Event Listener stopped.")

if __name__ == "__main__":
    logger.debug("Starting main function...")
    main()
    logger.debug("Main function finished.")
