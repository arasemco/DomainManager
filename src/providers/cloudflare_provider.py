import requests

from src.providers.abstract import SubdomainProvider
from src.utils.decorators import handle_api_errors


class CloudflareProvider(SubdomainProvider):
    keys = ('api_token', )

    def __init__(self, api_token, domain_name, target):
        super().__init__(domain_name, target)
        self.base_url = "https://api.cloudflare.com/client/v4"
        self._api_token = api_token
        self._session = requests.Session()
        self.authenticate()

    def authenticate(self):
        self._session.headers.update({
            "Authorization": f"Bearer {self._api_token}",
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
