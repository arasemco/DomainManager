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


def main():
    # Load environment variables
    if os.getenv('DNM_DOMAIN_NAME', None) is None:
        dotenv.load_dotenv()
    provider_name = os.getenv('DNM_PROVIDER', 'OVH')
    docker_base_url = os.getenv('DNM_DOCKER_BASE_URL', 'unix://var/run/docker.sock')

    logger.info(f"Welcome to Domain Manager!")
    logger.info(f"Provider          : {provider_name}")
    logger.info(f"Docker Base URL   : {docker_base_url}")
    logger.info(f"Domain Name       : {os.getenv('DNM_DOMAIN_NAME', '<not set>')}")
    logger.info(f"Target            : {os.getenv('DNM_TARGET', '<not set>')}")

    # Create instances
    provider = ProviderFactory.get_provider(name=provider_name)
    subdomain_manager = SubdomainManager(provider=provider)
    docker_event_listener = DockerEventListener(subdomain_manager=subdomain_manager, base_url=docker_base_url)

    # Start listening for Docker events in the background until the application is running
    docker_event_listener.listen()

    # Set up signal handlers
    signal.signal(signal.SIGTERM, handle_stop_signal)
    signal.signal(signal.SIGINT, handle_stop_signal)

    # Wait for stop signal to stop the application
    stop_signal.wait()
    logger.info("Docker Event Listener stopped.")


if __name__ == "__main__":
    main()