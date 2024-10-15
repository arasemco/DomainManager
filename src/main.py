import os
import re
import ovh
import time
import docker
import random
import requests
import functools
import validators

from abc import ABC, abstractmethod
from typing import Optional
from threading import Thread


class InvalidDomainException(Exception):
    """Custom exception to indicate an invalid domain name."""
    pass


def validate_domain(name: str):
    if not validators.domain(name):
        raise InvalidDomainException(f"The domain name '{name}' is not valid.")
    return name


def extract_subdomain(full_domain: str, base_domain: str) -> Optional[str]:
    if not validators.hostname(full_domain) or not validators.hostname(base_domain):
        return None

    # Split the domains into parts
    full_domain_parts = [part for part in full_domain.split('.') if part != '']
    base_domain_parts = [part for part in base_domain.split('.') if part != '']

    # Check if the full domain ends with the base domain
    if full_domain_parts[-len(base_domain_parts):] == base_domain_parts:
        # Extract the subdomain parts
        subdomain_parts = full_domain_parts[:-len(base_domain_parts)]
        return '.'.join(subdomain_parts) if subdomain_parts else None

    elif len(full_domain_parts) == 1:
        return full_domain

    return None


def handle_api_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ovh.exceptions.APIError, requests.RequestException) as exception:
            # Handle exceptions that have response attributes
            status_code = {
                400: "Bad Request:",
                401: "Unauthorized:",
                403: "Forbidden:",
                404: "Not Found:",
                500: "Internal Server Error:",
            }
            response = getattr(exception, 'response', None)

            if hasattr(response, 'status_code') and hasattr(response, 'url'):
                print(status_code.get(response.status_code, "Unexpected API Error:"), response.url)
            else:
                print("Unexpected Error: No response object available.")

            # Print the exception details and the traceback
            print(f"An exception of type '{type(exception).__name__}' occurred: {exception}")

    return wrapper


class SubdomainProvider(ABC):
    _providers = {}

    def __init_subclass__(cls, *args, **kwargs):
        cls._providers[cls.__name__.replace('Provider', '').upper()] = cls

    @classmethod
    def get_provider(cls, name, *args, **kwargs) -> 'SubdomainProvider':
        provider_cls = cls._providers.get(name)
        if not provider_cls:
            raise ValueError(f"Provider '{name}' is not registered.")
        return provider_cls(*args, **kwargs)

    def __init__(self, domain_name: str, target: str):
        self.domain_name = validate_domain(domain_name)
        self.target = validate_domain(target)

    @abstractmethod
    def add_subdomain(self, subdomain: str):
        pass

    @abstractmethod
    def remove_subdomain(self, subdomain: str):
        pass


class OVHProvider(SubdomainProvider):
    def __init__(self, application_key, application_secret, consumer_key, domain_name, target):
        super().__init__(domain_name=domain_name, target=target)
        self.client = ovh.Client(
            endpoint='ovh-eu',
            application_key=application_key,
            application_secret=application_secret,
            consumer_key=consumer_key
        )

    @handle_api_errors
    def add_subdomain(self, subdomain: str):
        self.client.post(f'/domain/zone/{self.domain_name}/record',
                         fieldType='CNAME',
                         subDomain=subdomain,
                         target=self.target,
                         ttl=3600)
        print(f"Successfully added subdomain '{subdomain}' to OVH for domain '{self.domain_name}' with target '{self.target}'.")

    @handle_api_errors
    def remove_subdomain(self, subdomain: str):
        records = self.client.get(f'/domain/zone/{self.domain_name}/record',
                                  fieldType='CNAME',
                                  subDomain=subdomain)
        for record_id in records:
            # Adding exponential backoff to avoid overwhelming the API
            delay = random.uniform(0.1, 0.5)
            self.client.delete(f'/domain/zone/{self.domain_name}/record/{record_id}')
            time.sleep(delay)
        print(f"Successfully removed subdomain '{subdomain}' from OVH for domain '{self.domain_name}'.")


