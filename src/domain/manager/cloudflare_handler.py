import requests
from src.utils.logger import logger
from src.domain.manager.base import DomainManager


class CloudflareDomainManager(DomainManager):
    def __init__(self, api_key, domain, target, field_type='CNAME', endpoint="https://api.cloudflare.com/client/v4"):
        super().__init__(domain, target, field_type)
        self.api_key = api_key
        self.endpoint = endpoint

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

        self.zone_id = self._get_zone_id()

    def _get_zone_id(self):
        try:
            zones = self.get("zones")
            for zone in zones:
                if zone["name"] == self.domain:
                    logger.info(f"Zone ID for domain {self.domain} found: {zone['id']}")
                    return zone["id"]
            logger.error(f"Zone {self.domain} not found")
            raise Exception(f"Zone {self.domain} not found")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch zone ID for domain {self.domain}: {e}")
            raise

    def get(self, url):
        try:
            response = self.session.get(f'{self.endpoint}/{url}')
            response.raise_for_status()
            logger.info(f"GET request to {url} successful")
            return response.json().get("result", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request to {url} failed: {e}")
            raise

    def create_subdomain(self, subdomain, ttl=0):
        url = f"{self.endpoint}/zones/{self.zone_id}/dns_records"
        data = {
            "type": self.field_type,
            "name": subdomain,
            "content": self.target,
            "ttl": ttl,
            "proxied": True
        }
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            logger.info(f"Subdomain {subdomain}.{self.domain} created successfully")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create subdomain {subdomain}.{self.domain}: {e}")
            raise

    def remove_subdomain(self, subdomain):
        try:
            records = self.get(f"zones/{self.zone_id}/dns_records")
            for record in records:
                if record["name"] == f"{subdomain}.{self.domain}":
                    delete_url = f"{self.endpoint}/zones/{self.zone_id}/dns_records/{record['id']}"
                    delete_response = self.session.delete(delete_url)
                    delete_response.raise_for_status()
                    logger.info(f"Subdomain {subdomain}.{self.domain} removed successfully")
                    return delete_response.json()
            logger.error(f"Subdomain {subdomain}.{self.domain} not found")
            return {"error": "Subdomain not found"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to remove subdomain {subdomain}.{self.domain}: {e}")
            raise
