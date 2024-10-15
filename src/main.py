import os
import re
import ovh
import docker
import requests

from abc import ABC, abstractmethod


def extract_subdomain(full_domain, base_domain):
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


class SubdomainProvider(ABC):
    def __init__(self, domain_name: str, target: str):
        self.domain_name = domain_name
        self.target = target

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

    def add_subdomain(self, subdomain: str):
        try:
            self.client.post(f'/domain/zone/{self.domain_name}/record',
                             fieldType='CNAME',
                             subDomain=subdomain,
                             target=self.target,
                             ttl=3600)
            print(f"Successfully added subdomain '{subdomain}' to OVH for domain '{self.domain_name}' with target '{self.target}'.")
        except ovh.exceptions.APIError as e:
            print(f"Failed to add subdomain '{subdomain}': {e}")

    def remove_subdomain(self, subdomain: str):
        try:
            records = self.client.get(f'/domain/zone/{self.domain_name}/record',
                                      fieldType='CNAME',
                                      subDomain=subdomain)
            for record_id in records:
                self.client.delete(f'/domain/zone/{self.domain_name}/record/{record_id}')
            print(f"Successfully removed subdomain '{subdomain}' from OVH for domain '{self.domain_name}'.")
        except ovh.exceptions.APIError as e:
            print(f"Failed to remove subdomain '{subdomain}': {e}")


class CloudflareProvider(SubdomainProvider):
    def __init__(self, api_key, domain_name, target):
        super().__init__(domain_name=domain_name, target=target)
        self.base_url = "https://api.cloudflare.com/client/v4"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def add_subdomain(self, subdomain: str):
        try:
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
            print(f"Successfully added subdomain '{subdomain}' to Cloudflare for domain '{self.domain_name}' with target '{self.target}'.")
        except requests.RequestException as e:
            print(f"Failed to add subdomain '{subdomain}': {e}")

    def remove_subdomain(self, subdomain: str):
        try:
            zone_id = self._get_zone_id()
            record_id = self._get_record_id(zone_id, subdomain)
            if record_id:
                url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"
                response = self._session.delete(url)
                response.raise_for_status()
                print(f"Successfully removed subdomain '{subdomain}' from Cloudflare for domain '{self.domain_name}'.")
            else:
                print(f"Subdomain '{subdomain}' not found for removal.")
        except requests.RequestException as e:
            print(f"Failed to remove subdomain '{subdomain}': {e}")

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


class SubdomainProviderFactory:
    @staticmethod
    def get_provider(provider_name: str) -> SubdomainProvider:
        domain_name = os.getenv('DNM_DOMAIN_NAME')
        target = os.getenv('DNM_TARGET', domain_name)

        if provider_name == 'OVH':
            consumer_key = os.getenv('DNM_OVH_CONSUMER_KEY')
            application_key = os.getenv('DNM_OVH_APPLICATION_KEY')
            application_secret = os.getenv('DNM_OVH_APPLICATION_SECRET')
            return OVHProvider(application_key, application_secret, consumer_key, domain_name, target)

        elif provider_name == 'CLOUDFLARE':
            api_key = os.getenv('DNM_CLOUDFLARE_API_TOKEN')
            return CloudflareProvider(api_key, domain_name, target)

        else:
            raise ValueError(f"Provider '{provider_name}' is not supported.")


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
        for event in self.docker_client.events(decode=True):
            if event['Type'] == 'container' and event['Action'] in ['create', 'destroy']:
                labels = event['Actor']['Attributes']
                rule_label = labels.get('traefik.http.routers.web.rule', None)
                if rule_label:
                    match = re.search(r"Host\(`(.+?)`\)", rule_label)
                    if match:
                        full_domain = match.group(1)
                        if event['Action'] == 'create':
                            self.subdomain_manager.add_subdomain(full_domain)
                        elif event['Action'] == 'destroy':
                            self.subdomain_manager.remove_subdomain(full_domain)


def main_test():
    provider = ['OVH', 'CLOUDFLARE'][0]
    provider = SubdomainProviderFactory.get_provider(provider)
    manager = SubdomainManager(provider)

    subdomain = 'test'
    manager.add_subdomain(subdomain)
    manager.remove_subdomain(subdomain)


def main():
    # Select provider based on environment variable
    provider = os.getenv('DNM_PROVIDER', 'OVH').upper()
    docker_base_url = os.getenv('DNM_DOCKER_BASE_URL', 'unix://var/run/docker.sock')

    provider = SubdomainProviderFactory.get_provider(provider_name=provider)
    manager = SubdomainManager(provider=provider)

    # Start Docker Event Listener
    listener = DockerEventListener(subdomain_manager=manager, base_url=docker_base_url)
    listener.listen()


if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv()
    main()
    # main_test()