class CloudflareProvider(SubdomainProvider):
    def __init__(self, api_key, domain_name, target):
        super().__init__(domain_name=domain_name, target=target)
        self.base_url = "https://api.cloudflare.com/client/v4"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    @handle_api_errors
    def add_subdomain(self, subdomain: str):
        zone_id = self._get_zone_id()
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        data = {
            "type": "CNAME",
            "name": f"{subdomain}.{self.domain_name}",
            "content": self.target,
            "ttl": 3600,
            "proxied": False
        }
        response = self._session.post(url, json=data)
        if response.status_code >= 400:
            print(f"HTTP Error {response.status_code}: {response.text}")
        response.raise_for_status()
        print(f"Successfully added subdomain '{subdomain}' to Cloudflare for domain '{self.domain_name}' with target '{self.target}'.")

    @handle_api_errors
    def remove_subdomain(self, subdomain: str):
        zone_id = self._get_zone_id()
        record_id = self._get_record_id(zone_id, subdomain)
        if record_id:
            url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"
            response = self._session.delete(url)
            response.raise_for_status()
            print(f"Successfully removed subdomain '{subdomain}' from Cloudflare for domain '{self.domain_name}'.")
        else:
            print(f"Subdomain '{subdomain}' not found for removal.")

    def _get_zone_id(self):
        url = f"{self.base_url}/zones"
        params = {"name": self.domain_name}
        response = self._session.get(url, params=params)
        response.raise_for_status()
        zones = response.json().get("result", [])
        if zones:
            return zones[0]["id"]
        raise ValueError(f"Zone ID for domain '{self.domain_name}' not found.")

    def _get_record_id(self, zone_id, subdomain):
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        params = {"type": "CNAME", "name": f"{subdomain}.{self.domain_name}"}
        response = self._session.get(url, params=params)
        response.raise_for_status()
        records = response.json().get("result", [])
        if records:
            return records[0]["id"]
        return None


class SubdomainManager:
    def __init__(self, provider: SubdomainProvider):
        self.provider = provider

    def add_subdomain(self, full_domain: str):
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            self.provider.add_subdomain(subdomain)
        else:
            print(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")

    def remove_subdomain(self, full_domain: str):
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            self.provider.remove_subdomain(subdomain)
        else:
            print(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")


class DockerEventListener:
    def __init__(self, subdomain_manager: SubdomainManager, base_url: str = 'unix://var/run/docker.sock'):
        self.subdomain_manager = subdomain_manager
        self.docker_client = docker.DockerClient(base_url=base_url)

    def listen(self):
        action_mapping = {
            'create': self.subdomain_manager.add_subdomain,
            'destroy': self.subdomain_manager.remove_subdomain
        }

        def event_listener():
            try:
                for event in self.docker_client.events(decode=True, filters={'type': 'container'}):
                    action = event['Action']
                    labels = event['Actor']['Attributes']
                    rule_label = labels.get('traefik.http.routers.web.rule', None)
                    if rule_label and action in action_mapping:
                        match = re.search(r"Host\(`(.+?)`\)", rule_label)
                        if match:
                            action_mapping[action](match.group(1))
            except Exception as e:
                print(f"Error while listening to Docker events: {e}")

        listening_thread = Thread(target=event_listener, daemon=True)
        listening_thread.start()
        return listening_thread


def main_test():
    provider = ['OVH', 'CLOUDFLARE'][0]
    provider = SubdomainProvider.get_provider(provider, os.getenv('DNM_OVH_APPLICATION_KEY'), os.getenv('DNM_OVH_APPLICATION_SECRET'), os.getenv('DNM_OVH_CONSUMER_KEY'), os.getenv('DNM_DOMAIN_NAME'), os.getenv('DNM_TARGET'))
    manager = SubdomainManager(provider)

    subdomain = 'test'
    manager.add_subdomain(subdomain)
    manager.remove_subdomain(subdomain)


def main():
    # Select provider based on environment variable
    provider_name = os.getenv('DNM_PROVIDER', 'OVH').upper()
    docker_base_url = os.getenv('DNM_DOCKER_BASE_URL', 'unix://var/run/docker.sock')

    domain_name = os.getenv('DNM_DOMAIN_NAME')
    target = os.getenv('DNM_TARGET', domain_name)

    if provider_name == 'OVH':
        provider = SubdomainProvider.get_provider(
            provider_name, os.getenv('DNM_OVH_APPLICATION_KEY'), os.getenv('DNM_OVH_APPLICATION_SECRET'), os.getenv('DNM_OVH_CONSUMER_KEY'), domain_name, target
        )
    elif provider_name == 'CLOUDFLARE':
        provider = SubdomainProvider.get_provider(
            provider_name, os.getenv('DNM_CLOUDFLARE_API_TOKEN'), domain_name, target
        )
    else:
        raise ValueError(f"Provider '{provider_name}' is not supported.")

    manager = SubdomainManager(provider=provider)

    # Start Docker Event Listener
    listener = DockerEventListener(subdomain_manager=manager, base_url=docker_base_url)
    listener.listen()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Docker Event Listener stopped.")


if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv()
    # main()
    main_test()
