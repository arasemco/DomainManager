import os
import re
import ovh
import time
import docker
import random
import requests
import functools
import validators
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, AnyStr, Type
from threading import Thread


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('domain_manager')


# Custom Exception Classes
class InvalidDomainException(Exception):
    """Custom exception to indicate an invalid domain name."""
    pass


# Utility Functions
def validate_domain(name: str):
    if not validators.domain(name):
        raise InvalidDomainException(f"The domain name '{name}' is not valid.")
    return name


def extract_subdomain(full_domain: str, base_domain: str) -> Optional[str]:
    if not validators.hostname(full_domain) or not validators.hostname(base_domain):
        return None

    full_domain_parts = full_domain.split('.')
    base_domain_parts = base_domain.split('.')

    if full_domain_parts[-len(base_domain_parts):] == base_domain_parts:
        subdomain_parts = full_domain_parts[:-len(base_domain_parts)]
        return '.'.join(subdomain_parts) if subdomain_parts else None

    elif len(full_domain_parts) == 1:
        return full_domain

    return None


# Decorators
def handle_api_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ovh.exceptions.APIError, requests.RequestException) as exception:
            response = getattr(exception, 'response', None)
            if hasattr(response, 'status_code') and hasattr(response, 'url'):
                logger.error(f"API Error {response.status_code}: {response.url}")
            else:
                logger.error(f"Unexpected Error: {exception}")
    return wrapper


# Abstract Base Classes
class SubdomainProvider(ABC):
    name: str
    keys: List[AnyStr]
    details: List[AnyStr] = ['domain_name', 'target']

    def __init__(self, domain_name: str, target: str):
        self.domain_name = validate_domain(domain_name)
        self.target = validate_domain(target)

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.name = cls.__name__.replace('Provider', '')
        ProviderFactory.register_provider(cls.name.upper(), cls)

    @abstractmethod
    def add_subdomain(self, subdomain: str):
        pass

    @abstractmethod
    def remove_subdomain(self, subdomain: str):
        pass

    def _log_action(self, action: str, subdomain: str):
        logger.info(f"{action} subdomain '{subdomain}' on '{self.name}' for domain '{self.domain_name}' with target '{self.target}'.")


# Environment Handler
class EnvironmentManager:
    @staticmethod
    def _get_variables(prefix: str, variables: list, message: str = "required environment variables") -> Dict[str, str]:
        result = {}
        for var in variables:
            result[var] = os.getenv(key=f'{prefix}_{var}'.upper(), default=None)

        missing = [key for key, value in result.items() if not value]
        if missing:
            formatted_missing = ', '.join(missing)
            formatted_pattern = '\n'.join([f'{prefix}_{key}'.upper() for key in missing])
            raise ValueError(
                f"Missing {message}: {formatted_missing}.\n"
                f"Please ensure you set the environment variables as shown below:\n{formatted_pattern}"
            )
        return result

    @classmethod
    def get_provider_keys(cls, provider: Type[SubdomainProvider]) -> Dict[str, str]:
        return cls._get_variables(
            prefix=f'DNM_{provider.__name__.replace("Provider", "").upper()}',
            variables=provider.keys,
            message=f"API keys for provider '{provider.name}'"
        )

    @classmethod
    def get_provider_details(cls, provider: Type[SubdomainProvider]) -> Dict[str, str]:
        return cls._get_variables(
            prefix='DNM',
            variables=provider.details,
            message="domain details"
        )

    @classmethod
    def get_docker_configuration(cls, variables: List[AnyStr]) -> Dict[str, str]:
        return cls._get_variables(
            prefix='DNM_DOCKER',
            variables=variables,
            message="Docker configuration"
        )


class ProviderFactory:
    _providers: Dict[str, type[SubdomainProvider]] = {}

    @classmethod
    def register_provider(cls, name: str, provider_cls):
        cls._providers[name.upper()] = provider_cls

    @classmethod
    def get_provider(cls, name) -> SubdomainProvider:
        provider_cls = cls._providers.get(name.upper())
        if not provider_cls:
            raise ValueError(f"Provider '{name}' is not registered.")

        keys = EnvironmentManager.get_provider_keys(provider_cls)
        domain_details = EnvironmentManager.get_provider_details(provider_cls)
        return provider_cls(**domain_details, **keys)


