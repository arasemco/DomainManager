import os
import time

import dotenv

from src.managers import ProviderFactory, SubdomainManager, DockerEventListener
from src.utils.logger import logger


def welcome():
    logger.info(f"Welcome to Domain Manager!")
    logger.info(f"Provider          : {provider_name}")
    logger.info(f"Docker Base URL   : {docker_base_url}")
    logger.info(f"Domain Name       : {os.getenv('DNM_DOMAIN_NAME', '<not set>')}")
    logger.info(f"Target            : {os.getenv('DNM_TARGET', '<not set>')}")


## Load environment variables
dotenv.load_dotenv()
provider_name = os.getenv('DNM_PROVIDER', 'OVH')
docker_base_url = os.getenv('DNM_DOCKER_BASE_URL', 'unix://var/run/docker.sock')
welcome()

## Create instances
provider = ProviderFactory.get_provider(name=provider_name)
subdomain_manager = SubdomainManager(provider=provider)
docker_event_listener = DockerEventListener(subdomain_manager=subdomain_manager, base_url=docker_base_url)

# Start listen for docker events in background until the application is running
docker_event_listener.listen()


## Wait for stop signal of CTL + C to stop the application
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Docker Event Listener stopped.")
