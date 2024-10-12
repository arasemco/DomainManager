import os
import sys

import ovh
import docker
import pandas as pd


class DomainManager:
    def __init__(self, domain, target, field_type='CNAME'):
        self.domain = domain
        self.target = target
        self.field_type = field_type

        self.domain_parts = self.domain.split('.')
        self.domain_length = len(self.domain_parts)

    def get_record(self, record: str = None):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def create_subdomain(self, subdomain, ttl=0):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def remove_subdomain(self, subdomain):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def handle_api_error(self, action, full_domain, error):
        print(f"[{type(self).__name__}] Failed to {action} subdomain {full_domain}: {str(error)}")

    def extract_subdomain(self, full_domain):
        full_domain_parts = full_domain.split('.')
        if full_domain_parts[-self.domain_length:] == self.domain_parts:
            return '.'.join(full_domain_parts[:-self.domain_length])
        elif len(full_domain_parts) == 1:
            return full_domain
        return None


class OVHDomainManager(DomainManager):
    def __init__(self, domain, target, application_credential, field_type='CNAME'):
        super().__init__(domain, target, field_type)
        self.client = ovh.Client(
            endpoint='ovh-eu',  # Change this to 'ovh-us' or your appropriate region if needed
            **application_credential
        )
        self._validate_domain()

    def _validate_domain(self):
        try:
            self.zone = self.client.get(f"/domain/zone/{self.domain}")
        except ovh.exceptions.ResourceNotFoundError:
            domains = self.client.get(f"/domain/zone")
            raise TypeError(f"The domain '{self.domain}' does not exist! Available domains: {domains}")

    def create_subdomain(self, subdomain, ttl=0):
        full_domain = f"{subdomain}.{self.domain}"
        try:
            response = self.client.post(
                f'/domain/zone/{self.domain}/record',
                fieldType=self.field_type,
                subDomain=subdomain,
                target=self.target,
                ttl=ttl
            )
            print(f"Subdomain {full_domain} created: {response}")
        except ovh.exceptions.APIError as e:
            self.handle_api_error("create", full_domain, e)

    def remove_subdomain(self, subdomain):
        full_domain = f"{subdomain}.{self.domain}"
        try:
            records = self.client.get(
                f'/domain/zone/{self.domain}/record',
                fieldType=self.field_type,
                subDomain=subdomain
            )
            for record in records:
                self.client.delete(f'/domain/zone/{self.domain}/record/{record}')
            print(f"Subdomain {full_domain} removed: {records}")
        except ovh.exceptions.APIError as e:
            self.handle_api_error("remove", full_domain, e)


class DockerEventListener:
    def __init__(self, domain_manager: DomainManager, base_url: str = 'unix://var/run/docker.sock'):
        self.domain_manager = domain_manager
        self.docker_client = docker.DockerClient(base_url=base_url)

    def listen_for_events(self):
        for event in self.docker_client.events(filters={"event": ["create", "destroy"]}, decode=True):
            if event['Type'] == 'container' and 'Action' in event:
                self._handle_container_event(event)

    def _handle_container_event(self, event):
        container_name = event['Actor']['Attributes'].get('name', '')
        subdomain = self._extract_subdomain(container_name, event)

        print(f"{event['Action']:8} {'*'*32}")
        print(pd.Series(data={
            'Action': event.get('Action'),
            'Container name': container_name,
            'Subdomain ': subdomain,
        }))

        if subdomain:
            if event['Action'] == 'create':
                self._create_subdomain(container_name, subdomain)
            elif event['Action'] == 'destroy':
                self._remove_subdomain(container_name, subdomain)
        print()

    def _create_subdomain(self, container_name, subdomain):
        print(f"Container {container_name} started. Creating subdomain {subdomain}.{self.domain_manager.domain}.")
        self.domain_manager.create_subdomain(subdomain)

    def _remove_subdomain(self, container_name, subdomain):
        print(f"Container {container_name} stopped. Removing subdomain {subdomain}.{self.domain_manager.domain}.")
        self.domain_manager.remove_subdomain(subdomain)

    def _extract_subdomain(self, container_hostname, event):
        subdomain = self.domain_manager.extract_subdomain(container_hostname)

        label_rule = event['Actor']['Attributes'].get('traefik.http.routers.web.rule', '')
        if label_rule.startswith('Host('):
            subdomain = label_rule.split('`')[1].split(f".{self.domain_manager.domain}")[0]

        return subdomain if subdomain else None


def main():
    domain_name = os.getenv('DOMAIN_NAME')
    target = os.getenv('TARGET', domain_name)
    provider = os.getenv('PROVIDER', 'OVH').upper()

    if not domain_name:
        print("Environment variable DOMAIN_NAME is required.")
        sys.exit(1)

    domain_manager = create_domain_manager(provider, domain_name, target)
    docker_event_listener = DockerEventListener(domain_manager=domain_manager, base_url='tcp://0.0.0.0:2375')
    docker_event_listener.listen_for_events()


def create_domain_manager(provider, domain_name, target):
    if provider == 'OVH':
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
        sys.exit(1)


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    main()
