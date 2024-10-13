import os

from src.docker_handler.listener.listener import DockerEventListener
from src.utils.logger import logger

try:
    import dotenv  # NOQA
    if os.getenv('DNM_ENV') != 'production':
        dotenv.load_dotenv()
except ImportError:
    logger.warning("dotenv is not installed. Skipping environment variable loading.")


def main():
    docker_base_url = os.getenv('DNM_DOCKER_BASE_URL', 'unix://var/run/docker.sock')
    domain_name = os.getenv('DNM_DOMAIN_NAME')
    target = os.getenv('DNM_TARGET', domain_name)
    provider = os.getenv('DNM_PROVIDER', 'OVH').upper()

    if not domain_name:
        logger.error("Environment variable DNM_DOMAIN_NAME is required.")
        raise SystemExit(1)

    domain_manager = create_domain_manager(provider, domain_name, target)
    docker_event_listener = DockerEventListener(domain_manager=domain_manager, base_url=docker_base_url)

    logger.info(f"""
Base docker url : {docker_base_url}
Provider        : {provider}
Domain name     : {domain_name}
Target          : {target}

Domain manager  : {type(domain_manager).__name__}
    """)

    docker_event_listener.listen_for_events()


def create_domain_manager(provider, domain_name, target):
    if provider == 'OVH':
        from src.domain.manager.ovh_handler import OVHDomainManager
        return OVHDomainManager(
            domain=domain_name,
            target=target,
            application_credential={
                'application_key': os.getenv('DNM_OVH_APPLICATION_KEY'),
                'application_secret': os.getenv('DNM_OVH_APPLICATION_SECRET'),
                'consumer_key': os.getenv('DNM_OVH_CONSUMER_KEY'),
            }
        )

    elif provider == 'CLOUDFLARE':
        from src.domain.manager.cloudflare_handler import CloudflareDomainManager
        return CloudflareDomainManager(
            api_key=os.getenv('DNM_CLOUDFLARE_API_TOKEN'),
            domain=domain_name,
            target=target,
        )

    else:
        logger.error(f"Unsupported provider: {provider}")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
