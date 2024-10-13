import docker
import docker.errors
from src.utils.logger import logger
from src.domain.manager.base import DomainManager


class DockerEventListener:
    def __init__(self, domain_manager: DomainManager, base_url: str = 'unix://var/run/docker.sock'):
        self.domain_manager = domain_manager
        self.docker_client = docker.DockerClient(base_url=base_url)

    def listen_for_events(self):
        retry_attempts = 3
        for _ in range(retry_attempts):
            try:
                for event in self.docker_client.events(filters={"event": ["create", "destroy"]}, decode=True):
                    if event['Type'] == 'container' and 'Action' in event:
                        self._handle_container_event(event)
            except docker.errors.APIError as e:
                logger.error(f"Docker API error: {str(e)}")

    def _handle_container_event(self, event):
        container_name = event['Actor']['Attributes'].get('name', '')
        container_hostname = event['Actor']['Attributes'].get('hostname', '')
        subdomain = self._extract_subdomain(container_hostname, event)

        logger.info(f"{event['Action']:8} {'*'*32}")
        logger.info({
            'Action': event.get('Action'),
            'Container name': container_name,
            'Subdomain ': subdomain,
        })

        if subdomain:
            if event['Action'] == 'create':
                self._create_subdomain(container_name, subdomain)
            elif event['Action'] == 'destroy':
                self._remove_subdomain(container_name, subdomain)
        logger.info("Event handling complete\n")

    def _create_subdomain(self, container_name, subdomain):
        logger.info(f"Container {container_name} started. Creating subdomain {subdomain}.{self.domain_manager.domain}.")
        self.domain_manager.create_subdomain(subdomain)

    def _remove_subdomain(self, container_name, subdomain):
        logger.info(f"Container {container_name} stopped. Removing subdomain {subdomain}.{self.domain_manager.domain}.")
        self.domain_manager.remove_subdomain(subdomain)

    def _extract_subdomain(self, container_hostname, event):
        subdomain = self.domain_manager.extract_subdomain(container_hostname)

        label_rule = event['Actor']['Attributes'].get('traefik.http.routers.web.rule', '')
        if label_rule and label_rule.startswith('Host('):
            subdomain = label_rule.split('`')[1].split(f".{self.domain_manager.domain}")[0]

        return subdomain if subdomain else None