# Concrete Providers
class OVHProvider(SubdomainProvider):
    keys = ['application_key', 'application_secret', 'consumer_key']

    def __init__(self, application_key, application_secret, consumer_key, domain_name, target):
        super().__init__(domain_name, target)
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
        self._log_action(action="Added", subdomain=subdomain)

    @handle_api_errors
    def remove_subdomain(self, subdomain: str):
        records = self.client.get(f'/domain/zone/{self.domain_name}/record',
                                  fieldType='CNAME',
                                  subDomain=subdomain)
        for record_id in records:
            delay = random.uniform(0.1, 0.5)
            self.client.delete(f'/domain/zone/{self.domain_name}/record/{record_id}')
            time.sleep(delay)
        self._log_action(action="Removed", subdomain=subdomain)


class CloudflareProvider(SubdomainProvider):
    keys = ['api_token']

    def __init__(self, api_token, domain_name, target):
        super().__init__(domain_name, target)
        self.base_url = "https://api.cloudflare.com/client/v4"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_token}",
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
        response.raise_for_status()
        self._log_action(action="Added", subdomain=subdomain)

    @handle_api_errors
    def remove_subdomain(self, subdomain: str):
        zone_id = self._get_zone_id()
        record_id = self._get_record_id(zone_id, subdomain)
        if record_id:
            url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"
            response = self._session.delete(url)
            response.raise_for_status()
            self._log_action(action="Removed", subdomain=subdomain)

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


# Subdomain Manager
class SubdomainManager:
    def __init__(self, provider: SubdomainProvider):
        self.provider = provider

    def add_subdomain(self, full_domain: str):
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            self.provider.add_subdomain(subdomain)
        else:
            logger.error(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")

    def remove_subdomain(self, full_domain: str):
        subdomain = extract_subdomain(full_domain, self.provider.domain_name)
        if subdomain:
            self.provider.remove_subdomain(subdomain)
        else:
            logger.error(f"Invalid subdomain '{full_domain}' for domain '{self.provider.domain_name}'.")


# Event Listener Interface
class EventListener(ABC):
    @abstractmethod
    def listen(self):
        pass


# Docker Event Listener
class DockerEventListener(EventListener):
    def __init__(self, subdomain_manager: SubdomainManager, base_url: str = 'unix://var/run/docker.sock'):
        self.subdomain_manager = subdomain_manager
        self.docker_client = docker.DockerClient(base_url=base_url)

    def listen(self):
        listening_thread = Thread(target=self._event_listener, daemon=True)
        listening_thread.start()
        return listening_thread

    def _event_listener(self):
        try:
            for event in self.docker_client.events(decode=True, filters={'type': 'container'}):
                self._handle_event(event)
        except Exception as e:
            logger.error(f"Error while listening to Docker events: {e}")

    def _handle_event(self, event):
        action_mapping = {
            'create': self.subdomain_manager.add_subdomain,
            'destroy': self.subdomain_manager.remove_subdomain
        }

        action = event['Action']
        labels = event['Actor']['Attributes']
        rule_label = labels.get('traefik.http.routers.web.rule', None)

        if rule_label and action in action_mapping:
            match = re.search(r"Host\(`(.+?)`\)", rule_label)
            if match:
                action_mapping[action](match.group(1))


# Event Manager
class EventManager:
    def __init__(self, listeners: List[EventListener]):
        self.listeners = listeners

    def start_listening(self):
        for listener in self.listeners:
            listener.listen()


# Main Functionality
def main():
    provider_name = os.getenv('DNM_PROVIDER', 'OVH')
    docker_base_url = os.getenv('DNM_DOCKER_BASE_URL', 'unix://var/run/docker.sock')

    provider = ProviderFactory.get_provider(provider_name)
    manager = SubdomainManager(provider=provider)

    # Using EventManager for managing all listeners
    docker_listener = DockerEventListener(subdomain_manager=manager, base_url=docker_base_url)

    event_manager = EventManager(listeners=[docker_listener])
    event_manager.start_listening()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Docker Event Listener stopped.")


def main_test():
    provider = ['OVH', 'CLOUDFLARE'][0]
    provider = ProviderFactory.get_provider(provider)
    manager = SubdomainManager(provider)

    subdomain = 'test'
    manager.add_subdomain(subdomain)
    manager.remove_subdomain(subdomain)


if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv()
    # main_test()
    main()
