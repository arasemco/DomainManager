import os

from src.docker_handler.listener.listener import DockerEventListener

try:
    import dotenv  # NOQA
    if os.getenv('ENV') != 'production':
        dotenv.load_dotenv()
except ImportError:
    pass


def main():
    docker_base_url = os.getenv('DOCKER_BASE_URL', 'unix://var/run/docker_handler.sock')
    print(docker_base_url)

    domain_name = os.getenv('DOMAIN_NAME')
    target = os.getenv('TARGET', domain_name)
    provider = os.getenv('PROVIDER', 'OVH').upper()

    if not domain_name:
        print("Environment variable DOMAIN_NAME is required.")
        raise SystemExit(1)

    domain_manager = create_domain_manager(provider, domain_name, target)
    docker_event_listener = DockerEventListener(domain_manager=domain_manager, base_url=docker_base_url)
    docker_event_listener.listen_for_events()


def create_domain_manager(provider, domain_name, target):
    if provider == 'OVH':
        from src.domain.manager.ovh import OVHDomainManager
        return OVHDomainManager(
            domain=domain_name,
            target=target,
            application_credential={
                'application_key': os.getenv('APPLICATION_KEY'),
                'application_secret': os.getenv('APPLICATION_SECRET'),
                'consumer_key': os.getenv('CONSUMER_KEY'),
            }
        )

    else:
        print(f"Unsupported provider: {provider}")
        raise SystemExit(1)


if __name__ == '__main__':
    main()