import requests

from src.utils.logger import logger
from src.utils.decorators import handle_api_errors
from src.providers.abstract import SubdomainProvider


class CloudflareProvider(SubdomainProvider):
    keys = ('api_token', )

    def __init__(self, api_token, domain_name, target):
        logger.debug(f"Initializing CloudflareProvider with domain: {domain_name} and target: {target}")
        super().__init__(domain_name, target)
        self.base_url = "https://api.cloudflare.com/client/v4"
        self._api_token = api_token
        self._session = requests.Session()
        self.authenticate()
        logger.info(f"CloudflareProvider initialized for domain: {domain_name}")

    def authenticate(self):
        logger.debug(f"Authenticating Cloudflare provider for domain: {self.domain_name}")
        self._session.headers.update({
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json"
        })
        logger.info("Cloudflare provider authenticated successfully.")

    @handle_api_errors
    def add_subdomain(self, subdomain: str):
        logger.debug(f"Attempting to add subdomain: {subdomain} to domain: {self.domain_name}")
        try:
            zone_id = self._get_zone_id()
            logger.debug(f"Zone ID for domain '{self.domain_name}' is {zone_id}")
            url = f"{self.base_url}/zones/{zone_id}/dns_records"
            data = {
                "type": "CNAME",
                "name": f"{subdomain}.{self.domain_name}",
                "content": self.target,
                "ttl": 3600,
                "proxied": False
            }
            logger.debug(f"Sending POST request to URL: {url} with data: {data}")
            response = self._session.post(url, json=data)
            response.raise_for_status()
            logger.info(f"Successfully added subdomain: {subdomain} to domain: {self.domain_name}")
            self._log_action(action="Added", subdomain=subdomain)
        except requests.RequestException as e:
            logger.error(f"Failed to add subdomain '{subdomain}' to domain '{self.domain_name}': {e}")

    @handle_api_errors
    def remove_subdomain(self, subdomain: str):
        logger.debug(f"Attempting to remove subdomain: {subdomain} from domain: {self.domain_name}")
        try:
            zone_id = self._get_zone_id()
            logger.debug(f"Zone ID for domain '{self.domain_name}' is {zone_id}")
            record_id = self._get_record_id(zone_id, subdomain)
            if record_id:
                logger.debug(f"Record ID for subdomain '{subdomain}' is {record_id}")
                url = f"{self.base_url}/zones/{zone_id}/dns_records/{record_id}"
                logger.debug(f"Sending DELETE request to URL: {url}")
                response = self._session.delete(url)
                response.raise_for_status()
                logger.info(f"Successfully removed subdomain: {subdomain} from domain: {self.domain_name}")
                self._log_action(action="Removed", subdomain=subdomain)
            else:
                logger.error(f"Record ID for subdomain '{subdomain}' not found in domain '{self.domain_name}'")
        except requests.RequestException as e:
            logger.error(f"Failed to remove subdomain '{subdomain}' from domain '{self.domain_name}': {e}")

    def _get_zone_id(self):
        logger.debug(f"Fetching zone ID for domain: {self.domain_name}")
        url = f"{self.base_url}/zones"
        params = {"name": self.domain_name}
        logger.debug(f"Sending GET request to URL: {url} with params: {params}")
        response = self._session.get(url, params=params)
        response.raise_for_status()
        zones = response.json().get("result", [])
        if zones:
            zone_id = zones[0]["id"]
            logger.debug(f"Zone ID for domain '{self.domain_name}': {zone_id}")
            return zone_id
        logger.error(f"Zone ID for domain '{self.domain_name}' not found.")
        raise ValueError(f"Zone ID for domain '{self.domain_name}' not found.")

    def _get_record_id(self, zone_id, subdomain):
        logger.debug(f"Fetching record ID for subdomain: {subdomain} in zone: {zone_id}")
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        params = {"type": "CNAME", "name": f"{subdomain}.{self.domain_name}"}
        logger.debug(f"Sending GET request to URL: {url} with params: {params}")
        response = self._session.get(url, params=params)
        response.raise_for_status()
        records = response.json().get("result", [])
        if records:
            record_id = records[0]["id"]
            logger.debug(f"Record ID for subdomain '{subdomain}': {record_id}")
            return record_id
        logger.error(f"Record ID for subdomain '{subdomain}' not found in domain '{self.domain_name}'")
        return None
